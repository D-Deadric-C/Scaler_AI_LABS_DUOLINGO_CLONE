"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { LessonAttempt } from "@/lib/types";
import { canSubmit, emptyAnswer } from "./answers";
import { playCorrect, playWrong } from "./sounds";
import type { Answer, AnswerFeedback, LessonMode, LessonResult } from "./types";

const LEGENDARY_SECONDS = 75;

/** All lesson state and server interaction; the components stay purely presentational. */
export function useLessonSession(lessonId: number, mode: LessonMode) {
  const [attempt, setAttempt] = useState<LessonAttempt | null>(null);
  const [answer, setAnswer] = useState<Answer>(emptyAnswer());
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [hearts, setHearts] = useState(5);
  const [heartsLost, setHeartsLost] = useState(0);
  const [streakRun, setStreakRun] = useState(0);
  const [result, setResult] = useState<LessonResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [outOfHearts, setOutOfHearts] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(mode === "legendary" ? LEGENDARY_SECONDS : null);
  const inFlight = useRef(false);

  const exercise = attempt?.exercises.find((item) => item.id === attempt.queue[0]);
  const total = attempt?.total_exercises ?? 0;
  const correctSoFar = feedback ? feedback.correct_count : (attempt?.correct_count ?? 0);
  const progress = result ? 100 : total ? (correctSoFar / total) * 100 : 0; // only correct answers fill the bar
  const timeUp = secondsLeft === 0 && !result;

  useEffect(() => {
    api.startAttempt(lessonId, mode)
      .then((value) => {
        setAttempt(value);
        setHearts(value.hearts);
        if (typeof value.seconds_left === "number") setSecondsLeft(value.seconds_left);
      })
      .catch((reason: Error) => setError(reason.message));
  }, [lessonId, mode]);

  // A resumed attempt that was fully answered still needs to be completed.
  useEffect(() => {
    if (!attempt || attempt.status !== "active" || attempt.queue.length > 0) return;
    let cancelled = false;
    api.complete(attempt.attempt_id)
      .then((value) => { if (!cancelled) { setResult(value); setError(""); } })
      .catch((reason: Error) => { if (!cancelled) setError(reason.message); });
    return () => { cancelled = true; };
  }, [attempt]);

  // Legendary countdown; the server enforces the same deadline.
  useEffect(() => {
    if (!attempt || secondsLeft === null || result || (feedback?.ready_to_complete ?? false) || attempt.queue.length === 0) return;
    if (secondsLeft <= 0) {
      void api.abandon(attempt.attempt_id).catch(() => undefined);
      return;
    }
    const timer = window.setTimeout(() => setSecondsLeft(secondsLeft - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [attempt, feedback?.ready_to_complete, result, secondsLeft]);

  const guarded = useCallback(async (work: () => Promise<void>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try { await work(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Something went wrong"); }
    finally { inFlight.current = false; setBusy(false); }
  }, []);

  const check = useCallback((skip = false) => {
    if (!attempt || !exercise || feedback || (!skip && !canSubmit(answer, exercise))) return;
    void guarded(async () => {
      const response = await api.answer(attempt.attempt_id, exercise.id, skip ? "" : answer);
      setFeedback(response);
      if (response.hearts < hearts) setHeartsLost((count) => count + 1);
      setHearts(response.hearts);
      setStreakRun((run) => (response.correct ? run + 1 : 0));
      if (response.correct) playCorrect(); else playWrong();
    });
  }, [answer, attempt, exercise, feedback, guarded, hearts]);

  const next = useCallback(() => {
    if (!attempt || !feedback) return;
    if (feedback.failed) { setOutOfHearts(true); return; }
    if (feedback.ready_to_complete) {
      void guarded(async () => setResult(await api.complete(attempt.attempt_id)));
      return;
    }
    setAttempt({ ...attempt, queue: feedback.queue, correct_count: feedback.correct_count, hearts }); // a wrong answer is already at the end of the queue
    setAnswer(emptyAnswer());
    setFeedback(null);
  }, [attempt, feedback, guarded, hearts]);

  const retryComplete = useCallback(() => {
    if (!attempt) return;
    setError("");
    void guarded(async () => setResult(await api.complete(attempt.attempt_id)));
  }, [attempt, guarded]);

  const abandon = useCallback(async () => {
    if (attempt) await api.abandon(attempt.attempt_id).catch(() => undefined);
  }, [attempt]);

  return { attempt, exercise, answer, setAnswer, feedback, hearts, heartsLost, streakRun, result, error, setError, busy, outOfHearts, secondsLeft, timeUp, progress, check, next, retryComplete, abandon, guarded };
}

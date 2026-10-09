"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Mascot } from "../GameIcon";
import { ExitDialog, OutOfHeartsDialog, TimeUpDialog } from "./Dialogs";
import { LessonComplete } from "./LessonComplete";
import { LessonScreen } from "./LessonScreen";
import type { LessonMode } from "./types";
import { useLessonSession } from "./useLessonSession";
import "./lesson.css";

const GEM_REFILL_COST = 350;

export function LessonPlayer({ lessonId, mode = "lesson" }: { lessonId: number; mode?: LessonMode }) {
  const router = useRouter();
  const session = useLessonSession(lessonId, mode);
  const { attempt, exercise, answer, setAnswer, feedback, check, next, error, setError } = session;
  const [exitOpen, setExitOpen] = useState(false);
  const [gems, setGems] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  useEffect(() => {
    if (session.outOfHearts) api.me().then((user) => setGems(user.gems)).catch(() => undefined);
  }, [session.outOfHearts]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(""), 2200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const leave = useCallback(async () => {
    await session.abandon();
    router.push("/learn");
  }, [router, session]);

  const refillWithGems = useCallback(async () => {
    await session.guarded(async () => {
      await api.gemRefill();
      window.location.reload();
    });
  }, [session]);

  const primaryAction = useCallback(() => {
    if (session.busy || exitOpen || session.outOfHearts || session.timeUp) return;
    if (feedback) next(); else check();
  }, [check, exitOpen, feedback, next, session.busy, session.outOfHearts, session.timeUp]);

  // Keyboard: Enter checks/continues, Escape toggles the exit prompt, 1-9 pick an option.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === "Escape") { setExitOpen((open) => !open); return; }
      if (exitOpen || session.outOfHearts || session.timeUp || session.result) return;
      if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); primaryAction(); return; }
      const typing = event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLInputElement;
      if (typing || feedback || !exercise || !/^[1-9]$/.test(event.key)) return;
      const options = exercise.payload.options as string[] | undefined;
      const choice = options?.[Number(event.key) - 1];
      if (choice && (exercise.type === "multiple_choice" || exercise.type === "fill_blank")) setAnswer(choice);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [exercise, exitOpen, feedback, primaryAction, session.outOfHearts, session.result, session.timeUp, setAnswer]);

  if (error && !attempt) {
    return <main className="lx-state"><Mascot mood="sad" /><h1>Lesson unavailable</h1><p>{error}</p><Link href="/learn" className="lx-button lx-button-primary">BACK TO PATH</Link></main>;
  }
  if (session.result) return <LessonComplete result={session.result} />;
  if (attempt && !exercise && error) {
    return <main className="lx-state"><Mascot mood="sad" /><h1>Couldn’t finish your lesson</h1><p>{error}</p><button type="button" className="lx-button lx-button-primary" onClick={session.retryComplete}>TRY AGAIN</button><Link href="/learn" className="lx-button lx-button-link">BACK TO PATH</Link></main>;
  }
  if (!attempt || !exercise) {
    return <main className="lx-state"><Mascot /><div className="loading-dots"><i /><i /><i /></div><p>{attempt ? "Finishing your lesson…" : "Preparing your lesson…"}</p></main>;
  }

  return (
    <>
      <LessonScreen
        exercise={exercise}
        exerciseIndex={attempt.correct_count}
        answer={answer}
        setAnswer={setAnswer}
        feedback={feedback}
        progress={session.progress}
        streakRun={session.streakRun}
        hearts={session.hearts}
        heartsLost={session.heartsLost}
        secondsLeft={session.secondsLeft}
        spotlight={session.outOfHearts}
        busy={session.busy}
        onClose={() => setExitOpen(true)}
        onCheck={() => check()}
        onSkip={() => check(true)}
        onContinue={next}
        onFeedbackAction={setToast}
      />
      {exitOpen ? <ExitDialog onStay={() => setExitOpen(false)} onQuit={leave} /> : null}
      {session.outOfHearts ? <OutOfHeartsDialog gems={gems} gemCost={GEM_REFILL_COST} busy={session.busy} onGems={refillWithGems} onSuper={() => setToast("Super is coming soon")} /> : null}
      {session.timeUp ? <TimeUpDialog onRetry={() => window.location.reload()} /> : null}
      {toast ? <div className="lx-toast" role="status">{toast}</div> : null}
      {error ? <div className="lx-toast error" role="alert" onAnimationEnd={() => setError("")}>{error}</div> : null}
    </>
  );
}

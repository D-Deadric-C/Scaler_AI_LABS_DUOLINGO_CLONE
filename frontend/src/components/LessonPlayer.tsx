"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Exercise, LessonAttempt } from "@/lib/types";
import { GameIcon, Mascot } from "./GameIcon";

type Answer = string | string[] | string[][];
type Feedback = { correct: boolean; explanation: string; correct_answer: unknown; ready_to_complete: boolean; failed: boolean };

function MultipleChoice({ exercise, answer, setAnswer, disabled }: ExerciseProps) {
  const options = exercise.payload.options as string[];
  return <div className="choice-grid">{options.map((option, index) => <button key={option} disabled={disabled} className={`answer-card ${answer === option ? "selected" : ""}`} onClick={() => setAnswer(option)}><span>{option}</span><kbd>{index + 1}</kbd></button>)}</div>;
}

function WordBank({ exercise, answer, setAnswer, disabled }: ExerciseProps) {
  const selected = Array.isArray(answer) ? answer as string[] : [];
  const tokens = exercise.payload.tokens as string[];
  return <div className="word-bank-wrap"><div className="sentence-line">{selected.map((word, index) => <button key={`${word}-${index}`} disabled={disabled} className="word-token selected" onClick={() => setAnswer(selected.filter((_, itemIndex) => itemIndex !== index))}>{word}</button>)}</div><div className="word-bank">{tokens.map((word, index) => { const used = selected.includes(word); return <button key={`${word}-${index}`} disabled={disabled || used} className="word-token" onClick={() => setAnswer([...selected, word])}>{word}</button>; })}</div></div>;
}

function FillBlank({ exercise, answer, setAnswer, disabled }: ExerciseProps) {
  const options = exercise.payload.options as string[];
  const sentence = exercise.payload.sentence as string;
  return <div className="fill-wrap"><div className="fill-sentence">{sentence.replace("___", String(answer || "________"))}</div><div className="choice-grid compact-choices">{options.map((option) => <button key={option} disabled={disabled} className={`answer-card ${answer === option ? "selected" : ""}`} onClick={() => setAnswer(option)}>{option}</button>)}</div></div>;
}

function TypeAnswer({ exercise, answer, setAnswer, disabled }: ExerciseProps) {
  return <label className="type-answer"><span>Your answer</span><textarea autoFocus disabled={disabled} value={typeof answer === "string" ? answer : ""} placeholder={String(exercise.payload.placeholder ?? "Type your answer")} onChange={(event) => setAnswer(event.target.value)}/></label>;
}

function MatchPairs({ exercise, answer, setAnswer, disabled }: ExerciseProps) {
  const left = exercise.payload.left as string[];
  const right = exercise.payload.right as string[];
  const matched = Array.isArray(answer) ? answer as string[][] : [];
  const [pending, setPending] = useState("");
  const used = new Set(matched.flat());
  const choose = (value: string, side: "left" | "right") => {
    if (used.has(value)) {
      setAnswer(matched.filter((pair) => !pair.includes(value)));
      return;
    }
    if (side === "left") { setPending(pending === value ? "" : value); return; }
    if (!pending) return;
    const next = [...matched, [pending, value]];
    setAnswer(next);
    setPending("");
  };
  return <div className="match-grid"><div>{left.map((value) => <button key={value} disabled={disabled} aria-pressed={pending === value || used.has(value)} className={`answer-card ${pending === value || used.has(value) ? "selected" : ""}`} onClick={() => choose(value, "left")}>{value}</button>)}</div><div>{right.map((value) => <button key={value} disabled={disabled} aria-pressed={used.has(value)} className={`answer-card ${used.has(value) ? "selected" : ""}`} onClick={() => choose(value, "right")}>{value}</button>)}</div></div>;
}

type ExerciseProps = { exercise: Exercise; answer: Answer; setAnswer: (answer: Answer) => void; disabled: boolean };

function ExerciseRenderer(props: ExerciseProps) {
  if (props.exercise.type === "multiple_choice") return <MultipleChoice {...props}/>;
  if (props.exercise.type === "word_bank") return <WordBank {...props}/>;
  if (props.exercise.type === "match_pairs") return <MatchPairs {...props}/>;
  if (props.exercise.type === "fill_blank") return <FillBlank {...props}/>;
  return <TypeAnswer {...props}/>;
}

function canSubmit(answer: Answer, exercise: Exercise) {
  if (typeof answer === "string") return answer.trim().length > 0;
  if (exercise.type === "match_pairs") return answer.length === (exercise.payload.left as string[]).length;
  return answer.length > 0;
}

export function LessonPlayer({ lessonId, mode = "lesson" }: { lessonId: number; mode?: "lesson" | "practice" | "legendary" }) {
  const router = useRouter();
  const [attempt, setAttempt] = useState<LessonAttempt | null>(null);
  const [answer, setAnswer] = useState<Answer>("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [hearts, setHearts] = useState(5);
  const [result, setResult] = useState<{ xp_awarded: number; accuracy: number; streak: number; new_achievements: { title: string }[] } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(mode === "legendary" ? 75 : null);
  const [exitOpen, setExitOpen] = useState(false);

  useEffect(() => { api.startAttempt(lessonId, mode).then((value) => { setAttempt(value); setHearts(value.hearts); if (typeof value.seconds_left === "number") setSecondsLeft(value.seconds_left); }).catch((reason: Error) => setError(reason.message)); }, [lessonId, mode]);
  useEffect(() => {
    if (!attempt || attempt.status !== "active" || attempt.current_index < attempt.exercises.length) return;
    let cancelled = false;
    api.complete(attempt.attempt_id)
      .then((value) => { if (!cancelled) { setResult(value); setError(""); } })
      .catch((reason: Error) => { if (!cancelled) setError(reason.message); });
    return () => { cancelled = true; };
  }, [attempt]);
  useEffect(() => {
    if (!attempt || secondsLeft === null || result || feedback?.ready_to_complete || attempt.current_index >= attempt.exercises.length) return;
    if (secondsLeft <= 0) {
      void api.abandon(attempt.attempt_id);
      return;
    }
    const timer = window.setTimeout(() => setSecondsLeft(secondsLeft - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [attempt, feedback?.ready_to_complete, result, secondsLeft]);
  const exercise = attempt?.exercises[attempt.current_index];
  const progress = attempt ? (attempt.current_index / attempt.exercises.length) * 100 : 0;

  const speak = () => {
    if (!exercise || !("speechSynthesis" in window)) return;
    const text = String(exercise.payload.phrase ?? exercise.payload.translation ?? exercise.prompt);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "es-ES";
    utterance.rate = 0.85;
    window.speechSynthesis.speak(utterance);
  };

  const check = async (skip = false) => {
    if (!attempt || !exercise || (!skip && !canSubmit(answer, exercise))) return;
    setBusy(true);
    try {
      const response = await api.answer(attempt.attempt_id, exercise.id, skip ? "" : answer);
      setFeedback(response);
      setHearts(response.hearts);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not check the answer"); }
    finally { setBusy(false); }
  };

  const leaveLesson = async () => {
    if (attempt) await api.abandon(attempt.attempt_id).catch(() => undefined);
    router.push("/learn");
  };

  const questionTitle = exercise?.type === "multiple_choice" && exercise.payload.phrase
    ? `What does “${exercise.payload.phrase}” mean?`
    : exercise?.type === "word_bank"
      ? "Translate this sentence"
      : exercise?.type === "match_pairs"
        ? "Tap the matching pairs"
        : exercise?.prompt;
  const questionLabel = exercise?.type === "multiple_choice" ? "NEW WORD" : exercise?.type === "match_pairs" ? "MATCH THE PAIRS" : "TRANSLATE";

  const next = async () => {
    if (!attempt || !feedback) return;
    if (feedback.failed) return;
    if (feedback.ready_to_complete) {
      setBusy(true);
      try { setResult(await api.complete(attempt.attempt_id)); }
      catch (reason) { setError(reason instanceof Error ? reason.message : "Could not complete the lesson"); }
      finally { setBusy(false); }
      return;
    }
    setAttempt({ ...attempt, current_index: attempt.current_index + 1, hearts });
    setAnswer("");
    setFeedback(null);
  };

  if (error && !attempt) return <div className="center-state lesson-state"><Mascot mood="sad"/><h1>Lesson unavailable</h1><p>{error}</p><Link href="/learn" className="game-button">BACK TO PATH</Link></div>;
  if (result) return <div className="completion-screen"><div className="confetti" aria-hidden>{Array.from({ length: 22 }, (_, index) => <i key={index} style={{ "--i": index } as React.CSSProperties}/>)}</div><Mascot mood="celebrate" size={150}/><span className="eyebrow">LESSON COMPLETE!</span><h1>Outstanding!</h1><div className="completion-stats"><div><GameIcon name="bolt" size={40}/><strong>{result.xp_awarded}</strong><span>XP EARNED</span></div><div><GameIcon name="trophy" size={40}/><strong>{result.accuracy}%</strong><span>ACCURACY</span></div><div><GameIcon name="flame" size={40}/><strong>{result.streak}</strong><span>DAY STREAK</span></div></div>{result.new_achievements.length > 0 && <div className="achievement-toast">🏅 Achievement unlocked: {result.new_achievements[0].title}</div>}<Link href="/learn" className="game-button wide">CONTINUE</Link></div>;
  if (secondsLeft === 0) return <div className="completion-screen"><Mascot mood="sad" size={150}/><span className="eyebrow red">TIME’S UP</span><h1>Great effort!</h1><p>Try the legendary challenge again and answer all five before the timer ends.</p><button className="game-button wide" onClick={() => location.reload()}>TRY AGAIN</button><Link href="/practice" className="text-button">BACK TO PRACTICE</Link></div>;
  if (attempt && !exercise && error) return <div className="center-state lesson-state"><Mascot mood="sad"/><h1>Couldn’t finish your lesson</h1><p>{error}</p><button className="game-button" onClick={() => { setError(""); void api.complete(attempt.attempt_id).then(setResult).catch((reason: Error) => setError(reason.message)); }}>TRY AGAIN</button><Link href="/learn" className="text-button">BACK TO PATH</Link></div>;
  if (!attempt || !exercise) return <div className="center-state lesson-state"><Mascot/><div className="loading-dots"><i/><i/><i/></div><p>{attempt ? "Finishing your lesson…" : "Preparing your lesson…"}</p></div>;
  if (feedback?.failed) return <div className="completion-screen"><Mascot mood="sad" size={150}/><span className="eyebrow red">OUT OF HEARTS</span><h1>Don’t give up!</h1><p>Practice to refill your hearts and come back stronger.</p><button className="game-button wide" onClick={async () => { await api.refill().catch(() => undefined); location.reload(); }}>PRACTICE + REFILL</button><Link href="/learn" className="text-button">RETURN TO PATH</Link></div>;
  return (
    <div className="lesson-page reference-lesson-page">
      <header className="lesson-header"><button type="button" onClick={() => setExitOpen(true)} aria-label="Exit lesson" className="close-button">×</button><div className="lesson-progress" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${progress}%` }}/></div><div className="lesson-hearts">{secondsLeft === null ? <><Image src="/learn-assets/heart.svg" width={30} height={30} alt=""/><strong>{hearts}</strong></> : <><GameIcon name="clock" size={28}/><strong>{secondsLeft}s</strong></>}</div></header>
      <main className="exercise-area">
        <div className="exercise-heading"><div><span className="exercise-counter"><span className="lesson-new-icon" aria-hidden>✦</span>{questionLabel}</span><h1>{questionTitle}</h1>{exercise.hint && <p>{exercise.hint}</p>}</div></div>
        {exercise.type === "multiple_choice" && exercise.payload.phrase ? <button type="button" className="lesson-phrase" onClick={speak} aria-label={`Read ${exercise.payload.phrase} aloud`}><span className="lesson-sound-icon" aria-hidden>◖))</span><strong>{String(exercise.payload.phrase)}</strong></button> : null}
        <ExerciseRenderer exercise={exercise} answer={answer} setAnswer={setAnswer} disabled={Boolean(feedback)}/>
      </main>
      <footer className={`lesson-footer ${feedback ? feedback.correct ? "correct" : "incorrect" : ""}`}>
        {feedback ? <div className="feedback-copy" aria-live="polite"><span className="feedback-icon">{feedback.correct ? "✓" : "×"}</span><div><h2>{feedback.correct ? "Great job!" : "Correct solution:"}</h2>{!feedback.correct && <p>{Array.isArray(feedback.correct_answer) ? feedback.correct_answer.join(" ") : String(feedback.correct_answer)}</p>}<div className="lesson-feedback-actions"><button type="button">ᶻz TOO EASY</button><button type="button">△ TOO DIFFICULT</button><button type="button">⚑ REPORT</button></div></div></div> : <button className="text-button" disabled={busy} onClick={() => check(true)}>SKIP</button>}
        <button className={`game-button ${feedback ? feedback.correct ? "green" : "red-button" : ""}`} disabled={busy || (!feedback && !canSubmit(answer, exercise))} onClick={feedback ? next : () => check()}>{busy ? "CHECKING…" : feedback ? "CONTINUE" : "CHECK"}</button>
      </footer>
      {exitOpen && <div className="lesson-exit-overlay" role="presentation"><div className="lesson-exit-dialog" role="dialog" aria-modal="true" aria-label="Exit lesson"><h2>Are you sure you want to quit?</h2><p>Your progress in this lesson won&apos;t be saved.</p><button type="button" className="game-button" onClick={() => setExitOpen(false)}>KEEP LEARNING</button><button type="button" className="text-button" onClick={leaveLesson}>QUIT</button></div></div>}
      {error && <div className="error-toast">{error}</div>}
    </div>
  );
}

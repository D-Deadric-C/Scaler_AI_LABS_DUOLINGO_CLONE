"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Exercise, LessonAttempt } from "@/lib/types";
import { GameIcon, Mascot } from "./GameIcon";

type Answer = string | string[] | string[][];
type Feedback = { correct: boolean; explanation: string; correct_answer: unknown; ready_to_complete: boolean; failed: boolean };

function MultipleChoice({ exercise, answer, setAnswer, disabled }: ExerciseProps) {
  const options = exercise.payload.options as string[];
  return <div className="choice-grid">{options.map((option, index) => <button key={option} disabled={disabled} className={`answer-card ${answer === option ? "selected" : ""}`} onClick={() => setAnswer(option)}><kbd>{index + 1}</kbd><span>{option}</span></button>)}</div>;
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
  const pairs = exercise.payload.pairs as string[][];
  const left = pairs.map((pair) => pair[0]);
  const right = [...pairs.map((pair) => pair[1])].reverse();
  const matched = Array.isArray(answer) ? answer as string[][] : [];
  const [pending, setPending] = useState("");
  const choose = (value: string, side: "left" | "right") => {
    if (side === "left") { setPending(value); return; }
    if (!pending) return;
    const next = [...matched, [pending, value]];
    setAnswer(next);
    setPending("");
  };
  const used = new Set(matched.flat());
  return <div className="match-grid"><div>{left.map((value) => <button key={value} disabled={disabled || used.has(value)} className={`answer-card ${pending === value ? "selected" : ""}`} onClick={() => choose(value, "left")}>{value}</button>)}</div><div>{right.map((value) => <button key={value} disabled={disabled || used.has(value)} className="answer-card" onClick={() => choose(value, "right")}>{value}</button>)}</div></div>;
}

type ExerciseProps = { exercise: Exercise; answer: Answer; setAnswer: (answer: Answer) => void; disabled: boolean };

function ExerciseRenderer(props: ExerciseProps) {
  if (props.exercise.type === "multiple_choice") return <MultipleChoice {...props}/>;
  if (props.exercise.type === "word_bank") return <WordBank {...props}/>;
  if (props.exercise.type === "match_pairs") return <MatchPairs {...props}/>;
  if (props.exercise.type === "fill_blank") return <FillBlank {...props}/>;
  return <TypeAnswer {...props}/>;
}

function canSubmit(answer: Answer, type: Exercise["type"]) {
  if (typeof answer === "string") return answer.trim().length > 0;
  if (type === "match_pairs") return answer.length >= 3;
  return answer.length > 0;
}

export function LessonPlayer({ lessonId, mode = "lesson" }: { lessonId: number; mode?: "lesson" | "practice" | "legendary" }) {
  const [attempt, setAttempt] = useState<LessonAttempt | null>(null);
  const [answer, setAnswer] = useState<Answer>("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [hearts, setHearts] = useState(5);
  const [result, setResult] = useState<{ xp_awarded: number; accuracy: number; streak: number; new_achievements: { title: string }[] } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(mode === "legendary" ? 75 : null);

  useEffect(() => { api.startAttempt(lessonId, mode).then((value) => { setAttempt(value); setHearts(value.hearts); }).catch((reason: Error) => setError(reason.message)); }, [lessonId, mode]);
  useEffect(() => {
    if (secondsLeft === null || result) return;
    if (secondsLeft <= 0) {
      if (attempt) void api.abandon(attempt.attempt_id);
      return;
    }
    const timer = window.setTimeout(() => setSecondsLeft(secondsLeft - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [attempt, result, secondsLeft]);
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

  const check = async () => {
    if (!attempt || !exercise || !canSubmit(answer, exercise.type)) return;
    setBusy(true);
    try {
      const response = await api.answer(attempt.attempt_id, exercise.id, answer);
      setFeedback(response);
      setHearts(response.hearts);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not check the answer"); }
    finally { setBusy(false); }
  };

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
  if (secondsLeft === 0) return <div className="completion-screen"><Mascot mood="sad" size={150}/><span className="eyebrow red">TIME’S UP</span><h1>Great effort!</h1><p>Try the legendary challenge again and answer all five before the timer ends.</p><button className="game-button wide" onClick={() => location.reload()}>TRY AGAIN</button><Link href="/practice" className="text-button">BACK TO PRACTICE</Link></div>;
  if (!attempt || !exercise) return <div className="center-state lesson-state"><Mascot/><div className="loading-dots"><i/><i/><i/></div><p>Preparing your lesson…</p></div>;
  if (result) return <div className="completion-screen"><div className="confetti" aria-hidden>{Array.from({ length: 22 }, (_, index) => <i key={index} style={{ "--i": index } as React.CSSProperties}/>)}</div><Mascot mood="celebrate" size={150}/><span className="eyebrow">LESSON COMPLETE!</span><h1>Outstanding!</h1><div className="completion-stats"><div><GameIcon name="bolt" size={40}/><strong>{result.xp_awarded}</strong><span>XP EARNED</span></div><div><GameIcon name="trophy" size={40}/><strong>{result.accuracy}%</strong><span>ACCURACY</span></div><div><GameIcon name="flame" size={40}/><strong>{result.streak}</strong><span>DAY STREAK</span></div></div>{result.new_achievements.length > 0 && <div className="achievement-toast">🏅 Achievement unlocked: {result.new_achievements[0].title}</div>}<Link href="/learn" className="game-button wide">CONTINUE</Link></div>;
  if (feedback?.failed) return <div className="completion-screen"><Mascot mood="sad" size={150}/><span className="eyebrow red">OUT OF HEARTS</span><h1>Don’t give up!</h1><p>Practice to refill your hearts and come back stronger.</p><button className="game-button wide" onClick={async () => { await api.refill(); location.reload(); }}>PRACTICE + REFILL</button><Link href="/learn" className="text-button">RETURN TO PATH</Link></div>;
  return (
    <div className="lesson-page">
      <header className="lesson-header"><Link href="/learn" aria-label="Exit lesson" className="close-button">×</Link><div className="lesson-progress"><span style={{ width: `${progress}%` }}/></div><div className="lesson-hearts">{secondsLeft === null ? <><GameIcon name="heart" size={28}/><strong>{hearts}</strong></> : <><GameIcon name="clock" size={28}/><strong>{secondsLeft}s</strong></>}</div></header>
      <main className="exercise-area">
        <div className="exercise-heading"><button className="sound-button" onClick={speak} aria-label="Read prompt aloud">🔊</button><div><span className="exercise-counter">QUESTION {attempt.current_index + 1} OF {attempt.exercises.length}</span><h1>{exercise.prompt}</h1>{exercise.hint && <p>{exercise.hint}</p>}</div></div>
        <ExerciseRenderer exercise={exercise} answer={answer} setAnswer={setAnswer} disabled={Boolean(feedback)}/>
      </main>
      <footer className={`lesson-footer ${feedback ? feedback.correct ? "correct" : "incorrect" : ""}`}>
        {feedback ? <div className="feedback-copy"><span className="feedback-icon">{feedback.correct ? "✓" : "×"}</span><div><h2>{feedback.correct ? "Excellent!" : "Correct answer:"}</h2><p>{feedback.correct ? feedback.explanation : String(feedback.correct_answer)}</p></div></div> : <button className="text-button" onClick={() => setAnswer("")}>SKIP</button>}
        <button className={`game-button ${feedback?.correct ? "green" : feedback ? "red-button" : ""}`} disabled={busy || (!feedback && !canSubmit(answer, exercise.type))} onClick={feedback ? next : check}>{busy ? "CHECKING…" : feedback ? "CONTINUE" : "CHECK"}</button>
      </footer>
      {error && <div className="error-toast">{error}</div>}
    </div>
  );
}

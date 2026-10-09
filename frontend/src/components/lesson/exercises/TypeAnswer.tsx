import type { ExerciseProps } from "../types";

export function TypeAnswer({ exercise, answer, setAnswer, feedback }: ExerciseProps) {
  const verdict = feedback ? (feedback.correct ? "correct" : "wrong") : "";
  return (
    <label className="lx-type">
      <span className="lx-visually-hidden">Your answer</span>
      <textarea
        autoFocus
        lang="es"
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        rows={4}
        disabled={Boolean(feedback)}
        className={verdict}
        value={typeof answer === "string" ? answer : ""}
        placeholder={String(exercise.payload.placeholder ?? "Type in Spanish")}
        onChange={(event) => setAnswer(event.target.value)}
      />
    </label>
  );
}

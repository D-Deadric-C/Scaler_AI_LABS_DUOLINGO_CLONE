import { Fragment } from "react";
import { blankCount } from "../answers";
import { Character } from "../Character";
import { Words } from "../Words";
import type { ExerciseProps } from "../types";

/** Chosen words per blank ("" = empty). A single blank is stored as a plain string. */
function slotsOf(answer: ExerciseProps["answer"], blanks: number): string[] {
  if (Array.isArray(answer)) return Array.from({ length: blanks }, (_, index) => String((answer as string[])[index] ?? ""));
  return [typeof answer === "string" ? answer : ""];
}

export function FillBlank({ exercise, answer, setAnswer, feedback }: ExerciseProps) {
  const options = exercise.payload.options as string[];
  const parts = String(exercise.payload.sentence).split("___");
  const blanks = blankCount(exercise);
  const slots = slotsOf(answer, blanks);
  const locked = Boolean(feedback);
  const verdict = feedback ? (feedback.correct ? "correct" : "wrong") : "";
  const store = (next: string[]) => setAnswer(blanks === 1 ? next[0] : next.some(Boolean) ? next : "");
  const place = (word: string) => {
    const index = slots.findIndex((slot) => !slot);
    if (index >= 0) store(slots.map((slot, slotIndex) => (slotIndex === index ? word : slot)));
  };
  const clear = (index: number) => store(slots.map((slot, slotIndex) => (slotIndex === index ? "" : slot)));

  return (
    <div className="lx-fill">
      <div className="lx-scene lx-fill-scene">
        <Character name={String(exercise.payload.character ?? "gus")} size={180} />
        <p className="lx-sentence" aria-label="Sentence with blanks">
          {parts.map((part, index) => (
            <Fragment key={index}>
              <Words text={part} />
              {index < blanks ? (
                <span className="lx-slot">
                  {slots[index] ? <button type="button" disabled={locked} className={`lx-chip ${verdict}`} onClick={() => clear(index)}>{slots[index]}</button> : <span className="lx-slot-empty" />}
                </span>
              ) : null}
            </Fragment>
          ))}
        </p>
      </div>
      <div className="lx-bank-tokens lx-fill-options" role="group" aria-label="Word options">
        {options.map((option) =>
          slots.includes(option) ? (
            <span key={option} className="lx-chip lx-chip-ghost" aria-hidden>{option}</span>
          ) : (
            <button key={option} type="button" disabled={locked} className="lx-chip" onClick={() => place(option)}>{option}</button>
          ),
        )}
      </div>
    </div>
  );
}

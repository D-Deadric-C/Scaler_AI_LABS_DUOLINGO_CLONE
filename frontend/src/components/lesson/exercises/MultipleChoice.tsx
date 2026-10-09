import type { ExerciseProps } from "../types";
import { cardState } from "./cardState";

export function MultipleChoice({ exercise, answer, setAnswer, feedback }: ExerciseProps) {
  const options = exercise.payload.options as string[];
  return (
    <div className="lx-choices" role="radiogroup" aria-label="Answer options">
      {options.map((option, index) => (
        <button
          key={option}
          type="button"
          role="radio"
          aria-checked={answer === option}
          disabled={Boolean(feedback)}
          className={`lx-card ${cardState(answer === option, feedback)}`}
          onClick={() => setAnswer(option)}
        >
          <kbd>{index + 1}</kbd>
          <span>{option}</span>
        </button>
      ))}
    </div>
  );
}

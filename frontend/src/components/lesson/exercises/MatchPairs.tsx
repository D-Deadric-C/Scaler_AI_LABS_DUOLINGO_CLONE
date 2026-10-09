import { useState } from "react";
import type { ExerciseProps } from "../types";

type Side = "left" | "right";
const PAIR_COLORS = ["#49c0f8", "#ce82ff", "#ffc800", "#ff9600", "#2fd2a5"];

export function MatchPairs({ exercise, answer, setAnswer, feedback }: ExerciseProps) {
  const left = exercise.payload.left as string[];
  const right = exercise.payload.right as string[];
  const pairs = Array.isArray(answer) ? (answer as string[][]) : [];
  const [pending, setPending] = useState<{ side: Side; value: string } | null>(null);
  const locked = Boolean(feedback);
  const pairIndex = (value: string) => pairs.findIndex((pair) => pair.includes(value));

  const choose = (side: Side, value: string) => {
    if (locked) return;
    if (pairIndex(value) >= 0) { // tapping a matched card breaks the pair
      setAnswer(pairs.filter((pair) => !pair.includes(value)));
      return;
    }
    if (!pending || pending.side === side) {
      setPending(pending && pending.value === value ? null : { side, value });
      return;
    }
    const [leftValue, rightValue] = side === "right" ? [pending.value, value] : [value, pending.value];
    setAnswer([...pairs, [leftValue, rightValue]]);
    setPending(null);
  };

  const column = (side: Side, values: string[]) => (
    <div className="lx-match-column">
      {values.map((value) => {
        const index = pairIndex(value);
        const isPending = pending?.value === value;
        const color = index >= 0 ? PAIR_COLORS[index % PAIR_COLORS.length] : undefined;
        return (
          <button
            key={value}
            type="button"
            disabled={locked}
            aria-pressed={isPending || index >= 0}
            className={`lx-card lx-match-card ${isPending ? "selected" : ""} ${index >= 0 ? "paired" : ""} ${feedback ? (feedback.correct ? "correct" : "wrong") : ""}`}
            style={color ? ({ "--pair": color } as React.CSSProperties) : undefined}
            onClick={() => choose(side, value)}
          >
            <span>{value}</span>
          </button>
        );
      })}
    </div>
  );

  return <div className="lx-match">{column("left", left)}{column("right", right)}</div>;
}

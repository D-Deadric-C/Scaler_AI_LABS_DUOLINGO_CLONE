import type { ExerciseProps } from "../types";

/** Index of each selected word inside the bank (first unused match, so duplicate words work). */
function usedIndexes(selected: string[], tokens: string[]): number[] {
  const taken = new Set<number>();
  return selected.map((word) => {
    const index = tokens.findIndex((token, tokenIndex) => token === word && !taken.has(tokenIndex));
    taken.add(index);
    return index;
  });
}

export function WordBank({ exercise, answer, setAnswer, feedback }: ExerciseProps) {
  const selected = Array.isArray(answer) ? (answer as string[]) : [];
  const tokens = exercise.payload.tokens as string[];
  const used = new Set(usedIndexes(selected, tokens));
  const locked = Boolean(feedback);
  const verdict = feedback ? (feedback.correct ? "correct" : "wrong") : "";
  return (
    <div className="lx-bank">
      <div className={`lx-answer-lines ${verdict}`} aria-label="Your answer" aria-live="polite">
        {selected.map((word, index) => (
          <button key={`${word}-${index}`} type="button" disabled={locked} className={`lx-chip ${verdict}`} onClick={() => setAnswer(selected.filter((_, itemIndex) => itemIndex !== index))}>
            {word}
          </button>
        ))}
      </div>
      <div className="lx-bank-tokens">
        {tokens.map((word, index) =>
          used.has(index) ? (
            <span key={`${word}-${index}`} className="lx-chip lx-chip-ghost" aria-hidden>{word}</span>
          ) : (
            <button key={`${word}-${index}`} type="button" disabled={locked} className="lx-chip" onClick={() => setAnswer([...selected, word])}>
              {word}
            </button>
          ),
        )}
      </div>
    </div>
  );
}

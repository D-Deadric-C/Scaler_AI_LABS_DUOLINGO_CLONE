import type { AnswerFeedback } from "../types";

/** CSS modifier for a selectable card: plain, selected, or (after checking) correct / wrong. */
export function cardState(selected: boolean, feedback: AnswerFeedback | null): string {
  if (!selected) return "";
  if (!feedback) return "selected";
  return feedback.correct ? "correct" : "wrong";
}

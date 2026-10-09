import type { Exercise } from "@/lib/types";
import type { Answer, AnswerFeedback } from "./types";

export function emptyAnswer(): Answer {
  return "";
}

/** Whether the learner has given enough input for the CHECK button to be enabled. */
export function blankCount(exercise: Exercise): number {
  return Math.max(1, String(exercise.payload.sentence ?? "").split("___").length - 1);
}

export function canSubmit(answer: Answer, exercise: Exercise): boolean {
  if (typeof answer === "string") return answer.trim().length > 0;
  if (exercise.type === "fill_blank") return answer.length === blankCount(exercise) && (answer as string[]).every((word) => word.length > 0);
  if (exercise.type === "match_pairs") return answer.length === (exercise.payload.left as string[]).length;
  return answer.length > 0;
}

/** Human readable "correct solution" line shown in the red feedback panel. */
export function solutionText(correctAnswer: unknown): string {
  if (Array.isArray(correctAnswer)) {
    return correctAnswer.map((item) => (Array.isArray(item) ? item.join(" – ") : String(item))).join(correctAnswer.some(Array.isArray) ? "   ·   " : " ");
  }
  return String(correctAnswer ?? "");
}

const PRAISE = ["Correct!", "Nice job!", "Great job!", "Awesome!", "Well done!"];

export function feedbackTitle(feedback: AnswerFeedback, index: number): string {
  return feedback.correct ? PRAISE[index % PRAISE.length] : "Correct solution:";
}

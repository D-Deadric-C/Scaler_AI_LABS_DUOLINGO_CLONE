import type { Exercise } from "@/lib/types";

export type LessonMode = "lesson" | "practice" | "legendary";
export type Answer = string | string[] | string[][];

export type AnswerFeedback = {
  correct: boolean;
  explanation: string;
  correct_answer: unknown;
  hearts: number;
  queue: number[];
  remaining: number;
  correct_count: number;
  ready_to_complete: boolean;
  failed: boolean;
};

export type LessonResult = {
  mode?: string;
  xp_awarded: number;
  accuracy: number;
  streak: number;
  hearts?: number;
  daily_goal_reached?: boolean;
  today_xp?: number;
  daily_goal?: number;
  perfect?: boolean;
  new_achievements: { title: string }[];
};

export type ExerciseProps = {
  exercise: Exercise;
  answer: Answer;
  setAnswer: (answer: Answer) => void;
  /** Set once the answer has been checked; inputs lock and show the verdict. */
  feedback: AnswerFeedback | null;
};

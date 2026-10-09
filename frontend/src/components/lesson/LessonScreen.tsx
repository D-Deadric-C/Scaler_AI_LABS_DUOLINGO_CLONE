import type { Exercise } from "@/lib/types";
import { canSubmit } from "./answers";
import { ExerciseView } from "./ExerciseView";
import { FeedbackFooter } from "./FeedbackFooter";
import { LessonHeader } from "./LessonHeader";
import type { Answer, AnswerFeedback } from "./types";

export type LessonScreenProps = {
  exercise: Exercise;
  exerciseIndex: number;
  answer: Answer;
  setAnswer: (answer: Answer) => void;
  feedback: AnswerFeedback | null;
  progress: number;
  streakRun: number;
  hearts: number;
  heartsLost: number;
  secondsLeft: number | null;
  spotlight?: boolean;
  busy: boolean;
  onClose: () => void;
  onCheck: () => void;
  onSkip: () => void;
  onContinue: () => void;
  onFeedbackAction: (label: string) => void;
};

/** Purely presentational lesson frame (header, exercise, feedback footer): no data fetching, easy to preview. */
export function LessonScreen(props: LessonScreenProps) {
  const { exercise, answer, feedback } = props;
  return (
    <div className="lx-page">
      <LessonHeader progress={props.progress} streakRun={props.streakRun} hearts={props.hearts} heartsLost={props.heartsLost} secondsLeft={props.secondsLeft} spotlight={props.spotlight} onClose={props.onClose} />
      <main className={`lx-main ${feedback && !feedback.correct ? "shake" : ""}`} key={exercise.id}>
        <ExerciseView exercise={exercise} answer={answer} setAnswer={props.setAnswer} feedback={feedback} />
      </main>
      <FeedbackFooter
        feedback={feedback}
        exerciseIndex={props.exerciseIndex}
        busy={props.busy}
        canCheck={canSubmit(answer, exercise)}
        onCheck={props.onCheck}
        onSkip={props.onSkip}
        onContinue={props.onContinue}
        onFeedbackAction={props.onFeedbackAction}
      />
    </div>
  );
}

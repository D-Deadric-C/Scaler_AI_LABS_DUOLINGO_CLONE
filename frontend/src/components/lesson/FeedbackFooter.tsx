import { feedbackTitle, solutionText } from "./answers";
import { CheckBadge, CrossBadge, FlagIcon, MountainIcon, SleepIcon } from "./Icons";
import type { AnswerFeedback } from "./types";

type Props = {
  feedback: AnswerFeedback | null;
  exerciseIndex: number;
  busy: boolean;
  canCheck: boolean;
  onCheck: () => void;
  onSkip: () => void;
  onContinue: () => void;
  onFeedbackAction: (label: string) => void;
};

export function FeedbackFooter({ feedback, exerciseIndex, busy, canCheck, onCheck, onSkip, onContinue, onFeedbackAction }: Props) {
  const state = feedback ? (feedback.correct ? "correct" : "incorrect") : "idle";
  return (
    <footer className={`lx-footer ${state}`}>
      <div className="lx-footer-inner">
        {feedback ? (
          <div className="lx-feedback" role="status" aria-live="assertive">
            <span className="lx-badge">{feedback.correct ? <CheckBadge /> : <CrossBadge />}</span>
            <div className="lx-feedback-text">
              <h2>{feedbackTitle(feedback, exerciseIndex)}</h2>
              {!feedback.correct ? <p>{solutionText(feedback.correct_answer)}</p> : null}
              <div className="lx-feedback-actions">
                <button type="button" onClick={() => onFeedbackAction("Marked as too easy")}><SleepIcon /> TOO EASY</button>
                <button type="button" onClick={() => onFeedbackAction("Marked as too difficult")}><MountainIcon /> TOO DIFFICULT</button>
                <button type="button" onClick={() => onFeedbackAction("Thanks, we'll take a look")}><FlagIcon /> REPORT</button>
              </div>
            </div>
          </div>
        ) : (
          <button type="button" className="lx-button lx-button-ghost" disabled={busy} onClick={onSkip}>SKIP</button>
        )}
        <button
          type="button"
          className={`lx-button lx-button-primary ${feedback && !feedback.correct ? "danger" : ""}`}
          disabled={busy || (!feedback && !canCheck)}
          onClick={feedback ? onContinue : onCheck}
        >
          {feedback ? "CONTINUE" : "CHECK"}
        </button>
      </div>
    </footer>
  );
}

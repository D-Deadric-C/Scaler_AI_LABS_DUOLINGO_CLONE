import Image from "next/image";
import { GameIcon } from "../GameIcon";
import { CloseIcon } from "./Icons";

type Props = {
  progress: number;
  streakRun: number;
  hearts: number;
  heartsLost: number;
  secondsLeft: number | null;
  spotlight?: boolean;
  onClose: () => void;
};

export function LessonHeader({ progress, streakRun, hearts, heartsLost, secondsLeft, spotlight = false, onClose }: Props) {
  return (
    <header className="lx-header">
      <button type="button" className="lx-close" aria-label="Exit lesson" onClick={onClose}><CloseIcon /></button>
      <div className="lx-progress-wrap">
        {streakRun >= 2 ? <span key={streakRun} className="lx-streak-label" style={{ left: `${Math.max(progress, 3.4) / 2}%` }}>{streakRun} IN A ROW</span> : null}
        <div className="lx-progress" role="progressbar" aria-label="Lesson progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress)}>
          <span style={{ width: `${Math.max(progress, 3.4)}%` }} />
        </div>
      </div>
      {secondsLeft === null ? (
        <div className={`lx-hearts ${hearts === 0 ? "empty" : ""} ${spotlight ? "spot" : ""}`} aria-label={`${hearts} hearts left`}>
          <span key={heartsLost} className={heartsLost > 0 ? "lx-heart-break" : ""}><Image src="/learn-assets/heart.svg" width={30} height={30} alt="" /></span>
          <strong>{hearts}</strong>
        </div>
      ) : (
        <div className={`lx-hearts lx-timer ${secondsLeft <= 10 ? "urgent" : ""}`} role="timer" aria-label={`${secondsLeft} seconds left`}>
          <GameIcon name="clock" size={28} /><strong>{secondsLeft}s</strong>
        </div>
      )}
    </header>
  );
}

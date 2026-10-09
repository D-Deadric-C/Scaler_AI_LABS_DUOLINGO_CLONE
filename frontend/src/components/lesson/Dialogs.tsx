import Link from "next/link";
import { useState } from "react";
import { Mascot } from "../GameIcon";
import { GemIcon, HeartIcon } from "./Icons";

function Modal({ label, wide = false, children }: { label: string; wide?: boolean; children: React.ReactNode }) {
  return (
    <div className="lx-overlay" role="presentation">
      <div className={`lx-dialog ${wide ? "wide" : ""}`} role="dialog" aria-modal="true" aria-label={label}>{children}</div>
    </div>
  );
}

export function ExitDialog({ onStay, onQuit }: { onStay: () => void; onQuit: () => void }) {
  return (
    <Modal label="Exit lesson">
      <Mascot mood="sad" size={102} />
      <h2>Wait, don’t go! You’ll lose your progress if you quit now</h2>
      <button type="button" className="lx-button lx-button-sky" autoFocus onClick={onStay}>KEEP LEARNING</button>
      <button type="button" className="lx-button lx-button-link danger" onClick={onQuit}>END SESSION</button>
    </Modal>
  );
}

type OutOfHeartsProps = { gems: number | null; gemCost: number; busy: boolean; onGems: () => void; onSuper: () => void };

export function OutOfHeartsDialog({ gems, gemCost, busy, onGems, onSuper }: OutOfHeartsProps) {
  const [choice, setChoice] = useState<"super" | "refill">("super");
  const canAfford = gems !== null && gems >= gemCost;
  return (
    <Modal label="Out of hearts" wide>
      <div className="lx-gems" aria-label={`${gems ?? 0} gems`}><GemIcon size={22} />{gems ?? 0}</div>
      <h2>You ran out of hearts!</h2>
      <div className="lx-options" role="radiogroup" aria-label="How to continue">
        <button type="button" role="radio" aria-checked={choice === "super"} className={`lx-option lx-option-super ${choice === "super" ? "chosen" : ""}`} onClick={() => setChoice("super")}>
          <span className="lx-super-tag">SUPER</span>
          <HeartIcon size={32} infinite /><strong>Unlimited Hearts</strong><em>GET SUPER</em>
          {choice === "super" ? <i className="lx-tick" aria-hidden>✓</i> : null}
        </button>
        <button type="button" role="radio" aria-checked={choice === "refill"} className={`lx-option ${choice === "refill" ? "chosen" : ""}`} onClick={() => setChoice("refill")}>
          <HeartIcon size={32} /><strong>Refill</strong><span className="lx-cost"><GemIcon size={18} />{gemCost}</span>
          {choice === "refill" ? <i className="lx-tick" aria-hidden>✓</i> : null}
        </button>
      </div>
      <button type="button" className="lx-button lx-button-sky light" disabled={busy || (choice === "refill" && !canAfford)} onClick={choice === "super" ? onSuper : onGems}>
        {choice === "super" ? "TRY 4 WEEKS FREE" : canAfford ? `REFILL FOR ${gemCost} GEMS` : "NOT ENOUGH GEMS"}
      </button>
      <Link href="/learn" className="lx-button lx-button-link">NO THANKS</Link>
    </Modal>
  );
}

export function TimeUpDialog({ onRetry }: { onRetry: () => void }) {
  return (
    <Modal label="Time is up">
      <Mascot mood="sad" size={90} />
      <h2>Time’s up! Answer all five questions before the timer ends</h2>
      <button type="button" className="lx-button lx-button-sky" autoFocus onClick={onRetry}>TRY AGAIN</button>
      <Link href="/practice" className="lx-button lx-button-link">BACK TO PRACTICE</Link>
    </Modal>
  );
}

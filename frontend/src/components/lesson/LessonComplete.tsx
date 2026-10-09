import Link from "next/link";
import { useEffect } from "react";
import { GameIcon } from "../GameIcon";
import { Character } from "./Character";
import { TargetIcon } from "./Icons";
import { playComplete } from "./sounds";
import type { LessonResult } from "./types";

const HEADINGS: Record<string, string> = { lesson: "Lesson complete!", practice: "Practice complete!", legendary: "Legendary!" };

function accuracyLabel(result: LessonResult): string {
  if (result.accuracy >= 100) return "PERFECT";
  if (result.accuracy >= 90) return "AMAZING";
  if (result.accuracy >= 70) return "GOOD";
  return "KEEP GOING";
}

export function LessonComplete({ result, showStreak = true }: { result: LessonResult; showStreak?: boolean }) {
  useEffect(() => { playComplete(); }, []);
  const badges = result.new_achievements ?? [];
  return (
    <main className="lx-complete">
      <div className="confetti" aria-hidden>{Array.from({ length: 22 }, (_, index) => <i key={index} style={{ "--i": index } as React.CSSProperties} />)}</div>
      <div className="lx-complete-body">
        <div className="lx-art"><Character name="zoe" size={340} /></div>
        <h1>{HEADINGS[result.mode ?? "lesson"] ?? "Lesson complete!"}</h1>
        <div className="lx-results">
          <div className="lx-result xp"><span>TOTAL XP</span><strong><GameIcon name="bolt" size={26} />{result.xp_awarded}</strong></div>
          <div className="lx-result accuracy"><span>{accuracyLabel(result)}</span><strong><TargetIcon size={24} />{result.accuracy}%</strong></div>
          {showStreak ? <div className="lx-result streak"><span>DAY STREAK</span><strong><GameIcon name="flame" size={26} />{result.streak}</strong></div> : null}
        </div>
        {result.daily_goal_reached ? <p className="lx-note goal">🎯 Daily goal reached — {result.today_xp} / {result.daily_goal} XP!</p> : null}
        {badges.map((badge) => <p key={badge.title} className="lx-note badge">🏅 Achievement unlocked: {badge.title}</p>)}
      </div>
      <footer className="lx-complete-footer">
        <div className="lx-footer-inner end"><Link href="/learn" className="lx-button lx-button-sky" autoFocus>CONTINUE</Link></div>
      </footer>
    </main>
  );
}

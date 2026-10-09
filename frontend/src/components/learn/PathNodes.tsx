"use client";

import Image from "next/image";
import Link from "next/link";
import type { CSSProperties } from "react";
import type { PathSkill, PathUnit } from "@/lib/types";
import { ArtSlot } from "./ArtSlot";
import { offsetFor } from "./pathLayout";

const GLYPH_LOCKED = ["grayheadphones.svg", "dumbleicon.svg", "trophy_white.svg"];

function LevelGlyph({ status, index }: { status: PathSkill["status"]; index: number }) {
  if (status === "available") {
    return (
      <svg className="pt-level-star" viewBox="0 0 48 48" aria-hidden>
        <path d="m24 5 5.5 11.2 12.4 1.8-9 8.7 2.1 12.4L24 33.3l-11 5.8 2.1-12.4-9-8.7 12.4-1.8L24 5Z" />
        <path d="m24 13 2.8 5.7 6.3.9-4.5 4.4 1 6.3-5.6-3-5.6 3 1-6.3-4.5-4.4 6.3-.9L24 13Z" className="inner" />
      </svg>
    );
  }
  if (status === "locked" && index % GLYPH_LOCKED.length === 0) {
    return <ArtSlot name="duo-radio" width={36} height={35} fallback={<Image src="/learn-assets/grayheadphones.svg" width={36} height={32} alt="" aria-hidden />} />;
  }
  const asset = status === "completed" ? "tick_white.svg" : GLYPH_LOCKED[index % GLYPH_LOCKED.length];
  return <Image src={`/learn-assets/${asset}`} width={36} height={32} alt="" aria-hidden />;
}

/** One skill (lesson) on the path: locked / available (with ring + START) / completed (with crown). */
type SkillNodeProps = {
  skill: PathSkill;
  status: PathSkill["status"];
  index: number;
  level: number;
  placement: "above" | "below";
  current: boolean;
  open: boolean;
  onToggle: () => void;
  mirrored?: boolean;
};

export function SkillNode({ skill, status, index, level, placement, current, open, onToggle, mirrored = false }: SkillNodeProps) {
  const locked = status === "locked";
  const shownProgress = status === skill.status ? skill.progress : 0;
  const progress = Math.min(100, Math.round((shownProgress / Math.max(1, skill.total_lessons)) * 100));
  return (
    <div className={`pt-item ${open ? "open" : ""}`} style={{ "--dx": `${offsetFor(index) * (mirrored ? -1 : 1)}px` } as CSSProperties} data-current={current || undefined}>
      {open ? (
        <div className={`pt-popover ${placement} skill ${status}`} role="dialog" aria-label={`${skill.title} level ${level}`}>
          <strong>{skill.title}</strong>
          <span>{skill.description}</span>
          <span>Level {level} of 6 · {shownProgress} / {skill.total_lessons} lessons complete</span>
          {locked ? <span className="pt-locked-pill">COMPLETE THE LEVELS ABOVE</span> : <Link href={`/lesson/${skill.lesson_id}${status === "completed" ? "?mode=practice" : ""}`}>{status === "completed" ? `PRACTICE +${Math.max(5, Math.round(skill.xp_reward / 2))} XP` : `START +${skill.xp_reward} XP`}</Link>}
          {status === "completed" ? <Link className="legendary" href={`/lesson/${skill.lesson_id}?mode=legendary`}>LEGENDARY +{skill.xp_reward * 2} XP</Link> : null}
        </div>
      ) : null}
      {current && !open ? <span className="pt-start" aria-hidden>START</span> : null}
      <div className={`pt-ring ${status}`} style={{ "--ring": `${status === "available" ? Math.max(progress, 8) : progress}%` } as CSSProperties}>
        <button type="button" className={`pt-node ${status}`} aria-expanded={open} aria-label={`${skill.title}, level ${level} of 6, ${status}, ${shownProgress} of ${skill.total_lessons} lessons complete`} onClick={onToggle}>
          <LevelGlyph status={status} index={index} />
        </button>
      </div>
      {status === "completed" ? <span className="pt-crown" aria-label="Crown earned">♛</span> : null}
    </div>
  );
}

/** Reward chest: locked (grey) until the unit is finished, then closed with an OPEN bubble, then opened. */
export function ChestNode({ unit, index, open, onToggle, onOpen, mirrored = false }: { unit: PathUnit; index: number; open: boolean; onToggle: () => void; onOpen: () => void; mirrored?: boolean }) {
  const { status } = unit.chest;
  return (
    <div className={`pt-item ${open ? "open" : ""}`} style={{ "--dx": `${offsetFor(index) * (mirrored ? -1 : 1)}px` } as CSSProperties}>
      {open ? (
        <div className="pt-popover above" role="dialog" aria-label={`Unit ${unit.position} reward chest`}>
          <strong>Unit reward</strong>
          <span>{status === "locked" ? "Complete the first three levels to unlock this chest." : status === "opened" ? "You already collected this unit reward." : `Open it to collect ${unit.chest.gems} gems.`}</span>
          {status === "ready" ? <button type="button" className="pt-popover-action" onClick={onOpen}>OPEN +{unit.chest.gems} GEMS</button> : <span className="pt-locked-pill">{status === "opened" ? "COLLECTED" : "LOCKED"}</span>}
        </div>
      ) : null}
      {status === "ready" ? <span className="pt-open-bubble">OPEN</span> : null}
      <button type="button" className={`pt-chest ${status}`} aria-expanded={open} aria-label={status === "ready" ? `Open the Unit ${unit.position} reward chest` : status === "opened" ? "Reward chest opened" : "Reward chest locked"} onClick={onToggle}>
        <Image src={status === "opened" ? "/learn-assets/Chest_open.svg" : "/learn-assets/chest.svg"} width={80} height={80} alt="" aria-hidden />
      </button>
    </div>
  );
}

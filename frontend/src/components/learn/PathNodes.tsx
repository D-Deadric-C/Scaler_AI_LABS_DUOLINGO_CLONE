"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, type CSSProperties } from "react";
import type { PathSkill, PathUnit } from "@/lib/types";
import { offsetFor } from "./pathLayout";

const GLYPH_LOCKED = ["grayheadphones.svg", "dumbleicon.svg", "trophy_white.svg"];

function glyph(skill: PathSkill, index: number): string {
  if (skill.status === "locked") return GLYPH_LOCKED[index % GLYPH_LOCKED.length];
  return skill.status === "completed" ? "tick_white.svg" : "openbook_white.svg";
}

/** One skill (lesson) on the path: locked / available (with ring + START) / completed (with crown). */
export function SkillNode({ skill, index, current }: { skill: PathSkill; index: number; current: boolean }) {
  const [open, setOpen] = useState(false);
  const locked = skill.status === "locked";
  const progress = Math.min(100, Math.round((skill.progress / Math.max(1, skill.total_lessons)) * 100));
  return (
    <div className="pt-item" style={{ "--dx": `${offsetFor(index)}px` } as CSSProperties} data-current={current || undefined}>
      {open && !locked ? (
        <div className="pt-popover" role="dialog" aria-label={`${skill.title} lesson`}>
          <strong>{skill.title}</strong>
          <span>{skill.description}</span>
          <span>{skill.progress} / {skill.total_lessons} lessons complete</span>
          <Link href={`/lesson/${skill.lesson_id}${skill.status === "completed" ? "?mode=practice" : ""}`}>{skill.status === "completed" ? "PRACTICE" : `START +${skill.xp_reward} XP`}</Link>
          {skill.status === "completed" ? <Link className="legendary" href={`/lesson/${skill.lesson_id}?mode=legendary`}>LEGENDARY ⚡</Link> : null}
        </div>
      ) : null}
      {current && !open ? <span className="pt-start" aria-hidden>START</span> : null}
      <div className={`pt-ring ${skill.status}`} style={{ "--ring": `${skill.status === "available" ? Math.max(progress, 8) : progress}%` } as CSSProperties}>
        <button type="button" className={`pt-node ${skill.status}`} disabled={locked} aria-expanded={locked ? undefined : open} aria-label={`${skill.title}, ${skill.status}, ${skill.progress} of ${skill.total_lessons} lessons complete`} onClick={() => setOpen((value) => !value)}>
          <Image src={`/learn-assets/${glyph(skill, index)}`} width={36} height={32} alt="" aria-hidden />
        </button>
      </div>
      {skill.status === "completed" ? <span className="pt-crown" aria-label="Crown earned">♛</span> : null}
    </div>
  );
}

/** Reward chest: locked (grey) until the unit is finished, then closed with an OPEN bubble, then opened. */
export function ChestNode({ unit, index, onOpen }: { unit: PathUnit; index: number; onOpen: () => void }) {
  const { status } = unit.chest;
  return (
    <div className="pt-item" style={{ "--dx": `${offsetFor(index)}px` } as CSSProperties}>
      {status === "ready" ? <span className="pt-open-bubble">OPEN</span> : null}
      <button type="button" className={`pt-chest ${status}`} disabled={status !== "ready"} aria-label={status === "ready" ? `Open the Unit ${unit.position} reward chest` : status === "opened" ? "Reward chest opened" : "Reward chest locked"} onClick={onOpen}>
        <Image src={status === "opened" ? "/learn-assets/Chest_open.svg" : "/learn-assets/chest.svg"} width={80} height={80} alt="" aria-hidden />
      </button>
    </div>
  );
}

/** Unit review trophy: unlocks once every skill in the unit is complete. */
export function ReviewNode({ unit, index }: { unit: PathUnit; index: number }) {
  const [open, setOpen] = useState(false);
  const ready = unit.skills.length > 0 && unit.skills.every((skill) => skill.status === "completed");
  const lessonId = unit.skills.at(-1)?.lesson_id;
  return (
    <div className="pt-item" style={{ "--dx": `${offsetFor(index)}px` } as CSSProperties}>
      {open ? (
        <div className="pt-popover" role="dialog" aria-label="Unit review">
          <strong>Unit review</strong>
          <span>{ready ? "Review everything you learned in this unit." : "Complete all levels above to unlock this!"}</span>
          {ready && lessonId ? <Link href={`/lesson/${lessonId}?mode=practice`}>START REVIEW</Link> : <span className="pt-locked-pill">LOCKED</span>}
        </div>
      ) : null}
      <div className={`pt-ring ${ready ? "completed" : "locked"}`}>
        <button type="button" className={`pt-node ${ready ? "available" : "locked"}`} aria-expanded={open} aria-label={ready ? "Unit review" : "Unit review, locked"} onClick={() => setOpen((value) => !value)}>
          <Image src="/learn-assets/trophy_white.svg" width={36} height={32} alt="" aria-hidden />
        </button>
      </div>
    </div>
  );
}

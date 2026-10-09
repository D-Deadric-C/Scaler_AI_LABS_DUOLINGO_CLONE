"use client";

import Image from "next/image";
import type { CSSProperties } from "react";
import { useState } from "react";
import type { PathUnit } from "@/lib/types";
import { Modal } from "../Modal";
import { ArtSlot } from "./ArtSlot";
import { ChestNode, SkillNode } from "./PathNodes";
import { unitTheme } from "./pathLayout";

type Props = {
  unit: PathUnit;
  first: boolean;
  currentSkillId: number | null;
  openPathItem: string | null;
  onTogglePathItem: (key: string) => void;
  onOpenChest: (unit: PathUnit) => void;
};

export function UnitSection({ unit, first, currentSkillId, openPathItem, onTogglePathItem, onOpenChest }: Props) {
  const [guideOpen, setGuideOpen] = useState(false);
  const skills = unit.skills.slice(0, 6);
  const levels = skills.map((skill, index) => ({
    skill,
    status: skills.slice(0, index).every((previous) => previous.status === "completed") ? skill.status : "locked" as const,
  }));
  const firstCurrentIndex = levels.findIndex(({ skill, status }) => skill.id === currentSkillId && status === "available");
  const unitUnlocked = levels.some(({ status }) => status !== "locked");
  const mirrored = unit.position === 2;
  const theme = unitTheme(unit.position, unit.color);
  return (
    <section className="pt-unit" style={{ "--unit-color": theme.banner, "--node-color": theme.node, "--node-shade": theme.shade } as CSSProperties} aria-label={`Unit ${unit.position}: ${unit.objective}`}>
      <header className="pt-banner">
        <div><span>← &nbsp;SECTION 1, UNIT {unit.position}</span><h1>{unit.objective}</h1></div>
        <button type="button" aria-label={`Open Unit ${unit.position} guidebook`} onClick={() => setGuideOpen(true)}><Image src="/learn-assets/notest_section.svg" width={25} height={25} alt="" aria-hidden /></button>
      </header>
      <div className="pt-nodes">
        {first ? <Image className="pt-guide" src="/learn-assets/path-guide.svg" width={240} height={240} loading="eager" alt="A sleepy bear holding an orb" /> : null}
        {unit.position === 2 ? (
          <ArtSlot
            name="unit-2-campfire"
            className={`pt-guide pt-guide-blue${unitUnlocked ? "" : " locked"}`}
            width={240}
            height={240}
            alt="A character in blue sitting beside a campfire"
            fallback={null}
          />
        ) : null}
        {levels.slice(0, 3).map(({ skill, status }, index) => {
          const itemKey = `unit-${unit.id}-level-${index}`;
          return <SkillNode key={itemKey} skill={skill} status={status} index={index} level={index + 1} placement="below" current={index === firstCurrentIndex} open={openPathItem === itemKey} onToggle={() => onTogglePathItem(itemKey)} mirrored={mirrored} />;
        })}
        <ChestNode unit={unit} index={3} open={openPathItem === `unit-${unit.id}-chest`} onToggle={() => onTogglePathItem(`unit-${unit.id}-chest`)} onOpen={() => onOpenChest(unit)} mirrored={mirrored} />
        {levels.slice(3).map(({ skill, status }, offset) => {
          const level = offset + 4;
          const itemKey = `unit-${unit.id}-level-${level - 1}`;
          return <SkillNode key={itemKey} skill={skill} status={status} index={level} level={level} placement="above" current={level - 1 === firstCurrentIndex} open={openPathItem === itemKey} onToggle={() => onTogglePathItem(itemKey)} mirrored={mirrored} />;
        })}
      </div>
      {guideOpen ? (
        <Modal title={`Unit ${unit.position} guidebook`} onClose={() => setGuideOpen(false)}>
          <p className="guide-objective">{unit.objective}</p>
          <ul className="guide-skills">{unit.skills.map((skill) => <li key={skill.id}><strong>{skill.title}</strong><span>{skill.description}</span></li>)}</ul>
        </Modal>
      ) : null}
    </section>
  );
}

"use client";

import Image from "next/image";
import type { CSSProperties } from "react";
import { useState } from "react";
import type { PathUnit } from "@/lib/types";
import { Modal } from "../Modal";
import { ChestNode, ReviewNode, SkillNode } from "./PathNodes";
import { unitTheme } from "./pathLayout";

type Props = { unit: PathUnit; first: boolean; currentSkillId: number | null; onOpenChest: (unit: PathUnit) => void };

export function UnitSection({ unit, first, currentSkillId, onOpenChest }: Props) {
  const [guideOpen, setGuideOpen] = useState(false);
  const chestIndex = unit.skills.length;
  const theme = unitTheme(unit.position, unit.color);
  return (
    <section className="pt-unit" style={{ "--unit-color": theme.banner, "--node-color": theme.node, "--node-shade": theme.shade } as CSSProperties} aria-label={`Unit ${unit.position}: ${unit.objective}`}>
      <header className="pt-banner">
        <div><span>← &nbsp;SECTION 1, UNIT {unit.position}</span><h1>{unit.objective}</h1></div>
        <button type="button" aria-label={`Open Unit ${unit.position} guidebook`} onClick={() => setGuideOpen(true)}><Image src="/learn-assets/notest_section.svg" width={25} height={25} alt="" aria-hidden /></button>
      </header>
      <div className="pt-nodes">
        {first ? <Image className="pt-guide" src="/learn-assets/path-guide.svg" width={240} height={240} loading="eager" alt="A sleepy bear holding an orb" /> : null}
        {unit.skills.map((skill, index) => <SkillNode key={skill.id} skill={skill} index={index} current={skill.id === currentSkillId} />)}
        <ChestNode unit={unit} index={chestIndex} onOpen={() => onOpenChest(unit)} />
        <ReviewNode unit={unit} index={chestIndex + 1} />
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

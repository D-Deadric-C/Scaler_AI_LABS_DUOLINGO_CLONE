"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useBootstrap } from "@/lib/useBootstrap";
import type { PathUnit } from "@/lib/types";
import { Mascot } from "./GameIcon";
import { useToast } from "./Toast";
import { RightRail } from "./learn/RightRail";
import { StatsRow } from "./learn/StatsRow";
import { UnitSection } from "./learn/UnitSection";
import "./learn/learn.css";

/** The first unlocked, unfinished skill: where the learner should go next. */
function currentSkillId(units: PathUnit[]): number | null {
  for (const unit of units) for (const skill of unit.skills) if (skill.status === "available") return skill.id;
  return null;
}

export function LearnDashboard() {
  const { data, error, reload } = useBootstrap();
  const toast = useToast();
  const [offscreen, setOffscreen] = useState(false);
  const column = useRef<HTMLElement>(null);
  const current = data ? currentSkillId(data.units) : null;

  useEffect(() => {
    const target = column.current?.querySelector("[data-current]");
    if (!target) return;
    const observer = new IntersectionObserver(([entry]) => setOffscreen(!entry.isIntersecting), { threshold: 0.4 });
    observer.observe(target);
    return () => observer.disconnect();
  }, [current, data]);

  const openChest = useCallback(async (unit: PathUnit) => {
    try {
      const result = await api.openChest(unit.id);
      toast.show(`Chest opened: +${result.gems_awarded} gems!`);
      await reload();
    } catch (reason) {
      toast.show(reason instanceof Error ? reason.message : "Could not open the chest");
    }
  }, [reload, toast]);

  if (error) return <div className="reference-center-state"><Mascot mood="sad" /><h1>We couldn&apos;t load your path</h1><p>{error}</p><button type="button" onClick={() => location.reload()}>TRY AGAIN</button></div>;
  if (!data) return <div className="reference-center-state"><Mascot /><div className="loading-dots"><i /><i /><i /></div><p>Loading your learning path…</p></div>;

  return (
    <div className="pt-layout">
      <section className="pt-path-column" ref={column}>
        {data.units.map((unit, index) => {
          const unlocked = unit.skills.some((skill) => skill.status !== "locked");
          return (
            <div key={unit.id}>
              {index > 0 ? (
                <section className={`pt-next-section ${unlocked ? "unlocked" : ""}`}>
                  <span>{unlocked ? "UNLOCKED" : "UP NEXT"}</span>
                  <h2>{unlocked ? null : <Image src="/learn-assets/lock.svg" width={14} height={18} alt="" aria-hidden />} Section {unit.position}</h2>
                  <p>{unit.objective}</p>
                  <button type="button" onClick={() => toast.show(unlocked ? "You're already here" : "Finish the sections before it to unlock this one")}>JUMP HERE?</button>
                </section>
              ) : null}
              <UnitSection unit={unit} first={index === 0} currentSkillId={current} onOpenChest={openChest} />
            </div>
          );
        })}
        {offscreen ? (
          <button type="button" className="pt-jump" aria-label="Jump to your current lesson" onClick={() => column.current?.querySelector("[data-current]")?.scrollIntoView({ behavior: "smooth", block: "center" })}>↓</button>
        ) : null}
      </section>
      <div className="pt-rail">
        <StatsRow data={data} onChange={reload} />
        <RightRail data={data} />
      </div>
    </div>
  );
}

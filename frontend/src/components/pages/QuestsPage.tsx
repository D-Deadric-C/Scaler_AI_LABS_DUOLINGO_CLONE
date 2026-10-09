"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Quest } from "@/lib/types";
import { SupportLayout } from "./SupportLayout";

export function QuestsPage() {
  const [data, setData] = useState<{ ends_in: string; quests: Quest[] }>();
  useEffect(() => { api.quests().then(setData).catch(() => undefined); }, []);
  return (
    <SupportLayout rail="quests">
      <div className="reference-quests-page">
        <section className="reference-quests-hero"><div><h1>Welcome<br />Back!</h1><p>Complete quests to earn rewards!</p></div><Image src="/duolingo-assets/64d0bbcd8f4e6d5018502540f1e0094b.svg" width={172} height={184} alt="" aria-hidden /></section>
        <div className="reference-quests-heading"><h2>Daily Quests</h2><span>◷ {data?.ends_in ?? "…"}</span></div>
        {data?.quests.map((quest) => {
          const percent = Math.min(100, (quest.progress / Math.max(1, quest.target)) * 100);
          return (
            <article key={quest.id} className={`reference-daily-quest ${quest.completed ? "done" : ""}`}>
              <Image src="/learn-assets/Daily_quest.svg" width={56} height={56} alt="" aria-hidden />
              <div>
                <strong>{quest.title}</strong>
                <div className="reference-quest-track" role="progressbar" aria-valuemin={0} aria-valuemax={quest.target} aria-valuenow={quest.progress} aria-label={quest.title}><span style={{ width: `${percent}%` }} /><small>{quest.progress} / {quest.target}</small></div>
              </div>
              {quest.completed ? <span className="quest-done" aria-label="Quest complete">✓</span> : <Image src="/learn-assets/daily_quest_chest.svg" width={33} height={31} alt={`Reward: ${quest.reward_gems} gems`} />}
            </article>
          );
        })}
      </div>
    </SupportLayout>
  );
}

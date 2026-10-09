"use client";

import Image from "next/image";
import { Fragment, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { LeaderboardEntry } from "@/lib/types";
import { SupportLayout } from "./SupportLayout";

type League = { league: string; ends_in: string; entries: LeaderboardEntry[] };

export function LeaderboardPage() {
  const [data, setData] = useState<League>();
  useEffect(() => { api.leaderboard().then(setData).catch(() => undefined); }, []);
  return (
    <SupportLayout rail="league">
      <div className="reference-leaderboard">
        <div className="reference-league-emblem"><Image src="/duolingo-assets/660a07cd535396f03982f24bd0c3844a.svg" width={110} height={110} alt="Bronze League medal" /><Image src="/duolingo-assets/d4280fdf64d66de7390fe84802432a53.svg" width={50} height={56} alt="" aria-hidden /><Image src="/duolingo-assets/d4280fdf64d66de7390fe84802432a53.svg" width={50} height={56} alt="" aria-hidden /></div>
        <h1>{data?.league ?? "Bronze"} League</h1><p>Finish in the top 3 to advance to the next league</p>
        <div className="reference-league-period"><span>WEEKLY LEAGUE</span><strong>{data?.ends_in ?? "…"} left</strong></div>
        <section className="reference-league-standings" aria-label="League standings">
          {data?.entries.map((entry, index) => {
            const previous = data.entries[index - 1];
            return (
              <Fragment key={entry.id}>
                {entry.zone === "demotion" && previous?.zone !== "demotion" ? <div className="league-zone demotion">▼ DEMOTION ZONE ▼</div> : null}
                <div className={`reference-rank-row ${entry.is_current ? "current" : ""} ${entry.zone ?? ""}`}>
                  <b>{entry.rank}</b>
                  <span className="reference-rank-avatar" style={{ background: entry.avatar_color }}>{entry.name[0]}</span>
                  <strong>{entry.name}{entry.is_current ? " (you)" : ""}</strong>
                  <span>{entry.xp} XP</span>
                </div>
                {entry.zone === "promotion" && data.entries[index + 1]?.zone !== "promotion" ? <div className="league-zone promotion">▲ PROMOTION ZONE ▲</div> : null}
              </Fragment>
            );
          })}
        </section>
      </div>
    </SupportLayout>
  );
}

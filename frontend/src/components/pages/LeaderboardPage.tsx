"use client";

import Image from "next/image";
import { Fragment, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { LeaderboardEntry } from "@/lib/types";
import { SupportLayout } from "./SupportLayout";

type League = { league: string; ends_in: string; entries: LeaderboardEntry[] };

const MEDALS = {
  1: { ribbon: "#f4b800", disc: "#f4c002", inner: "#f3e063", digit: "#f48f02" },
  2: { ribbon: "#a9bccd", disc: "#b7c9d9", inner: "#cddae6", digit: "#8aa0b4" },
  3: { ribbon: "#c88e57", disc: "#e0a06a", inner: "#eab98a", digit: "#cf7a1c" },
} as const;

/** Original gold / silver / bronze rank ribbon for the top three places. */
function RankMedal({ rank }: { rank: 1 | 2 | 3 }) {
  const color = MEDALS[rank];
  return (
    <svg className="lb-medal" width="30" height="36" viewBox="0 0 30 36" aria-label={`Place ${rank}`} role="img">
      <path d="M5 20h20v14l-10-5-10 5z" fill={color.ribbon} />
      <circle cx="15" cy="15" r="15" fill={color.disc} />
      <circle cx="15" cy="15" r="11.5" fill={color.inner} />
      <path d="M15 3.5a11.5 11.5 0 0 1 0 23z" fill={color.disc} opacity=".28" />
      <text x="15" y="20.5" textAnchor="middle" fontSize="15" fontWeight="900" fill={color.digit}>{rank}</text>
    </svg>
  );
}

function ZoneArrow({ down }: { down?: boolean }) {
  return (
    <svg className={`lb-arrow ${down ? "down" : ""}`} width="26" height="22" viewBox="0 0 26 22" aria-hidden>
      <path d="M13 1.5c1 0 1.8.5 2.4 1.2l8.4 10.3c1 1.3.1 3.3-1.6 3.3h-4.4v3.5c0 .8-.7 1.5-1.5 1.5H10.7c-.8 0-1.5-.7-1.5-1.5v-3.5H4.8c-1.7 0-2.6-2-1.6-3.3l8.4-10.3c.6-.7 1.4-1.2 2.4-1.2z" fill="currentColor" />
    </svg>
  );
}

export function LeaderboardPage() {
  const [data, setData] = useState<League>();
  useEffect(() => { api.leaderboard().then(setData).catch(() => undefined); }, []);
  const promoted = data?.entries.filter((entry) => entry.zone === "promotion").length ?? 3;
  return (
    <SupportLayout rail="league">
      <div className="lb">
        <div className="lb-leagues">
          <Image className="lb-current" src="/leaderboard-assets/bronze.svg" width={80} height={88} alt={`${data?.league ?? "Bronze"} League shield`} priority />
          {[0, 1, 2].map((slot) => <Image key={slot} className="lb-locked" src="/leaderboard-assets/randomleague.svg" width={52} height={58} alt="Locked league" />)}
        </div>
        <h1>{data?.league ?? "Bronze"} League</h1>
        <p className="lb-rule">Top {promoted} advance to the next league</p>
        <p className="lb-days">{data ? data.ends_in : "…"}</p>
        <ol className="lb-list" aria-label="League standings">
          {data?.entries.map((entry, index) => {
            const next = data.entries[index + 1];
            return (
              <Fragment key={entry.id}>
                {entry.zone === "demotion" && data.entries[index - 1]?.zone !== "demotion" ? <li className="lb-zone demotion"><ZoneArrow down /><span>DEMOTION ZONE</span><ZoneArrow down /></li> : null}
                <li className={`lb-row ${entry.is_current ? "current" : ""}`}>
                  <span className="lb-rank">{entry.rank <= 3 ? <RankMedal rank={entry.rank as 1 | 2 | 3} /> : entry.rank}</span>
                  <span className="lb-avatar" style={{ background: entry.avatar_color }}>{entry.name[0]}</span>
                  <strong className="lb-name">{entry.name}{entry.is_current ? " (you)" : ""}</strong>
                  <span className="lb-xp">{entry.xp} XP</span>
                </li>
                {entry.zone === "promotion" && next?.zone !== "promotion" ? <li className="lb-zone promotion"><ZoneArrow /><span>PROMOTION ZONE</span><ZoneArrow /></li> : null}
              </Fragment>
            );
          })}
        </ol>
      </div>
    </SupportLayout>
  );
}

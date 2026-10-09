"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Bootstrap, LeaderboardEntry } from "@/lib/types";
import { useToast } from "../Toast";
import { BronzeBadge } from "./icons";

function LeagueCard({ data }: { data: Bootstrap }) {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  useEffect(() => { api.leaderboard().then((board) => setEntries(board.entries)).catch(() => undefined); }, [data.user.total_xp]);
  const joined = data.user.weekly_xp > 0 && data.user.today_xp + 0 >= 0;
  const rank = entries.find((entry) => entry.is_current)?.rank;
  return (
    <section className="reference-card bronze-card">
      <header><h3>Bronze League</h3><Link href="/leaderboards">VIEW LEAGUE</Link></header>
      {joined ? (
        <div className="bronze-message joined"><BronzeBadge size={64} /><div><strong>{rank ? `You're ranked #${rank}` : "You're in the league"}</strong><p>You&apos;ve earned {data.user.weekly_xp} XP this week so far</p></div></div>
      ) : (
        <div className="bronze-message"><Image src="/learn-assets/bronze_league.svg" width={70} height={55} alt="" aria-hidden /><p>Complete a lesson to join this week&apos;s leaderboard and compete against other learners</p></div>
      )}
    </section>
  );
}

export function RightRail({ data, showSuper = true }: { data: Bootstrap; showSuper?: boolean }) {
  const toast = useToast();
  const goal = Math.min(100, Math.round((data.user.today_xp / Math.max(1, data.user.daily_goal)) * 100));
  return (
    <aside className="reference-right-rail">
      {showSuper ? (
        <section className="reference-card super-card">
          <Image className="super-badge-image" src="/learn-assets/super.svg" width={87} height={23} alt="Super" />
          <h3>Try Super for free</h3>
          <p>No ads, personalized practice, and unlimited Legendary!</p>
          <Image className="super-illustration" src="/learn-assets/super_bird.svg" width={121} height={116} alt="" aria-hidden />
          <button type="button" onClick={() => toast.soon("Super")}>START MY FREE MONTH</button>
        </section>
      ) : null}
      <LeagueCard data={data} />
      <section className="reference-card quests-card">
        <header><h3>Daily Quests</h3><Link href="/quests">VIEW ALL</Link></header>
        <div className="reference-quest">
          <Image src="/learn-assets/Daily_quest.svg" width={48} height={48} alt="" aria-hidden />
          <div>
            <strong>Earn {data.user.daily_goal} XP</strong>
            <div className="quest-bar-row">
              <div className="reference-progress" role="progressbar" aria-valuemin={0} aria-valuemax={data.user.daily_goal} aria-valuenow={data.user.today_xp} aria-label="Daily XP goal"><span style={{ width: `${goal}%` }} /><small>{data.user.today_xp} / {data.user.daily_goal}</small></div>
              <Image src="/learn-assets/daily_quest_chest.svg" width={34} height={34} alt="Quest reward chest" />
            </div>
          </div>
        </div>
      </section>
      <section className="ad-block-card">
        <div className="ad-owl" aria-hidden />
        <h3>Using an ad blocker?</h3>
        <p>Support education with Super Duolingo and we&apos;ll remove ads for you</p>
        <button type="button" onClick={() => toast.soon("Super")}>TRY SUPER FOR FREE</button>
        <button type="button" className="link-button" onClick={() => toast.show("Thanks for supporting free education!")}>DISABLE AD BLOCKER</button>
      </section>
    </aside>
  );
}

"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { Bootstrap } from "@/lib/types";
import { RightRail } from "../learn/RightRail";
import { StatsRow } from "../learn/StatsRow";
import "../learn/learn.css";

export type RailKind = "standard" | "quests" | "shop" | "league" | "profile" | "none";

export function SupportFooter() {
  return (
    <div className="reference-support-footer">
      <div>{["ABOUT", "BLOG", "STORE", "EFFICACY", "CAREERS"].map((item) => <span key={item}>{item}</span>)}</div>
      <div>{["INVESTORS", "TERMS", "PRIVACY"].map((item) => <span key={item}>{item}</span>)}</div>
    </div>
  );
}

const STATUS_FACES = ["glasses", "party", "flex", "eyes", "popcorn", "flag", "angry", "hundred", "poop", "trophy", "fire", "cat"] as const;
const STATUS_EMOJI: Record<string, string> = { party: "🎉", flex: "💪", eyes: "👀", popcorn: "🍿", flag: "🇺🇸", hundred: "💯", poop: "💩", trophy: "🏆", fire: "🔥", cat: "😾" };

function LeagueRail({ data }: { data: Bootstrap }) {
  return (
    <aside className="reference-support-custom-rail">
      <StatsRow data={data} />
      <section className="reference-social-card lb-status">
        <h3>Set your status</h3>
        <div className="lb-status-avatar" aria-hidden>
          <span>{data.user.display_name[0]}</span>
          <i className="lb-status-bubble" />
          <i className="lb-status-dot" />
        </div>
        <div className="lb-status-grid">
          {STATUS_FACES.map((face) => (
            <button key={face} type="button" className={face === "glasses" || face === "angry" ? "owl" : ""} aria-label={`Status ${face}`}>
              {face === "glasses" || face === "angry"
                ? <Image src={`/leaderboard-assets/${face}.svg`} width={42} height={28} alt="" />
                : <span aria-hidden>{STATUS_EMOJI[face]}</span>}
            </button>
          ))}
        </div>
      </section>
      <SupportFooter />
    </aside>
  );
}

function ProfileRail({ data, onSoon }: { data: Bootstrap; onSoon: (feature: string) => void }) {
  return (
    <aside className="reference-support-custom-rail">
      <StatsRow data={data} />
      <section className="reference-social-card reference-friends-card"><div className="reference-friend-tabs"><strong>FOLLOWING</strong><strong>FOLLOWERS</strong></div><Image className="reference-friends-art" src="/duolingo-assets/a925a18c6be921a81bf0e13102983168.svg" width={306} height={142} alt="A group of learners" /><p>Learning is more fun and effective when you connect with others.</p></section>
      <section className="reference-social-card reference-add-friends"><h3>Add friends</h3>
        <button type="button" onClick={() => onSoon("Finding friends")}><Image src="/duolingo-assets/48b8884ac9d7513e65f3a2b54984c5c4.svg" width={35} height={35} alt="" aria-hidden />Find friends<span>❯</span></button>
        <button type="button" onClick={() => onSoon("Inviting friends")}><Image src="/duolingo-assets/146923c24e252de2fd1a124f57905359.svg" width={35} height={35} alt="" aria-hidden />Invite friends<span>❯</span></button>
      </section>
      <SupportFooter />
    </aside>
  );
}

/** Two-column frame shared by Practice, Leaderboards, Quests, Shop, Profile and Settings. */
export function SupportLayout({ children, rail = "standard", onSoon }: { children: ReactNode; rail?: RailKind; onSoon?: (feature: string) => void }) {
  const [data, setData] = useState<Bootstrap>();
  useEffect(() => { api.bootstrap().then(setData).catch(() => undefined); }, []);
  const soon = onSoon ?? (() => undefined);
  return (
    <div className={`reference-support-layout rail-${rail}`}>
      <div className="reference-support-main">{children}</div>
      {rail === "quests" ? <aside className="reference-support-quest-rail">{data && <StatsRow data={data} />}<div className="reference-quest-rail-card"><Image src="/duolingo-assets/e07e459ea20aef826b42caa71498d85f.svg" width={116} height={138} alt="" aria-hidden /><h3>Monthly challenges unlock soon!</h3><p>Complete each month&apos;s challenge to earn exclusive badges</p><Link href="/learn">START A LESSON</Link></div><SupportFooter /></aside> : null}
      {data && rail === "standard" ? <RightRail data={data} /> : null}
      {data && rail === "shop" ? <RightRail data={data} showSuper={false} /> : null}
      {data && rail === "league" ? <LeagueRail data={data} /> : null}
      {data && rail === "profile" ? <ProfileRail data={data} onSoon={soon} /> : null}
    </div>
  );
}

export function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="reference-page-heading"><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></header>;
}

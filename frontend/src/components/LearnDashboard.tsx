"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Bootstrap, PathSkill } from "@/lib/types";
import { Mascot } from "./GameIcon";

const pathPositions = [
  { left: "49%", top: "36px" },
  { left: "41%", top: "140px" },
  { left: "36%", top: "250px" },
  { left: "49%", top: "456px" },
  { left: "57%", top: "554px" },
  { left: "49%", top: "654px" },
] as const;

function LessonGlyph({ skill }: { skill: PathSkill }) {
  if (skill.status === "locked") return <span className="reference-lock" aria-hidden />;
  if (skill.status === "completed") return <span className="reference-check" aria-hidden />;
  return <span className="reference-book" aria-hidden><i /><i /></span>;
}

function SkillNode({ skill, index }: { skill: PathSkill; index: number }) {
  const [open, setOpen] = useState(false);
  const locked = skill.status === "locked";
  const position = pathPositions[index % pathPositions.length];

  return (
    <div className={`reference-step step-${index + 1}`} style={{ left: position.left, top: position.top }}>
      {open && !locked && (
        <div className="reference-node-popover" role="dialog" aria-label={`${skill.title} lesson`}>
          <strong>{skill.title}</strong>
          <span>{skill.description}</span>
          <Link href={`/lesson/${skill.lesson_id}`}>{skill.status === "completed" ? "PRACTICE" : `START +${skill.xp_reward} XP`}</Link>
        </div>
      )}
      <button
        type="button"
        className={`reference-path-node ${skill.status}`}
        onClick={() => !locked && setOpen((value) => !value)}
        disabled={locked}
        aria-label={`${skill.title}, ${skill.status}`}
        aria-expanded={locked ? undefined : open}
      >
        <LessonGlyph skill={skill} />
      </button>
    </div>
  );
}

function PathGuide() {
  return (
    <svg className="reference-path-guide" viewBox="0 0 180 225" role="img" aria-label="A sleepy bear holding a glowing orb">
      <ellipse cx="96" cy="209" rx="53" ry="10" fill="#26383f" />
      <circle cx="58" cy="40" r="11" fill="#a96746" />
      <circle cx="135" cy="40" r="11" fill="#a96746" />
      <path d="M50 79c0-35 17-55 47-55s48 20 48 55v49c0 16-7 28-14 37 11 8 17 21 17 34 0 14-10 22-24 22-9 0-17-3-27-10-9 7-18 10-27 10-14 0-25-8-25-22 0-14 6-26 18-34-8-9-13-21-13-37Z" fill="#aa6b49" />
      <path d="M76 86c7 4 14 4 21 0m8 0c7 4 14 4 20 0" stroke="#e8e4df" strokeWidth="6" strokeLinecap="round" />
      <circle cx="89" cy="92" r="3.5" fill="#252f33" /><circle cx="113" cy="92" r="3.5" fill="#252f33" />
      <ellipse cx="101" cy="116" rx="15" ry="13" fill="#8560c8" />
      <path d="M94 116c5-2 10-2 15 0" stroke="#5d4590" strokeWidth="3" strokeLinecap="round" />
      <path d="M53 156c10-8 22-4 28 4l18 25c6 9-4 22-14 16l-26-17c-13-8-17-19-6-28Zm93 0c-10-8-22-4-28 4l-18 25c-6 9 4 22 14 16l26-17c13-8 17-19 6-28Z" fill="#c473e5" />
      <circle cx="99" cy="176" r="32" fill="#58d7ea" opacity=".35" />
      <circle cx="99" cy="176" r="23" fill="#75e2f0" />
      <path d="M82 172c10-7 22-7 34 0M87 184c8-5 16-5 24 0" fill="none" stroke="#c9f7ff" strokeWidth="4" strokeLinecap="round" opacity=".8" />
    </svg>
  );
}

function StatsRow({ data }: { data: Bootstrap }) {
  const stats = data.user;
  const items = [
    { asset: "0day_streak.svg", value: stats.current_streak, label: `${stats.current_streak} day streak` },
    { asset: "bluepoints.svg", value: stats.gems, label: `${stats.gems} gems` },
    { asset: "heart.svg", value: stats.hearts, label: `${stats.hearts} hearts` },
  ];
  return (
    <div className="reference-stats" aria-label="Learner resources">
      <button type="button" aria-label="English course"><Image src="/learn-assets/usaflag.svg" width={35} height={27} alt="" /></button>
      {items.map((item) => (
        <button type="button" key={item.asset} aria-label={item.label}>
          <Image src={`/learn-assets/${item.asset}`} width={31} height={31} alt="" />
          <strong>{item.value}</strong>
        </button>
      ))}
    </div>
  );
}

function SuperIllustration() {
  return (
    <svg className="super-illustration" viewBox="0 0 116 88" aria-hidden>
      <defs><linearGradient id="superGradient" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#36e2bd" /><stop offset=".5" stopColor="#3a88ff" /><stop offset="1" stopColor="#a343f5" /></linearGradient></defs>
      <path d="M18 41c0-21 18-34 39-30 11 2 16 10 19 18 11-5 26 0 29 12 5 19-13 39-38 42-27 3-49-16-49-42Z" fill="url(#superGradient)" />
      <path d="M39 28v23m35-23v23M43 59c9 8 18 8 28 0" fill="none" stroke="#1159d8" strokeWidth="5" strokeLinecap="round" />
      <circle cx="39" cy="41" r="4" fill="#101b9c" /><circle cx="74" cy="41" r="4" fill="#101b9c" />
      <path d="M100 72c8 5 12 10 12 15-8 0-14-4-17-11Z" fill="#e92fd8" />
    </svg>
  );
}

function RightRail({ data }: { data: Bootstrap }) {
  const goal = Math.min(100, Math.round((data.user.today_xp / Math.max(1, data.user.daily_goal)) * 100));
  return (
    <aside className="reference-right-rail">
      <StatsRow data={data} />
      <section className="reference-card super-card">
        <div className="super-badge">SUPER</div>
        <h3>Try Super for free</h3>
        <p>No ads, personalized practice, and unlimited Legendary!</p>
        <SuperIllustration />
        <button type="button">START MY FREE MONTH</button>
      </section>
      <section className="reference-card bronze-card">
        <header><h3>Bronze League</h3><Link href="/leaderboards">VIEW LEAGUE</Link></header>
        <div className="bronze-message"><span className="sleeping-podium" aria-hidden><i>Z</i><i>Z</i><b /></span><p>Complete a lesson to join this week&apos;s leaderboard and compete against other learners</p></div>
      </section>
      <section className="reference-card quests-card">
        <header><h3>Daily Quests</h3><Link href="/quests">VIEW ALL</Link></header>
        <div className="reference-quest">
          <span className="quest-bolt" aria-hidden>ϟ</span>
          <div><strong>Earn {data.user.daily_goal} XP</strong><div className="reference-progress"><span style={{ width: `${goal}%` }} /><small>{data.user.today_xp} / {data.user.daily_goal}</small></div></div>
          <Image src="/learn-assets/chest.svg" width={39} height={39} alt="Quest chest" />
        </div>
      </section>
      <section className="ad-block-card">
        <div className="ad-owl" aria-hidden><span>●</span><span>●</span></div>
        <h3>Using an ad blocker?</h3>
        <p>Support education with Super Duolingo and we&apos;ll remove ads for you</p>
        <button type="button">TRY SUPER FOR FREE</button>
        <a href="#disable-ad-blocker">DISABLE AD BLOCKER</a>
      </section>
    </aside>
  );
}

export function LearnDashboard() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.bootstrap().then(setData).catch((reason: Error) => setError(reason.message));
  }, []);

  const allSkills = useMemo(() => data?.units.flatMap((unit) => unit.skills) ?? [], [data]);

  if (error) return <div className="reference-center-state"><Mascot mood="sad" /><h1>We couldn&apos;t load your path</h1><p>{error}</p><button type="button" onClick={() => location.reload()}>TRY AGAIN</button></div>;
  if (!data) return <div className="reference-center-state"><Mascot /><div className="loading-dots"><i /><i /><i /></div><p>Loading your learning path…</p></div>;

  const activeUnit = data.units[0];
  const visibleSkills = allSkills.slice(0, 6);
  return (
    <div className="reference-learn-layout">
      <section className="reference-path-column">
        <header className="reference-unit-banner">
          <div><span>←&nbsp;&nbsp; SECTION 1, UNIT {activeUnit?.position ?? 1}</span><h1>{activeUnit?.objective ?? "Start your learning journey"}</h1></div>
          <button type="button" aria-label="Open guidebook"><span className="guide-list" aria-hidden>☷</span> GUIDEBOOK</button>
        </header>
        <div className="reference-unit-divider"><i /><strong>{activeUnit?.objective ?? "Learning path"}</strong><i /></div>
        <div className="reference-path-stage">
          {visibleSkills.map((skill, index) => <SkillNode key={skill.id} skill={skill} index={index} />)}
          <div className="reference-chest-node">
            <span className="open-label">OPEN</span>
            <Image src="/learn-assets/chest.svg" width={84} height={84} alt="Open reward chest" />
          </div>
          <PathGuide />
        </div>
        <section className="reference-next-section">
          <span>UP NEXT</span>
          <h2><span className="tiny-lock" aria-hidden /> Section 2</h2>
        </section>
      </section>
      <RightRail data={data} />
    </div>
  );
}

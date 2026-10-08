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

function LessonGlyph({ skill, index }: { skill: PathSkill; index: number }) {
  const asset = skill.status === "locked"
    ? ["grayheadphones.svg", "dumbleicon.svg", "trophy_white.svg"][Math.max(0, index - 3) % 3]
    : index === 1 || skill.status === "available"
      ? "openbook_white.svg"
      : "tick_white.svg";
  return <Image src={`/learn-assets/${asset}`} width={42} height={35} alt="" aria-hidden />;
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
        <LessonGlyph skill={skill} index={index} />
      </button>
    </div>
  );
}

function PathGuide() {
  return <Image className="reference-path-guide" src="/learn-assets/path-guide.svg" width={300} height={300} alt="A sleepy bear holding an orb" />;
}

export function ReferenceStatsRow({ data }: { data: Bootstrap }) {
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
    <Image className="super-illustration" src="/learn-assets/super_bird.svg" width={121} height={116} alt="" aria-hidden />
  );
}

export function ReferenceRightRail({ data, showSuper = true }: { data: Bootstrap; showSuper?: boolean }) {
  const goal = Math.min(100, Math.round((data.user.today_xp / Math.max(1, data.user.daily_goal)) * 100));
  return (
    <aside className="reference-right-rail">
      <ReferenceStatsRow data={data} />
      {showSuper && <section className="reference-card super-card">
        <Image className="super-badge-image" src="/learn-assets/super.svg" width={87} height={23} alt="Super" />
        <h3>Try Super for free</h3>
        <p>No ads, personalized practice, and unlimited Legendary!</p>
        <SuperIllustration />
        <button type="button">START MY FREE MONTH</button>
      </section>}
      <section className="reference-card bronze-card">
        <header><h3>Bronze League</h3><Link href="/leaderboards">VIEW LEAGUE</Link></header>
        <div className="bronze-message"><Image src="/learn-assets/bronze_league.svg" width={72} height={55} alt="" aria-hidden /><p>Complete a lesson to join this week&apos;s leaderboard and compete against other learners</p></div>
      </section>
      <section className="reference-card quests-card">
        <header><h3>Daily Quests</h3><Link href="/quests">VIEW ALL</Link></header>
        <div className="reference-quest">
          <Image src="/learn-assets/Daily_quest.svg" width={48} height={48} alt="" aria-hidden />
          <div><strong>Earn {data.user.daily_goal} XP</strong><div className="reference-progress"><span style={{ width: `${goal}%` }} /><small>{data.user.today_xp} / {data.user.daily_goal}</small></div></div>
          <Image src="/learn-assets/daily_quest_chest.svg" width={39} height={39} alt="Quest chest" />
        </div>
      </section>
      <section className="ad-block-card">
        <div className="ad-owl" aria-hidden />
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
          <button type="button" aria-label="Open guidebook"><Image src="/learn-assets/notest_section.svg" width={25} height={25} alt="" aria-hidden /><span className="guidebook-label">GUIDEBOOK</span></button>
        </header>
        <div className="reference-unit-divider"><i /><strong>{activeUnit?.objective ?? "Learning path"}</strong><i /></div>
        <div className="reference-path-stage">
          {visibleSkills.map((skill, index) => <SkillNode key={skill.id} skill={skill} index={index} />)}
          <div className="reference-chest-node">
            <span className="open-label">OPEN</span>
            <Image src="/learn-assets/Chest_open.svg" width={84} height={90} alt="Open reward chest" />
          </div>
          <PathGuide />
        </div>
        <section className="reference-next-section">
          <span>UP NEXT</span>
          <h2><span className="tiny-lock" aria-hidden /> Section 2</h2>
        </section>
      </section>
      <ReferenceRightRail data={data} />
    </div>
  );
}

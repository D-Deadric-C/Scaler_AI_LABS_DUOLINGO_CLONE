"use client";

import Image from "next/image";
import Link from "next/link";
import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Bootstrap, PathSkill, PathUnit } from "@/lib/types";
import { Mascot } from "./GameIcon";
import { Modal } from "./Modal";
import { useToast } from "./Toast";

const pathPositions = [
  { left: "49%", top: "36px" },
  { left: "41%", top: "140px" },
  { left: "36%", top: "250px" },
] as const;

function LessonGlyph({ skill, index }: { skill: PathSkill; index: number }) {
  const asset = skill.status === "locked"
    ? ["grayheadphones.svg", "dumbleicon.svg", "trophy_white.svg"][index % 3]
    : index === 1 || skill.status === "available"
      ? "openbook_white.svg"
      : "tick_white.svg";
  return <Image src={`/learn-assets/${asset}`} width={42} height={35} alt="" aria-hidden />;
}

function SkillNode({ skill, index }: { skill: PathSkill; index: number }) {
  const [open, setOpen] = useState(false);
  const locked = skill.status === "locked";
  const position = pathPositions[index % pathPositions.length];
  const progress = Math.min(100, Math.round((skill.progress / Math.max(1, skill.total_lessons)) * 100));

  return (
    <div className={`reference-step step-${index + 1}`} style={{ left: position.left, top: position.top }}>
      {open && !locked && (
        <div className="reference-node-popover" role="dialog" aria-label={`${skill.title} lesson`}>
          <strong>{skill.title}</strong>
          <span>{skill.description}</span>
          <span>{skill.progress} / {skill.total_lessons} lessons complete</span>
          <Link href={`/lesson/${skill.lesson_id}${skill.status === "completed" ? "?mode=practice" : ""}`}>{skill.status === "completed" ? "PRACTICE" : `START +${skill.xp_reward} XP`}</Link>
          {skill.status === "completed" ? <Link className="legendary-link" href={`/lesson/${skill.lesson_id}?mode=legendary`}>LEGENDARY ⚡</Link> : null}
        </div>
      )}
      <div className={`reference-node-ring ${skill.status}`} style={{ "--ring-progress": `${progress}%` } as CSSProperties}>
        <button
          type="button"
          className={`reference-path-node ${skill.status}`}
          onClick={() => !locked && setOpen((value) => !value)}
          disabled={locked}
          aria-label={`${skill.title}, ${skill.status}, ${skill.progress} of ${skill.total_lessons} lessons complete`}
          aria-expanded={locked ? undefined : open}
        >
          <LessonGlyph skill={skill} index={index} />
        </button>
      </div>
      {skill.status === "completed" && <span className="reference-node-crown" aria-label="Crown earned">♛</span>}
    </div>
  );
}

function UnitPath({ unit, index }: { unit: PathUnit; index: number }) {
  const isFirst = index === 0;
  const toast = useToast();
  const [guideOpen, setGuideOpen] = useState(false);
  return (
    <section className="reference-unit" aria-label={`Unit ${unit.position}: ${unit.objective}`}>
      <header className={`reference-unit-banner${isFirst ? "" : " reference-unit-banner-next"}`}>
        <div><span>←&nbsp;&nbsp; SECTION 1, UNIT {unit.position}</span><h1>{unit.objective}</h1></div>
        <button type="button" aria-label={`Open Unit ${unit.position} guidebook`} onClick={() => setGuideOpen(true)}><Image src="/learn-assets/notest_section.svg" width={25} height={25} alt="" aria-hidden /><span className="guidebook-label">GUIDEBOOK</span></button>
      </header>
      <div className="reference-unit-divider"><i /><strong>{unit.objective}</strong><i /></div>
      <div className={`reference-path-stage${isFirst ? "" : " reference-path-stage-next"}`}>
        {unit.skills.map((skill, skillIndex) => <SkillNode key={skill.id} skill={skill} index={skillIndex} />)}
        {isFirst && <>
          <button type="button" className="reference-chest-node" onClick={() => toast.soon("Reward chests")}>
            <span className="open-label">OPEN</span>
            <Image src="/learn-assets/Chest_open.svg" width={84} height={84} alt="Open reward chest" />
          </button>
          <PathGuide />
          <div className="reference-path-preview" aria-hidden="true">
            {["grayheadphones.svg", "dumbleicon.svg", "trophy_white.svg"].map((asset, previewIndex) => <span className={`reference-preview-node preview-${previewIndex + 1}`} key={asset}><Image src={`/learn-assets/${asset}`} width={38} height={38} alt="" /></span>)}
          </div>
        </>}
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

function PathGuide() {
  return <Image className="reference-path-guide" src="/learn-assets/path-guide.svg" width={300} height={300} loading="eager" alt="A sleepy bear holding an orb" />;
}

export function ReferenceStatsRow({ data }: { data: Bootstrap }) {
  const stats = data.user;
  const router = useRouter();
  const toast = useToast();
  const items = [
    { asset: "0day_streak.svg", value: stats.current_streak, label: `${stats.current_streak} day streak`, go: "/profile" },
    { asset: "bluepoints.svg", value: stats.gems, label: `${stats.gems} gems`, go: "/shop" },
    { asset: "Daily_quest.svg", value: stats.total_xp, label: `${stats.total_xp} total XP`, go: "/profile" },
    { asset: "heart.svg", value: stats.hearts, label: `${stats.hearts} hearts`, go: "/shop" },
  ];
  return (
    <div className="reference-stats" aria-label="Learner resources">
      <button type="button" aria-label="Spanish course" onClick={() => toast.show("Spanish is the only course for now")}><Image src="/learn-assets/usaflag.svg" width={35} height={27} alt="" /></button>
      {items.map((item) => (
        <button type="button" key={item.asset} aria-label={item.label} onClick={() => router.push(item.go)}>
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
  const toast = useToast();
  const goal = Math.min(100, Math.round((data.user.today_xp / Math.max(1, data.user.daily_goal)) * 100));
  return (
    <aside className="reference-right-rail">
      <ReferenceStatsRow data={data} />
      {showSuper && <section className="reference-card super-card">
        <Image className="super-badge-image" src="/learn-assets/super.svg" width={87} height={23} alt="Super" />
        <h3>Try Super for free</h3>
        <p>No ads, personalized practice, and unlimited Legendary!</p>
        <SuperIllustration />
        <button type="button" onClick={() => toast.soon("Super")}>START MY FREE MONTH</button>
      </section>}
      <section className="reference-card bronze-card">
        <header><h3>Bronze League</h3><Link href="/leaderboards">VIEW LEAGUE</Link></header>
        <div className="bronze-message"><Image src="/learn-assets/bronze_league.svg" width={70} height={55} alt="" aria-hidden /><p>Complete a lesson to join this week&apos;s leaderboard and compete against other learners</p></div>
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
        <button type="button" onClick={() => toast.soon("Super")}>TRY SUPER FOR FREE</button>
        <button type="button" className="link-button" onClick={() => toast.show("Thanks for supporting free education!")}>DISABLE AD BLOCKER</button>
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

  if (error) return <div className="reference-center-state"><Mascot mood="sad" /><h1>We couldn&apos;t load your path</h1><p>{error}</p><button type="button" onClick={() => location.reload()}>TRY AGAIN</button></div>;
  if (!data) return <div className="reference-center-state"><Mascot /><div className="loading-dots"><i /><i /><i /></div><p>Loading your learning path…</p></div>;

  return (
    <div className="reference-learn-layout">
      <section className="reference-path-column">
        {data.units.map((unit, index) => <div key={unit.id}>
          {index > 0 && <section className={`reference-next-section${unit.skills.some((skill) => skill.status !== "locked") ? " unlocked" : ""}`}>
            <span>{unit.skills.some((skill) => skill.status !== "locked") ? "UNLOCKED" : "UP NEXT"}</span>
            <h2>{unit.skills.every((skill) => skill.status === "locked") && <span className="tiny-lock" aria-hidden />} Section {unit.position}</h2>
          </section>}
          <UnitPath unit={unit} index={index} />
        </div>)}
      </section>
      <ReferenceRightRail data={data} />
    </div>
  );
}

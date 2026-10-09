"use client";

import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import { useHoverMenu } from "@/lib/useHoverMenu";
import type { Bootstrap } from "@/lib/types";
import { GemIcon } from "../lesson/Icons";
import { useToast } from "../Toast";
import { ArtSlot } from "./ArtSlot";
import { FlameIcon, HeartsRow } from "./icons";

type Which = "course" | "streak" | "gems" | "hearts";

function timeUntil(iso: string | null): string {
  if (!iso) return "";
  const minutes = Math.max(1, Math.round((new Date(iso).getTime() - Date.now()) / 60000));
  return minutes >= 60 ? `${Math.round(minutes / 60)} hour${Math.round(minutes / 60) === 1 ? "" : "s"}` : `${minutes} minute${minutes === 1 ? "" : "s"}`;
}

const DAY_MS = 86_400_000;
const isoOf = (time: number) => new Date(time).toISOString().slice(0, 10);

/** Sunday-first week containing `today` (an ISO date), with each day marked done when it falls inside the current streak. */
function streakWeek(today: string, lastActive: string | null, streak: number) {
  const base = Date.parse(`${today}T00:00:00Z`);
  const sunday = base - new Date(base).getUTCDay() * DAY_MS;
  const last = lastActive && streak > 0 ? Date.parse(`${lastActive}T00:00:00Z`) : null;
  const first = last === null ? null : last - (streak - 1) * DAY_MS; // a streak of N covers N consecutive days ending on the last active day
  return Array.from({ length: 7 }, (_, index) => {
    const time = sunday + index * DAY_MS;
    return {
      label: "SMTWTFS"[index],
      name: new Date(time).toLocaleDateString("en", { weekday: "long", timeZone: "UTC" }),
      done: last !== null && first !== null && time >= first && time <= last,
      today: isoOf(time) === today,
    };
  });
}

function StreakPopover({ streak, longest, today, lastActive, onSoon }: { streak: number; longest: number; today: string; lastActive: string | null; onSoon: (feature: string) => void }) {
  const week = streakWeek(today, lastActive, streak);
  return (
    <>
      <section className="pt-streak-top">
        <div><h3>{streak} day streak</h3><p>{streak === 0 ? "Do a lesson today to start a streak!" : streak >= longest ? "You've earned your longest streak ever!" : "Keep it going — practice every day."}</p></div>
        <ArtSlot name="flame-big" width={70} height={85} fallback={<FlameIcon lit={streak > 0} size={64} />} />
        <div className="pt-week" role="list" aria-label="This week">
          {week.map((day) => (
            <div key={day.name} role="listitem" aria-label={`${day.name}${day.today ? " (today)" : ""}: ${day.done ? "streak day" : "no streak"}`} className={day.today ? "today" : ""}><span>{day.label}</span><i className={day.done ? "done" : ""}>{day.done ? <FlameIcon lit size={20} /> : null}</i></div>
          ))}
        </div>
      </section>
      <section className="pt-friend-streaks"><div><strong>Friend Streaks</strong><span>0 active Friend Streaks</span><button type="button" onClick={() => onSoon("Friend Streaks")}>VIEW LIST</button></div><ArtSlot name="friend-streak" width={142} height={136} fallback={null} /></section>
      <section className="pt-society"><span aria-hidden>{streak >= 7 ? "🏅" : "🔒"}</span><div><strong>Streak Society</strong><p>{streak >= 7 ? "You're in the Streak Society — keep your streak going!" : "Reach a 7 day streak to join the Streak Society and earn exclusive rewards."}</p></div></section>
      <button type="button" className="pt-wide-button" onClick={() => onSoon("Streak details")}>VIEW MORE</button>
    </>
  );
}

function HeartsPopover({ data, close, onChange }: { data: Bootstrap; close: () => void; onChange: () => void }) {
  const toast = useToast();
  const { user } = data;
  const full = user.hearts >= user.max_hearts;
  const refill = async () => {
    try { toast.show((await api.gemRefill()).message); onChange(); }
    catch (reason) { toast.show(reason instanceof Error ? reason.message : "Could not refill hearts"); }
    close();
  };
  return (
    <>
      <h3 className="pt-center">Hearts</h3>
      <HeartsRow hearts={user.hearts} max={user.max_hearts} />
      <p className="pt-next-heart">{full ? "You have full hearts" : <>Next heart in <b>{timeUntil(user.next_heart_at)}</b></>}</p>
      <p className="pt-center pt-muted">{user.hearts > 0 ? "You still have hearts left! Keep on learning" : "You're out of hearts — refill or practice to keep going"}</p>
      <button type="button" className="pt-option" onClick={() => toast.soon("Super")}><strong>UNLIMITED HEARTS</strong><em>FREE TRIAL</em></button>
      <button type="button" className="pt-option" disabled={full || user.gems < 350} onClick={refill}><strong>REFILL HEARTS</strong><span><GemIcon size={18} /> 350</span></button>
      <Link className="pt-option" href={data.practice_lesson_id ? `/lesson/${data.practice_lesson_id}?mode=practice` : "/practice"} onClick={close}><strong>PRACTICE TO EARN HEARTS</strong></Link>
    </>
  );
}

/**
 * Flag / streak / gems / hearts. Each opens its own popover (it never navigates away):
 * hovering shows it, clicking pins it open, and Escape or a click outside closes it.
 */
export function StatsRow({ data, onChange }: { data: Bootstrap; onChange?: () => void }) {
  const { user } = data;
  const toast = useToast();
  const { open, root, caret, dismiss, triggerProps, panelProps } = useHoverMenu<Which>();
  const lit = user.current_streak > 0;
  return (
    <div className="pt-stats" ref={root}>
      <button type="button" className={open === "course" ? "open" : ""} aria-label="Spanish course" {...triggerProps("course")}><Image src="/learn-assets/usaflag.svg" width={35} height={27} alt="" /></button>
      <button type="button" className={`${open === "streak" ? "open" : ""} streak ${lit ? "lit" : ""}`} aria-label={`${user.current_streak} day streak`} {...triggerProps("streak")}><FlameIcon lit={lit} size={30} /><strong>{user.current_streak}</strong></button>
      <button type="button" className={`${open === "gems" ? "open" : ""} gems`} aria-label={`${user.gems} gems`} {...triggerProps("gems")}><GemIcon size={30} /><strong>{user.gems}</strong></button>
      <button type="button" className={`${open === "hearts" ? "open" : ""} hearts`} aria-label={`${user.hearts} hearts`} {...triggerProps("hearts")}><Image src="/learn-assets/heart.svg" width={31} height={31} alt="" /><strong>{user.hearts}</strong></button>
      {open ? (
        <div className={`pt-stat-popover ${open}`} style={{ "--caret": `${caret}px` } as React.CSSProperties} role="dialog" aria-label={open} {...panelProps}>
          {open === "course" ? (
            <>
              <h3 className="pt-muted-title">MY COURSES</h3>
              <button type="button" className="pt-course chosen" onClick={dismiss}><Image src="/learn-assets/usaflag.svg" width={40} height={30} alt="" />Spanish</button>
              <button type="button" className="pt-course" onClick={() => { toast.soon("More courses"); dismiss(); }}><span className="pt-plus" aria-hidden>+</span>Add a new course</button>
            </>
          ) : null}
          {open === "streak" ? <StreakPopover streak={user.current_streak} longest={user.longest_streak} today={user.today} lastActive={user.last_active_date} onSoon={toast.soon} /> : null}
          {open === "gems" ? (
            <div className="pt-gems-pop"><ArtSlot name="gems-chest" width={80} fallback={<Image src="/learn-assets/bluepoints.svg" width={64} height={64} alt="" aria-hidden />} /><div><h3>Gems</h3><p>You have {user.gems} gems</p><Link href="/shop" onClick={dismiss}>GO TO SHOP</Link></div></div>
          ) : null}
          {open === "hearts" ? <HeartsPopover data={data} close={dismiss} onChange={onChange ?? (() => undefined)} /> : null}
        </div>
      ) : null}
    </div>
  );
}

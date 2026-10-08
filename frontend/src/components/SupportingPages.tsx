"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { Achievement, Bootstrap, LeaderboardEntry, UserStats } from "@/lib/types";
import { GameIcon, Mascot } from "./GameIcon";
import { ReferenceRightRail, ReferenceStatsRow } from "./LearnDashboard";

type RailKind = "standard" | "quests" | "shop" | "league" | "profile" | "none";

function SupportFooter() {
  return <div className="reference-support-footer">ABOUT　 BLOG　 STORE　 EFFICACY　 CAREERS<br />INVESTORS　 TERMS　 PRIVACY</div>;
}

function LeagueRail({ data }: { data: Bootstrap }) {
  return <aside className="reference-support-custom-rail"><ReferenceStatsRow data={data} /><section className="reference-social-card"><h3>Set your status</h3><div className="reference-status-avatar">{data.user.display_name[0]}</div><div className="reference-status-icons">{["😎", "🎉", "💪", "👀", "🍿", "🇺🇸", "🦉", "💯", "🏆", "🥇"].map((icon, index) => <span key={`${icon}-${index}`}>{icon}</span>)}</div></section><SupportFooter /></aside>;
}

function ProfileRail({ data }: { data: Bootstrap }) {
  return <aside className="reference-support-custom-rail"><ReferenceStatsRow data={data} /><section className="reference-social-card reference-friends-card"><div className="reference-friend-tabs"><strong>FOLLOWING</strong><strong>FOLLOWERS</strong></div><Image className="reference-friends-art" src="/duolingo-assets/a925a18c6be921a81bf0e13102983168.svg" width={306} height={142} alt="A group of Duolingo learners" /><p>Learning is more fun and effective when you connect with others.</p></section><section className="reference-social-card reference-add-friends"><h3>Add friends</h3><p><Image src="/duolingo-assets/48b8884ac9d7513e65f3a2b54984c5c4.svg" width={35} height={35} alt="" aria-hidden />Find friends　<span>❯</span></p><p><Image src="/duolingo-assets/146923c24e252de2fd1a124f57905359.svg" width={35} height={35} alt="" aria-hidden />Invite friends　<span>❯</span></p></section><SupportFooter /></aside>;
}

function SupportLayout({ children, rail = "standard" }: { children: ReactNode; rail?: RailKind }) {
  const [data, setData] = useState<Bootstrap>();
  useEffect(() => { api.bootstrap().then(setData).catch(() => undefined); }, []);
  return (
    <div className={`reference-support-layout rail-${rail}`}>
      <div className="reference-support-main">{children}</div>
      {rail === "quests" ? <aside className="reference-support-quest-rail">{data && <ReferenceStatsRow data={data} />}<div className="reference-quest-rail-card"><Image src="/duolingo-assets/e07e459ea20aef826b42caa71498d85f.svg" width={116} height={138} alt="" aria-hidden /><h3>Monthly challenges unlock soon!</h3><p>Complete each month&apos;s challenge to earn exclusive badges</p><Link href="/learn">START A LESSON</Link></div><SupportFooter /></aside> : null}
      {data && rail === "standard" ? <ReferenceRightRail data={data} /> : null}
      {data && rail === "shop" ? <ReferenceRightRail data={data} showSuper={false} /> : null}
      {data && rail === "league" ? <LeagueRail data={data} /> : null}
      {data && rail === "profile" ? <ProfileRail data={data} /> : null}
    </div>
  );
}

function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="reference-page-heading"><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></header>;
}

export function LeaderboardPage() {
  const [data, setData] = useState<{ league: string; ends_in: string; entries: LeaderboardEntry[] }>();
  useEffect(() => { api.leaderboard().then(setData).catch(() => undefined); }, []);
  return <SupportLayout rail="league"><div className="reference-leaderboard">
    <div className="reference-league-emblem"><Image src="/duolingo-assets/660a07cd535396f03982f24bd0c3844a.svg" width={110} height={110} alt="Bronze League medal" /><Image src="/duolingo-assets/d4280fdf64d66de7390fe84802432a53.svg" width={50} height={56} alt="" aria-hidden /><Image src="/duolingo-assets/d4280fdf64d66de7390fe84802432a53.svg" width={50} height={56} alt="" aria-hidden /></div>
    <h1>Bronze League</h1><p>Finish in the top 3 to advance to the next league</p>
    <div className="reference-league-period"><span>WEEKLY LEAGUE</span><strong>{data?.ends_in ?? "Loading…"} left</strong></div>
    <section className="reference-league-standings" aria-label="League standings">
      {data?.entries.map((entry) => <div key={entry.id} className={`reference-rank-row ${entry.is_current ? "current" : ""}`}><b>{entry.rank}</b><span className="reference-rank-avatar" style={{ background: entry.avatar_color }}>{entry.name[0]}</span><strong>{entry.name}</strong><span>{entry.xp} XP</span></div>)}
    </section>
  </div></SupportLayout>;
}

export function ProfilePage() {
  const [user, setUser] = useState<UserStats>();
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  useEffect(() => { Promise.all([api.me(), api.achievements()]).then(([me, badges]) => { setUser(me); setAchievements(badges); }).catch(() => undefined); }, []);
  if (!user) return <SupportLayout rail="profile"><div className="reference-support-loading"><Mascot /><p>Loading your profile…</p></div></SupportLayout>;
  const stats = [
    { icon: "flame", value: user.current_streak, label: "Day streak" },
    { icon: "bolt", value: user.total_xp, label: "Total XP" },
    { icon: "trophy", value: "Bronze", label: "Current league" },
    { icon: "gem", value: 0, label: "Top 3 finishes" },
  ];
  return <SupportLayout rail="profile"><div className="reference-profile">
    <section className="reference-profile-art"><Image className="reference-profile-silhouette" src="/duolingo-assets/05147135350f5234cbf147813eee4db8.svg" width={225} height={225} alt="Add a profile photo" /><button type="button" aria-label="Edit profile placeholder"><Image src="/duolingo-assets/0aa7f1c48ca54ecad58016ec87276fde.svg" width={24} height={24} alt="" aria-hidden /></button></section>
    <section className="reference-profile-hero"><div><h1>{user.display_name}</h1><p>{user.username}</p><span>Learning Spanish</span><strong>0 Following　 0 Followers</strong></div><Image src="/learn-assets/usaflag.svg" width={34} height={27} alt="English course" /></section>
    <h2>Statistics</h2><section className="reference-profile-stats">{stats.map((stat) => <div key={stat.label}><GameIcon name={stat.icon} size={38} /><strong>{stat.value}</strong><span>{stat.label}</span></div>)}</section>
    <h2>Achievements</h2><section className="reference-achievements">{achievements.map((achievement) => <article key={achievement.id} className={achievement.earned ? "earned" : ""}><span className="reference-achievement-icon">{achievement.earned ? "★" : "♙"}</span><div><strong>{achievement.title}</strong><p>{achievement.description}</p><div className="reference-achievement-track"><span style={{ width: `${Math.min(100, ((achievement.progress ?? 0) / Math.max(1, achievement.threshold ?? 1)) * 100)}%` }} /></div><small>{achievement.progress} / {achievement.threshold}</small></div></article>)}</section>
  </div></SupportLayout>;
}

export function PracticePage() {
  return <SupportLayout><div className="reference-practice-hub">
    <h1>Today&apos;s Review</h1>
    <section className="reference-unit-rewind"><Image src="/learn-assets/super.svg" width={78} height={23} alt="Super" /><h2>Unit Rewind</h2><p>Keep your memory fresh with this review of Unit 1!</p><Link href="/shop">UNLOCK</Link><Image className="reference-rewind-art" src="/duolingo-assets/071159d03311fcb556c4dfe730941de1.svg" width={170} height={170} alt="" aria-hidden /></section>
    <h2 className="reference-practice-section-title">Conversation</h2>
    <Link className="reference-practice-tile" href="/lesson/2?mode=practice"><div><strong>Listen</strong><Image src="/learn-assets/super.svg" width={76} height={22} alt="Super" /></div><p>Boost your listening skills with an audio-only session</p><span className="reference-practice-tile-art" aria-hidden>🎧</span></Link>
    <h2 className="reference-practice-section-title">Your collections</h2>
    <Link className="reference-practice-tile" href="/lesson/2?mode=practice"><div><strong>Mistakes</strong><Image src="/learn-assets/super.svg" width={76} height={22} alt="Super" /></div><p>Start a personalized lesson to practice your mistakes</p><span className="reference-practice-tile-art" aria-hidden>✦</span></Link>
    <Link className="reference-practice-tile" href="/lesson/2?mode=practice"><div><strong>Stories</strong></div><p>Reread a story to review words in context</p><Image className="reference-practice-tile-art image" src="/learn-assets/openbook_white.svg" width={85} height={75} alt="" aria-hidden /></Link>
    <Link className="reference-practice-free" href="/lesson/2?mode=practice">Practice to earn hearts</Link>
  </div></SupportLayout>;
}

export function QuestsPage() {
  const [user, setUser] = useState<UserStats>();
  useEffect(() => { api.me().then(setUser).catch(() => undefined); }, []);
  const xp = user?.today_xp ?? 0;
  const goal = user?.daily_goal ?? 10;
  return <SupportLayout rail="quests"><div className="reference-quests-page">
    <section className="reference-quests-hero"><div><h1>Welcome<br />Back!</h1><p>Complete quests to earn rewards!</p></div><Image src="/duolingo-assets/64d0bbcd8f4e6d5018502540f1e0094b.svg" width={172} height={184} alt="Duo celebrating" /></section>
    <div className="reference-quests-heading"><h2>Daily Quests</h2><span>◷ 23 HOURS</span></div>
    <article className="reference-daily-quest"><Image src="/learn-assets/Daily_quest.svg" width={56} height={56} alt="" aria-hidden /><div><strong>Earn {goal} XP</strong><div className="reference-quest-track"><span style={{ width: `${Math.min(100, xp / Math.max(1, goal) * 100)}%` }} /><small>{xp} / {goal}</small></div></div><Image src="/learn-assets/daily_quest_chest.svg" width={33} height={31} alt="Quest reward chest" /></article>
    <article className="reference-locked-quest"><Image src="/learn-assets/lock.svg" width={29} height={36} alt="" aria-hidden /><strong>More quests unlock soon</strong></article>
  </div></SupportLayout>;
}

export function ShopPage() {
  const [message, setMessage] = useState("");
  const [user, setUser] = useState<UserStats>();
  useEffect(() => { api.me().then(setUser).catch(() => undefined); }, []);
  const heartsFull = user ? user.hearts >= user.max_hearts : false;
  return <SupportLayout rail="shop"><div className="reference-shop">
    <section className="reference-shop-promo"><Image src="/learn-assets/super_bird.svg" width={115} height={120} alt="" aria-hidden /><Image src="/learn-assets/super.svg" width={80} height={24} alt="Super" /><h2>Get started with a 1 month free trial on Super</h2><button type="button" onClick={() => setMessage("Super subscriptions are coming soon.")}>START MY FREE MONTH</button></section>
    <section className="reference-shop-section"><h1>Hearts</h1><article className="reference-shop-item"><Image src="/duolingo-assets/547ffcf0e6256af421ad1a32c26b8f1a.svg" width={68} height={68} alt="" aria-hidden /><div><h2>Refill Hearts</h2><p>Get full hearts so you can worry less about making mistakes in a lesson</p></div><button type="button" disabled={heartsFull} onClick={async () => { try { const value = await api.refill(); setMessage(value.message); setUser(await api.me()); } catch { setMessage("Your hearts are already full."); } }}>{heartsFull ? "FULL" : "PRACTICE FREE"}</button></article><article className="reference-shop-item"><Image className="reference-unlimited-heart" src="/duolingo-assets/4f3842c690acf9bf0d4b06e6ab2fffcf.svg" width={72} height={72} alt="" aria-hidden /><div><h2>Unlimited Hearts</h2><p>Never run out of hearts with Super!</p></div><button type="button" onClick={() => setMessage("Super subscriptions are coming soon.")}>FREE TRIAL</button></article></section>
    <section className="reference-shop-section"><h1>Power-Ups</h1><article className="reference-shop-item"><span className="reference-freeze-icon" aria-hidden>◆</span><div><h2>Streak Freeze <small>0 / 2 EQUIPPED</small></h2><p>Streak Freeze allows your streak to remain in place for one full day of inactivity.</p></div><button type="button" onClick={() => setMessage("Streak Freeze is coming soon.")}><span>GET FOR:</span><Image src="/learn-assets/bluepoints.svg" width={20} height={24} alt="" /> 200</button></article></section>
    {message && <div className="success-toast" role="status">{message}</div>}
  </div></SupportLayout>;
}

export function SettingsPage() {
  const [dark, setDark] = useState(false);
  const [sound, setSound] = useState(true);
  const [message, setMessage] = useState("");
  useEffect(() => { api.me().then((user) => { setDark(user.dark_mode); document.documentElement.dataset.theme = user.dark_mode ? "dark" : "light"; }).catch(() => undefined); }, []);
  const save = async () => { await api.updateSettings({ dark_mode: dark }); setMessage("Preferences saved"); };
  return <SupportLayout rail="none"><div className="reference-settings"><PageHeader eyebrow="ACCOUNT" title="Settings" description="Manage your learning preferences." /><section className="reference-settings-card"><Setting title="Sound effects" description="Play sounds during lessons" checked={sound} setChecked={setSound} /><Setting title="Dark mode" description="Use the dark Duolingo theme" checked={dark} setChecked={(value) => { setDark(value); document.documentElement.dataset.theme = value ? "dark" : "light"; }} /><Setting title="Motivational messages" description="Show reminders and celebrations" checked setChecked={() => undefined} /></section><button type="button" className="reference-settings-save" onClick={save}>SAVE CHANGES</button>{message && <div className="success-toast" role="status">✓ {message}</div>}</div></SupportLayout>;
}

function Setting({ title, description, checked, setChecked }: { title: string; description: string; checked: boolean; setChecked: (checked: boolean) => void }) {
  return <label className="reference-setting-row"><span><strong>{title}</strong><small>{description}</small></span><input type="checkbox" checked={checked} onChange={(event) => setChecked(event.target.checked)} /><i /></label>;
}

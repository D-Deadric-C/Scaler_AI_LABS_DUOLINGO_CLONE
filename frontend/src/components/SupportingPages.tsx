"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Achievement, LeaderboardEntry, UserStats } from "@/lib/types";
import { GameIcon, Mascot } from "./GameIcon";

function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="page-heading"><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></header>;
}

export function LeaderboardPage() {
  const [data, setData] = useState<{ league: string; ends_in: string; entries: LeaderboardEntry[] }>();
  useEffect(() => { api.leaderboard().then(setData); }, []);
  return <div className="support-page"><PageHeader eyebrow="WEEKLY LEAGUE" title="Bronze League" description={`Top learners advance · ${data?.ends_in ?? "Loading"} remaining`}/><div className="podium">{data?.entries.slice(0, 3).map((entry, index) => <div key={entry.id} className={`podium-user place-${index + 1}`}><span className="podium-rank">{index + 1}</span><span className="avatar large" style={{ background: entry.avatar_color }}>{entry.name[0]}</span><strong>{entry.name}</strong><span>{entry.xp} XP</span></div>)}</div><section className="ranking-list">{data?.entries.map((entry) => <div key={entry.id} className={entry.is_current ? "current" : ""}><b>{entry.rank}</b><span className="avatar" style={{ background: entry.avatar_color }}>{entry.name[0]}</span><strong>{entry.name}</strong><span>{entry.xp} XP</span></div>)}</section></div>;
}

export function ProfilePage() {
  const [user, setUser] = useState<UserStats>();
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  useEffect(() => { Promise.all([api.me(), api.achievements()]).then(([me, badges]) => { setUser(me); setAchievements(badges); }); }, []);
  if (!user) return <div className="center-state"><Mascot/><p>Loading your profile…</p></div>;
  return <div className="support-page"><section className="profile-hero"><span className="avatar hero-avatar" style={{ background: user.avatar_color }}>{user.display_name[0]}</span><div><h1>{user.display_name}</h1><p>@{user.username} · Joined the Spanish course</p><span>Following 12 · Followers 8</span></div></section><h2 className="section-heading">Statistics</h2><div className="stat-grid"><div><GameIcon name="flame"/><strong>{user.current_streak}</strong><span>Day streak</span></div><div><GameIcon name="bolt"/><strong>{user.total_xp}</strong><span>Total XP</span></div><div><GameIcon name="trophy"/><strong>{user.longest_streak}</strong><span>Longest streak</span></div><div><GameIcon name="gem"/><strong>{user.gems}</strong><span>Gems earned</span></div></div><h2 className="section-heading">Achievements</h2><div className="achievement-grid">{achievements.map((item) => <div key={item.id} className={item.earned ? "earned" : ""}><span className="achievement-medal">{item.earned ? "🏅" : "◌"}</span><strong>{item.title}</strong><p>{item.description}</p><div className="mini-progress"><span style={{ width: `${Math.min(100, ((item.progress ?? 0) / (item.threshold ?? 1)) * 100)}%` }}/></div><small>{item.progress} / {item.threshold}</small></div>)}</div></div>;
}

export function PracticePage() {
  return <div className="support-page"><PageHeader eyebrow="PRACTICE HUB" title="Turn mistakes into strength" description="Personalized sessions from the skills you have unlocked."/><div className="feature-cards"><article className="feature-card featured"><Mascot size={100}/><div><span>SMART REVIEW</span><h2>Practice your recent mistakes</h2><p>Practice without losing hearts, then refill them from the completion screen.</p><Link className="game-button" href="/lesson/2?mode=practice">START PRACTICE</Link></div></article><article className="feature-card"><GameIcon name="bolt" size={60}/><h2>Timed challenge</h2><p>Beat 75 seconds and earn double XP.</p><Link className="game-button blue" href="/lesson/2?mode=legendary">PLAY LEGENDARY</Link></article></div></div>;
}

export function QuestsPage() {
  return <div className="support-page"><PageHeader eyebrow="QUESTS" title="Today’s challenges" description="Complete quests to earn gems and keep your momentum."/><div className="quest-list"><Quest icon="bolt" title="Earn 20 XP" progress={75}/><Quest icon="book" title="Complete 2 lessons" progress={50}/><Quest icon="flame" title="Get 5 answers correct in a row" progress={40}/></div></div>;
}

function Quest({ icon, title, progress }: { icon: string; title: string; progress: number }) { return <article><GameIcon name={icon} size={54}/><div><strong>{title}</strong><div className="mini-progress large"><span style={{ width: `${progress}%` }}/></div><small>{progress}% complete</small></div><span className="quest-reward"><GameIcon name="gem" size={22}/> 10</span></article>; }

export function ShopPage() {
  const [message, setMessage] = useState("");
  return <div className="support-page"><PageHeader eyebrow="SHOP" title="Power-ups" description="Use your gems to protect your learning momentum."/><div className="shop-grid"><article><GameIcon name="heart" size={66}/><div><h2>Heart refill</h2><p>Restore all five hearts instantly.</p></div><button className="game-button" onClick={async () => { try { const value = await api.refill(); setMessage(value.message); } catch { setMessage("Your hearts are already full."); } }}>PRACTICE FREE</button></article><article><GameIcon name="flame" size={66}/><div><h2>Streak freeze</h2><p>Protect your streak for one missed day.</p></div><button className="game-button blue"><GameIcon name="gem" size={22}/> 200</button></article></div>{message && <div className="success-toast">{message}</div>}</div>;
}

export function SettingsPage() {
  const [dark, setDark] = useState(false);
  const [sound, setSound] = useState(true);
  const [message, setMessage] = useState("");
  useEffect(() => { api.me().then((user) => { setDark(user.dark_mode); document.documentElement.dataset.theme = user.dark_mode ? "dark" : "light"; }); }, []);
  const save = async () => { await api.updateSettings({ dark_mode: dark }); setMessage("Preferences saved"); };
  return <div className="support-page"><PageHeader eyebrow="PREFERENCES" title="Settings" description="Tune the learning experience to suit you."/><section className="settings-card"><Setting title="Sound effects" description="Hear feedback and celebrations" checked={sound} setChecked={setSound}/><Setting title="Dark mode" description="Use a low-light color theme" checked={dark} setChecked={(value) => { setDark(value); document.documentElement.dataset.theme = value ? "dark" : "light"; }}/><Setting title="Motivational messages" description="Let Pip cheer you along" checked setChecked={() => undefined}/></section><button className="game-button" onClick={save}>SAVE CHANGES</button>{message && <div className="success-toast">✓ {message}</div>}</div>;
}

function Setting({ title, description, checked, setChecked }: { title: string; description: string; checked: boolean; setChecked: (checked: boolean) => void }) { return <label className="setting-row"><span><strong>{title}</strong><small>{description}</small></span><input type="checkbox" checked={checked} onChange={(event) => setChecked(event.target.checked)}/><i/></label>; }

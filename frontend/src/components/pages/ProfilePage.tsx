"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Achievement, Activity, UserStats } from "@/lib/types";
import { GameIcon, Mascot } from "../GameIcon";
import { useToast } from "../Toast";
import { SupportLayout } from "./SupportLayout";

function ActivityCalendar({ activity }: { activity: Activity }) {
  return (
    <section className="profile-activity" aria-label="Last 14 days of activity">
      <div className="activity-grid">
        {activity.days.map((day) => (
          <div key={day.date} className={`activity-day ${day.goal_met ? "met" : day.xp > 0 ? "some" : ""}`} title={`${day.date}: ${day.xp} XP, ${day.lessons} lessons`}>
            <span>{new Date(`${day.date}T00:00:00`).toLocaleDateString("en", { weekday: "narrow" })}</span>
            <i aria-hidden />
          </div>
        ))}
      </div>
      <p>Longest streak: <strong>{activity.longest_streak} days</strong></p>
    </section>
  );
}

export function ProfilePage() {
  const toast = useToast();
  const [user, setUser] = useState<UserStats>();
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [activity, setActivity] = useState<Activity>();
  useEffect(() => {
    Promise.all([api.me(), api.achievements(), api.activity(14)])
      .then(([me, badges, days]) => { setUser(me); setAchievements(badges); setActivity(days); })
      .catch(() => undefined);
  }, []);
  if (!user) return <SupportLayout rail="profile" onSoon={toast.soon}><div className="reference-support-loading"><Mascot /><p>Loading your profile…</p></div></SupportLayout>;
  const stats = [
    { icon: "flame", value: user.current_streak, label: "Day streak" },
    { icon: "bolt", value: user.total_xp, label: "Total XP" },
    { icon: "trophy", value: "Bronze", label: "Current league" },
    { icon: "gem", value: user.gems, label: "Gems" },
  ];
  return (
    <SupportLayout rail="profile" onSoon={toast.soon}>
      <div className="reference-profile">
        <section className="reference-profile-art"><Image className="reference-profile-silhouette" src="/duolingo-assets/05147135350f5234cbf147813eee4db8.svg" width={225} height={225} alt="Add a profile photo" /><button type="button" aria-label="Edit profile" onClick={() => toast.soon("Profile editing")}><Image src="/duolingo-assets/0aa7f1c48ca54ecad58016ec87276fde.svg" width={24} height={24} alt="" aria-hidden /></button></section>
        <section className="reference-profile-hero"><div><h1>{user.display_name}</h1><p>{user.username}</p><span>Learning Spanish</span><strong>0 Following　 0 Followers</strong></div><Image src="/learn-assets/usaflag.svg" width={34} height={27} alt="English course" /></section>
        <h2>Statistics</h2>
        <section className="reference-profile-stats">{stats.map((stat) => <div key={stat.label}><GameIcon name={stat.icon} size={38} /><strong>{stat.value}</strong><span>{stat.label}</span></div>)}</section>
        <h2>Activity</h2>
        {activity ? <ActivityCalendar activity={activity} /> : null}
        <h2>Achievements</h2>
        <section className="reference-achievements">{achievements.map((achievement) => <article key={achievement.id} className={achievement.earned ? "earned" : ""}><span className="reference-achievement-icon">{achievement.earned ? "★" : "♙"}</span><div><strong>{achievement.title}</strong><p>{achievement.description}</p><div className="reference-achievement-track"><span style={{ width: `${Math.min(100, ((achievement.progress ?? 0) / Math.max(1, achievement.threshold ?? 1)) * 100)}%` }} /></div><small>{achievement.progress} / {achievement.threshold}</small></div></article>)}</section>
      </div>
    </SupportLayout>
  );
}

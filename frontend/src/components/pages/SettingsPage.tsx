"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { setSoundEnabled, useSoundEnabled } from "../lesson/sounds";
import { useToast } from "../Toast";
import { PageHeader, SupportLayout } from "./SupportLayout";

const GOALS = [10, 20, 30, 50];

function Setting({ title, description, checked, setChecked }: { title: string; description: string; checked: boolean; setChecked: (checked: boolean) => void }) {
  return <label className="reference-setting-row"><span><strong>{title}</strong><small>{description}</small></span><input type="checkbox" checked={checked} onChange={(event) => setChecked(event.target.checked)} /><i /></label>;
}

export function SettingsPage() {
  const toast = useToast();
  const sound = useSoundEnabled();
  const [dark, setDark] = useState(false);
  const [goal, setGoal] = useState(20);
  const [motivation, setMotivation] = useState(true);
  const applyTheme = (value: boolean) => { document.documentElement.dataset.theme = value ? "dark" : "light"; };

  useEffect(() => {
    api.me().then((user) => { setDark(user.dark_mode); setGoal(user.daily_goal); applyTheme(user.dark_mode); }).catch(() => undefined);
  }, []);

  const save = async () => {
    try { await api.updateSettings({ dark_mode: dark, daily_goal: goal }); toast.show("Preferences saved"); }
    catch (reason) { toast.show(reason instanceof Error ? reason.message : "Could not save your preferences"); }
  };
  const demoAction = async (action: "simulate" | "reset") => {
    if (action === "reset" && !window.confirm("Restore the demo learner to the seeded starting progress?")) return;
    try {
      const result = action === "simulate" ? await api.simulateDay() : await api.resetDemo();
      toast.show(result.message);
    } catch (reason) { toast.show(reason instanceof Error ? reason.message : "That action is not available"); }
  };

  return (
    <SupportLayout rail="none" onSoon={toast.soon}>
      <div className="reference-settings">
        <PageHeader eyebrow="ACCOUNT" title="Settings" description="Manage your learning preferences." />
        <section className="reference-settings-card">
          <Setting title="Sound effects" description="Play sounds during lessons" checked={sound} setChecked={setSoundEnabled} />
          <Setting title="Dark mode" description="Use the dark Duolingo theme" checked={dark} setChecked={(value) => { setDark(value); applyTheme(value); }} />
          <Setting title="Motivational messages" description="Show reminders and celebrations" checked={motivation} setChecked={setMotivation} />
        </section>
        <h2 className="settings-heading">Daily goal</h2>
        <div className="goal-picker" role="radiogroup" aria-label="Daily XP goal">
          {GOALS.map((value) => <button key={value} type="button" role="radio" aria-checked={goal === value} className={goal === value ? "chosen" : ""} onClick={() => setGoal(value)}><strong>{value}</strong><span>XP / day</span></button>)}
        </div>
        <button type="button" className="reference-settings-save" onClick={save}>SAVE CHANGES</button>
        <h2 className="settings-heading">Demo tools</h2>
        <section className="reference-settings-card demo-tools">
          <div><strong>Simulate next day</strong><small>Pretend a day has passed to see streaks, the daily goal and heart regeneration change.</small><button type="button" onClick={() => demoAction("simulate")}>NEXT DAY</button></div>
          <div><strong>Reset demo progress</strong><small>Restore the learner to the seeded starting state.</small><button type="button" className="danger" onClick={() => demoAction("reset")}>RESET</button></div>
        </section>
      </div>
    </SupportLayout>
  );
}

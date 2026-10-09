"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Bootstrap } from "@/lib/types";
import { useToast } from "../Toast";
import { SupportLayout } from "./SupportLayout";

export function PracticePage() {
  const toast = useToast();
  const [data, setData] = useState<Bootstrap>();
  useEffect(() => { api.bootstrap().then(setData).catch(() => undefined); }, []);
  const practiceId = data?.practice_lesson_id ?? null;
  const practiceHref = practiceId ? `/lesson/${practiceId}?mode=practice` : "/learn";
  const finished = data?.units.flatMap((unit) => unit.skills).filter((skill) => skill.status === "completed") ?? [];
  const legendary = finished.at(-1);
  return (
    <SupportLayout onSoon={toast.soon}>
      <div className="reference-practice-hub">
        <h1>Today&apos;s Review</h1>
        <section className="reference-unit-rewind"><Image src="/learn-assets/super.svg" width={78} height={23} alt="Super" /><h2>Unit Rewind</h2><p>Keep your memory fresh with this review of Unit 1!</p><button type="button" onClick={() => toast.soon("Unit Rewind")}>UNLOCK</button><Image className="reference-rewind-art" src="/duolingo-assets/071159d03311fcb556c4dfe730941de1.svg" width={170} height={170} alt="" aria-hidden /></section>
        <h2 className="reference-practice-section-title">Challenges</h2>
        {legendary?.lesson_id ? (
          <Link className="reference-practice-tile" href={`/lesson/${legendary.lesson_id}?mode=legendary`}><div><strong>Legendary</strong></div><p>Race the 75-second timer on “{legendary.title}” and earn double XP</p><span className="reference-practice-tile-art" aria-hidden>⚡</span></Link>
        ) : (
          <div className="reference-practice-tile locked" aria-disabled="true"><div><strong>Legendary</strong></div><p>Complete a skill to unlock its timed challenge</p><span className="reference-practice-tile-art" aria-hidden>🔒</span></div>
        )}
        <h2 className="reference-practice-section-title">Conversation</h2>
        <button type="button" className="reference-practice-tile" onClick={() => toast.soon("Listening practice")}><div><strong>Listen</strong><Image src="/learn-assets/super.svg" width={76} height={22} alt="Super" /></div><p>Boost your listening skills with an audio-only session</p><span className="reference-practice-tile-art" aria-hidden>🎧</span></button>
        <h2 className="reference-practice-section-title">Your collections</h2>
        <Link className="reference-practice-tile" href={practiceHref}><div><strong>Practice</strong></div><p>Review the words you have learned so far</p><span className="reference-practice-tile-art" aria-hidden>✦</span></Link>
        <button type="button" className="reference-practice-tile" onClick={() => toast.soon("Stories")}><div><strong>Stories</strong></div><p>Reread a story to review words in context</p><Image className="reference-practice-tile-art image" src="/learn-assets/openbook_white.svg" width={85} height={75} alt="" aria-hidden /></button>
        <Link className="reference-practice-free" href={practiceHref}>Practice to earn hearts</Link>
      </div>
    </SupportLayout>
  );
}

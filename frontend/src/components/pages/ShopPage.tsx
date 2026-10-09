"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { UserStats } from "@/lib/types";
import { useToast } from "../Toast";
import { SupportLayout } from "./SupportLayout";

const GEM_REFILL_COST = 350;

export function ShopPage() {
  const toast = useToast();
  const [user, setUser] = useState<UserStats>();
  const reload = useCallback(() => api.me().then(setUser).catch(() => undefined), []);
  useEffect(() => { void reload(); }, [reload]);
  const heartsFull = user ? user.hearts >= user.max_hearts : false;
  const afford = user ? user.gems >= GEM_REFILL_COST : false;

  const refill = async (kind: "practice" | "gems") => {
    try {
      const result = kind === "practice" ? await api.refill() : await api.gemRefill();
      toast.show(result.message);
    } catch (reason) {
      toast.show(reason instanceof Error ? reason.message : "Could not refill hearts");
    }
    await reload();
  };

  return (
    <SupportLayout rail="shop" onSoon={toast.soon}>
      <div className="reference-shop">
        <section className="reference-shop-promo"><Image src="/learn-assets/super_bird.svg" width={115} height={120} alt="" aria-hidden /><Image src="/learn-assets/super.svg" width={80} height={24} alt="Super" /><h2>Get started with a 1 month free trial on Super</h2><button type="button" onClick={() => toast.soon("Super")}>START MY FREE MONTH</button></section>
        <section className="reference-shop-section"><h1>Hearts</h1>
          <article className="reference-shop-item"><Image src="/duolingo-assets/547ffcf0e6256af421ad1a32c26b8f1a.svg" width={68} height={68} alt="" aria-hidden /><div><h2>Refill Hearts <small>{user ? `${user.hearts} / ${user.max_hearts}` : ""}</small></h2><p>Get full hearts so you can worry less about making mistakes in a lesson</p></div>
            <button type="button" disabled={heartsFull || !afford} onClick={() => refill("gems")}>{heartsFull ? "FULL" : <><Image src="/learn-assets/bluepoints.svg" width={20} height={24} alt="" /> {GEM_REFILL_COST}</>}</button></article>
          <article className="reference-shop-item"><Image src="/duolingo-assets/547ffcf0e6256af421ad1a32c26b8f1a.svg" width={68} height={68} alt="" aria-hidden /><div><h2>Practice for hearts</h2><p>Finish a practice session to win a heart back for free</p></div>
            <button type="button" disabled={heartsFull} onClick={() => refill("practice")}>{heartsFull ? "FULL" : "PRACTICE FREE"}</button></article>
          <article className="reference-shop-item"><Image className="reference-unlimited-heart" src="/duolingo-assets/4f3842c690acf9bf0d4b06e6ab2fffcf.svg" width={72} height={72} alt="" aria-hidden /><div><h2>Unlimited Hearts</h2><p>Never run out of hearts with Super!</p></div><button type="button" onClick={() => toast.soon("Super")}>FREE TRIAL</button></article>
        </section>
        <section className="reference-shop-section"><h1>Power-Ups</h1><article className="reference-shop-item"><span className="reference-freeze-icon" aria-hidden>◆</span><div><h2>Streak Freeze <small>0 / 2 EQUIPPED</small></h2><p>Streak Freeze allows your streak to remain in place for one full day of inactivity.</p></div><button type="button" onClick={() => toast.soon("Streak Freeze")}><span>GET FOR:</span><Image src="/learn-assets/bluepoints.svg" width={20} height={24} alt="" /> 200</button></article></section>
      </div>
    </SupportLayout>
  );
}

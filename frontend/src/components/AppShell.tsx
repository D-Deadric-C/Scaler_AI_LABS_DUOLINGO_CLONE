"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { GameIcon } from "./GameIcon";

const nav = [
  ["/learn", "LEARN", "⌂"],
  ["/practice", "PRACTICE", "◈"],
  ["/leaderboards", "LEADERBOARDS", "♛"],
  ["/quests", "QUESTS", "▣"],
  ["/shop", "SHOP", "◆"],
  ["/profile", "PROFILE", "●"],
];

const learnNav = [
  ["/learn", "LEARN", "homeicon.svg"],
  ["/learn#sounds", "SOUNDS", "speakicon.svg"],
  ["/practice", "PRACTICE", "dumbleicon.svg"],
  ["/leaderboards", "LEADERBOARDS", "goldenicon.svg"],
  ["/quests", "QUESTS", "chest.svg"],
  ["/shop", "SHOP", "bakery.svg"],
  ["/profile", "PROFILE", "duolingocompact.svg"],
  ["/settings", "MORE", "opetions.svg"],
] as const;

function ReferenceSidebar({ pathname }: { pathname: string }) {
  return (
    <aside className="reference-side-nav">
      <Link href="/learn" className="reference-wordmark" aria-label="Duolingo home">
        <Image className="reference-logo-full" src="/learn-assets/duolingomain.svg" width={148} height={36} alt="Duolingo" priority />
        <Image className="reference-logo-compact" src="/learn-assets/duolingocompact.svg" width={44} height={44} alt="" priority aria-hidden />
      </Link>
      <nav aria-label="Primary navigation">
        {learnNav.map(([href, label, asset]) => {
          const route = href.split("#")[0];
          const active = label === "LEARN" && pathname.startsWith(route);
          return (
            <Link key={label} href={href} className={`reference-nav-item ${active ? "active" : ""}`}>
              {label === "PROFILE" ? (
                <span className="reference-profile-icon" aria-hidden><Image src={`/learn-assets/${asset}`} width={35} height={35} alt="" /></span>
              ) : (
                <Image src={`/learn-assets/${asset}`} width={35} height={35} alt="" aria-hidden />
              )}
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="reference-chess-card">
        <span className="chess-pieces" aria-hidden>♞♟</span>
        <strong>Want to learn chess?</strong>
        <p>Duolingo makes it easy!</p>
        <Link href="/learn#chess">TRY CHESS</Link>
      </div>
    </aside>
  );
}

function ReferenceMobileNav({ pathname }: { pathname: string }) {
  return (
    <nav className="reference-mobile-nav" aria-label="Mobile navigation">
      {learnNav.slice(0, 5).map(([href, label, asset]) => (
        <Link key={label} href={href} aria-label={label} className={label === "LEARN" && pathname.startsWith("/learn") ? "active" : ""}>
          <Image src={`/learn-assets/${asset}`} width={31} height={31} alt="" />
        </Link>
      ))}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith("/learn")) {
    return (
      <div className="app-shell duolingo-learn-shell">
        <a className="reference-skip-link" href="#learn-main">Skip to learning path</a>
        <ReferenceSidebar pathname={pathname} />
        <main id="learn-main" className="shell-content">{children}</main>
        <ReferenceMobileNav pathname={pathname} />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <Link href="/learn" className="wordmark" aria-label="Duolingo home"><Image src="/learn-assets/duolingomain.svg" width={148} height={36} alt="Duolingo" /></Link>
        <nav aria-label="Primary navigation">
          {nav.map(([href, label, icon]) => (
            <Link key={href} href={href} className={`nav-item ${pathname.startsWith(href) ? "active" : ""}`}>
              <span className="nav-icon" aria-hidden>{icon}</span><span>{label}</span>
            </Link>
          ))}
          <Link href="/settings" className={`nav-item ${pathname.startsWith("/settings") ? "active" : ""}`}><span className="nav-icon">•••</span><span>MORE</span></Link>
        </nav>
        <div className="nav-promo"><GameIcon name="bolt" size={42}/><strong>Keep your momentum</strong><span>Finish a lesson today</span></div>
      </aside>
      <main className="shell-content">{children}</main>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        {nav.slice(0, 5).map(([href, label, icon]) => <Link key={href} href={href} aria-label={label} className={pathname.startsWith(href) ? "active" : ""}><span>{icon}</span></Link>)}
      </nav>
    </div>
  );
}

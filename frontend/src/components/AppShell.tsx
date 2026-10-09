"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useHoverMenu } from "@/lib/useHoverMenu";
import { ArtSlot } from "./learn/ArtSlot";
import { ToastProvider, useToast } from "./Toast";

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

/** The purple MORE entry: hover or click opens a small menu (test, settings, help, log out). */
function MoreMenu({ asset, pathname }: { asset: string; pathname: string }) {
  const toast = useToast();
  const { open, root, dismiss, triggerProps, panelProps } = useHoverMenu<"more">();
  return (
    <div className="more-wrap" ref={root}>
      <button type="button" className={`reference-nav-item ${open || pathname.startsWith("/settings") ? "active" : ""}`} aria-haspopup="menu" {...triggerProps("more")}>
        <Image src={`/learn-assets/${asset}`} width={35} height={35} alt="" aria-hidden />
        <span>MORE</span>
      </button>
      {open ? (
        <div className="more-menu" role="menu" {...panelProps}>
          <button type="button" role="menuitem" className="more-test" aria-label="Duolingo test" onClick={() => { toast.soon("The Duolingo test"); dismiss(); }}><ArtSlot name="english-test" width={244} height={37} fallback={<><Image src="/learn-assets/duolingocompact.svg" width={30} height={30} alt="" aria-hidden />DUOLINGO SPANISH TEST</>} /></button>
          <Link href="/settings" role="menuitem" onClick={dismiss}>SETTINGS</Link>
          <button type="button" role="menuitem" onClick={() => { toast.soon("The help center"); dismiss(); }}>HELP</button>
          <button type="button" role="menuitem" onClick={() => { toast.show("You're using the demo learner — signing out isn't needed"); dismiss(); }}>LOG OUT</button>
        </div>
      ) : null}
    </div>
  );
}

function ReferenceSidebar({ pathname }: { pathname: string }) {
  const toast = useToast();
  return (
    <aside className="reference-side-nav">
      <Link href="/learn" className="reference-wordmark" aria-label="Duolingo home">
        <Image className="reference-logo-full" src="/learn-assets/duolingomain.svg" width={148} height={36} alt="Duolingo" priority />
        <Image className="reference-logo-compact" src="/learn-assets/duolingocompact.svg" width={44} height={44} alt="" priority aria-hidden />
      </Link>
      <nav aria-label="Primary navigation">
        {learnNav.map(([href, label, asset]) => {
          const route = href.split("#")[0];
          const active = !href.includes("#") && pathname.startsWith(route);
          if (label === "MORE") return <MoreMenu key={label} asset={asset} pathname={pathname} />;
          if (href.includes("#")) { // sections that are not built yet
            return (
              <button key={label} type="button" className="reference-nav-item" onClick={() => toast.soon(label.charAt(0) + label.slice(1).toLowerCase())}>
                <Image src={`/learn-assets/${asset}`} width={35} height={35} alt="" aria-hidden />
                <span>{label}</span>
              </button>
            );
          }
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
        <ArtSlot name="chess-sidebar" width={58} height={48} className="chess-illustration" fallback={<span className="chess-pieces" aria-hidden>♞♟</span>} />
        <strong>Want to learn chess?</strong>
        <p>Duolingo makes it easy!</p>
        <button type="button" onClick={() => toast.soon("Chess")}>TRY CHESS</button>
      </div>
    </aside>
  );
}

function ReferenceMobileNav({ pathname }: { pathname: string }) {
  return (
    <nav className="reference-mobile-nav" aria-label="Mobile navigation">
      {learnNav.slice(0, 5).map(([href, label, asset]) => (
        <Link key={label} href={href} aria-label={label} className={!href.includes("#") && pathname.startsWith(href) ? "active" : ""}>
          <Image src={`/learn-assets/${asset}`} width={31} height={31} alt="" />
        </Link>
      ))}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <ToastProvider>
      <div className="app-shell duolingo-learn-shell">
        <a className="reference-skip-link" href="#app-main">Skip to content</a>
        <ReferenceSidebar pathname={pathname} />
        <main id="app-main" className="shell-content">{children}</main>
        <ReferenceMobileNav pathname={pathname} />
      </div>
    </ToastProvider>
  );
}

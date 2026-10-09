import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import "./globals.css";
import { TimezoneSync } from "@/components/TimezoneSync";

// Closest free match to Duolingo's rounded DIN typeface.
const ui = Nunito({ subsets: ["latin"], weight: ["600", "700", "800", "900"], display: "swap", variable: "--font-ui" });

export const metadata: Metadata = {
  title: "Duolingo — Learn Spanish",
  description: "A playful language learning experience with lessons, streaks, hearts and XP.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={ui.variable}><body><TimezoneSync />{children}</body></html>;
}

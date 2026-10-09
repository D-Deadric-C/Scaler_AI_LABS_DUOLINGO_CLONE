import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import "./globals.css";
import { ThemeSync } from "@/components/ThemeSync";
import { TimezoneSync } from "@/components/TimezoneSync";

// Closest free match to Duolingo's rounded DIN typeface.
const ui = Nunito({ subsets: ["latin"], weight: ["600", "700", "800", "900"], display: "swap", variable: "--font-ui" });

export const metadata: Metadata = {
  title: "duolingo_clone_by_suryansh",
  description: "A playful language learning experience with lessons, streaks, hearts and XP.",
};

// Applies the saved theme before first paint so pages never flash the wrong colours.
const themeScript = `try{var t=localStorage.getItem("theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={ui.variable} data-theme="dark" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body><TimezoneSync /><ThemeSync />{children}</body>
    </html>
  );
}

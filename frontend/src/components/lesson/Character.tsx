import { Mascot } from "../GameIcon";

/**
 * Original character artwork used beside speech bubbles and on result screens.
 * Every character is drawn here as inline SVG; "pip" is the app mascot.
 */
export type CharacterName = "pip" | "gus" | "mia" | "kai" | "zoe";

/** Grandpa Gus watching TV from a purple armchair (180 x 131). */
function GusTV({ size }: { size: number }) {
  return (
    <svg width={size} height={(size * 131) / 180} viewBox="0 0 180 131" role="img" aria-label="Grandpa watching television" className="lx-character">
      <ellipse cx="90" cy="127" rx="86" ry="4" fill="#0d171b" />
      {/* TV on a wooden stand */}
      <path d="M6 112h64v14H6z" fill="#9a5a34" /><path d="M6 112h64v4H6z" fill="#b87245" />
      <rect x="10" y="62" width="56" height="50" rx="5" fill="#4a5258" /><rect x="15" y="68" width="38" height="38" rx="3" fill="#2c3237" />
      <circle cx="59" cy="76" r="2.4" fill="#8c979e" /><circle cx="59" cy="86" r="2.4" fill="#8c979e" />
      <path d="M28 62 16 40M44 62l14-25" stroke="#cfd6da" strokeWidth="2.4" strokeLinecap="round" />
      {/* armchair */}
      <path d="M78 54c0-12 8-20 20-20h30c12 0 20 8 20 20v60H78z" fill="#6b4fc4" />
      <rect x="70" y="84" width="34" height="34" rx="12" fill="#7d62d6" /><rect x="142" y="84" width="34" height="34" rx="12" fill="#7d62d6" />
      <rect x="82" y="96" width="82" height="24" rx="8" fill="#8a70e0" /><rect x="86" y="118" width="8" height="8" fill="#4c378f" /><rect x="152" y="118" width="8" height="8" fill="#4c378f" />
      {/* Gus */}
      <path d="M98 100c-2-22 4-34 24-34s26 12 24 34z" fill="#3f8fe0" />
      <path d="M116 66h12v18h-12z" fill="#f2c7a3" />
      <circle cx="122" cy="48" r="19" fill="#f2c7a3" />
      <path d="M103 44c0-14 8-20 19-20s19 6 19 20c-4-6-10-9-19-9s-15 3-19 9z" fill="#f5f5f5" />
      <path d="M108 56c4 8 10 9 14 9s10-1 14-9c-3 2-7 3-14 3s-11-1-14-3z" fill="#f5f5f5" />
      <rect x="107" y="43" width="14" height="10" rx="4" fill="none" stroke="#7a4fd0" strokeWidth="2.4" /><rect x="125" y="43" width="14" height="10" rx="4" fill="none" stroke="#7a4fd0" strokeWidth="2.4" />
      <path d="M121 47h4" stroke="#7a4fd0" strokeWidth="2.4" /><circle cx="114" cy="48" r="2" fill="#2b2f33" /><circle cx="132" cy="48" r="2" fill="#2b2f33" />
      <rect x="100" y="84" width="14" height="14" rx="5" fill="#f2c7a3" />
    </svg>
  );
}

function Avatar({ size, skin, hair, top, accent, ariaLabel, bun = false, beard = false }: { size: number; skin: string; hair: string; top: string; accent: string; ariaLabel: string; bun?: boolean; beard?: boolean }) {
  return (
    <svg width={size} height={(size * 64) / 56} viewBox="0 0 56 64" role="img" aria-label={ariaLabel} className="lx-character">
      <path d="M4 64c0-14 10-22 24-22s24 8 24 22z" fill={top} />
      <path d="M20 46h16l-8 10z" fill={accent} />
      {bun ? <circle cx="28" cy="7" r="6" fill={hair} /> : null}
      <circle cx="28" cy="28" r="19" fill={skin} />
      <path d={bun ? "M9 27c0-12 8-18 19-18s19 6 19 18c-6-5-11-7-19-7s-13 2-19 7z" : "M9 26c0-13 8-19 19-19 12 0 19 7 19 19-3-6-9-9-19-9-9 0-16 3-19 9z"} fill={hair} />
      {beard ? <path d="M12 32c2 12 9 16 16 16s14-4 16-16c-5 6-10 8-16 8s-11-2-16-8z" fill={hair} /> : null}
      <circle cx="21" cy="29" r="2.4" fill="#2b2f33" /><circle cx="35" cy="29" r="2.4" fill="#2b2f33" />
      <path d="M23 37c3 3 7 3 10 0" fill="none" stroke="#7a3b2e" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** Zoe celebrating next to Pip on the lesson-complete screen (about 340 x 290). */
function ZoeCelebrate({ size }: { size: number }) {
  return (
    <svg width={size} height={(size * 290) / 340} viewBox="0 0 340 290" role="img" aria-label="Pip and Zoe celebrating" className="lx-character">
      <g stroke="#ffc800" strokeWidth="7" strokeLinecap="round"><path d="M150 60 140 18M190 70l20-36M112 96 80 74M236 100l34-22M130 210l-26 30M232 214l22 30" /></g>
      <g stroke="#8eca32" strokeWidth="5" strokeLinecap="round"><path d="M50 36v28M36 50h28M40 40l20 20M60 40 40 60" /></g>
      <rect x="40" y="276" width="110" height="7" rx="3.500" fill="#36444d" /><rect x="170" y="276" width="140" height="7" rx="3.500" fill="#36444d" />
      {/* Pip */}
      <path d="M52 188c0-34 22-56 52-56s52 22 52 56v34c-8 18-28 28-52 28s-44-10-52-28z" fill="#58cc02" />
      <ellipse cx="86" cy="178" rx="19" ry="21" fill="#fff" /><ellipse cx="124" cy="178" rx="19" ry="21" fill="#fff" />
      <circle cx="90" cy="180" r="8" fill="#24303b" /><circle cx="120" cy="180" r="8" fill="#24303b" /><path d="m105 192-10 8 10 7 10-7z" fill="#ffc800" />
      <path d="M62 262h24l-10 10zM122 262h24l-12 10z" fill="#ff9600" />
      {/* Zoe */}
      <path d="M210 150c-8-26 6-40 28-40s34 14 28 40z" fill="#3a2f4f" />
      <circle cx="238" cy="126" r="26" fill="#d9966a" />
      <path d="M210 120c0-22 12-34 28-34s28 12 28 34c-8-8-16-12-28-12s-20 4-28 12z" fill="#3a2f4f" />
      <circle cx="228" cy="126" r="3" fill="#2b2f33" /><circle cx="248" cy="126" r="3" fill="#2b2f33" /><path d="M230 138c5 5 11 5 16 0" stroke="#7a3b2e" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M214 152h52l8 52h-68z" fill="#7a4fd0" />
      <path d="M214 160c-26-6-40-20-50-44M266 160c24-6 38-24 44-48" stroke="#d9966a" strokeWidth="14" strokeLinecap="round" fill="none" />
      <path d="M222 204h18l-8 62h-16zM246 204h18l10 62h-18z" fill="#1cb0f6" />
      <path d="M208 266h28v10h-28zM252 266h28v10h-28z" fill="#ff4b4b" />
    </svg>
  );
}

export function Character({ name = "pip", size = 96 }: { name?: CharacterName | string; size?: number }) {
  if (name === "gus") return <GusTV size={size} />;
  if (name === "mia") return <Avatar size={size} skin="#f2c7a3" hair="#2b2f33" top="#ff9600" accent="#fff" ariaLabel="Mia" bun />;
  if (name === "kai") return <Avatar size={size} skin="#c98a5e" hair="#1f2a30" top="#1cb0f6" accent="#fff" ariaLabel="Kai" beard />;
  if (name === "zoe") return <ZoeCelebrate size={size} />;
  return <span className="lx-character" aria-hidden><Mascot size={size} /></span>;
}

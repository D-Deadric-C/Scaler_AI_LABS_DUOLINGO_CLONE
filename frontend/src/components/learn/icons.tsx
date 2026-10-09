import { ArtSlot } from "./ArtSlot";

/** Original inline icons for the Learn page (flame, league badge, hearts row); each can be overridden via ArtSlot. */
export function FlameIcon({ lit, size = 30 }: { lit: boolean; size?: number }) {
  return (
    <ArtSlot name={lit ? "flame-lit" : "flame-unlit"} width={size} fallback={<FlameDrawing lit={lit} size={size} />} />
  );
}

function FlameDrawing({ lit, size }: { lit: boolean; size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden className={`pt-flame ${lit ? "lit" : ""}`}>
      <path d="M17 2c1 6-6 8-4 15 2-3 5-4 6-8 5 4 8 9 7 14-1 6-6 9-11 9-6 0-10-4-10-10 0-6 5-10 9-14-1 4 0 7 3 8 1-4 1-9 0-14Z" fill={lit ? "#ff9600" : "#5b6c74"} />
      <path d="M16 31c-4 0-7-3-7-7 0-3 3-6 6-8 0 3 2 4 3 5 1-2 3-3 3-5 3 2 4 5 4 8 0 4-5 7-9 7Z" fill={lit ? "#ffc800" : "#7a8a92"} />
    </svg>
  );
}

/** Bronze league badge shown once the learner has earned XP in the weekly league. */
export function BronzeBadge({ size = 60 }: { size?: number }) {
  return <ArtSlot name="league-bronze" width={size} fallback={<BadgeDrawing size={size} />} />;
}

function BadgeDrawing({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="Bronze league badge">
      <path d="M32 4 56 12v18c0 15-10 26-24 30C18 56 8 45 8 30V12z" fill="#a8632e" />
      <path d="M32 9 51 15v15c0 12-8 21-19 25C21 51 13 42 13 30V15z" fill="#d9914b" />
      <path d="M32 9 51 15v15c0 12-8 21-19 25z" fill="#e7a763" />
      <path d="M22 42c4-12 12-20 22-22-3 6-6 10-10 13 2 0 4 0 6-1-4 7-10 11-18 10z" fill="#fbe3c0" />
    </svg>
  );
}

export function HeartsRow({ hearts, max }: { hearts: number; max: number }) {
  return (
    <div className="pt-hearts-row" aria-label={`${hearts} of ${max} hearts`}>
      {Array.from({ length: max }, (_, index) => (
        <ArtSlot key={index} name={index < hearts ? "heart-full" : "heart-empty"} width={40} height={36} fallback={
          <svg width="40" height="36" viewBox="0 0 34 30" aria-hidden>
            <path d="M17 28S2 19 2 10C2 5.500 5.500 3 9 3c3 0 6 1.700 8 4.500C19 4.700 22 3 25 3c3.500 0 7 2.500 7 7 0 9-15 18-15 18Z" fill={index < hearts ? "#f44949" : "#dcdcdc"} />
          </svg>
        } />
      ))}
    </div>
  );
}

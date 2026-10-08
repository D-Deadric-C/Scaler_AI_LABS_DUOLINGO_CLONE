type GameIconProps = { name: string; size?: number; className?: string };

export function GameIcon({ name, size = 28, className }: GameIconProps) {
  const common = { width: size, height: size, viewBox: "0 0 64 64", role: "img", "aria-hidden": true, className };
  if (name === "heart") {
    return <svg {...common}><path fill="#ff4b4b" d="M32 55S7 42 7 22c0-9 6-15 15-15 5 0 9 3 10 7 2-4 6-7 11-7 8 0 14 6 14 15 0 20-25 33-25 33Z"/><path fill="#ff8585" d="M17 14c4-3 9-2 11 2-8 0-12 5-13 11-3-5-2-10 2-13Z"/></svg>;
  }
  if (name === "flame") {
    return <svg {...common}><path fill="#ff9600" d="M34 3c4 12-7 14-2 26 3-5 8-7 10-14 8 8 13 18 10 29-3 11-12 17-22 16C17 59 9 50 11 38c2-10 10-17 18-24-1 8 2 11 5 13 1-7 4-13 0-24Z"/><path fill="#ffc800" d="M31 58c-8-1-13-7-12-14 1-6 5-10 10-14 0 6 3 8 5 10 2-4 4-7 4-11 6 6 9 12 7 19-2 7-8 11-14 10Z"/></svg>;
  }
  if (name === "gem") {
    return <svg {...common}><path fill="#1cb0f6" d="M11 23 23 8h18l12 15-21 34L11 23Z"/><path fill="#84d8ff" d="m23 8 9 15 9-15H23Z"/><path fill="#168dcc" d="M11 23h21L23 8 11 23Zm21 34V23h21L32 57Z"/></svg>;
  }
  if (name === "bolt") {
    return <svg {...common}><path fill="#ffc800" d="M36 3 11 36h18l-2 25 26-36H36V3Z"/><path fill="#ffde59" d="m36 3-9 29h18L29 55l24-30H36V3Z"/></svg>;
  }
  if (name === "lock") {
    return <svg {...common}><rect x="13" y="28" width="38" height="29" rx="9" fill="#afafaf"/><path d="M22 29V20c0-14 20-14 20 0v9" fill="none" stroke="#afafaf" strokeWidth="8"/><circle cx="32" cy="42" r="5" fill="#777"/></svg>;
  }
  if (name === "check") {
    return <svg {...common}><path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="10" d="m13 33 12 12 27-29"/></svg>;
  }
  if (name === "trophy") {
    return <svg {...common}><path fill="#ffc800" d="M19 8h26v13c0 12-6 20-13 20s-13-8-13-20V8Z"/><path fill="none" stroke="#ff9600" strokeWidth="6" d="M19 14H8v7c0 8 6 13 13 13m24-20h11v7c0 8-6 13-13 13"/><path fill="#ff9600" d="M28 39h8v10h10v8H18v-8h10V39Z"/></svg>;
  }
  if (name === "book") {
    return <svg {...common}><path fill="#1cb0f6" d="M8 10h20c5 0 8 3 8 8v38H15c-4 0-7-3-7-7V10Z"/><path fill="#84d8ff" d="M56 10H36v46h21V10Z"/><path fill="none" stroke="#fff" strokeLinecap="round" strokeWidth="4" d="M17 21h11m-11 9h11m17-9h5m-5 9h5"/></svg>;
  }
  if (name === "clock") {
    return <svg {...common}><circle cx="32" cy="32" r="26" fill="#1cb0f6"/><circle cx="32" cy="32" r="20" fill="#fff"/><path fill="none" stroke="#168dcc" strokeLinecap="round" strokeWidth="5" d="M32 18v15l10 7"/></svg>;
  }
  return <svg {...common}><path fill="currentColor" d="m32 4 8 17 19 2-14 13 4 19-17-9-17 9 4-19L5 23l19-2 8-17Z"/></svg>;
}

export function Mascot({ mood = "happy", size = 112 }: { mood?: "happy" | "sad" | "celebrate"; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 140 140" role="img" aria-label={`Pip the owl is ${mood}`} className={`mascot mascot-${mood}`}>
      <path fill="#58cc02" d="M25 54C25 28 45 11 70 11s45 17 45 43v47c-10 20-29 30-45 30s-35-10-45-30V54Z"/>
      <path fill="#89e219" d="M25 55 13 37c13-1 23 4 29 13m73 5 12-18c-13-1-23 4-29 13"/>
      <ellipse cx="51" cy="58" rx="25" ry="27" fill="#fff"/><ellipse cx="89" cy="58" rx="25" ry="27" fill="#fff"/>
      <circle cx="56" cy="59" r="10" fill="#24303b"/><circle cx="84" cy="59" r="10" fill="#24303b"/>
      <circle cx="60" cy="55" r="3" fill="#fff"/><circle cx="88" cy="55" r="3" fill="#fff"/>
      <path fill="#ffc800" d="m70 67-13 9 13 10 13-10-13-9Z"/>
      <path fill="#46a302" d={mood === "sad" ? "M49 102q21-18 42 0" : "M48 94q22 24 44 0q-4 29-22 29T48 94Z"}/>
      {mood !== "sad" && <path fill="#ff6b6b" d="M58 108q12 10 24 0c-2 10-22 10-24 0Z"/>}
      <path fill="#ff9600" d="M38 125h25l-12 9-13-9Zm39 0h25l-13 9-12-9Z"/>
    </svg>
  );
}

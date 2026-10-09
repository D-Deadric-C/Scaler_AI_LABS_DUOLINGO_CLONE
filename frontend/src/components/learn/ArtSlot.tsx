import Image from "next/image";
import type { ReactNode } from "react";

/**
 * Optional custom artwork. Put `<name>.svg` in `public/learn-assets/custom/` and list the name in
 * NEXT_PUBLIC_CUSTOM_ART_SLOTS (comma separated, e.g. in .env.local). Slots that are not listed draw the built-in icon.
 */
export type ArtName = "flame-lit" | "flame-unlit" | "flame-big" | "friend-streak" | "gem" | "gems-chest" | "heart-full" | "heart-empty" | "heart-unlimited" | "league-bronze" | "english-test" | "chess-sidebar" | "duo-radio" | "unit-2-campfire";

const AVAILABLE = new Set((process.env.NEXT_PUBLIC_CUSTOM_ART_SLOTS ?? "").split(",").map((name) => name.trim()).filter(Boolean));

export function ArtSlot({ name, width, height = width, className, alt = "", fallback }: { name: ArtName; width: number; height?: number; className?: string; alt?: string; fallback: ReactNode }) {
  if (!AVAILABLE.has(name)) return <>{fallback}</>;
  return <Image src={`/learn-assets/custom/${name}.svg`} width={width} height={height} className={className} alt={alt} aria-hidden={alt ? undefined : true} unoptimized />;
}

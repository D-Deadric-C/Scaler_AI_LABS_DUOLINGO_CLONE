import Image from "next/image";
import { ArtSlot } from "../learn/ArtSlot";

/** Small inline icons used by the lesson player. */
export function SpeakerIcon({ size = 22 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden><path fill="currentColor" d="M3 9v6h4l5 4V5L7 9H3Z" /><path fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" d="M15.5 8.5a5 5 0 0 1 0 7m2.8-9.8a9 9 0 0 1 0 12.6" /></svg>;
}

export function CheckBadge() {
  return <svg width="40" height="28" viewBox="0 0 40 28" aria-hidden><path fill="none" stroke="currentColor" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" d="m4 14 9 9L36 4" /></svg>;
}

export function CrossBadge() {
  return <svg width="31" height="31" viewBox="0 0 31 31" aria-hidden><path fill="none" stroke="currentColor" strokeWidth="6.4" strokeLinecap="round" d="m3.2 3.2 24.6 24.6m0-24.6L3.2 27.8" /></svg>;
}

export function SleepIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden><path fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" d="M4 5h7L4 12h8m4-1h5l-5 6h5" /></svg>;
}

export function MountainIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden><path fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" d="m3 20 6-12 4 7 3-4 5 9H3Z" /></svg>;
}

export function FlagIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden><path fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" d="M5 21V4h13l-3 5 3 5H5" /></svg>;
}

export function CloseIcon() {
  return <svg width="17" height="17" viewBox="0 0 17 17" aria-hidden><path fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" d="m1.5 1.5 14 14m0-14-14 14" /></svg>;
}

export function TargetIcon({ size = 24 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="3" /><circle cx="12" cy="12" r="4.6" fill="none" stroke="currentColor" strokeWidth="3" /><path d="m13 11 8-8" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" /></svg>;
}

export function GemIcon({ size = 22 }: { size?: number }) {
  return <ArtSlot name="gem" width={size} fallback={<GemDrawing size={size} />} />;
}

function GemDrawing({ size }: { size: number }) {
  return <Image src="/learn-assets/bluepoints.svg" width={size} height={size} alt="" aria-hidden />;
}

export function HeartIcon({ size = 30, infinite = false }: { size?: number; infinite?: boolean }) {
  return <ArtSlot name={infinite ? "heart-unlimited" : "heart-full"} width={size} fallback={<HeartDrawing size={size} infinite={infinite} />} />;
}

function HeartDrawing({ size, infinite }: { size: number; infinite: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 34 34" aria-hidden>
      <defs><linearGradient id="lx-heart-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#26d77f" /><stop offset=".5" stopColor="#2690e4" /><stop offset="1" stopColor="#bf5ff4" /></linearGradient></defs>
      <path d="M17 29.5S3 21.5 3 11.8C3 7.4 6.3 4.5 10 4.5c3 0 5.2 1.7 7 4.2 1.8-2.5 4-4.2 7-4.2 3.7 0 7 2.9 7 7.3 0 9.700-14 17.700-14 17.700Z" fill={infinite ? "url(#lx-heart-grad)" : "#f44949"} stroke="#f4f4f4" strokeWidth="2.4" strokeLinejoin="round" />
      {infinite ? <path d="M11.500 14.800c1.800-2.700 4.200-2.700 5.500 0s3.700 2.700 5.500 0M11.500 14.800c-1.200 2 .8 3.700 2.700 2.200M22.500 14.800c1.200 2-.8 3.700-2.700 2.200" fill="none" stroke="#fff" strokeWidth="2.200" strokeLinecap="round" /> : null}
    </svg>
  );
}

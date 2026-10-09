/** Tiny synthesised sound effects (no audio files). Honors the learner's sound preference. */
import { useSyncExternalStore } from "react";

const STORAGE_KEY = "duolingo:sound";
const listeners = new Set<() => void>();
let context: AudioContext | null = null;

export function soundEnabled(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) !== "off";
  } catch {
    return true;
  }
}

export function setSoundEnabled(enabled: boolean): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, enabled ? "on" : "off");
  } catch {
    /* storage unavailable (private mode): preference simply isn't remembered */
  }
  listeners.forEach((listener) => listener());
}

/** Current sound preference as React state (true on the server so hydration matches). */
export function useSoundEnabled(): boolean {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => listeners.delete(listener); }, soundEnabled, () => true);
}

function tone(frequency: number, start: number, duration: number, type: OscillatorType, volume: number): void {
  if (!context) return;
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = type;
  oscillator.frequency.value = frequency;
  const begin = context.currentTime + start;
  gain.gain.setValueAtTime(0.0001, begin);
  gain.gain.exponentialRampToValueAtTime(volume, begin + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, begin + duration);
  oscillator.connect(gain).connect(context.destination);
  oscillator.start(begin);
  oscillator.stop(begin + duration + 0.05);
}

function play(notes: [number, number, number, OscillatorType, number][]): void {
  if (typeof window === "undefined" || !soundEnabled()) return;
  try {
    context ??= new (window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    if (context.state === "suspended") void context.resume();
    notes.forEach(([frequency, start, duration, type, volume]) => tone(frequency, start, duration, type, volume));
  } catch {
    /* audio is a nicety; never break a lesson over it */
  }
}

export const playCorrect = () => play([[659, 0, 0.14, "triangle", 0.18], [880, 0.1, 0.22, "triangle", 0.18]]);
export const playWrong = () => play([[220, 0, 0.18, "sawtooth", 0.09], [165, 0.12, 0.3, "sawtooth", 0.09]]);
export const playComplete = () => play([[523, 0, 0.16, "triangle", 0.16], [659, 0.14, 0.16, "triangle", 0.16], [784, 0.28, 0.16, "triangle", 0.16], [1047, 0.42, 0.4, "triangle", 0.18]]);

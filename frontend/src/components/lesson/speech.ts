/** Speak Spanish text with the browser's speech synthesis (silently ignored where unsupported). */
export function speak(text: string): void {
  if (typeof window === "undefined" || !("speechSynthesis" in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "es-ES";
  utterance.rate = 0.85;
  window.speechSynthesis.speak(utterance);
}

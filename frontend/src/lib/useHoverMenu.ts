"use client";

import { useCallback, useEffect, useRef, useState, type MouseEvent } from "react";

/**
 * Popover behaviour shared by the Learn page: hovering a trigger opens its panel, clicking pins it open,
 * and Escape or a click outside closes it. `caret` is the trigger's horizontal centre relative to the root.
 */
export function useHoverMenu<K extends string>() {
  const [open, setOpen] = useState<K | null>(null);
  const [pinned, setPinned] = useState(false);
  const [caret, setCaret] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const timer = useRef<number | undefined>(undefined);

  const cancelClose = useCallback(() => window.clearTimeout(timer.current), []);
  const scheduleClose = useCallback(() => {
    if (pinned) return;
    cancelClose();
    timer.current = window.setTimeout(() => setOpen(null), 180); // grace period to reach the panel
  }, [cancelClose, pinned]);
  const dismiss = useCallback(() => { cancelClose(); setPinned(false); setOpen(null); }, [cancelClose]);

  useEffect(() => cancelClose, [cancelClose]);
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") dismiss(); };
    const onDown = (event: globalThis.MouseEvent) => { if (root.current && !root.current.contains(event.target as Node)) dismiss(); };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onDown);
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener("mousedown", onDown); };
  }, [open, dismiss]);

  const show = useCallback((key: K, element: HTMLElement) => {
    cancelClose();
    const box = element.getBoundingClientRect();
    const parent = root.current?.getBoundingClientRect();
    if (parent) setCaret(box.left + box.width / 2 - parent.left);
    setOpen(key);
  }, [cancelClose]);

  const triggerProps = (key: K) => ({
    "aria-expanded": open === key,
    onMouseEnter: (event: MouseEvent<HTMLElement>) => { if (open !== key) setPinned(false); show(key, event.currentTarget); },
    onMouseLeave: scheduleClose,
    onClick: (event: MouseEvent<HTMLElement>) => {
      if (open === key && pinned) { dismiss(); return; }
      setPinned(true); // a click keeps the panel open until dismissed
      show(key, event.currentTarget);
    },
  });

  return { open, root, caret, dismiss, triggerProps, panelProps: { onMouseEnter: cancelClose, onMouseLeave: scheduleClose } };
}

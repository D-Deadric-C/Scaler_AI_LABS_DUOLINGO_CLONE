"use client";

import { useEffect, type ReactNode } from "react";

/** Simple accessible dialog used by the Learn page (guidebook, reward chest). Closes on Escape or backdrop click. */
export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="app-modal-overlay" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="app-modal" role="dialog" aria-modal="true" aria-label={title}>
        <h2>{title}</h2>
        {children}
        <button type="button" className="app-modal-close" autoFocus onClick={onClose}>GOT IT</button>
      </div>
    </div>
  );
}

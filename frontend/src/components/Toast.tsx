"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

type ToastApi = { show: (message: string) => void; soon: (feature: string) => void };
const ToastContext = createContext<ToastApi>({ show: () => undefined, soon: () => undefined });

/** App-wide toast: one short message at a time, used for confirmations and "coming soon" placeholders. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  const timer = useRef<number | undefined>(undefined);
  const show = useCallback((next: string) => {
    setMessage(next);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setMessage(""), 2600);
  }, []);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const api = useMemo<ToastApi>(() => ({ show, soon: (feature) => show(`${feature} is coming soon`) }), [show]);
  return (
    <ToastContext.Provider value={api}>
      {children}
      {message ? <div className="app-toast" role="status" key={message}>{message}</div> : null}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

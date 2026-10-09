"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";

/** Tells the server the browser's UTC offset once, so streak days and the daily goal use the learner's own calendar. */
export function TimezoneSync() {
  useEffect(() => {
    const offset = -new Date().getTimezoneOffset(); // minutes ahead of UTC (India = +330)
    api.me()
      .then((user) => (user.tz_offset_minutes === offset ? undefined : api.updateSettings({ tz_offset_minutes: offset })))
      .catch(() => undefined);
  }, []);
  return null;
}

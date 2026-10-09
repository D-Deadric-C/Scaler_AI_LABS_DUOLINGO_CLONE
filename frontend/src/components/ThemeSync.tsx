"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";
import { applyTheme } from "@/lib/theme";

/** Loads the learner's saved theme from the server, so it follows them across browsers. */
export function ThemeSync() {
  useEffect(() => {
    api.me().then((user) => applyTheme(user.dark_mode ? "dark" : "light")).catch(() => undefined);
  }, []);
  return null;
}

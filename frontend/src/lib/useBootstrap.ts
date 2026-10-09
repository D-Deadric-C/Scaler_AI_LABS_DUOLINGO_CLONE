"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Bootstrap } from "./types";

/** Loads the home-screen bundle (path, learner, rail data) and exposes a reload for after-actions. */
export function useBootstrap() {
  const [data, setData] = useState<Bootstrap>();
  const [error, setError] = useState("");
  const reload = useCallback(() => api.bootstrap().then((value) => { setData(value); setError(""); }).catch((reason: Error) => setError(reason.message)), []);
  useEffect(() => {
    api.bootstrap().then(setData).catch((reason: Error) => setError(reason.message));
  }, []);
  return { data, error, reload };
}

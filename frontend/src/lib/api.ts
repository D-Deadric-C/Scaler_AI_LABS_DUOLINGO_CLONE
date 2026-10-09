import type { AnswerFeedback, LessonResult } from "@/components/lesson/types";
import type { Achievement, Activity, Bootstrap, LeaderboardEntry, LessonAttempt, Quest, UserStats } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail ?? "Something went wrong");
  }
  return response.json() as Promise<T>;
}

export const api = {
  bootstrap: () => request<Bootstrap>("/bootstrap"),
  path: () => request<Bootstrap>("/courses/1/path"),
  me: () => request<UserStats>("/me"),
  updateSettings: (settings: { dark_mode?: boolean; daily_goal?: number }) => request<UserStats>("/me/settings", { method: "PATCH", body: JSON.stringify(settings) }),
  leaderboard: () => request<{ league: string; ends_in: string; ends_at: string; entries: LeaderboardEntry[] }>("/leaderboards/weekly"),
  achievements: () => request<Achievement[]>("/achievements"),
  quests: () => request<{ ends_in: string; quests: Quest[] }>("/quests"),
  activity: (days = 14) => request<Activity>(`/me/activity?days=${days}`),
  simulateDay: () => request<{ message: string }>("/dev/simulate-day", { method: "POST", body: "{}" }),
  resetDemo: () => request<{ message: string }>("/dev/reset", { method: "POST", body: "{}" }),
  startAttempt: (lessonId: number, mode = "lesson") => request<LessonAttempt>(`/lessons/${lessonId}/attempts`, { method: "POST", body: JSON.stringify({ mode }) }),
  getAttempt: (attemptId: number) => request<LessonAttempt>(`/attempts/${attemptId}`),
  answer: (attemptId: number, exerciseId: number, answer: unknown) => request<AnswerFeedback>(`/attempts/${attemptId}/answers`, { method: "POST", body: JSON.stringify({ exercise_id: exerciseId, answer }) }),
  complete: (attemptId: number) => request<LessonResult>(`/attempts/${attemptId}/complete`, { method: "POST", body: "{}" }),
  abandon: (attemptId: number) => request<{ status: string }>(`/attempts/${attemptId}/abandon`, { method: "POST", body: "{}" }),
  refill: () => request<{ hearts: number; message: string }>("/hearts/practice-refill", { method: "POST", body: "{}" }),
  gemRefill: () => request<{ hearts: number; gems: number; message: string }>("/hearts/gem-refill", { method: "POST", body: "{}" }),
};

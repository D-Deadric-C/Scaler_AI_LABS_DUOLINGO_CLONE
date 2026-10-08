import type { Achievement, Bootstrap, LeaderboardEntry, LessonAttempt, UserStats } from "./types";

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
  leaderboard: () => request<{ league: string; ends_in: string; entries: LeaderboardEntry[] }>("/leaderboards/weekly"),
  achievements: () => request<Achievement[]>("/achievements"),
  startAttempt: (lessonId: number, mode = "lesson") => request<LessonAttempt>(`/lessons/${lessonId}/attempts`, { method: "POST", body: JSON.stringify({ mode }) }),
  getAttempt: (attemptId: number) => request<LessonAttempt>(`/attempts/${attemptId}`),
  answer: (attemptId: number, exerciseId: number, answer: unknown) => request<{ correct: boolean; explanation: string; correct_answer: unknown; hearts: number; next_index: number; ready_to_complete: boolean; failed: boolean }>(`/attempts/${attemptId}/answers`, { method: "POST", body: JSON.stringify({ exercise_id: exerciseId, answer }) }),
  complete: (attemptId: number) => request<{ xp_awarded: number; accuracy: number; streak: number; total_xp: number; new_achievements: Achievement[] }>(`/attempts/${attemptId}/complete`, { method: "POST", body: "{}" }),
  abandon: (attemptId: number) => request<{ status: string }>(`/attempts/${attemptId}/abandon`, { method: "POST", body: "{}" }),
  refill: () => request<{ hearts: number; message: string }>("/hearts/practice-refill", { method: "POST", body: "{}" }),
};

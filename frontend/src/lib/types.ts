export type UserStats = {
  id: number;
  username: string;
  display_name: string;
  avatar_color: string;
  total_xp: number;
  weekly_xp: number;
  gems: number;
  hearts: number;
  max_hearts: number;
  current_streak: number;
  longest_streak: number;
  daily_goal: number;
  today_xp: number;
  dark_mode: boolean;
  next_heart_at: string | null;
  /** Learner-local ISO dates: the last day a lesson was finished, and today's date. */
  last_active_date: string | null;
  today: string;
  tz_offset_minutes: number;
};

export type PathSkill = {
  id: number;
  title: string;
  description: string;
  icon: string;
  status: "completed" | "available" | "locked";
  progress: number;
  total_lessons: number;
  lesson_id: number;
  xp_reward: number;
};

export type PathUnit = {
  id: number;
  position: number;
  title: string;
  objective: string;
  color: string;
  skills: PathSkill[];
  chest: { status: "locked" | "ready" | "opened"; gems: number };
};

export type LeaderboardEntry = {
  rank: number;
  id: number;
  name: string;
  username: string;
  xp: number;
  avatar_color: string;
  is_current: boolean;
  zone?: "promotion" | "safe" | "demotion";
};

export type Achievement = {
  id?: number;
  title: string;
  description?: string;
  icon: string;
  earned?: boolean;
  progress?: number;
  threshold?: number;
};

export type Bootstrap = {
  course: { id: number; title: string; flag: string };
  user: UserStats;
  units: PathUnit[];
  leaderboard: LeaderboardEntry[];
  achievements: Achievement[];
  practice_lesson_id: number | null;
};

export type Exercise = {
  id: number;
  type: "multiple_choice" | "word_bank" | "match_pairs" | "fill_blank" | "type_answer";
  prompt: string;
  hint?: string;
  payload: Record<string, unknown>;
};

export type LessonAttempt = {
  attempt_id: number;
  lesson: { id: number; title: string; xp_reward: number };
  mode?: string;
  status: string;
  /** Exercise ids still to answer, in order; wrong answers are re-queued at the end. */
  queue: number[];
  total_exercises: number;
  correct_count: number;
  hearts: number;
  seconds_left?: number | null;
  exercises: Exercise[];
};


export type Quest = { id: string; title: string; progress: number; target: number; completed: boolean; reward_gems: number };
export type ActivityDay = { date: string; xp: number; lessons: number; goal_met: boolean };
export type Activity = { days: ActivityDay[]; current_streak: number; longest_streak: number };

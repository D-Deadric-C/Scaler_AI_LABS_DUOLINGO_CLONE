import { LessonPlayer } from "@/components/lesson/LessonPlayer";

export default async function LessonPage({ params, searchParams }: { params: Promise<{ lessonId: string }>; searchParams: Promise<{ mode?: string }> }) {
  const { lessonId } = await params;
  const { mode } = await searchParams;
  const safeMode = mode === "practice" || mode === "legendary" ? mode : "lesson";
  return <LessonPlayer lessonId={Number(lessonId)} mode={safeMode}/>;
}

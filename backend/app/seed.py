from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    AttemptMode,
    AttemptStatus,
    XPSource,
    Achievement,
    Course,
    DailyActivity,
    Exercise,
    ExerciseAttempt,
    Lesson,
    LessonAttempt,
    Skill,
    SkillProgress,
    Unit,
    User,
    XPEvent,
    utc_now,
)
from .services import clock
from .services.achievements import evaluate_achievements
from .services.leaderboard import ensure_bot_weekly_xp


SKILLS = [
    ("Order at a café", "Use greetings and order drinks", "coffee"),
    ("Introduce yourself", "Share your name and where you live", "chat"),
    ("Talk about family", "Describe people close to you", "people"),
    ("Find your way", "Ask for and understand directions", "compass"),
    ("Plan your day", "Talk about routines and time", "clock"),
    ("Travel confidently", "Use practical phrases on a trip", "plane"),
]


EXERCISE_SETS = [
    [
        ("multiple_choice", "Choose the correct translation", {"phrase": "hola", "options": ["hello", "goodbye", "please", "thanks"]}, {"value": "hello"}, "‘Hola’ means ‘hello’."),
        ("word_bank", "Translate: I want coffee", {"tokens": ["Quiero", "café", "agua", "Yo"], "translation": "I want coffee"}, {"tokens": ["Quiero", "café"]}, "Quiero café means ‘I want coffee’."),
        ("match_pairs", "Match the pairs", {"pairs": [["hola", "hello"], ["café", "coffee"], ["gracias", "thanks"]]}, {"pairs": [["hola", "hello"], ["café", "coffee"], ["gracias", "thanks"]]}, "All three pairs match."),
        ("fill_blank", "Complete the sentence", {"sentence": "Yo ___ agua", "options": ["quiero", "comes", "eres"]}, {"value": "quiero"}, "Yo quiero agua means ‘I want water’."),
        ("type_answer", "Type in Spanish: thank you", {"placeholder": "Type in Spanish"}, {"accepted": ["gracias"]}, "‘Thank you’ is ‘gracias’."),
    ],
    [
        ("multiple_choice", "What does ‘Me llamo Ana’ mean?", {"options": ["My name is Ana", "I know Ana", "Ana is here", "Goodbye Ana"]}, {"value": "My name is Ana"}, "Me llamo means ‘my name is’."),
        ("word_bank", "Translate: I live in Delhi", {"tokens": ["Vivo", "en", "Delhi", "Soy", "de"], "translation": "I live in Delhi"}, {"tokens": ["Vivo", "en", "Delhi"]}, "Vivo en Delhi means ‘I live in Delhi’."),
        ("match_pairs", "Match the introductions", {"pairs": [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]]}, {"pairs": [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]]}, "Great introductions!"),
        ("fill_blank", "Complete the sentence", {"sentence": "Me ___ Ravi", "options": ["llamo", "vivo", "tengo"]}, {"value": "llamo"}, "Me llamo Ravi means ‘My name is Ravi’."),
        ("type_answer", "Type in Spanish: nice to meet you", {"placeholder": "Type in Spanish"}, {"accepted": ["mucho gusto"]}, "‘Nice to meet you’ is ‘mucho gusto’."),
    ],
]


LEARNER_USERNAME = "learner"
LEARNER_WEEKLY_SEED_XP = 95
LEARNER_BASELINE = {
    "total_xp": 185, "gems": 480, "hearts": 4, "max_hearts": 5, "current_streak": 7, "longest_streak": 12,
    "daily_goal": 20, "dark_mode": False,
}
ACHIEVEMENTS = [
    ("first-step", "First Steps", "Complete your first lesson", "shoe", 1, "lessons"),
    ("xp-100", "XP Explorer", "Earn 100 total XP", "bolt", 100, "xp"),
    ("streak-7", "Wildfire", "Reach a 7 day streak", "flame", 7, "streak"),
    ("scholar", "Scholar", "Complete 5 lessons", "book", 5, "lessons"),
    ("flawless", "Flawless", "Finish a lesson without a single mistake", "star", 1, "perfect"),
    ("streak-14", "Unstoppable", "Reach a 14 day streak", "flame", 14, "streak"),
]


def ensure_achievements(db: Session) -> None:
    known = set(db.scalars(select(Achievement.slug)).all())
    for slug, title, description, icon, threshold, metric in ACHIEVEMENTS:
        if slug not in known:
            db.add(Achievement(slug=slug, title=title, description=description, icon=icon, threshold=threshold, metric=metric))
    db.flush()


def seed_learner_week(db: Session, user: User) -> None:
    """Record the sample learner's starting weekly XP once (never re-granted in later weeks)."""
    already_seeded = db.scalar(select(XPEvent.id).where(XPEvent.user_id == user.id, XPEvent.source == XPSource.SEED).limit(1))
    if already_seeded is None:
        monday = clock.week_start(clock.current_time())
        db.add(XPEvent(user_id=user.id, amount=LEARNER_WEEKLY_SEED_XP, source=XPSource.SEED, idempotency_key=f"seed:weekly:{user.id}:{monday:%Y%m%d}", created_at=monday))
        db.flush()


def seed_sample_completion(db: Session, user: User, lesson: Lesson) -> None:
    existing = db.scalar(select(LessonAttempt.id).where(
        LessonAttempt.user_id == user.id,
        LessonAttempt.lesson_id == lesson.id,
        LessonAttempt.status == AttemptStatus.COMPLETED,
    ))
    if existing is not None:
        return
    db.flush()
    exercises = db.scalars(select(Exercise).where(Exercise.lesson_id == lesson.id).order_by(Exercise.position)).all()
    completed_at = utc_now() - timedelta(days=1)
    attempt = LessonAttempt(
        user_id=user.id,
        lesson_id=lesson.id,
        mode=AttemptMode.LESSON,
        status=AttemptStatus.COMPLETED,
        current_index=len(exercises),
        correct_count=len(exercises),
        xp_awarded=20,
        started_at=completed_at - timedelta(minutes=3),
        completed_at=completed_at,
    )
    db.add(attempt)
    db.flush()
    for exercise in exercises:
        answer = exercise.answer
        submitted = answer.get("value") or answer.get("tokens") or answer.get("pairs") or answer["accepted"][0]
        db.add(ExerciseAttempt(attempt_id=attempt.id, exercise_id=exercise.id, submitted_answer={"value": submitted}, correct=True))


def seed_database(db: Session) -> None:
    if db.scalar(select(Course.id).limit(1)) is not None:
        ensure_achievements(db)
        user = db.scalar(select(User).where(User.username == "learner"))
        first_skill = db.scalar(select(Skill).join(Unit).order_by(Unit.position, Skill.position).limit(1))
        if user and first_skill and db.scalar(select(SkillProgress.id).where(
            SkillProgress.user_id == user.id,
            SkillProgress.skill_id == first_skill.id,
            SkillProgress.completed_lessons > 0,
        )):
            lesson = db.scalar(select(Lesson).where(Lesson.skill_id == first_skill.id).order_by(Lesson.position).limit(1))
            if lesson:
                seed_sample_completion(db, user, lesson)
            evaluate_achievements(db, user)
        if user:
            seed_learner_week(db, user)
        ensure_bot_weekly_xp(db)
        db.commit()
        return

    course = Course(slug="spanish-for-english", title="Spanish", target_language="Spanish", flag="ES")
    db.add(course)
    db.flush()

    units = [
        Unit(course_id=course.id, position=1, title="Unit 1", objective="Order food and introduce yourself", color="#58cc02"),
        Unit(course_id=course.id, position=2, title="Unit 2", objective="Talk about your life and travel", color="#1cb0f6"),
    ]
    db.add_all(units)
    db.flush()

    all_skills: list[Skill] = []
    first_lesson: Lesson | None = None
    for index, (title, description, icon) in enumerate(SKILLS):
        unit = units[0] if index < 3 else units[1]
        skill = Skill(unit_id=unit.id, position=(index % 3) + 1, title=title, description=description, icon=icon)
        db.add(skill)
        db.flush()
        all_skills.append(skill)
        lesson = Lesson(skill_id=skill.id, position=1, title=f"{title} · Lesson 1", xp_reward=10)
        db.add(lesson)
        db.flush()
        if index == 0:
            first_lesson = lesson
        source = EXERCISE_SETS[index % len(EXERCISE_SETS)]
        for position, (kind, prompt, payload, answer, explanation) in enumerate(source, start=1):
            exercise = Exercise(lesson_id=lesson.id, position=position, type=kind, prompt=prompt, payload=payload, answer=answer, explanation=explanation)
            db.add(exercise)

    users = [
        User(username="learner", display_name="Alex", avatar_color="#1cb0f6", total_xp=185, gems=480, hearts=4, current_streak=7, longest_streak=12, last_active_date=clock.current_time().date() - timedelta(days=1), daily_goal=20),
        User(username="maya", display_name="Maya", avatar_color="#ce82ff", total_xp=940, current_streak=18, longest_streak=18),
        User(username="leo", display_name="Leo", avatar_color="#ff9600", total_xp=810, current_streak=11, longest_streak=11),
        User(username="sam", display_name="Sam", avatar_color="#ff4b4b", total_xp=720, current_streak=9, longest_streak=9),
        User(username="nora", display_name="Nora", avatar_color="#58cc02", total_xp=640, current_streak=6, longest_streak=6),
        User(username="ari", display_name="Ari", avatar_color="#2b70c9", total_xp=510, current_streak=4, longest_streak=4),
    ]
    db.add_all(users)
    db.flush()

    db.add(SkillProgress(user_id=users[0].id, skill_id=all_skills[0].id, completed_lessons=1, crowns=1))
    seed_sample_completion(db, users[0], first_lesson)
    db.add(DailyActivity(user_id=users[0].id, activity_date=clock.current_time().date(), xp_earned=15, lessons_completed=0))
    ensure_achievements(db)
    seed_learner_week(db, users[0])
    ensure_bot_weekly_xp(db)
    db.flush()
    evaluate_achievements(db, users[0])
    db.commit()

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


# Three additional lessons per unit complete the six-node path. Positions 1–3
# above are kept intact so existing learner progress remains attached to them.
EXTRA_SKILLS = {
    1: [
        (4, "At the market", "Buy food and ask for what you need", "basket", [
            ("multiple_choice", "What does ‘manzana’ mean?", {"options": ["apple", "bread", "milk", "rice"]}, {"value": "apple"}, "‘Manzana’ means ‘apple’."),
            ("word_bank", "Translate: I want an apple", {"tokens": ["Quiero", "una", "manzana", "agua"], "translation": "I want an apple"}, {"tokens": ["Quiero", "una", "manzana"]}, "Quiero una manzana means ‘I want an apple’."),
            ("match_pairs", "Match the market words", {"pairs": [["manzana", "apple"], ["pan", "bread"], ["leche", "milk"]]}, {"pairs": [["manzana", "apple"], ["pan", "bread"], ["leche", "milk"]]}, "You know these market words."),
            ("fill_blank", "Complete the sentence", {"sentence": "Quiero ___ manzana", "options": ["una", "un", "el"]}, {"value": "una"}, "Use ‘una’ with ‘manzana’."),
            ("type_answer", "Type in Spanish: bread", {"placeholder": "Type in Spanish"}, {"accepted": ["pan"]}, "‘Bread’ is ‘pan’."),
        ]),
        (5, "Ask about food", "Order from a menu and ask for the bill", "menu", [
            ("multiple_choice", "What does ‘¿Cuánto cuesta?’ mean?", {"options": ["How much does it cost?", "Where is it?", "What time is it?", "Do you like it?"]}, {"value": "How much does it cost?"}, "‘¿Cuánto cuesta?’ asks for the price."),
            ("word_bank", "Translate: The menu, please", {"tokens": ["El", "menú", "por", "favor", "agua"], "translation": "The menu, please"}, {"tokens": ["El", "menú", "por", "favor"]}, "El menú, por favor means ‘The menu, please’."),
            ("match_pairs", "Match the food words", {"pairs": [["agua", "water"], ["comida", "food"], ["menú", "menu"]]}, {"pairs": [["agua", "water"], ["comida", "food"], ["menú", "menu"]]}, "You matched all the food words."),
            ("fill_blank", "Complete the sentence", {"sentence": "La cuenta, ___ favor", "options": ["por", "con", "sin"]}, {"value": "por"}, "‘Por favor’ means ‘please’."),
            ("type_answer", "Type in Spanish: the bill", {"placeholder": "Type in Spanish"}, {"accepted": ["la cuenta"]}, "‘The bill’ is ‘la cuenta’."),
        ]),
        (6, "Describe a meal", "Say what you like to eat", "food", [
            ("multiple_choice", "What does ‘Está delicioso’ mean?", {"options": ["It is delicious", "It is cold", "I am hungry", "It is late"]}, {"value": "It is delicious"}, "‘Está delicioso’ means ‘It is delicious’."),
            ("word_bank", "Translate: I like the soup", {"tokens": ["Me", "gusta", "la", "sopa", "arroz"], "translation": "I like the soup"}, {"tokens": ["Me", "gusta", "la", "sopa"]}, "Me gusta la sopa means ‘I like the soup’."),
            ("match_pairs", "Match the meal words", {"pairs": [["sopa", "soup"], ["arroz", "rice"], ["queso", "cheese"]]}, {"pairs": [["sopa", "soup"], ["arroz", "rice"], ["queso", "cheese"]]}, "You matched all the meal words."),
            ("fill_blank", "Complete the sentence", {"sentence": "Me gusta ___ arroz", "options": ["el", "la", "un"]}, {"value": "el"}, "Use ‘el’ with ‘arroz’."),
            ("type_answer", "Type in Spanish: It is delicious", {"placeholder": "Type in Spanish"}, {"accepted": ["Está delicioso", "Es delicioso"]}, "‘It is delicious’ is ‘Está delicioso’."),
        ]),
    ],
    2: [
        (4, "Book a ticket", "Get a ticket for your journey", "ticket", [
            ("multiple_choice", "What does ‘un boleto’ mean?", {"options": ["a ticket", "a hotel", "a bag", "a train"]}, {"value": "a ticket"}, "‘Un boleto’ means ‘a ticket’."),
            ("word_bank", "Translate: I need a ticket", {"tokens": ["Necesito", "un", "boleto", "tren"], "translation": "I need a ticket"}, {"tokens": ["Necesito", "un", "boleto"]}, "Necesito un boleto means ‘I need a ticket’."),
            ("match_pairs", "Match the travel words", {"pairs": [["boleto", "ticket"], ["tren", "train"], ["estación", "station"]]}, {"pairs": [["boleto", "ticket"], ["tren", "train"], ["estación", "station"]]}, "You matched all the travel words."),
            ("fill_blank", "Complete the sentence", {"sentence": "Necesito un ___", "options": ["boleto", "leche", "familia"]}, {"value": "boleto"}, "Necesito un boleto means ‘I need a ticket’."),
            ("type_answer", "Type in Spanish: train", {"placeholder": "Type in Spanish"}, {"accepted": ["tren"]}, "‘Train’ is ‘tren’."),
        ]),
        (5, "Talk about plans", "Describe what you will do next", "clock", [
            ("multiple_choice", "What does ‘mañana’ mean?", {"options": ["tomorrow", "yesterday", "tonight", "now"]}, {"value": "tomorrow"}, "‘Mañana’ means ‘tomorrow’."),
            ("word_bank", "Translate: I am going to the park", {"tokens": ["Voy", "al", "parque", "museo"], "translation": "I am going to the park"}, {"tokens": ["Voy", "al", "parque"]}, "Voy al parque means ‘I am going to the park’."),
            ("match_pairs", "Match the time words", {"pairs": [["mañana", "tomorrow"], ["hoy", "today"], ["tarde", "afternoon"]]}, {"pairs": [["mañana", "tomorrow"], ["hoy", "today"], ["tarde", "afternoon"]]}, "You matched all the time words."),
            ("fill_blank", "Complete the sentence", {"sentence": "Voy ___ parque", "options": ["al", "de", "por"]}, {"value": "al"}, "‘Al’ means ‘to the’ here."),
            ("type_answer", "Type in Spanish: tomorrow", {"placeholder": "Type in Spanish"}, {"accepted": ["mañana"]}, "‘Tomorrow’ is ‘mañana’."),
        ]),
        (6, "Share a trip", "Tell someone about a journey", "plane", [
            ("multiple_choice", "What does ‘el viaje’ mean?", {"options": ["the trip", "the ticket", "the hotel", "the city"]}, {"value": "the trip"}, "‘El viaje’ means ‘the trip’."),
            ("word_bank", "Translate: We visit the city", {"tokens": ["Visitamos", "la", "ciudad", "foto"], "translation": "We visit the city"}, {"tokens": ["Visitamos", "la", "ciudad"]}, "Visitamos la ciudad means ‘We visit the city’."),
            ("match_pairs", "Match the trip words", {"pairs": [["viaje", "trip"], ["ciudad", "city"], ["foto", "photo"]]}, {"pairs": [["viaje", "trip"], ["ciudad", "city"], ["foto", "photo"]]}, "You matched all the trip words."),
            ("fill_blank", "Complete the sentence", {"sentence": "La ciudad es ___", "options": ["bonita", "mañana", "boleto"]}, {"value": "bonita"}, "La ciudad es bonita means ‘The city is beautiful’."),
            ("type_answer", "Type in Spanish: the city", {"placeholder": "Type in Spanish"}, {"accepted": ["la ciudad"]}, "‘The city’ is ‘la ciudad’."),
        ]),
    ],
}


def ensure_extra_skills(db: Session, course: Course | None) -> None:
    """Extend older Spanish databases without changing existing skills or progress."""
    if course is None or course.slug != "spanish-for-english":
        return
    units = {unit.position: unit for unit in db.scalars(select(Unit).where(Unit.course_id == course.id)).all()}
    for unit_position, additions in EXTRA_SKILLS.items():
        unit = units.get(unit_position)
        if unit is None:
            continue
        existing = set(db.scalars(select(Skill.position).where(Skill.unit_id == unit.id)).all())
        for position, title, description, icon, exercises in additions:
            if position in existing:
                continue
            skill = Skill(unit_id=unit.id, position=position, title=title, description=description, icon=icon)
            db.add(skill)
            db.flush()
            lesson = Lesson(skill_id=skill.id, position=1, title=f"{title} · Lesson 1", xp_reward=10)
            db.add(lesson)
            db.flush()
            for exercise_position, (kind, prompt, payload, answer, explanation) in enumerate(exercises, start=1):
                db.add(Exercise(lesson_id=lesson.id, position=exercise_position, type=kind, prompt=prompt, payload=payload, answer=answer, explanation=explanation))


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
    for turn, exercise in enumerate(exercises, start=1):
        answer = exercise.answer
        submitted = answer.get("value") or answer.get("tokens") or answer.get("pairs") or answer["accepted"][0]
        db.add(ExerciseAttempt(attempt_id=attempt.id, exercise_id=exercise.id, turn=turn, submitted_answer={"value": submitted}, correct=True))


def seed_database(db: Session) -> None:
    if db.scalar(select(Course.id).limit(1)) is not None:
        ensure_extra_skills(db, db.scalar(select(Course).where(Course.slug == "spanish-for-english")))
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

    ensure_extra_skills(db, course)

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

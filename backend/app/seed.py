from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Achievement,
    Course,
    DailyActivity,
    Exercise,
    Lesson,
    Skill,
    SkillProgress,
    Unit,
    User,
)


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


def seed_database(db: Session) -> None:
    if db.scalar(select(Course.id).limit(1)) is not None:
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
    for index, (title, description, icon) in enumerate(SKILLS):
        unit = units[0] if index < 3 else units[1]
        skill = Skill(unit_id=unit.id, position=(index % 3) + 1, title=title, description=description, icon=icon)
        db.add(skill)
        db.flush()
        all_skills.append(skill)
        lesson = Lesson(skill_id=skill.id, position=1, title=f"{title} · Lesson 1", xp_reward=10)
        db.add(lesson)
        db.flush()
        source = EXERCISE_SETS[index % len(EXERCISE_SETS)]
        for position, (kind, prompt, payload, answer, explanation) in enumerate(source, start=1):
            db.add(Exercise(lesson_id=lesson.id, position=position, type=kind, prompt=prompt, payload=payload, answer=answer, explanation=explanation))

    users = [
        User(username="learner", display_name="Alex", avatar_color="#1cb0f6", total_xp=185, weekly_xp=95, gems=480, hearts=4, current_streak=7, longest_streak=12, last_active_date=date.today() - timedelta(days=1), daily_goal=20),
        User(username="maya", display_name="Maya", avatar_color="#ce82ff", total_xp=940, weekly_xp=260, current_streak=18),
        User(username="leo", display_name="Leo", avatar_color="#ff9600", total_xp=810, weekly_xp=210, current_streak=11),
        User(username="sam", display_name="Sam", avatar_color="#ff4b4b", total_xp=720, weekly_xp=170, current_streak=9),
        User(username="nora", display_name="Nora", avatar_color="#58cc02", total_xp=640, weekly_xp=125, current_streak=6),
        User(username="ari", display_name="Ari", avatar_color="#2b70c9", total_xp=510, weekly_xp=80, current_streak=4),
    ]
    db.add_all(users)
    db.flush()

    db.add(SkillProgress(user_id=users[0].id, skill_id=all_skills[0].id, completed_lessons=1, crowns=1))
    db.add(DailyActivity(user_id=users[0].id, activity_date=date.today(), xp_earned=15, lessons_completed=0))
    db.add_all([
        Achievement(slug="first-step", title="First Steps", description="Complete your first lesson", icon="shoe", threshold=1, metric="lessons"),
        Achievement(slug="xp-100", title="XP Explorer", description="Earn 100 total XP", icon="bolt", threshold=100, metric="xp"),
        Achievement(slug="streak-7", title="Wildfire", description="Reach a 7 day streak", icon="flame", threshold=7, metric="streak"),
        Achievement(slug="scholar", title="Scholar", description="Complete 5 lessons", icon="book", threshold=5, metric="lessons"),
    ])
    db.commit()


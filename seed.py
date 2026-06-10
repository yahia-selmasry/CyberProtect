"""Dev-only seed script. Run with: python seed.py"""
import os
from datetime import date
from app import app
from database import db, Athlete, Result
from utils import seconds_to_display


def init_db():
    """Create all tables if they don't exist."""
    db.create_all()


def seed():
    init_db()

    athletes = [
        Athlete(name="Alex Chen",    grade=11, specialty="1600m"),
        Athlete(name="Jordan Smith", grade=10, specialty="5K XC"),
        Athlete(name="Sam Rivera",   grade=11, specialty="800m"),
    ]
    for a in athletes:
        db.session.add(a)
    db.session.flush()  # populate ids before creating results

    alex, jordan, sam = athletes

    raw_results = [
        # Alex Chen — 1600m, two meets + one practice
        dict(athlete=alex,   event="1600m", time_seconds=272.1,  session_type="meet",
             meet_name="Regionals",    meet_date=date(2026, 3, 15)),
        dict(athlete=alex,   event="1600m", time_seconds=268.5,  session_type="meet",
             meet_name="State Quals",  meet_date=date(2026, 4, 10)),
        dict(athlete=alex,   event="1600m", time_seconds=275.0,  session_type="practice",
             meet_name=None,           meet_date=date(2026, 4, 2),
             notes="tempo day, held back"),

        # Jordan Smith — 5K XC, one meet + one practice
        dict(athlete=jordan, event="5K XC",  time_seconds=1142.0, session_type="meet",
             meet_name="Invitational",  meet_date=date(2026, 10, 5)),
        dict(athlete=jordan, event="5K XC",  time_seconds=1160.0, session_type="practice",
             meet_name=None,            meet_date=date(2026, 9, 28)),

        # Sam Rivera — 800m, three entries
        dict(athlete=sam,    event="800m",   time_seconds=122.4,  session_type="meet",
             meet_name="Regionals",    meet_date=date(2026, 3, 15)),
        dict(athlete=sam,    event="800m",   time_seconds=119.8,  session_type="meet",
             meet_name="State Quals",  meet_date=date(2026, 4, 10)),
        dict(athlete=sam,    event="800m",   time_seconds=121.0,  session_type="practice",
             meet_name=None,           meet_date=date(2026, 4, 5),
             notes="negative split workout"),
    ]

    result_objs = []
    for r in raw_results:
        obj = Result(
            athlete_id=r["athlete"].id,
            event=r["event"],
            time_seconds=r["time_seconds"],
            session_type=r["session_type"],
            meet_name=r.get("meet_name"),
            meet_date=r.get("meet_date"),
            notes=r.get("notes"),
        )
        db.session.add(obj)
        result_objs.append(obj)

    db.session.commit()

    # Mark personal bests per athlete+event
    seen = set()
    for r in result_objs:
        key = (r.athlete_id, r.event)
        if key not in seen:
            seen.add(key)
            peers = [x for x in result_objs if x.athlete_id == r.athlete_id and x.event == r.event]
            best = min(peers, key=lambda x: x.time_seconds)
            for p in peers:
                p.is_personal_best = p.id == best.id

    db.session.commit()

    print(f"Seeded successfully — {len(athletes)} athletes, {len(result_objs)} results")

    for a in athletes:
        pb = next((r for r in result_objs if r.athlete_id == a.id and r.is_personal_best), None)
        pb_str = seconds_to_display(pb.time_seconds) if pb else "n/a"
        print(f"  {a.name} ({a.specialty}) — PB: {pb_str}")


if __name__ == "__main__":
    with app.app_context():
        seed()

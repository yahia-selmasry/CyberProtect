import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


def _make_app(db_path):
    """Create a fresh configured Flask app pointing at db_path."""
    os.environ.setdefault("SECRET_KEY", "test-secret")
    # Import fresh to avoid engine caching — must happen inside fixture
    from flask import Flask
    from flask_login import LoginManager
    from database import db as _db, User, TrackUser

    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"))
    app.secret_key = "test-secret"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    _db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.track_login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("t:"):
            return TrackUser.query.get(int(user_id[2:]))
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.scans import scans_bp
    from routes.findings import findings_bp
    from routes.team import team_bp
    from routes.export import export_bp
    from routes.time_entry import time_entry_bp

    for bp in (auth_bp, dashboard_bp, scans_bp, findings_bp, team_bp, export_bp, time_entry_bp):
        if bp.name not in app.blueprints:
            app.register_blueprint(bp)

    return app


@pytest.fixture()
def client():
    """Coach TrackUser client — used by the existing time-entry tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    from database import db as _db, Athlete, TrackUser

    app = _make_app(db_path)

    with app.app_context():
        _db.create_all()

        coach = TrackUser(username="coach1", role="coach")
        coach.set_password("password")
        _db.session.add(coach)

        athlete = Athlete(name="Jane Doe", grade=11)
        _db.session.add(athlete)
        _db.session.commit()

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["_user_id"] = f"t:{coach.id}"
                sess["_fresh"] = True
            yield c, athlete.id, app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def auth_client():
    """Returns (app, test_client_factory) with two athletes and one coach seeded."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    from database import db as _db, Athlete, TrackUser

    app = _make_app(db_path)

    with app.app_context():
        _db.create_all()

        athlete_a_record = Athlete(name="Athlete A", grade=10)
        athlete_b_record = Athlete(name="Athlete B", grade=11)
        _db.session.add_all([athlete_a_record, athlete_b_record])
        _db.session.flush()

        athlete_a = TrackUser(username="athlete_a", role="athlete", athlete_id=athlete_a_record.id)
        athlete_a.set_password("pw")
        athlete_b = TrackUser(username="athlete_b", role="athlete", athlete_id=athlete_b_record.id)
        athlete_b.set_password("pw")
        coach = TrackUser(username="coach", role="coach")
        coach.set_password("pw")

        _db.session.add_all([athlete_a, athlete_b, coach])
        _db.session.commit()

        ids = {
            "athlete_a_id": athlete_a_record.id,
            "athlete_b_id": athlete_b_record.id,
            "athlete_a_track_id": athlete_a.id,
            "athlete_b_track_id": athlete_b.id,
            "coach_track_id": coach.id,
        }

        yield app, ids

    os.close(db_fd)
    os.unlink(db_path)


def _login_as(app, track_user_id):
    """Return a test client with the given TrackUser logged in."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = f"t:{track_user_id}"
        sess["_fresh"] = True
    return c


def test_add_time_post_redirects_and_saves(client):
    c, athlete_id, app = client

    resp = c.post("/add", data={
        "athlete_id": str(athlete_id),
        "event": "1600m",
        "time": "4:32.10",
        "meet_name": "Spring Invitational",
        "meet_date": "2026-05-01",
        "session_type": "meet",
        "notes": "",
    }, follow_redirects=False)

    assert resp.status_code == 302

    from database import Result
    with app.app_context():
        result = Result.query.filter_by(athlete_id=athlete_id, event="1600m").first()
        assert result is not None
        assert abs(result.time_seconds - 272.10) < 0.001
        assert result.meet_name == "Spring Invitational"
        assert result.is_personal_best is True


def test_add_time_future_date_rejected(client):
    c, athlete_id, app = client

    resp = c.post("/add", data={
        "athlete_id": str(athlete_id),
        "event": "1600m",
        "time": "4:32.10",
        "meet_name": "",
        "meet_date": "2099-01-01",
        "session_type": "meet",
        "notes": "",
    })

    assert resp.status_code == 422
    assert b"future" in resp.data


def test_add_time_bad_time_format_rejected(client):
    c, athlete_id, app = client

    resp = c.post("/add", data={
        "athlete_id": str(athlete_id),
        "event": "1600m",
        "time": "not-a-time",
        "meet_name": "",
        "meet_date": "2026-05-01",
        "session_type": "meet",
        "notes": "",
    })

    assert resp.status_code == 422
    assert b"MM:SS" in resp.data


def test_add_time_missing_athlete_rejected(client):
    c, _, app = client

    resp = c.post("/add", data={
        "athlete_id": "",
        "event": "1600m",
        "time": "4:32.10",
        "meet_name": "",
        "meet_date": "2026-05-01",
        "session_type": "meet",
        "notes": "",
    })

    assert resp.status_code == 422


def test_athlete_dashboard_returns_200_with_name(client):
    c, athlete_id, app = client

    resp = c.get(f"/athlete/{athlete_id}")

    assert resp.status_code == 200
    assert b"Jane Doe" in resp.data


def test_chart_data_returns_json(client):
    c, athlete_id, app = client

    from database import Result, db as _db
    import datetime

    with app.app_context():
        r = Result(
            athlete_id=athlete_id,
            event="1600m",
            time_seconds=272.10,
            meet_date=datetime.date(2026, 5, 1),
            session_type="meet",
        )
        _db.session.add(r)
        _db.session.commit()

    resp = c.get(f"/athlete/{athlete_id}/chart-data?event=1600m")

    assert resp.status_code == 200
    data = resp.get_json()
    assert "labels" in data
    assert "times" in data
    assert len(data["labels"]) == 1
    assert abs(data["times"][0] - 272.10) < 0.001


def test_compare_returns_200(client):
    c, athlete_id, app = client

    resp = c.get(f"/athlete/{athlete_id}/compare?event=1600m")

    assert resp.status_code == 200
    assert b"Meet vs Practice" in resp.data


# ---------------------------------------------------------------------------
# Auth and access-control tests
# ---------------------------------------------------------------------------

def test_unauthenticated_athlete_page_redirects_to_login(auth_client):
    app, ids = auth_client
    c = app.test_client()
    resp = c.get(f"/athlete/{ids['athlete_a_id']}", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_correct_login_redirects_to_dashboard(auth_client):
    app, ids = auth_client
    c = app.test_client()
    resp = c.post("/track/login", data={"username": "coach", "password": "pw"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"] != "/track/login"


def test_bad_login_stays_on_login_page(auth_client):
    app, ids = auth_client
    c = app.test_client()
    resp = c.post("/track/login", data={"username": "coach", "password": "wrong"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid" in resp.data


def test_athlete_cannot_access_other_athletes_page(auth_client):
    app, ids = auth_client
    c = _login_as(app, ids["athlete_a_track_id"])
    resp = c.get(f"/athlete/{ids['athlete_b_id']}")
    assert resp.status_code == 403


def test_athlete_can_access_own_page(auth_client):
    app, ids = auth_client
    c = _login_as(app, ids["athlete_a_track_id"])
    resp = c.get(f"/athlete/{ids['athlete_a_id']}")
    assert resp.status_code == 200


def test_coach_can_access_any_athlete_page(auth_client):
    app, ids = auth_client
    c = _login_as(app, ids["coach_track_id"])
    resp_a = c.get(f"/athlete/{ids['athlete_a_id']}")
    resp_b = c.get(f"/athlete/{ids['athlete_b_id']}")
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200


def test_athlete_cannot_access_team_page(auth_client):
    app, ids = auth_client
    c = _login_as(app, ids["athlete_a_track_id"])
    resp = c.get("/team")
    assert resp.status_code == 403


def test_coach_can_access_team_page(auth_client):
    app, ids = auth_client
    c = _login_as(app, ids["coach_track_id"])
    resp = c.get("/team")
    assert resp.status_code == 200


def test_team_page_shows_pb_and_team_fastest(auth_client):
    import datetime
    from database import Result, db as _db

    app, ids = auth_client

    with app.app_context():
        _db.session.add(Result(
            athlete_id=ids["athlete_a_id"],
            event="1600m",
            time_seconds=272.10,
            meet_date=datetime.date(2026, 5, 1),
            session_type="meet",
            is_personal_best=True,
        ))
        _db.session.add(Result(
            athlete_id=ids["athlete_b_id"],
            event="1600m",
            time_seconds=265.00,
            meet_date=datetime.date(2026, 5, 2),
            session_type="meet",
            is_personal_best=True,
        ))
        _db.session.commit()

    c = _login_as(app, ids["coach_track_id"])
    resp = c.get("/team")

    assert resp.status_code == 200
    # Both athlete names appear
    assert b"Athlete A" in resp.data
    assert b"Athlete B" in resp.data
    # Athlete A's PB (4:32.10)
    assert b"4:32.10" in resp.data
    # Athlete B's faster time (4:25.00) should appear as team fastest
    assert b"4:25.00" in resp.data
    # "Team fastest" label present
    assert b"Team fastest" in resp.data

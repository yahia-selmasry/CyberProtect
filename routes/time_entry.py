from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, abort
from flask_login import login_required, current_user

from database import Athlete, Result, TrackUser, db, update_personal_bests
from utils import display_to_seconds, seconds_to_display

time_entry_bp = Blueprint("time_entry", __name__)

EVENTS = ["800m", "1600m", "3200m", "5K XC", "10K XC"]


def _require_coach_or_own_athlete(athlete_id: int):
    """Abort 403 if current user is an athlete viewing another athlete's page."""
    if not isinstance(current_user, TrackUser):
        return
    if current_user.role == "athlete" and current_user.athlete_id != athlete_id:
        abort(403)


def _require_coach():
    """Abort 403 if current user is not a coach."""
    if not isinstance(current_user, TrackUser) or current_user.role != "coach":
        abort(403)


@time_entry_bp.route("/add", methods=["GET"])
@login_required
def add_time_form():
    """Render the add time entry form."""
    athletes = Athlete.query.order_by(Athlete.name).all()
    return render_template("add_time.html", athletes=athletes, events=EVENTS)


@time_entry_bp.route("/add", methods=["POST"])
@login_required
def add_time_submit():
    """Validate and save a new time entry."""
    athlete_id = request.form.get("athlete_id", "").strip()
    event = request.form.get("event", "").strip()
    time_str = request.form.get("time", "").strip()
    meet_name = request.form.get("meet_name", "").strip()
    meet_date_str = request.form.get("meet_date", "").strip()
    session_type = request.form.get("session_type", "meet").strip()
    notes = request.form.get("notes", "").strip()

    errors = _validate(athlete_id, event, time_str, meet_date_str)
    if errors:
        for msg in errors:
            flash(msg)
        athletes = Athlete.query.order_by(Athlete.name).all()
        return render_template("add_time.html", athletes=athletes, events=EVENTS), 422

    time_seconds = display_to_seconds(time_str)
    meet_date = date.fromisoformat(meet_date_str) if meet_date_str else None

    result = Result(
        athlete_id=int(athlete_id),
        event=event,
        time_seconds=time_seconds,
        meet_name=meet_name or None,
        meet_date=meet_date,
        session_type=session_type,
        notes=notes or None,
    )
    db.session.add(result)
    db.session.commit()
    update_personal_bests(int(athlete_id), event)

    return redirect(url_for("time_entry.athlete_detail", athlete_id=athlete_id))


@time_entry_bp.route("/team")
@login_required
def team():
    """List all athletes with PBs per event — coach only."""
    _require_coach()
    athletes = (
        Athlete.query
        .order_by(Athlete.grade.asc().nullslast(), Athlete.name.asc())
        .all()
    )
    pbs = _build_pb_table(athletes)
    team_fastest = _build_team_fastest(pbs)
    return render_template(
        "team_roster.html",
        athletes=athletes,
        events=EVENTS,
        pbs=pbs,
        team_fastest=team_fastest,
    )


def _build_pb_table(athletes):
    """Return {athlete_id: {event: display_str}} for all PB results."""
    if not athletes:
        return {}
    athlete_ids = [a.id for a in athletes]
    pb_rows = (
        Result.query
        .filter(Result.athlete_id.in_(athlete_ids), Result.is_personal_best == True)  # noqa: E712
        .all()
    )
    table = {a.id: {} for a in athletes}
    for r in pb_rows:
        table[r.athlete_id][r.event] = seconds_to_display(r.time_seconds)
    return table


def _build_team_fastest(pbs):
    """Return {event: display_str} for the team-fastest time in each event."""
    fastest = {}
    for athlete_pbs in pbs.values():
        for event, display in athlete_pbs.items():
            if event not in fastest:
                fastest[event] = display
            elif display_to_seconds(display) < display_to_seconds(fastest[event]):
                fastest[event] = display
    return fastest


@time_entry_bp.route("/athlete/<int:athlete_id>")
@login_required
def athlete_detail(athlete_id):
    """Show all results and performance chart for a single athlete."""
    _require_coach_or_own_athlete(athlete_id)
    athlete = Athlete.query.get_or_404(athlete_id)
    results = (
        Result.query.filter_by(athlete_id=athlete_id)
        .order_by(Result.meet_date.desc())
        .all()
    )
    for r in results:
        r.time_display = seconds_to_display(r.time_seconds)
    return render_template("athlete_detail.html", athlete=athlete, results=results, events=EVENTS)


@time_entry_bp.route("/athlete/<int:athlete_id>/compare")
@login_required
def compare(athlete_id):
    """Compare meet vs practice times for a given event."""
    _require_coach_or_own_athlete(athlete_id)
    athlete = Athlete.query.get_or_404(athlete_id)
    event = request.args.get("event", EVENTS[0])

    def _rows(session_type):
        return (
            Result.query
            .filter_by(athlete_id=athlete_id, event=event, session_type=session_type)
            .filter(Result.meet_date.isnot(None))
            .order_by(Result.meet_date.asc())
            .all()
        )

    meet_rows = _rows("meet")
    practice_rows = _rows("practice")

    def _series(rows):
        return {
            "labels": [str(r.meet_date) for r in rows],
            "times": [r.time_seconds for r in rows],
        }

    meet_series = _series(meet_rows)
    practice_series = _series(practice_rows)

    avg_meet = (sum(meet_series["times"]) / len(meet_series["times"])) if meet_series["times"] else None
    avg_practice = (sum(practice_series["times"]) / len(practice_series["times"])) if practice_series["times"] else None

    gap_seconds = round(avg_meet - avg_practice, 2) if (avg_meet and avg_practice) else None
    gap_pct = round((gap_seconds / avg_practice) * 100, 1) if gap_seconds is not None else None

    return render_template(
        "compare.html",
        athlete=athlete,
        event=event,
        events=EVENTS,
        meet_series=meet_series,
        practice_series=practice_series,
        avg_meet=seconds_to_display(avg_meet) if avg_meet else None,
        avg_practice=seconds_to_display(avg_practice) if avg_practice else None,
        gap_seconds=gap_seconds,
        gap_pct=gap_pct,
    )


@time_entry_bp.route("/athlete/<int:athlete_id>/chart-data")
@login_required
def chart_data(athlete_id):
    """Return JSON time-series data for a single athlete+event."""
    _require_coach_or_own_athlete(athlete_id)
    Athlete.query.get_or_404(athlete_id)
    event = request.args.get("event", "").strip()
    rows = (
        Result.query
        .filter_by(athlete_id=athlete_id, event=event)
        .filter(Result.meet_date.isnot(None))
        .order_by(Result.meet_date.asc())
        .all()
    )
    labels = [str(r.meet_date) for r in rows]
    times = [r.time_seconds for r in rows]
    return jsonify({"labels": labels, "times": times})


def _validate(athlete_id, event, time_str, meet_date_str):
    """Return a list of validation error messages."""
    errors = []
    if not athlete_id:
        errors.append("Athlete is required.")
    if not event or event not in EVENTS:
        errors.append("A valid event is required.")
    if not time_str:
        errors.append("Time is required.")
    else:
        try:
            display_to_seconds(time_str)
        except Exception:
            errors.append("Time must be in MM:SS.ms format, e.g. 4:32.10.")
    if meet_date_str:
        try:
            entered = date.fromisoformat(meet_date_str)
            if entered > date.today():
                errors.append("Date cannot be in the future.")
        except ValueError:
            errors.append("Invalid date format.")
    return errors

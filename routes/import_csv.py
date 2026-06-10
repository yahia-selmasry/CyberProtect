import csv
import io
import logging
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from database import Athlete, Result, TrackUser, db, update_personal_bests
from utils import display_to_seconds

logger = logging.getLogger(__name__)

import_bp = Blueprint("import_csv", __name__)

# Athletic.net event name → canonical event name used in DB
EVENT_MAP = {
    "1 mile run": "1600m",
    "mile run": "1600m",
    "1600 meters": "1600m",
    "1600m": "1600m",
    "800 meters": "800m",
    "800m": "800m",
    "3200 meters": "3200m",
    "3200m": "3200m",
    "2 mile run": "3200m",
    "5000 meters": "5K XC",
    "5k": "5K XC",
    "5k xc": "5K XC",
    "5000m": "5K XC",
    "10000 meters": "10K XC",
    "10k": "10K XC",
    "10k xc": "10K XC",
    "10000m": "10K XC",
}

VALID_EVENTS = {"800m", "1600m", "3200m", "5K XC", "10K XC"}


def _map_event(raw: str):
    """Normalize Athletic.net event name to our canonical event. Returns None if unrecognized."""
    return EVENT_MAP.get(raw.strip().lower())


def _parse_mark(mark: str):
    """Parse Athletic.net Mark string (e.g. '4:32.10') to seconds. Returns None on failure."""
    try:
        return display_to_seconds(mark.strip())
    except Exception:
        return None


def _parse_date(date_str: str):
    """Parse date string; supports YYYY-MM-DD and M/D/YYYY. Returns None on failure."""
    date_str = date_str.strip()
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return date.fromisoformat(date_str) if fmt == "%Y-%m-%d" else _strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _strptime(date_str: str, fmt: str) -> date:
    """Wrapper around strptime returning a date object."""
    from datetime import datetime
    return datetime.strptime(date_str, fmt).date()


def _athlete_for_user():
    """Return the Athlete linked to the current TrackUser, or None."""
    if not isinstance(current_user, TrackUser):
        return None
    if current_user.athlete_id is None:
        return None
    return Athlete.query.get(current_user.athlete_id)


@import_bp.route("/import", methods=["GET"])
@login_required
def import_form():
    """Render the CSV import upload form."""
    return render_template("import.html")


@import_bp.route("/import", methods=["POST"])
@login_required
def import_submit():
    """Parse an Athletic.net CSV upload and insert results for the logged-in athlete."""
    athlete = _athlete_for_user()
    if athlete is None:
        flash("Only athletes linked to an account can import results.")
        return redirect(url_for("import_csv.import_form"))

    file = request.files.get("csv_file")
    if not file or file.filename == "":
        flash("Please select a CSV file to upload.")
        return redirect(url_for("import_csv.import_form"))

    try:
        text = file.read().decode("utf-8-sig")  # strip BOM if present
    except UnicodeDecodeError:
        flash("Could not read the file. Please upload a UTF-8 CSV.")
        return redirect(url_for("import_csv.import_form"))

    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    events_updated: set[str] = set()

    for row in reader:
        mark = (row.get("Mark") or row.get("mark") or "").strip()
        raw_event = (row.get("Event") or row.get("event") or "").strip()
        raw_date = (row.get("Date") or row.get("date") or "").strip()
        meet_name = (row.get("Meet") or row.get("meet") or "").strip()

        event = _map_event(raw_event)
        if event is None:
            logger.info("CSV import: skipping unrecognized event %r", raw_event)
            skipped += 1
            continue

        time_seconds = _parse_mark(mark)
        if time_seconds is None:
            logger.info("CSV import: skipping unparseable mark %r (event=%s)", mark, event)
            skipped += 1
            continue

        meet_date = _parse_date(raw_date)

        result = Result(
            athlete_id=athlete.id,
            event=event,
            time_seconds=time_seconds,
            meet_name=meet_name or None,
            meet_date=meet_date,
            session_type="meet",
        )
        db.session.add(result)
        events_updated.add(event)
        imported += 1

    db.session.commit()

    for event in events_updated:
        update_personal_bests(athlete.id, event)

    flash(f"Imported {imported} result{'s' if imported != 1 else ''} successfully. {skipped} row{'s' if skipped != 1 else ''} skipped.")
    return redirect(url_for("time_entry.athlete_detail", athlete_id=athlete.id))

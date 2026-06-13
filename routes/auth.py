from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from database import db, User, TrackUser, Athlete

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/pricing")
def pricing():
    """Public pricing page."""
    return render_template("pricing.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard.index"))
        flash("Invalid email or password.")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already registered.")
            return redirect(url_for("auth.register"))
        user = User(email=request.form["email"])
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard.index"))
    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/track/login", methods=["GET", "POST"])
def track_login():
    """Login for track athletes and coaches."""
    if request.method == "POST":
        user = TrackUser.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("time_entry.add_time_form"))
        flash("Invalid username or password.")
    return render_template("track_login.html")


@auth_bp.route("/track/logout")
@login_required
def track_logout():
    """Logout for track athletes and coaches."""
    logout_user()
    return redirect(url_for("auth.track_login"))


@auth_bp.route("/track/register", methods=["GET", "POST"])
def track_register():
    """Register a new athlete account (coaches create these)."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "athlete").strip()
        athlete_name = request.form.get("athlete_name", "").strip()

        if not username or not password:
            flash("Username and password are required.")
            return render_template("track_register.html"), 422

        if TrackUser.query.filter_by(username=username).first():
            flash("Username already taken.")
            return redirect(url_for("auth.track_register"))

        if role not in ("athlete", "coach"):
            role = "athlete"

        athlete_id = None
        if role == "athlete" and athlete_name:
            athlete = Athlete(name=athlete_name)
            db.session.add(athlete)
            db.session.flush()
            athlete_id = athlete.id

        track_user = TrackUser(username=username, role=role, athlete_id=athlete_id)
        track_user.set_password(password)
        db.session.add(track_user)
        db.session.commit()

        login_user(track_user)
        return redirect(url_for("time_entry.add_time_form"))

    return render_template("track_register.html")

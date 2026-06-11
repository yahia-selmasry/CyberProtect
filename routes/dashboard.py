from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db, AccountMembership, Business, Account

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    memberships = AccountMembership.query.filter_by(
        user_id=current_user.id, revoked_at=None
    ).all()
    return render_template("dashboard.html", memberships=memberships)


@dashboard_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    """Create a business and first account during initial setup."""
    if request.method == "POST":
        business_name = request.form.get("business_name", "").strip()
        account_name = request.form.get("account_name", "").strip()
        domain_url = request.form.get("domain_url", "").strip()
        scan_day = int(request.form.get("scan_schedule_day", 1))

        if not business_name or not domain_url:
            flash("Business name and domain URL are required.")
            return render_template("onboarding.html")

        if scan_day < 1 or scan_day > 28:
            scan_day = 1

        business = Business(name=business_name)
        db.session.add(business)
        db.session.flush()

        account = Account(
            business_id=business.id,
            name=account_name or business_name,
            domain_url=domain_url,
            scan_schedule_day=scan_day,
        )
        db.session.add(account)
        db.session.flush()

        membership = AccountMembership(
            account_id=account.id,
            user_id=current_user.id,
            role="owner",
        )
        db.session.add(membership)
        db.session.commit()

        flash(f"Account created! Your first scan is scheduled for day {scan_day} of each month.")
        return redirect(url_for("dashboard.index"))

    return render_template("onboarding.html")

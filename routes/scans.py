from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from database import db, Account, AccountMembership, Scan, Finding
from scanner import run_scan, calculate_security_score
from notifications import dispatch_scan_notifications

scans_bp = Blueprint("scans", __name__)


def _get_account_or_403(account_id):
    membership = AccountMembership.query.filter_by(
        account_id=account_id, user_id=current_user.id, revoked_at=None
    ).first_or_404()
    return membership.account


@scans_bp.route("/accounts/<account_id>/scans")
@login_required
def list_scans(account_id):
    account = _get_account_or_403(account_id)
    scans = Scan.query.filter_by(account_id=account_id).order_by(Scan.scheduled_at.desc()).all()
    return render_template("scans.html", account=account, scans=scans)


@scans_bp.route("/accounts/<account_id>/scans/trigger", methods=["POST"])
@login_required
def trigger_scan(account_id):
    account = _get_account_or_403(account_id)
    scan = Scan(
        account_id=account_id,
        scheduled_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        status="running",
        triggered_by="manual",
    )
    db.session.add(scan)
    db.session.commit()

    result = run_scan(account.domain_url)

    for f in result["findings"]:
        finding = Finding(
            scan_id=scan.id,
            first_seen_scan_id=scan.id,
            **f
        )
        db.session.add(finding)

    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    scan.security_score = result["security_score"]
    db.session.commit()

    members = [m.user for m in account.memberships if m.revoked_at is None]
    dispatch_scan_notifications(scan, members)

    flash("Scan complete.")
    return redirect(url_for("scans.list_scans", account_id=account_id))

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from database import db, User, AccountMembership

team_bp = Blueprint("team", __name__)


def _require_owner(account_id):
    return AccountMembership.query.filter_by(
        account_id=account_id, user_id=current_user.id, role="owner", revoked_at=None
    ).first_or_404()


@team_bp.route("/accounts/<account_id>/team")
@login_required
def manage_team(account_id):
    _require_owner(account_id)
    members = AccountMembership.query.filter_by(account_id=account_id, revoked_at=None).all()
    return render_template("team.html", members=members, account_id=account_id)


@team_bp.route("/accounts/<account_id>/team/invite", methods=["POST"])
@login_required
def invite_member(account_id):
    _require_owner(account_id)
    email = request.form["email"]
    invitee = User.query.filter_by(email=email).first()
    if not invitee:
        flash(f"No user found with email {email}.")
        return redirect(url_for("team.manage_team", account_id=account_id))
    existing = AccountMembership.query.filter_by(
        account_id=account_id, user_id=invitee.id, revoked_at=None
    ).first()
    if existing:
        flash("User is already a member.")
        return redirect(url_for("team.manage_team", account_id=account_id))
    membership = AccountMembership(account_id=account_id, user_id=invitee.id, role="member")
    db.session.add(membership)
    db.session.commit()
    flash(f"{email} added to the account.")
    return redirect(url_for("team.manage_team", account_id=account_id))


@team_bp.route("/accounts/<account_id>/team/<membership_id>/revoke", methods=["POST"])
@login_required
def revoke_member(account_id, membership_id):
    _require_owner(account_id)
    membership = AccountMembership.query.filter_by(
        id=membership_id, account_id=account_id
    ).first_or_404()
    if membership.role == "owner":
        flash("Cannot revoke the account owner.")
        return redirect(url_for("team.manage_team", account_id=account_id))
    membership.revoked_at = datetime.utcnow()
    db.session.commit()
    flash("Access revoked immediately.")
    return redirect(url_for("team.manage_team", account_id=account_id))

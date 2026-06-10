from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import AccountMembership, Scan, Finding

findings_bp = Blueprint("findings", __name__)


@findings_bp.route("/accounts/<account_id>/scans/<scan_id>/findings")
@login_required
def list_findings(account_id, scan_id):
    AccountMembership.query.filter_by(
        account_id=account_id, user_id=current_user.id, revoked_at=None
    ).first_or_404()
    scan = Scan.query.filter_by(id=scan_id, account_id=account_id).first_or_404()
    findings = Finding.query.filter_by(scan_id=scan_id).order_by(
        Finding.severity
    ).all()
    return render_template("findings.html", scan=scan, findings=findings)

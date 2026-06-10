from flask import Blueprint, render_template, make_response
from flask_login import login_required, current_user
from database import AccountMembership, Scan, Finding

export_bp = Blueprint("export", __name__)


@export_bp.route("/accounts/<account_id>/scans/<scan_id>/export.pdf")
@login_required
def export_pdf(account_id, scan_id):
    AccountMembership.query.filter_by(
        account_id=account_id, user_id=current_user.id, revoked_at=None
    ).first_or_404()
    scan = Scan.query.filter_by(id=scan_id, account_id=account_id).first_or_404()
    findings = Finding.query.filter_by(scan_id=scan_id).all()
    html = render_template("report_pdf.html", scan=scan, findings=findings)
    # TODO: pipe html through WeasyPrint once integrated
    response = make_response(html)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=scan-{scan_id}.pdf"
    return response

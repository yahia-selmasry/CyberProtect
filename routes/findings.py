from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import AccountMembership, Scan, Finding

findings_bp = Blueprint("findings", __name__)

SCAN_CATEGORIES = [
    ("SQL Injection",            lambda f: "injection" in f.title.lower() or "sql" in f.title.lower()),
    ("Cross-Site Scripting (XSS)", lambda f: "xss" in f.title.lower() or "cross-site scripting" in f.title.lower()),
    ("Security Misconfiguration", lambda f: "misconfiguration" in f.title.lower() or "exposed" in f.title.lower() or "header" in f.title.lower()),
    ("Broken Authentication",    lambda f: "authentication" in f.title.lower() or "cookie" in f.title.lower() or "https" in f.title.lower()),
    ("Sensitive Data Exposure",  lambda f: "sensitive" in f.title.lower() or "exposure" in f.title.lower() or "data" in f.title.lower()),
    ("Known CVEs",               lambda f: "cve" in f.title.lower()),
]


def _build_checklist(findings):
    """Return list of (category_name, passed, [matching_findings]) for the scan summary."""
    checklist = []
    for name, matcher in SCAN_CATEGORIES:
        matches = [f for f in findings if matcher(f)]
        checklist.append((name, len(matches) == 0, matches))
    return checklist


@findings_bp.route("/accounts/<account_id>/scans/<scan_id>/findings")
@login_required
def list_findings(account_id, scan_id):
    AccountMembership.query.filter_by(
        account_id=account_id, user_id=current_user.id, revoked_at=None
    ).first_or_404()
    scan = Scan.query.filter_by(id=scan_id, account_id=account_id).first_or_404()
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
    findings = sorted(
        Finding.query.filter_by(scan_id=scan_id).all(),
        key=lambda f: severity_order.get(f.severity, 99)
    )
    checklist = _build_checklist(findings)
    return render_template("findings.html", scan=scan, findings=findings, checklist=checklist)

"""Dispatch email, SMS, and in-app notifications after a scan completes."""
import os
from database import db, Notification


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email via SendGrid. Returns True on success."""
    # TODO: integrate SendGrid SDK
    return True


def send_sms(to_phone: str, message: str) -> bool:
    """Send SMS via Twilio. Returns True on success."""
    # TODO: integrate Twilio SDK
    return True


def dispatch_scan_notifications(scan, users: list):
    """Fire email + SMS + in_app for all users on the account simultaneously."""
    findings = scan.findings
    severity_counts = {}
    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    top_finding = next(
        (f for f in findings if f.severity == "critical"), None
    ) or next((f for f in findings if f.severity == "high"), None)

    subject = f"CyberProtect scan complete — {scan.account.domain_url}"
    body_lines = [
        f"Scan completed at {scan.completed_at}",
        f"Security score: {scan.security_score}/100",
        f"Findings: {severity_counts}",
    ]
    if top_finding:
        body_lines.append(f"Top finding: [{top_finding.severity.upper()}] {top_finding.title}")
    body = "\n".join(body_lines)

    channels_to_create = []
    for user in users:
        email_ok = send_email(user.email, subject, body)
        channels_to_create.append(Notification(
            scan_id=scan.id, user_id=user.id, channel="email",
            status="sent" if email_ok else "failed"
        ))

        if user.sms_notifications_enabled and user.phone_number:
            sms_ok = send_sms(user.phone_number, body)
            channels_to_create.append(Notification(
                scan_id=scan.id, user_id=user.id, channel="sms",
                status="sent" if sms_ok else "failed"
            ))

        channels_to_create.append(Notification(
            scan_id=scan.id, user_id=user.id, channel="in_app", status="sent"
        ))

    db.session.bulk_save_objects(channels_to_create)
    db.session.commit()

# CyberProtect — Claude Code Context

## What this project is
A Flask web app that automatically scans web applications for security vulnerabilities on a monthly schedule. SMB owners register a domain, scans run automatically, findings are delivered via email/SMS/in-app alerts, and reports map to SOC 2 controls. See @SPEC.md for full spec.

## Tech stack
- Python 3.11 + Flask
- SQLite (local dev) / PostgreSQL (production via DATABASE_URL)
- SQLAlchemy ORM for all DB access
- flask-login for session management
- werkzeug for password hashing
- Celery + Redis for background scan jobs and async notifications
- Twilio SDK for SMS alerts
- SendGrid for email alerts
- WeasyPrint for PDF export
- Deployed on Render.com

## Key files
- app.py — all Flask routes
- database.py — SQLAlchemy models and DB helpers
- scanner.py — AI scan engine logic
- notifications.py — email, SMS, and in-app notification dispatch
- docs/data-model.md — full DB schema reference
- docs/api-routes.md — all routes listed
- PROGRESS.md — current status and what's done

## Data model (quick ref — see docs/data-model.md for full schema)
- businesses → accounts → account_memberships (owner/member) → users
- scans belong to accounts; findings belong to scans
- notifications log every email/SMS/in-app delivery per user per scan

## Critical rules
- Never store plain-text passwords — use werkzeug generate_password_hash
- Credentials stored in accounts.credentials_encrypted must use AES-256 encryption
- Access revocation is immediate — set revoked_at AND invalidate active sessions
- One owner per account. Owner cannot be demoted or transferred in V1
- Security score is 0–100; only set on completed scans (nullable until then)
- soc2_controls is a JSON array field (e.g., ["CC6.1", "CC7.2"])
- SQLite for local dev. PostgreSQL for production via DATABASE_URL env var
- Run tests after every change: `python -m pytest tests/ -v`
- After any DB schema change, update docs/data-model.md

## Coding style
- Functions have one-line docstrings
- Flask routes are grouped by feature (auth, dashboard, scans, findings, team, export)
- API routes return JSON with {"error": "message"} on failure
- HTML errors: flash() then redirect — never raw error pages
- Role checks: verify account_membership role before any sensitive operation

## Do not
- Add new packages without updating requirements.txt
- Modify the DB schema without updating docs/data-model.md
- Write more than 50 lines per function — split it
- Implement penetration testing, network/IP scanning, or auto-fix features (out of scope V1)
- Allow members to access billing, team management, or account settings routes

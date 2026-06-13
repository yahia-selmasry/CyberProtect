import os
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from utils import seconds_to_display, display_to_seconds  # noqa: F401 — re-exported

db = SQLAlchemy()


def _fernet():
    key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("CREDENTIALS_ENCRYPTION_KEY env var not set")
    return Fernet(key.encode())


def encrypt_credentials(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_credentials(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


class Business(db.Model):
    __tablename__ = "businesses"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_status = db.Column(db.Enum("active", "trialing", "cancelled", "past_due", name="sub_status"), default="trialing")
    subscription_plan = db.Column(db.String(50), default="v1_standard")

    stripe_customer_id = db.Column(db.String(255), nullable=True)

    accounts = db.relationship("Account", back_populates="business", lazy=True)


class Account(db.Model):
    __tablename__ = "accounts"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = db.Column(db.String(36), db.ForeignKey("businesses.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    domain_url = db.Column(db.String(2048), nullable=False)
    scan_schedule_day = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    credentials_stored = db.Column(db.Boolean, default=False)
    credentials_encrypted = db.Column(db.Text, nullable=True)

    business = db.relationship("Business", back_populates="accounts")
    memberships = db.relationship("AccountMembership", back_populates="account", lazy=True)
    scans = db.relationship("Scan", back_populates="account", lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sms_notifications_enabled = db.Column(db.Boolean, default=True)

    memberships = db.relationship("AccountMembership", back_populates="user", lazy=True)
    notifications = db.relationship("Notification", back_populates="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class AccountMembership(db.Model):
    __tablename__ = "account_memberships"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.Enum("owner", "member", name="membership_role"), nullable=False)
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    account = db.relationship("Account", back_populates="memberships")
    user = db.relationship("User", back_populates="memberships")

    @property
    def is_active(self):
        return self.revoked_at is None


class Scan(db.Model):
    __tablename__ = "scans"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum("scheduled", "running", "completed", "failed", name="scan_status"), default="scheduled")
    security_score = db.Column(db.Integer, nullable=True)
    triggered_by = db.Column(db.Enum("scheduled", "manual", name="scan_trigger"), default="scheduled")

    account = db.relationship("Account", back_populates="scans")
    findings = db.relationship("Finding", back_populates="scan", lazy=True, foreign_keys="Finding.scan_id")
    notifications = db.relationship("Notification", back_populates="scan", lazy=True)


class Finding(db.Model):
    __tablename__ = "findings"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = db.Column(db.String(36), db.ForeignKey("scans.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.Enum("critical", "high", "medium", "low", "informational", name="finding_severity"), nullable=False)
    affected_url = db.Column(db.String(2048), nullable=False)
    remediation_steps = db.Column(db.Text, nullable=False)
    soc2_controls = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.Enum("open", "acknowledged", "resolved", name="finding_status"), default="open")
    first_seen_scan_id = db.Column(db.String(36), db.ForeignKey("scans.id"), nullable=False)
    resolved_scan_id = db.Column(db.String(36), db.ForeignKey("scans.id"), nullable=True)

    scan = db.relationship("Scan", back_populates="findings", foreign_keys=[scan_id])


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = db.Column(db.String(36), db.ForeignKey("scans.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel = db.Column(db.Enum("email", "sms", "in_app", name="notif_channel"), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum("sent", "failed", "delivered", name="notif_status"), default="sent")

    scan = db.relationship("Scan", back_populates="notifications")
    user = db.relationship("User", back_populates="notifications")


# ---------------------------------------------------------------------------
# CyberProtect tables
# ---------------------------------------------------------------------------

class Athlete(db.Model):
    """Athlete profile record."""
    __tablename__ = "athletes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    specialty = db.Column(db.Text, nullable=True)
    athletic_net_id = db.Column(db.Text, nullable=True)

    results = db.relationship("Result", back_populates="athlete", lazy=True)
    track_user = db.relationship("TrackUser", back_populates="athlete", uselist=False)


class Result(db.Model):
    """Individual performance result for an athlete."""
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    meet_name = db.Column(db.String(255), nullable=True)
    meet_date = db.Column(db.Date, nullable=True)
    event = db.Column(db.String(100), nullable=False)
    time_seconds = db.Column(db.Float, nullable=False)
    session_type = db.Column(db.Enum("meet", "practice", name="session_type"), nullable=False, default="meet")
    split_400 = db.Column(db.Float, nullable=True)
    split_800 = db.Column(db.Float, nullable=True)
    split_1200 = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_personal_best = db.Column(db.Boolean, nullable=False, default=False)

    athlete = db.relationship("Athlete", back_populates="results")


class TrackUser(UserMixin, db.Model):
    """App user for the track system (athlete or coach)."""
    __tablename__ = "track_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("athlete", "coach", name="track_user_role"), nullable=False, default="athlete")
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=True)

    athlete = db.relationship("Athlete", back_populates="track_user")

    def get_id(self) -> str:
        """Return prefixed ID so user loader can distinguish TrackUser from User."""
        return f"t:{self.id}"

    def set_password(self, password: str):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)


# ---------------------------------------------------------------------------
# CyberProtect helper functions
# ---------------------------------------------------------------------------

def update_personal_bests(athlete_id: int, event: str):
    """Recalculate and flag the personal best result for an athlete/event pair."""
    results = (
        Result.query
        .filter_by(athlete_id=athlete_id, event=event)
        .order_by(Result.time_seconds.asc())
        .all()
    )
    best_id = results[0].id if results else None
    for r in results:
        r.is_personal_best = r.id == best_id
    db.session.commit()

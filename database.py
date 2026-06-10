import os
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

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
    findings = db.relationship("Finding", back_populates="scan", lazy=True)
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

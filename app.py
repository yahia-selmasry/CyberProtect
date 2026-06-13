import os
from flask import Flask
from flask_login import LoginManager
from database import db, User, TrackUser

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-key")

db_url = os.environ.get("DATABASE_URL", "sqlite:///cyberprotect.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("t:"):
        return TrackUser.query.get(int(user_id[2:]))
    return User.query.get(int(user_id))

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.scans import scans_bp
from routes.findings import findings_bp
from routes.team import team_bp
from routes.export import export_bp
from routes.time_entry import time_entry_bp
from routes.import_csv import import_bp
from routes.billing import billing_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(scans_bp)
app.register_blueprint(findings_bp)
app.register_blueprint(team_bp)
app.register_blueprint(export_bp)
app.register_blueprint(time_entry_bp)
app.register_blueprint(import_bp)
app.register_blueprint(billing_bp)

with app.app_context():
    db.create_all()
    # Add columns introduced after initial deploy; safe to re-run (errors mean column exists)
    _new_cols = [
        "ALTER TABLE businesses ADD COLUMN subscription_status VARCHAR(20) DEFAULT 'trialing'",
        "ALTER TABLE businesses ADD COLUMN subscription_plan VARCHAR(50) DEFAULT 'v1_standard'",
        "ALTER TABLE businesses ADD COLUMN stripe_customer_id VARCHAR(255)",
    ]
    with db.engine.connect() as _conn:
        for _sql in _new_cols:
            try:
                _conn.execute(db.text(_sql))
                _conn.commit()
            except Exception:
                _conn.rollback()

if __name__ == "__main__":
    app.run(debug=True)

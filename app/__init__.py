import datetime
from flask import Flask

from app import config as _cfg

app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static',
)
app.secret_key = _cfg.SECRET_KEY
app.permanent_session_lifetime = _cfg.SESSION_LIFETIME
app.config.update(
    SMTP_HOST=_cfg.SMTP_HOST,
    SMTP_PORT=_cfg.SMTP_PORT,
    SMTP_USER=_cfg.SMTP_USER,
    SMTP_PASSWORD=_cfg.SMTP_PASSWORD,
    SMTP_FROM=_cfg.SMTP_FROM,
    SMTP_USE_TLS=_cfg.SMTP_USE_TLS,
)

# Register DB teardown
from app.db import close_db
app.teardown_appcontext(close_db)

# Register context processor
from app.auth import register_context_processor
register_context_processor(app)

# Register all route modules (import-time side-effect: @app.route decorators fire)
from app.routes import auth, dashboard, employees, admin, org, company, vacation  # noqa: F401
from app.routes import notifications, search, calendar, imports, analytics, benchmarks, skills_intelligence  # noqa: F401

# Register page-view tracker (after_request hook)
from app.services import page_tracker as _pt
_pt.register(app)

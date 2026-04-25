import datetime
from flask import Flask

from app.config import SECRET_KEY, SESSION_LIFETIME

app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static',
)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = SESSION_LIFETIME

# Register DB teardown
from app.db import close_db
app.teardown_appcontext(close_db)

# Register context processor
from app.auth import register_context_processor
register_context_processor(app)

# Register all route modules (import-time side-effect: @app.route decorators fire)
from app.routes import auth, dashboard, employees, admin, org, company, vacation  # noqa: F401

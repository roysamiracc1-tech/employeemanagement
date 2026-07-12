import os
import datetime

# Deployment environment: 'development' (default) | 'production'.
APP_ENV       = os.getenv('APP_ENV', 'development').lower()
IS_PRODUCTION = APP_ENV == 'production'

# Secret key. In production a real SECRET_KEY MUST be supplied — fail fast rather
# than silently signing sessions with a public dev key. Dev/test fall back so the
# app (and the test suite) run without extra setup.
_secret_env = os.getenv('SECRET_KEY')
if IS_PRODUCTION and not _secret_env:
    raise RuntimeError(
        'SECRET_KEY environment variable is required when APP_ENV=production.'
    )
SECRET_KEY = _secret_env or 'hr-portal-dev-secret-2024'

SESSION_LIFETIME = datetime.timedelta(hours=8)

# Session cookie hardening. Secure is on only in production (dev/test use plain
# HTTP); HttpOnly + SameSite=Lax always. Debug follows the environment unless
# explicitly overridden via FLASK_DEBUG.
SESSION_COOKIE_SECURE   = IS_PRODUCTION
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
DEBUG = os.getenv('FLASK_DEBUG', '0' if IS_PRODUCTION else '1') == '1'

# Cap request/upload body size (8 MB) to bound memory/disk from oversized uploads.
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 8 * 1024 * 1024))

# ── Email / SMTP ──────────────────────────────────────────────────────────────
SMTP_HOST     = os.getenv('SMTP_HOST', '')          # empty = log-only dev mode
SMTP_PORT     = int(os.getenv('SMTP_PORT', 587))
SMTP_USER     = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM     = os.getenv('SMTP_FROM', 'noreply@hrportal.local')
SMTP_USE_TLS  = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

DB_CONFIG = {
    'host':     os.getenv('PGHOST',     'localhost'),
    'port':     int(os.getenv('PGPORT', 5432)),
    'dbname':   os.getenv('PGDATABASE', 'employee'),
    'user':     os.getenv('PGUSER',     'samirroy'),
    'password': os.getenv('PGPASSWORD') or None,
}

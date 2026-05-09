import os
import datetime

SECRET_KEY = os.getenv('SECRET_KEY', 'hr-portal-dev-secret-2024')
SESSION_LIFETIME = datetime.timedelta(hours=8)

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

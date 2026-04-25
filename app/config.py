import os
import datetime

SECRET_KEY = os.getenv('SECRET_KEY', 'hr-portal-dev-secret-2024')
SESSION_LIFETIME = datetime.timedelta(hours=8)

DB_CONFIG = {
    'host':     os.getenv('PGHOST',     'localhost'),
    'port':     int(os.getenv('PGPORT', 5432)),
    'dbname':   os.getenv('PGDATABASE', 'employee'),
    'user':     os.getenv('PGUSER',     'samirroy'),
    'password': os.getenv('PGPASSWORD') or None,
}

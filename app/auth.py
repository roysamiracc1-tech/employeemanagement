import datetime
from functools import wraps

from flask import session, redirect, url_for, flash, request


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def require_roles(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if not any(r in session.get('roles', []) for r in roles):
                flash('You do not have access to that page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def register_context_processor(app):
    @app.context_processor
    def inject_ctx():
        def has_role(*roles):
            return any(r in session.get('roles', []) for r in roles)
        branding   = session.get('branding') or {}
        theme_pref = session.get('theme_pref', 'light')
        return dict(
            has_role=has_role,
            session=session,
            request=request,
            now=datetime.datetime.now,
            branding=branding,
            theme_pref=theme_pref,
        )

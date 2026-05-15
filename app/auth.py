import datetime
import uuid as _uuid_mod
from functools import wraps

from flask import g, session, redirect, url_for, flash, request


def _is_valid_uuid(val):
    try:
        _uuid_mod.UUID(str(val))
        return True
    except (ValueError, AttributeError):
        return False


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


def _load_feature_access():
    """Return per-request cached map of {feature_code: {r, w, d}} for the current user.

    Access = global role_feature_access AND company_role_feature_access override (if set).
    No company override row means the global setting stands.
    """
    if hasattr(g, '_feature_access'):
        return g._feature_access
    roles = list(session.get('roles', []))
    if not roles:
        g._feature_access = {}
        return g._feature_access
    from app.db import query
    if 'SYSTEM_ADMIN' in roles:
        rows = query("SELECT code FROM portal_features")
        g._feature_access = {r['code']: {'r': True, 'w': True, 'd': True} for r in rows}
    else:
        company_id = session.get('company_id')
        if _is_valid_uuid(company_id):
            rows = query("""
                SELECT pf.code,
                       bool_or(
                           rfa.can_read  AND COALESCE(crfa.is_enabled, TRUE)
                       ) AS r,
                       bool_or(
                           rfa.can_write AND COALESCE(crfa.is_enabled, TRUE)
                       ) AS w,
                       bool_or(
                           rfa.can_delete AND COALESCE(crfa.is_enabled, TRUE)
                       ) AS d
                FROM role_feature_access rfa
                JOIN roles ro ON ro.id = rfa.role_id
                JOIN portal_features pf ON pf.id = rfa.feature_id
                LEFT JOIN company_role_feature_access crfa
                       ON crfa.role_id    = rfa.role_id
                      AND crfa.feature_id = rfa.feature_id
                      AND crfa.company_id = %s::uuid
                WHERE ro.name = ANY(%s)
                  AND (ro.company_id = %s::uuid OR ro.company_id IS NULL)
                GROUP BY pf.code
            """, (company_id, roles, company_id))
        else:
            rows = query("""
                SELECT pf.code,
                       bool_or(rfa.can_read)   AS r,
                       bool_or(rfa.can_write)  AS w,
                       bool_or(rfa.can_delete) AS d
                FROM role_feature_access rfa
                JOIN roles ro ON ro.id = rfa.role_id
                JOIN portal_features pf ON pf.id = rfa.feature_id
                WHERE ro.name = ANY(%s)
                GROUP BY pf.code
            """, (roles,))
        g._feature_access = {
            r['code']: {'r': bool(r['r']), 'w': bool(r['w']), 'd': bool(r['d'])}
            for r in rows
        }
    return g._feature_access


def can_access_feature(feature_code, action='r'):
    return _load_feature_access().get(feature_code, {}).get(action, False)


def require_feature_access(feature_code, action='r'):
    """Decorator: allow access if the user's roles grant the given feature permission."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if not can_access_feature(feature_code, action):
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

        def has_feature_access(feature_code, action='r'):
            return can_access_feature(feature_code, action)

        branding        = session.get('branding') or {}
        theme_pref      = session.get('theme_pref', 'light')
        is_tech_admin   = 'SYSTEM_ADMIN' in session.get('roles', [])
        is_portal_admin = 'PORTAL_ADMIN' in session.get('roles', [])
        return dict(
            has_role=has_role,
            has_feature_access=has_feature_access,
            session=session,
            request=request,
            now=datetime.datetime.now,
            branding=branding,
            theme_pref=theme_pref,
            is_tech_admin=is_tech_admin,
            is_portal_admin=is_portal_admin,
        )

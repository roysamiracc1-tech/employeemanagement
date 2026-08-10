import datetime
import uuid as _uuid_mod
from functools import wraps

from flask import (g, session, redirect, url_for, flash, request,
                   render_template, jsonify)


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


# ── The tenant switch (KAN-188 · R7) ──────────────────────────────────────────
#
#     effective access = TENANT SWITCH  AND  ROLE GRANT
#
# `company_features.is_enabled` says whether a company has the feature at all;
# `role_feature_access` (with the per-company override) says whether this role
# may use it. Both must be true. They answer different questions and neither
# substitutes for the other: turning a feature off for a tenant must not require
# editing ten role grants, and granting a role access must not silently license
# a feature the tenant has not bought.
#
# ONE JOIN, ON THE QUERY THAT ALREADY RUNS. This is the whole implementation, and
# it belongs here rather than in ten routes because there is exactly one place
# effective access is decided (CLAUDE.md). The two hand-rolled per-feature checks
# this replaces — `_analytics_enabled` and `_si_enabled` — were the same idea
# implemented twice, badly: neither consulted role access, both returned a bare
# 403, and no other feature got the behaviour at all.
#
# COALESCE on `default_enabled`, not on TRUE: after migration 11 every existing
# pair is materialised, so a missing row means a company or feature created
# SINCE. The right answer for those is the product's stated default, and that
# default is data (`portal_features.default_enabled`) rather than a constant
# buried here, so onboarding policy is administrable instead of a code change.
_TENANT_SWITCH_JOIN = """
        LEFT JOIN company_features cf
               ON cf.feature_id = pf.id
              AND cf.company_id = %s::uuid
"""


def _load_feature_access():
    """Return per-request cached map of {feature_code: {r, w, d}} for the current user.

    Access = tenant switch (`company_features.is_enabled`, KAN-188) AND global
    `role_feature_access` AND the `company_role_feature_access` override if set.
    No company override row means the global setting stands; no `company_features`
    row means `portal_features.default_enabled` stands.
    """
    if hasattr(g, '_feature_access'):
        return g._feature_access
    roles = list(session.get('roles', []))
    if not roles:
        g._feature_access = {}
        return g._feature_access
    from app.db import query
    if 'SYSTEM_ADMIN' in roles:
        # SYSTEM_ADMIN bypasses BOTH terms — the role grant and the tenant
        # switch. They administer the switch, so being locked out by it would
        # make a mis-toggle unrecoverable through the UI. Signposted to the user
        # rather than silent: see `tenant_feature_state()` below, which the
        # off-state screen uses to say "this is off for this company, and you can
        # see it because you are a system administrator".
        rows = query("SELECT code FROM portal_features")
        g._feature_access = {r['code']: {'r': True, 'w': True, 'd': True} for r in rows}
    else:
        company_id = session.get('company_id')
        if _is_valid_uuid(company_id):
            rows = query("""
                SELECT pf.code,
                       bool_or(
                           COALESCE(cf.is_enabled, pf.default_enabled)
                           AND rfa.can_read   AND COALESCE(crfa.can_read,   rfa.can_read)
                       ) AS r,
                       bool_or(
                           COALESCE(cf.is_enabled, pf.default_enabled)
                           AND rfa.can_write  AND COALESCE(crfa.can_write,  rfa.can_write)
                       ) AS w,
                       bool_or(
                           COALESCE(cf.is_enabled, pf.default_enabled)
                           AND rfa.can_delete AND COALESCE(crfa.can_delete, rfa.can_delete)
                       ) AS d
                FROM role_feature_access rfa
                JOIN roles ro ON ro.id = rfa.role_id
                JOIN portal_features pf ON pf.id = rfa.feature_id
                LEFT JOIN company_role_feature_access crfa
                       ON crfa.role_id    = rfa.role_id
                      AND crfa.feature_id = rfa.feature_id
                      AND crfa.company_id = %s::uuid
            """ + _TENANT_SWITCH_JOIN + """
                WHERE ro.name = ANY(%s)
                  AND (ro.company_id = %s::uuid OR ro.company_id IS NULL)
                GROUP BY pf.code
            """, (company_id, company_id, roles, company_id))
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


def feature_access_for(user_id, company_id):
    """Effective access for a user who is NOT the one making the request.

    Same two terms, same precedence, same SQL shape as `_load_feature_access()` —
    but resolved from a `user_id` instead of the session, and NOT cached in `g`
    (the answer is about somebody else, so caching it under a request-global key
    would hand the next caller the wrong person's access).

    Exists because KAN-196 has to ask *"does this approver hold `compensation:r`?"*
    about a chain of other people before it will let a money-bearing request be
    created (CFL-42-12). Answering that by reading `role_feature_access` directly
    would be a second implementation of effective access that silently ignores the
    tenant switch — which is the exact class of bug KAN-188 exists to delete.

    Returns {feature_code: {'r','w','d'}}. An inactive or unknown user gets {}.
    """
    from app.db import query
    if not user_id:
        return {}
    row = query("SELECT id::text FROM users WHERE id=%s::uuid AND is_active",
                (user_id,), one=True)
    if not row:
        return {}

    # SYSTEM_ADMIN bypasses both terms, exactly as in the session path. Resolved
    # from the database rather than a session, because there is no session here.
    is_sa = query("""
        SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = %s::uuid AND r.name = 'SYSTEM_ADMIN' LIMIT 1
    """, (user_id,), one=True)
    if is_sa:
        return {r['code']: {'r': True, 'w': True, 'd': True}
                for r in query("SELECT code FROM portal_features")}

    if not _is_valid_uuid(company_id):
        return {}
    rows = query("""
        SELECT pf.code,
               bool_or(
                   COALESCE(cf.is_enabled, pf.default_enabled)
                   AND rfa.can_read   AND COALESCE(crfa.can_read,   rfa.can_read)
               ) AS r,
               bool_or(
                   COALESCE(cf.is_enabled, pf.default_enabled)
                   AND rfa.can_write  AND COALESCE(crfa.can_write,  rfa.can_write)
               ) AS w,
               bool_or(
                   COALESCE(cf.is_enabled, pf.default_enabled)
                   AND rfa.can_delete AND COALESCE(crfa.can_delete, rfa.can_delete)
               ) AS d
        FROM user_roles ur
        JOIN roles ro ON ro.id = ur.role_id
        JOIN role_feature_access rfa ON rfa.role_id = ro.id
        JOIN portal_features pf ON pf.id = rfa.feature_id
        LEFT JOIN company_role_feature_access crfa
               ON crfa.role_id    = rfa.role_id
              AND crfa.feature_id = rfa.feature_id
              AND crfa.company_id = %s::uuid
    """ + _TENANT_SWITCH_JOIN + """
        WHERE ur.user_id = %s::uuid
          AND (ro.company_id = %s::uuid OR ro.company_id IS NULL)
        GROUP BY pf.code
    """, (company_id, company_id, user_id, company_id))
    return {r['code']: {'r': bool(r['r']), 'w': bool(r['w']), 'd': bool(r['d'])}
            for r in rows}


def tenant_feature_state(feature_code, company_id=None):
    """Is *feature_code* switched on for this tenant, independently of role?

    Lets a surface tell the two "no" answers apart, which matters because they
    need opposite responses: **"your company does not have this"** is a sales or
    admin conversation and is answered by an explanatory screen, while **"your
    role may not use it"** is a permissions conversation. Collapsing both into a
    403 — which is what the code being deleted here did — tells the user nothing
    and sends them to the wrong person.

    Also what lets the off-state screen signpost the SYSTEM_ADMIN bypass: they
    can see a page whose tenant switch is OFF, and should be told so rather than
    left to conclude the feature works for everyone.

    Returns True/False, or None if the feature code is unknown.
    """
    from app.db import query
    company_id = company_id or session.get('company_id')
    if not _is_valid_uuid(company_id):
        return None
    row = query("""
        SELECT COALESCE(cf.is_enabled, pf.default_enabled) AS on
        FROM portal_features pf
        LEFT JOIN company_features cf
               ON cf.feature_id = pf.id AND cf.company_id = %s::uuid
        WHERE pf.code = %s
    """, (company_id, feature_code), one=True)
    return None if row is None else bool(row['on'])


def require_feature_access(feature_code, action='r'):
    """Decorator: allow access if the user's roles grant the given feature permission.

    A refusal caused by the TENANT SWITCH renders the explanatory off-state screen
    (KAN-188) rather than the generic "you do not have access" flash. The two are
    different answers to the user: one means the company does not have the
    feature, the other means their role may not use it. A silent redirect to the
    dashboard for the first is how you generate a support ticket.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if not can_access_feature(feature_code, action):
                # The off-state screen is shown ONLY to somebody the switch is
                # actually costing — i.e. whose role WOULD grant this if the
                # company had it. Two reasons, and the second is the important
                # one:
                #   • it is only true for them. To a user with no role grant,
                #     "your company hasn't switched this on" is misleading: it
                #     would still be refused if the company had;
                #   • it would otherwise leak the tenant's licensing to anyone
                #     who pokes a URL. A plain employee learning which features
                #     their employer has not bought is an information leak, and
                #     a support call to an administrator who cannot help them.
                if (tenant_feature_state(feature_code) is False
                        and _role_grants(feature_code, action)):
                    return _tenant_off_response(feature_code)
                flash('You do not have access to that page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def _tenant_off_response(feature_code):
    """The refusal when the TENANT SWITCH is off, shaped for who is asking.

    A page and an API need opposite things and the story asks for both:

    • **A page gets a 200 and a real explanatory screen.** Not a 403, not a
      bounce to the dashboard — those are the two behaviours KAN-188 exists to
      replace. Nothing is broken and the user has done nothing wrong; the
      company does not have the feature, and the screen says so and names who
      can change it. A 403 on an HTML route also tells monitoring and crawlers
      that something is failing when nothing is.

    • **An API gets a 403 and JSON.** A caller expecting JSON cannot render a
      screen, and returning 200 with an HTML body would be a lie about the
      outcome that breaks the client in a much more confusing way.

    Decided on the REQUEST, not on a flag per route, so no route has to remember.
    """
    wants_json = (request.path.startswith('/api/')
                  or request.accept_mimetypes.best == 'application/json')
    if wants_json:
        return jsonify({
            'error': f'{_feature_label(feature_code)} is not switched on for '
                     f'your company. Your portal administrator can enable it '
                     f'under Company Settings → Feature Access.',
            'reason': 'tenant_feature_disabled',
            'feature_code': feature_code,
        }), 403
    return render_template('feature_unavailable.html',
                           feature_code=feature_code,
                           feature=_feature_label(feature_code)), 200


def _role_grants(feature_code, action='r'):
    """Would this user's ROLES allow *feature_code*, ignoring the tenant switch?

    The other half of `effective = tenant switch AND role grant`, asked on its
    own so a refusal can name which half caused it. Runs only on the denial
    path, which is rare, so the extra query costs nothing on a normal request.
    """
    from app.db import query
    roles = list(session.get('roles', []))
    if not roles:
        return False
    if 'SYSTEM_ADMIN' in roles:
        return True
    col = {'r': 'can_read', 'w': 'can_write', 'd': 'can_delete'}.get(action, 'can_read')
    company_id = session.get('company_id')
    if not _is_valid_uuid(company_id):
        row = query(f"""
            SELECT bool_or(rfa.{col}) AS ok
            FROM role_feature_access rfa
            JOIN roles ro ON ro.id = rfa.role_id
            JOIN portal_features pf ON pf.id = rfa.feature_id
            WHERE ro.name = ANY(%s) AND pf.code = %s
        """, (roles, feature_code), one=True)
    else:
        row = query(f"""
            SELECT bool_or(rfa.{col} AND COALESCE(crfa.{col}, rfa.{col})) AS ok
            FROM role_feature_access rfa
            JOIN roles ro ON ro.id = rfa.role_id
            JOIN portal_features pf ON pf.id = rfa.feature_id
            LEFT JOIN company_role_feature_access crfa
                   ON crfa.role_id = rfa.role_id
                  AND crfa.feature_id = rfa.feature_id
                  AND crfa.company_id = %s::uuid
            WHERE ro.name = ANY(%s)
              AND (ro.company_id = %s::uuid OR ro.company_id IS NULL)
              AND pf.code = %s
        """, (company_id, roles, company_id, feature_code), one=True)
    return bool(row and row['ok'])


def _feature_label(feature_code):
    """Human label for a feature code, for the off-state screen."""
    from app.db import query
    row = query("SELECT label FROM portal_features WHERE code=%s",
                (feature_code,), one=True)
    return (row['label'] if row else None) or feature_code.replace('_', ' ').title()


def _company_has_vacation_types():
    """Return True if the user's company has at least one active vacation type.
    SYSTEM_ADMIN always returns True (they manage types for all companies).
    Result cached in g for the duration of the request."""
    if hasattr(g, '_has_vac_types'):
        return g._has_vac_types
    if 'user_id' not in session:
        g._has_vac_types = False
        return False
    if 'SYSTEM_ADMIN' in session.get('roles', []):
        g._has_vac_types = True
        return True
    co_id = session.get('company_id')
    if not _is_valid_uuid(co_id):
        g._has_vac_types = False
        return False
    from app.db import query as _query
    row = _query(
        "SELECT 1 FROM vacation_types WHERE company_id = %s::uuid AND is_active LIMIT 1",
        (co_id,), one=True,
    )
    g._has_vac_types = row is not None
    return g._has_vac_types


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
        # Imported here, not at module scope: app.helpers imports from app.db and
        # this module is imported during app construction.
        from app.helpers import fmt_period, fmt_last_day
        return dict(
            has_role=has_role,
            has_feature_access=has_feature_access,
            session=session,
            request=request,
            now=datetime.datetime.now,
            # KAN-189 / ADR-020 — the ONLY sanctioned way to render an
            # effective-dated period. `effective_to` is exclusive, so printing it
            # raw is always off by one day.
            fmt_period=fmt_period,
            fmt_last_day=fmt_last_day,
            branding=branding,
            theme_pref=theme_pref,
            is_tech_admin=is_tech_admin,
            is_portal_admin=is_portal_admin,
            company_has_vacation_types=_company_has_vacation_types,
        )

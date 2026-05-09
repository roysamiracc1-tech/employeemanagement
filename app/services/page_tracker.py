"""Non-blocking page-view logger.

Registers an after_request hook that writes one row to page_views in a
background thread so it never adds latency to the response.
"""
import threading
import logging

from flask import request, session

log = logging.getLogger(__name__)

# Human-readable labels for known routes
_PAGE_LABELS: dict[str, str] = {
    '/':                      'Dashboard',
    '/dashboard':             'Dashboard',
    '/vacation':              'My Vacation',
    '/vacation/calendar':     'Vacation Calendar',
    '/vacation/team':         'Team Vacation',
    '/org-tree':              'Org Chart',
    '/directory':             'Employee Directory',
    '/search':                'Search',
    '/profile':               'My Profile',
    '/my-team':               'My Team',
    '/my-company':            'My Company',
    '/admin':                 'Admin Panel',
    '/admin/vacation-types':  'Vacation Types (Admin)',
    '/admin/companies':       'Companies (Admin)',
    '/admin/company-settings':'Company Settings',
    '/admin/imports':         'Bulk Import',
    '/admin/analytics':       'Analytics',
}

# Route prefixes that are never worth logging
_SKIP_PREFIXES = ('/api/', '/static/', '/login', '/logout')


def _should_log(path: str, status: int) -> bool:
    if status >= 400:
        return False
    if any(path.startswith(p) for p in _SKIP_PREFIXES):
        return False
    return True


def _insert(app_ctx, user_id, employee_id, company_id, role, route, label):
    with app_ctx.app_context():
        try:
            from app.db import execute
            execute(
                "INSERT INTO page_views "
                "(user_id, employee_id, company_id, role, route, page_label) "
                "VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s)",
                (user_id, employee_id, company_id, role, route, label),
            )
        except Exception as exc:
            log.debug('page_view insert failed: %s', exc)


def register(app):
    @app.after_request
    def _track(response):
        path = request.path
        if not _should_log(path, response.status_code):
            return response

        user_id     = session.get('user_id')
        if not user_id:           # not authenticated
            return response

        employee_id = session.get('employee_id')
        company_id  = session.get('company_id') or session.get('admin_company_id')
        roles       = session.get('roles', [])
        role        = roles[0] if roles else None
        # Normalise profile/<id> → /profile for cleaner grouping
        route = path
        for prefix in ('/profile/', '/admin/vacation-types/', '/admin/companies/'):
            if path.startswith(prefix):
                route = prefix.rstrip('/') or prefix
        label = _PAGE_LABELS.get(route, route)

        from flask import current_app
        app_ctx = current_app._get_current_object()
        threading.Thread(
            target=_insert,
            args=(app_ctx, user_id, employee_id, company_id, role, route, label),
            daemon=True,
        ).start()
        return response

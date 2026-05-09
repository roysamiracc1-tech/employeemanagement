"""Single source of truth for resolving the active company_id from session.

All four previous _company_scope / _dash_company_scope / _vac_company_scope /
_viewer_company duplicates are replaced by this module.
"""
from flask import session


# Role hierarchy used for notification config inheritance
ROLE_HIERARCHY = {
    'PORTAL_ADMIN':         ['HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
                              'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER',
                              'HIRING_MANAGER', 'EMPLOYEE'],
    'HR_ADMIN':             ['EMPLOYEE'],
    'DEPARTMENT_HEAD':      ['LOCATION_HEAD', 'SOLID_LINE_MANAGER',
                              'DOTTED_LINE_MANAGER', 'EMPLOYEE'],
    'LOCATION_HEAD':        ['EMPLOYEE'],
    'SOLID_LINE_MANAGER':   ['DOTTED_LINE_MANAGER', 'EMPLOYEE'],
    'DOTTED_LINE_MANAGER':  ['EMPLOYEE'],
    'HIRING_MANAGER':       ['EMPLOYEE'],
    'EMPLOYEE':             [],
}


def current_company_id():
    """Return the active company_id for the current request.

    - SYSTEM_ADMIN: returns ``session['admin_company_id']`` (may be None = all companies)
    - Everyone else: returns ``session['company_id']`` (their own company)
    """
    roles = session.get('roles', [])
    if 'SYSTEM_ADMIN' in roles:
        return session.get('admin_company_id') or None
    return session.get('company_id') or None


def viewer_company_id():
    """Like current_company_id() but always returns the user's own company.

    Used in data-isolation checks (org tree, employee directory) where a
    Tech Admin's selected context is irrelevant — only their own affiliation
    matters for boundary enforcement.
    """
    if 'SYSTEM_ADMIN' in session.get('roles', []):
        return None   # Tech Admin has no company boundary
    return session.get('company_id') or None


def sub_roles(role: str):
    """Return all roles that inherit from *role* (direct + transitive)."""
    seen, queue = set(), [role]
    while queue:
        r = queue.pop()
        for child in ROLE_HIERARCHY.get(r, []):
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return list(seen)

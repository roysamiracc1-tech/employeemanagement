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


def resolve_report_scope(emp_id: str, roles: list) -> list | None:
    """
    Returns a list of employee UUIDs the user can see data for.
    Returns None for full-company scope (SYSTEM_ADMIN / PORTAL_ADMIN / HR_ADMIN).
    Manager roles get their team subtree only.
    """
    from app.db import query
    if any(r in roles for r in ('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')):
        return None

    ids: set = set()

    if 'SOLID_LINE_MANAGER' in roles:
        # Recursive solid-line subtree
        rows = query("""
            WITH RECURSIVE sub AS (
                SELECT employee_id::text FROM manager_relationships
                WHERE manager_id = %s::uuid AND relationship_type = 'SOLID_LINE' AND is_current
                UNION ALL
                SELECT mr.employee_id::text FROM manager_relationships mr
                JOIN sub ON sub.employee_id = mr.manager_id::text
                WHERE mr.relationship_type = 'SOLID_LINE' AND mr.is_current
            ) SELECT employee_id FROM sub
        """, (emp_id,))
        ids.update(r['employee_id'] for r in rows)

    if 'DOTTED_LINE_MANAGER' in roles:
        rows = query(
            "SELECT employee_id::text FROM manager_relationships "
            "WHERE manager_id = %s::uuid AND relationship_type = 'DOTTED_LINE' AND is_current",
            (emp_id,))
        ids.update(r['employee_id'] for r in rows)

    if 'DEPARTMENT_HEAD' in roles:
        rows = query("""
            SELECT DISTINCT e.id::text
            FROM employees e
            JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
            WHERE oa.business_unit_id IN (
                SELECT oa2.business_unit_id FROM employee_org_assignments oa2
                WHERE oa2.employee_id = %s::uuid AND oa2.is_current
            ) AND e.employment_status = 'ACTIVE'
        """, (emp_id,))
        ids.update(r['id'] for r in rows)

    if 'LOCATION_HEAD' in roles:
        rows = query("""
            SELECT DISTINCT e.id::text
            FROM employees e
            JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
            WHERE oa.location_id IN (
                SELECT oa2.location_id FROM employee_org_assignments oa2
                WHERE oa2.employee_id = %s::uuid AND oa2.is_current
            ) AND e.employment_status = 'ACTIVE'
        """, (emp_id,))
        ids.update(r['id'] for r in rows)

    if 'HIRING_MANAGER' in roles:
        # Hiring managers see their solid-line direct reports only
        rows = query(
            "SELECT employee_id::text FROM manager_relationships "
            "WHERE manager_id = %s::uuid AND relationship_type = 'SOLID_LINE' AND is_current",
            (emp_id,))
        ids.update(r['employee_id'] for r in rows)

    return list(ids)

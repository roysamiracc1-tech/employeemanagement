from flask import session, request, render_template, jsonify

from app import app
from app.db import query, to_dict
from app.auth import login_required
from app.helpers import TREE_CTE, build_nested


def _viewer_company():
    """Return the company_id of the logged-in user, or None for Tech Admin."""
    if 'SYSTEM_ADMIN' in session.get('roles', []):
        return None          # Tech Admin: no company boundary
    return session.get('company_id') or None


@app.route('/org-tree')
@login_required
def org_tree():
    return render_template('org/tree.html', own_emp_id=session['employee_id'])


@app.route('/api/org-tree')
@login_required
def api_org_tree():
    root_id       = request.args.get('root', '').strip() or session['employee_id']
    viewer_company = _viewer_company()

    # Company employees may only view trees rooted within their own company.
    # If the requested root belongs to a different company, fall back to own node.
    if viewer_company:
        root_row = query(
            "SELECT company_id::text FROM employees WHERE id=%s::uuid",
            (root_id,), one=True)
        if not root_row or root_row['company_id'] != viewer_company:
            root_id = session['employee_id']

    flat  = [to_dict(r) for r in query(TREE_CTE, ([root_id],))]
    roots = build_nested(flat)
    if not roots:
        return jsonify(None)
    return jsonify(roots[0] if len(roots) == 1 else roots)


@app.route('/api/org-tree/context')
@login_required
def api_org_tree_context():
    """Return focus person's info + ancestor chain, scoped to company boundary."""
    emp_id = request.args.get('of', '').strip() or session['employee_id']

    focus = query("""
        SELECT e.id::text, e.first_name, e.last_name, e.job_title,
               e.company_id::text AS company_id
        FROM employees e
        WHERE e.id = %s::uuid AND e.employment_status = 'ACTIVE'
    """, (emp_id,), one=True)

    if not focus:
        return jsonify({'focus': None, 'ancestors': []})

    focus_dict = to_dict(focus)
    company_id = focus_dict.pop('company_id', None)  # not exposed to the client

    if company_id:
        # Traverse ancestors only within the same company.
        # The JOIN on mgr.company_id stops the chain the moment it would
        # cross into an employee (including the Super Admin) with no company
        # affiliation or a different company.
        ancestors = query("""
            WITH RECURSIVE up AS (
                SELECT mr.manager_id AS id, 1 AS level
                FROM manager_relationships mr
                JOIN employees mgr ON mgr.id = mr.manager_id
                    AND mgr.company_id = %s::uuid
                    AND mgr.employment_status = 'ACTIVE'
                WHERE mr.employee_id = %s::uuid
                  AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
                UNION ALL
                SELECT mr.manager_id, up.level + 1
                FROM manager_relationships mr
                JOIN up ON mr.employee_id = up.id
                JOIN employees mgr ON mgr.id = mr.manager_id
                    AND mgr.company_id = %s::uuid
                    AND mgr.employment_status = 'ACTIVE'
                WHERE mr.relationship_type = 'SOLID_LINE' AND mr.is_current
            )
            SELECT e.id::text, e.first_name, e.last_name, e.job_title
            FROM up JOIN employees e ON e.id = up.id
            ORDER BY up.level DESC
        """, (company_id, emp_id, company_id))
    else:
        # Tech Admin (no company): unrestricted ancestor traversal
        ancestors = query("""
            WITH RECURSIVE up AS (
                SELECT mr.manager_id AS id, 1 AS level
                FROM manager_relationships mr
                WHERE mr.employee_id = %s::uuid
                  AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
                UNION ALL
                SELECT mr.manager_id, up.level + 1
                FROM manager_relationships mr
                JOIN up ON mr.employee_id = up.id
                WHERE mr.relationship_type = 'SOLID_LINE' AND mr.is_current
            )
            SELECT e.id::text, e.first_name, e.last_name, e.job_title
            FROM up JOIN employees e ON e.id = up.id
            ORDER BY up.level DESC
        """, (emp_id,))

    return jsonify({
        'focus':     focus_dict,
        'ancestors': [to_dict(a) for a in ancestors],
    })

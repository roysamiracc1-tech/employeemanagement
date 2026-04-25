from flask import session, request, render_template, jsonify

from app import app
from app.db import query, to_dict
from app.auth import require_roles
from app.helpers import MGMT_ROLES, TREE_CTE, build_nested


@app.route('/org-tree')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
               'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def org_tree():
    roles    = session.get('roles', [])
    is_admin = any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD'])
    all_employees = []
    if is_admin:
        all_employees = [to_dict(r) for r in query("""
            SELECT e.id::text, e.first_name, e.last_name, e.job_title
            FROM employees e WHERE e.employment_status='ACTIVE'
            ORDER BY e.first_name, e.last_name
        """)]
    return render_template('org/tree.html',
                           is_admin=is_admin,
                           own_emp_id=session['employee_id'],
                           all_employees=all_employees)


@app.route('/api/org-tree')
@require_roles('SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
               'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER')
def api_org_tree():
    roles    = session.get('roles', [])
    is_admin = any(r in roles for r in ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD'])
    root_id  = request.args.get('root', '').strip()

    if not is_admin:
        root_ids = [session['employee_id']]
    elif root_id:
        root_ids = [root_id]
    else:
        top_rows = query("""
            SELECT e.id::text FROM employees e
            WHERE e.employment_status = 'ACTIVE'
              AND NOT EXISTS (
                  SELECT 1 FROM manager_relationships mr
                  WHERE mr.employee_id = e.id
                    AND mr.relationship_type = 'SOLID_LINE'
                    AND mr.is_current
              )
            ORDER BY e.first_name, e.last_name
        """)
        root_ids = [r['id'] for r in top_rows]

    if not root_ids:
        return jsonify([])

    flat  = [to_dict(r) for r in query(TREE_CTE, (root_ids,))]
    roots = build_nested(flat)
    return jsonify(roots if len(roots) != 1 else roots[0])

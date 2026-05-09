from flask import session, request, render_template, jsonify

from app import app
from app.db import query, to_dict
from app.auth import login_required
from app.helpers import TREE_CTE, build_nested


@app.route('/org-tree')
@login_required
def org_tree():
    return render_template('org/tree.html', own_emp_id=session['employee_id'])


@app.route('/api/org-tree')
@login_required
def api_org_tree():
    root_id = request.args.get('root', '').strip() or session['employee_id']
    flat    = [to_dict(r) for r in query(TREE_CTE, ([root_id],))]
    roots   = build_nested(flat)
    if not roots:
        return jsonify(None)
    return jsonify(roots[0] if len(roots) == 1 else roots)


@app.route('/api/org-tree/context')
@login_required
def api_org_tree_context():
    """Return focus person's basic info + ancestor chain from root to their direct manager."""
    emp_id = request.args.get('of', '').strip() or session['employee_id']

    focus = query("""
        SELECT e.id::text, e.first_name, e.last_name, e.job_title
        FROM employees e
        WHERE e.id = %s::uuid AND e.employment_status = 'ACTIVE'
    """, (emp_id,), one=True)

    ancestors = query("""
        WITH RECURSIVE up AS (
            SELECT mr.manager_id AS id, 1 AS level
            FROM manager_relationships mr
            WHERE mr.employee_id = %s::uuid
              AND mr.relationship_type = 'SOLID_LINE'
              AND mr.is_current
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
        'focus':     to_dict(focus) if focus else None,
        'ancestors': [to_dict(a) for a in ancestors],
    })

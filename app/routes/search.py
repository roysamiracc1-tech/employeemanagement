"""Full-text and natural-language search API."""
import threading
import logging

from flask import session, request, jsonify, render_template, current_app

from app import app
from app.auth import login_required
from app.services.search_service import unified_search
from app.services.company_scope import current_company_id

log = logging.getLogger(__name__)


def _log_search(app_ctx, user_id, company_id, role, query, result_count, search_type):
    with app_ctx.app_context():
        try:
            from app.db import execute
            execute(
                "INSERT INTO search_logs "
                "(user_id, company_id, role, query, result_count, search_type) "
                "VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s)",
                (user_id, company_id, role, query, result_count, search_type),
            )
        except Exception as exc:
            log.debug('search_log insert failed: %s', exc)


@app.route('/search')
@login_required
def search_page():
    q = request.args.get('q', '').strip()
    return render_template('search/results.html', q=q)


@app.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'employees': [], 'vacations': [], 'org': None})

    company_id  = current_company_id() or session.get('company_id')
    employee_id = session['employee_id']

    results = unified_search(q, employee_id=employee_id, company_id=company_id)

    # Log search query asynchronously
    total = (len(results.get('employees', [])) +
             len(results.get('vacations', [])) +
             (1 if results.get('org') else 0))
    roles = session.get('roles', [])
    ctx = current_app._get_current_object()
    threading.Thread(
        target=_log_search,
        args=(ctx, session.get('user_id'), company_id,
              roles[0] if roles else None, q, total, 'unified'),
        daemon=True,
    ).start()

    return jsonify(results)

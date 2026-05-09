"""Full-text and natural-language search API."""
from flask import session, request, jsonify, render_template

from app import app
from app.auth import login_required
from app.services.search_service import unified_search
from app.services.company_scope import current_company_id


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
    return jsonify(results)

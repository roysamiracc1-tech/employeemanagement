"""Stack Overflow survey benchmark page — SYSTEM_ADMIN only."""
from flask import session, request, jsonify, render_template

from app import app
from app.auth import require_roles
from app.db import query, to_dict

_ROLE = ('SYSTEM_ADMIN',)

# Skills categories that can be cross-matched with actual employee skills
_SKILL_CATS = {'Programming Languages', 'Databases', 'Web Frameworks',
               'Cloud & DevOps', 'Dev IDEs', 'Large Language Models'}

CATEGORY_ORDER = [
    'Programming Languages',
    'Databases',
    'Web Frameworks',
    'Cloud & DevOps',
    'Dev IDEs',
    'Large Language Models',
    'Collaboration Tools',
    'Community Platforms',
    'Operating Systems',
    'Trending Topics',
]


@app.route('/admin/benchmarks')
@require_roles(*_ROLE)
def admin_benchmarks():
    years = [r['survey_year'] for r in query(
        "SELECT DISTINCT survey_year FROM survey_benchmarks ORDER BY survey_year DESC")]
    companies = [dict(r) for r in query(
        "SELECT id::text, name FROM companies ORDER BY name")]
    return render_template('admin/benchmarks.html',
                           years=years, companies=companies,
                           category_order=CATEGORY_ORDER)


@app.route('/api/admin/benchmarks')
@require_roles(*_ROLE)
def api_admin_benchmarks():
    """Return benchmark data for one category + optional company skill overlay."""
    category   = request.args.get('category', 'Programming Languages')
    year       = int(request.args.get('year', 2025))
    company_id = request.args.get('company_id', '')
    context    = request.args.get('context', 'all_respondents')

    rows = [to_dict(r) for r in query("""
        SELECT technology, usage_pct, context, rank_in_category,
               desired_pct, admired_pct, sankey_role
        FROM survey_benchmarks
        WHERE survey_year = %s AND category = %s AND context = %s
        ORDER BY rank_in_category
    """, (year, category, context))]

    overlay = []
    if company_id and category in _SKILL_CATS:
        # Count how many employees in this company have each skill
        total_emp = (query("""
            SELECT COUNT(*)::int AS n FROM employees
            WHERE company_id = %s::uuid AND employment_status = 'ACTIVE'
        """, (company_id,), one=True) or {}).get('n', 1) or 1

        skill_counts = [to_dict(r) for r in query("""
            SELECT s.name AS technology,
                   COUNT(DISTINCT es.employee_id)::int AS emp_count,
                   ROUND(COUNT(DISTINCT es.employee_id)::numeric / %s * 100, 1) AS company_pct
            FROM employee_skills es
            JOIN skills s ON s.id = es.skill_id
            JOIN employees e ON e.id = es.employee_id
            WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
            GROUP BY s.name
        """, (total_emp, company_id))]
        overlay = skill_counts

    return jsonify({
        'category':   category,
        'year':       year,
        'source':     'Stack Overflow Developer Survey',
        'source_url': 'https://survey.stackoverflow.co/2025',
        'rows':       rows,
        'overlay':    overlay,
        'total_employees': (query("""
            SELECT COUNT(*)::int AS n FROM employees
            WHERE company_id = %s::uuid AND employment_status = 'ACTIVE'
        """, (company_id,), one=True) or {}).get('n', 0) if company_id else 0,
    })


@app.route('/api/admin/benchmarks/categories')
@require_roles(*_ROLE)
def api_admin_benchmark_categories():
    rows = [to_dict(r) for r in query("""
        SELECT category, COUNT(*) AS item_count, survey_year
        FROM survey_benchmarks
        GROUP BY category, survey_year
        ORDER BY survey_year DESC, category
    """)]
    return jsonify(rows)

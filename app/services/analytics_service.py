"""Analytics query service.

All functions accept (company_id, start, end) where start/end are
datetime.date objects.  Returns plain dicts/lists ready for jsonify().
"""
import datetime
from app.db import query, to_dict


# ── helpers ──────────────────────────────────────────────────────────────────

def _rows(sql, params=()):
    return [to_dict(r) for r in query(sql, params)]


def _one(sql, params=()):
    r = query(sql, params, one=True)
    return to_dict(r) if r else {}


def _fmt(d):
    return str(d) if d else None


def _scope(company_id: str | None, emp_ids: list | None):
    if emp_ids is not None:
        return "e.id = ANY(%s::uuid[])", emp_ids
    return "e.company_id = %s::uuid", company_id


# ── 1. Overview / Feature Adoption ───────────────────────────────────────────

def get_overview(company_id: str, start: datetime.date, end: datetime.date,
                 emp_ids: list | None = None) -> dict:
    co = '%s::uuid'

    # Daily active users — page_views scoped by company_id only (no employee filter)
    dau = _rows("""
        SELECT DATE(created_at) AS day, COUNT(DISTINCT user_id) AS users
        FROM page_views
        WHERE company_id = {co} AND created_at::date BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 1
    """.format(co=co), (company_id, start, end))
    for r in dau:
        r['day'] = str(r['day'])

    # Top pages by visits
    top_pages = _rows("""
        SELECT page_label, route, COUNT(*) AS views,
               COUNT(DISTINCT user_id) AS unique_users
        FROM page_views
        WHERE company_id = {co} AND created_at::date BETWEEN %s AND %s
        GROUP BY page_label, route ORDER BY views DESC LIMIT 15
    """.format(co=co), (company_id, start, end))

    # Feature adoption — distinct users who touched each feature in the period
    # Always scoped by company for page_view data; emp count uses scope
    wh_e, sc_e = _scope(company_id, emp_ids)
    wh_e_bare = wh_e.replace('e.', '')
    total_emp = (query(
        f"SELECT COUNT(*)::int AS n FROM employees WHERE {wh_e_bare} AND employment_status='ACTIVE'",
        (sc_e,), one=True) or {}).get('n') or 1

    feature_routes = {
        'Vacation Requests':   ['/vacation'],
        'Vacation Calendar':   ['/vacation/calendar'],
        'Team Vacation':       ['/vacation/team'],
        'Org Chart':           ['/org-tree'],
        'Employee Directory':  ['/directory'],
        'Search':              ['/search'],
        'My Profile':          ['/profile'],
        'My Team':             ['/my-team'],
        'Bulk Import':         ['/admin/imports'],
    }
    adoption = []
    for feature, routes in feature_routes.items():
        row = _one("""
            SELECT COUNT(DISTINCT user_id)::int AS users
            FROM page_views
            WHERE company_id = {co}
              AND route = ANY(%s::text[])
              AND created_at::date BETWEEN %s AND %s
        """.format(co=co), (company_id, routes, start, end))
        users = row.get('users', 0)
        adoption.append({
            'feature':       feature,
            'users':         users,
            'total_employees': total_emp,
            'pct':           round(users / total_emp * 100, 1),
        })
    adoption.sort(key=lambda x: x['users'], reverse=True)

    # Bulk import — last 6 months count
    bulk = _one("""
        SELECT COUNT(*)::int AS imports,
               SUM(CASE WHEN status='APPLIED' THEN 1 ELSE 0 END)::int AS applied,
               MAX(created_at) AS last_used
        FROM employee_imports
        WHERE company_id = {co}
          AND created_at >= NOW() - INTERVAL '6 months'
    """.format(co=co), (company_id,))
    if bulk.get('last_used'):
        bulk['last_used'] = str(bulk['last_used'])[:10]

    # Period totals
    totals = _one("""
        SELECT COUNT(*)::int AS total_views,
               COUNT(DISTINCT user_id)::int AS unique_users
        FROM page_views
        WHERE company_id = {co} AND created_at::date BETWEEN %s AND %s
    """.format(co=co), (company_id, start, end))

    return {
        'totals':          totals,
        'dau':             dau,
        'top_pages':       top_pages,
        'feature_adoption': adoption,
        'bulk_import':     bulk,
    }


# ── 2. Vacation Analytics ─────────────────────────────────────────────────────

def get_vacation_analytics(company_id: str, start: datetime.date,
                           end: datetime.date, group_by: str = 'company',
                           emp_ids: list | None = None) -> dict:
    wh_e, sc_e = _scope(company_id, emp_ids)

    # KPIs
    kpis = _one(f"""
        SELECT
            COUNT(*)::int                                                        AS total,
            SUM(CASE WHEN status='APPROVED'  THEN 1 ELSE 0 END)::int            AS approved,
            SUM(CASE WHEN status='REJECTED'  THEN 1 ELSE 0 END)::int            AS rejected,
            SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END)::int            AS cancelled,
            SUM(CASE WHEN status='PENDING'   THEN 1 ELSE 0 END)::int            AS pending,
            ROUND(AVG(EXTRACT(EPOCH FROM (reviewed_at - vr.created_at))/3600)
                  FILTER (WHERE reviewed_at IS NOT NULL), 1)                     AS avg_decision_h
        FROM vacation_requests vr
        JOIN employees e ON e.id = vr.employee_id
        WHERE {wh_e}
          AND vr.created_at::date BETWEEN %s AND %s
    """, (sc_e, start, end))

    total = kpis.get('total') or 1
    kpis['approval_rate']     = round((kpis.get('approved')  or 0) / total * 100, 1)
    kpis['rejection_rate']    = round((kpis.get('rejected')  or 0) / total * 100, 1)
    kpis['cancellation_rate'] = round((kpis.get('cancelled') or 0) / total * 100, 1)

    # Oldest pending (days)
    oldest = _one(f"""
        SELECT COALESCE(MAX(EXTRACT(DAY FROM NOW() - vr.created_at))::int, 0) AS oldest_days
        FROM vacation_requests vr
        JOIN employees e ON e.id = vr.employee_id
        WHERE {wh_e} AND vr.status='PENDING'
    """, (sc_e,))
    kpis['oldest_pending_days'] = oldest.get('oldest_days', 0)

    # Requests over time (monthly buckets)
    over_time = _rows(f"""
        SELECT TO_CHAR(DATE_TRUNC('month', vr.created_at), 'YYYY-MM') AS period,
               SUM(CASE WHEN status='APPROVED'  THEN 1 ELSE 0 END)::int AS approved,
               SUM(CASE WHEN status='REJECTED'  THEN 1 ELSE 0 END)::int AS rejected,
               SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END)::int AS cancelled,
               SUM(CASE WHEN status='PENDING'   THEN 1 ELSE 0 END)::int AS pending,
               COUNT(*)::int AS total
        FROM vacation_requests vr
        JOIN employees e ON e.id = vr.employee_id
        WHERE {wh_e}
          AND vr.created_at::date BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 1
    """, (sc_e, start, end))

    # By vacation type
    by_type = _rows(f"""
        SELECT vt.name AS type_name, vt.color,
               COUNT(*)::int AS total,
               SUM(CASE WHEN vr.status='APPROVED' THEN 1 ELSE 0 END)::int AS approved,
               SUM(CASE WHEN vr.status='PENDING'  THEN 1 ELSE 0 END)::int AS pending
        FROM vacation_requests vr
        JOIN vacation_types vt ON vt.id = vr.vacation_type_id
        JOIN employees e ON e.id = vr.employee_id
        WHERE {wh_e}
          AND vr.created_at::date BETWEEN %s AND %s
        GROUP BY vt.name, vt.color ORDER BY total DESC
    """, (sc_e, start, end))

    # Leave utilisation grouped
    utilisation = _get_utilisation(company_id, group_by, emp_ids=emp_ids)

    # Employee drilldown
    drilldown = _rows(f"""
        SELECT e.id::text, e.first_name || ' ' || e.last_name AS name,
               e.job_title,
               COALESCE(bu.name, 'Unassigned') AS department,
               COALESCE(loc.name, 'Unassigned') AS location,
               mgr_e.first_name || ' ' || mgr_e.last_name AS manager_name,
               COALESCE(SUM(CASE WHEN vr.status='APPROVED'
                            AND EXTRACT(YEAR FROM vr.start_date) = EXTRACT(YEAR FROM CURRENT_DATE)
                            THEN vr.working_days ELSE 0 END), 0)::int AS used_days,
               COUNT(CASE WHEN vr.created_at::date BETWEEN %s AND %s
                          THEN 1 END)::int AS period_requests
        FROM employees e
        LEFT JOIN employee_org_assignments eoa ON eoa.employee_id = e.id AND eoa.is_current
        LEFT JOIN business_units bu ON bu.id = eoa.business_unit_id
        LEFT JOIN locations loc ON loc.id = eoa.location_id
        LEFT JOIN manager_relationships mr
               ON mr.employee_id = e.id AND mr.relationship_type='SOLID_LINE' AND mr.is_current
        LEFT JOIN employees mgr_e ON mgr_e.id = mr.manager_id
        LEFT JOIN vacation_requests vr ON vr.employee_id = e.id
        WHERE {wh_e} AND e.employment_status = 'ACTIVE'
        GROUP BY e.id, e.first_name, e.last_name, e.job_title,
                 bu.name, loc.name, mgr_e.first_name, mgr_e.last_name
        ORDER BY used_days ASC
    """, (start, end, sc_e))

    return {
        'kpis':         kpis,
        'over_time':    over_time,
        'by_type':      by_type,
        'utilisation':  utilisation,
        'drilldown':    drilldown,
        'group_by':     group_by,
    }


def _get_utilisation(company_id: str, group_by: str, emp_ids: list | None = None) -> list:
    wh_e, sc_e = _scope(company_id, emp_ids)
    year = datetime.date.today().year

    if group_by == 'department':
        return _rows(f"""
            SELECT COALESCE(bu.name, 'Unassigned') AS group_name,
                   COUNT(DISTINCT e.id)::int AS employees,
                   COALESCE(SUM(CASE WHEN vr.status='APPROVED'
                                AND EXTRACT(YEAR FROM vr.start_date) = %s
                                THEN vr.working_days ELSE 0 END), 0)::int AS used_days
            FROM employees e
            LEFT JOIN employee_org_assignments eoa ON eoa.employee_id = e.id AND eoa.is_current
            LEFT JOIN business_units bu ON bu.id = eoa.business_unit_id
            LEFT JOIN vacation_requests vr ON vr.employee_id = e.id
            WHERE {wh_e} AND e.employment_status = 'ACTIVE'
            GROUP BY bu.name ORDER BY used_days DESC
        """, (year, sc_e))

    elif group_by == 'location':
        return _rows(f"""
            SELECT COALESCE(loc.name, 'Unassigned') AS group_name,
                   COUNT(DISTINCT e.id)::int AS employees,
                   COALESCE(SUM(CASE WHEN vr.status='APPROVED'
                                AND EXTRACT(YEAR FROM vr.start_date) = %s
                                THEN vr.working_days ELSE 0 END), 0)::int AS used_days
            FROM employees e
            LEFT JOIN employee_org_assignments eoa ON eoa.employee_id = e.id AND eoa.is_current
            LEFT JOIN locations loc ON loc.id = eoa.location_id
            LEFT JOIN vacation_requests vr ON vr.employee_id = e.id
            WHERE {wh_e} AND e.employment_status = 'ACTIVE'
            GROUP BY loc.name ORDER BY used_days DESC
        """, (year, sc_e))

    elif group_by == 'manager':
        return _rows(f"""
            SELECT COALESCE(mgr_e.first_name || ' ' || mgr_e.last_name, 'No Manager')
                     AS group_name,
                   COUNT(DISTINCT e.id)::int AS employees,
                   COALESCE(SUM(CASE WHEN vr.status='APPROVED'
                                AND EXTRACT(YEAR FROM vr.start_date) = %s
                                THEN vr.working_days ELSE 0 END), 0)::int AS used_days
            FROM employees e
            LEFT JOIN manager_relationships mr
                   ON mr.employee_id = e.id AND mr.relationship_type='SOLID_LINE' AND mr.is_current
            LEFT JOIN employees mgr_e ON mgr_e.id = mr.manager_id
            LEFT JOIN vacation_requests vr ON vr.employee_id = e.id
            WHERE {wh_e} AND e.employment_status = 'ACTIVE'
            GROUP BY mgr_e.first_name, mgr_e.last_name ORDER BY used_days DESC
        """, (year, sc_e))

    else:  # company-wide
        return _rows(f"""
            SELECT 'Company Wide' AS group_name,
                   COUNT(DISTINCT e.id)::int AS employees,
                   COALESCE(SUM(CASE WHEN vr.status='APPROVED'
                                AND EXTRACT(YEAR FROM vr.start_date) = %s
                                THEN vr.working_days ELSE 0 END), 0)::int AS used_days
            FROM employees e
            LEFT JOIN vacation_requests vr ON vr.employee_id = e.id
            WHERE {wh_e} AND e.employment_status = 'ACTIVE'
        """, (year, sc_e))


# ── 3. Skills Analytics ───────────────────────────────────────────────────────

def get_skills_analytics(company_id: str, start: datetime.date,
                         end: datetime.date, emp_ids: list | None = None) -> dict:
    wh_e, sc_e = _scope(company_id, emp_ids)
    wh_e_bare = wh_e.replace('e.', '')

    # KPIs
    total_emp = (query(
        f"SELECT COUNT(*)::int AS n FROM employees WHERE {wh_e_bare} AND employment_status='ACTIVE'",
        (sc_e,), one=True) or {}).get('n') or 1

    with_skills = (_one(f"""
        SELECT COUNT(DISTINCT es.employee_id)::int AS n
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh_e}
    """, (sc_e,)).get('n') or 0)

    validated = (_one(f"""
        SELECT COUNT(*)::int AS total,
               SUM(CASE WHEN es.validation_status='VALIDATED' THEN 1 ELSE 0 END)::int AS validated
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh_e}
    """, (sc_e,)))

    kpis = {
        'total_employees':     total_emp,
        'with_skills':         with_skills,
        'completeness_pct':    round(with_skills / total_emp * 100, 1),
        'total_skill_entries': validated.get('total', 0),
        'validated_entries':   validated.get('validated', 0),
        'validation_rate_pct': round(
            (validated.get('validated', 0) / max(validated.get('total', 1), 1)) * 100, 1),
    }

    # Skills added per month
    per_month = _rows(f"""
        SELECT TO_CHAR(DATE_TRUNC('month', es.created_at), 'YYYY-MM') AS period,
               COUNT(*)::int AS added
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh_e}
          AND es.created_at::date BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 1
    """, (sc_e, start, end))

    # Top skills company-wide
    top_skills = _rows(f"""
        SELECT s.name AS skill_name, sc.name AS category,
               COUNT(*)::int AS employees,
               SUM(CASE WHEN es.validation_status='VALIDATED' THEN 1 ELSE 0 END)::int AS validated
        FROM employee_skills es
        JOIN skills s ON s.id = es.skill_id
        LEFT JOIN skill_categories sc ON sc.id = s.skill_category_id
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh_e}
        GROUP BY s.name, sc.name ORDER BY employees DESC LIMIT 15
    """, (sc_e,))

    # Top skills by department
    by_dept = _rows(f"""
        SELECT COALESCE(bu.name, 'Unassigned') AS department,
               s.name AS skill_name, COUNT(*)::int AS cnt
        FROM employee_skills es
        JOIN skills s ON s.id = es.skill_id
        JOIN employees e ON e.id = es.employee_id
        LEFT JOIN employee_org_assignments eoa ON eoa.employee_id = e.id AND eoa.is_current
        LEFT JOIN business_units bu ON bu.id = eoa.business_unit_id
        WHERE {wh_e}
        GROUP BY bu.name, s.name ORDER BY department, cnt DESC
    """, (sc_e,))

    # Employee profile completeness
    emp_completeness = _rows(f"""
        SELECT e.id::text, e.first_name || ' ' || e.last_name AS name,
               e.job_title,
               COALESCE(bu.name, 'Unassigned') AS department,
               COUNT(es.id)::int AS skill_count,
               SUM(CASE WHEN es.validation_status='VALIDATED' THEN 1 ELSE 0 END)::int AS validated_count
        FROM employees e
        LEFT JOIN employee_org_assignments eoa ON eoa.employee_id = e.id AND eoa.is_current
        LEFT JOIN business_units bu ON bu.id = eoa.business_unit_id
        LEFT JOIN employee_skills es ON es.employee_id = e.id
        WHERE {wh_e} AND e.employment_status='ACTIVE'
        GROUP BY e.id, e.first_name, e.last_name, e.job_title, bu.name
        ORDER BY skill_count DESC
    """, (sc_e,))

    return {
        'kpis':             kpis,
        'per_month':        per_month,
        'top_skills':       top_skills,
        'by_dept':          by_dept,
        'emp_completeness': emp_completeness,
    }


# ── 4. Org Chart Analytics ────────────────────────────────────────────────────

def get_org_analytics(company_id: str, start: datetime.date,
                      end: datetime.date, emp_ids: list | None = None) -> dict:
    wh_e, sc_e = _scope(company_id, emp_ids)

    # Headcount KPIs — use bare company_id for the basic count (no alias needed)
    # When scoped, use the emp_ids path
    if emp_ids is not None:
        hc = _one("""
            SELECT
                COUNT(*)::int                                              AS total_employees,
                SUM(CASE WHEN employment_status='ACTIVE' THEN 1 ELSE 0 END)::int AS active,
                SUM(CASE WHEN employment_status='INACTIVE' THEN 1 ELSE 0 END)::int AS inactive
            FROM employees WHERE id = ANY(%s::uuid[])
        """, (emp_ids,))
    else:
        co = '%s::uuid'
        hc = _one("""
            SELECT
                COUNT(*)::int                                              AS total_employees,
                SUM(CASE WHEN employment_status='ACTIVE' THEN 1 ELSE 0 END)::int AS active,
                SUM(CASE WHEN employment_status='INACTIVE' THEN 1 ELSE 0 END)::int AS inactive
            FROM employees WHERE company_id = {co}
        """.format(co=co), (company_id,))

    # Manager count vs IC count
    mgr_count = _one(f"""
        SELECT COUNT(DISTINCT manager_id)::int AS managers
        FROM manager_relationships
        WHERE is_current
          AND manager_id IN (SELECT id FROM employees WHERE {wh_e})
    """, (sc_e,)).get('managers', 0)

    hc['managers'] = mgr_count
    hc['ics']      = max((hc.get('active') or 0) - mgr_count, 0)
    hc['mgr_ratio'] = round(mgr_count / max(hc.get('active') or 1, 1) * 100, 1)

    # Org depth — only meaningful for full-company scope; scope to emp set when filtered
    if emp_ids is not None:
        depth = _one("""
            WITH RECURSIVE tree AS (
                SELECT e.id, 0 AS depth
                FROM employees e
                WHERE e.id = ANY(%s::uuid[])
                  AND NOT EXISTS (
                      SELECT 1 FROM manager_relationships mr
                      WHERE mr.employee_id = e.id AND mr.is_current
                        AND mr.manager_id = ANY(%s::uuid[])
                  )
                UNION ALL
                SELECT mr.employee_id, t.depth + 1
                FROM tree t
                JOIN manager_relationships mr ON mr.manager_id = t.id AND mr.is_current
                JOIN employees e ON e.id = mr.employee_id AND e.id = ANY(%s::uuid[])
            )
            SELECT MAX(depth)::int AS max_depth FROM tree
        """, (emp_ids, emp_ids, emp_ids)).get('max_depth', 0)
    else:
        co = '%s::uuid'
        depth = _one("""
            WITH RECURSIVE tree AS (
                SELECT e.id, 0 AS depth
                FROM employees e
                WHERE e.company_id = {co}
                  AND NOT EXISTS (
                      SELECT 1 FROM manager_relationships mr
                      WHERE mr.employee_id = e.id AND mr.is_current
                  )
                UNION ALL
                SELECT mr.employee_id, t.depth + 1
                FROM tree t
                JOIN manager_relationships mr ON mr.manager_id = t.id AND mr.is_current
                JOIN employees e ON e.id = mr.employee_id AND e.company_id = {co}
            )
            SELECT MAX(depth)::int AS max_depth FROM tree
        """.format(co=co), (company_id, company_id)).get('max_depth', 0)
    hc['max_depth'] = depth or 0

    # Avg span of control
    span = _one(f"""
        SELECT ROUND(AVG(report_count), 1) AS avg_span
        FROM (
            SELECT mr.manager_id, COUNT(*)::float AS report_count
            FROM manager_relationships mr
            JOIN employees e ON e.id = mr.employee_id AND ({wh_e})
            WHERE mr.is_current AND mr.relationship_type = 'SOLID_LINE'
            GROUP BY mr.manager_id
        ) s
    """, (sc_e,))
    hc['avg_span'] = float(span.get('avg_span') or 0)

    # Headcount by department
    by_dept = _rows(f"""
        SELECT COALESCE(bu.name, 'Unassigned') AS department,
               COUNT(DISTINCT e.id)::int AS employees
        FROM employees e
        LEFT JOIN employee_org_assignments eoa ON eoa.employee_id = e.id AND eoa.is_current
        LEFT JOIN business_units bu ON bu.id = eoa.business_unit_id
        WHERE {wh_e} AND e.employment_status = 'ACTIVE'
        GROUP BY bu.name ORDER BY employees DESC
    """, (sc_e,))

    # Headcount over time (monthly joins)
    if emp_ids is not None:
        hc_over_time = _rows("""
            SELECT TO_CHAR(DATE_TRUNC('month', join_date), 'YYYY-MM') AS period,
                   COUNT(*)::int AS joined,
                   SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', join_date))::int AS cumulative
            FROM employees
            WHERE id = ANY(%s::uuid[])
              AND join_date IS NOT NULL
              AND join_date::date BETWEEN %s AND %s
            GROUP BY 1 ORDER BY 1
        """, (emp_ids, start, end))
    else:
        co = '%s::uuid'
        hc_over_time = _rows("""
            SELECT TO_CHAR(DATE_TRUNC('month', join_date), 'YYYY-MM') AS period,
                   COUNT(*)::int AS joined,
                   SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', join_date))::int AS cumulative
            FROM employees
            WHERE company_id = {co}
              AND join_date IS NOT NULL
              AND join_date::date BETWEEN %s AND %s
            GROUP BY 1 ORDER BY 1
        """.format(co=co), (company_id, start, end))

    # Manager span-of-control table
    span_table = _rows(f"""
        SELECT mgr.first_name || ' ' || mgr.last_name AS manager_name,
               mgr.job_title,
               COUNT(mr.employee_id)::int AS direct_reports
        FROM manager_relationships mr
        JOIN employees mgr ON mgr.id = mr.manager_id
        JOIN employees e ON e.id = mr.employee_id
        WHERE ({wh_e}) AND mr.is_current
          AND mr.relationship_type = 'SOLID_LINE'
        GROUP BY mgr.id, mgr.first_name, mgr.last_name, mgr.job_title
        ORDER BY direct_reports DESC
    """, (sc_e,))

    # Org chart page views — always company-wide (not scoped to emp list)
    co = '%s::uuid'
    org_views = _rows("""
        SELECT DATE(created_at) AS day, COUNT(*)::int AS views
        FROM page_views
        WHERE company_id = {co}
          AND route = '/org-tree'
          AND created_at::date BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 1
    """.format(co=co), (company_id, start, end))
    for r in org_views:
        r['day'] = str(r['day'])

    org_view_total = _one("""
        SELECT COUNT(*)::int AS total, COUNT(DISTINCT user_id)::int AS unique_users
        FROM page_views
        WHERE company_id = {co} AND route = '/org-tree'
          AND created_at::date BETWEEN %s AND %s
    """.format(co=co), (company_id, start, end))

    return {
        'kpis':          hc,
        'by_dept':       by_dept,
        'hc_over_time':  hc_over_time,
        'span_table':    span_table,
        'org_views':     org_views,
        'org_view_total': org_view_total,
    }


# ── 5. Search Analytics ───────────────────────────────────────────────────────

def get_search_analytics(company_id: str, start: datetime.date,
                         end: datetime.date, emp_ids: list | None = None) -> dict:
    # Search analytics are company-wide (no employee scope filter makes sense here)
    co = '%s::uuid'

    # KPIs
    kpis = _one("""
        SELECT COUNT(*)::int AS total_searches,
               COUNT(DISTINCT user_id)::int AS unique_searchers,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END)::int AS zero_results,
               ROUND(AVG(result_count), 1) AS avg_results
        FROM search_logs
        WHERE company_id = {co}
          AND created_at::date BETWEEN %s AND %s
    """.format(co=co), (company_id, start, end))

    total = kpis.get('total_searches') or 1
    kpis['zero_result_rate'] = round(
        (kpis.get('zero_results') or 0) / total * 100, 1)

    # Volume over time
    volume = _rows("""
        SELECT DATE(created_at) AS day,
               COUNT(*)::int AS searches,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END)::int AS zero_results
        FROM search_logs
        WHERE company_id = {co}
          AND created_at::date BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 1
    """.format(co=co), (company_id, start, end))
    for r in volume:
        r['day'] = str(r['day'])

    # Top search terms
    top_terms = _rows("""
        SELECT query, COUNT(*)::int AS searches,
               ROUND(AVG(result_count), 1) AS avg_results,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END)::int AS zero_count
        FROM search_logs
        WHERE company_id = {co}
          AND created_at::date BETWEEN %s AND %s
        GROUP BY query ORDER BY searches DESC LIMIT 25
    """.format(co=co), (company_id, start, end))

    # Zero-result searches (worst offenders)
    zero_results = _rows("""
        SELECT query, COUNT(*)::int AS searches
        FROM search_logs
        WHERE company_id = {co}
          AND result_count = 0
          AND created_at::date BETWEEN %s AND %s
        GROUP BY query ORDER BY searches DESC LIMIT 15
    """.format(co=co), (company_id, start, end))

    return {
        'kpis':         kpis,
        'volume':       volume,
        'top_terms':    top_terms,
        'zero_results': zero_results,
    }

"""Full-text and natural-language search service."""
import re
import datetime

from app.db import query, to_dict
from app.services.company_scope import viewer_company_id


# ── Natural-language pattern matching ────────────────────────────────────────

_ORG_PATTERNS = [
    (re.compile(r'report(?:ing|s)? to me', re.I),        'REPORTING_TO_ME'),
    (re.compile(r'my (?:direct )?reports?',  re.I),       'REPORTING_TO_ME'),
    (re.compile(r'my team',                  re.I),       'REPORTING_TO_ME'),
    (re.compile(r'(\w[\w ]+?) (?:and their?|and his|and her) team', re.I), 'NAMED_TEAM'),
]

_VACATION_PATTERNS = [
    (re.compile(r'(?:my )?(?:upcoming|next(?: month)?|future) (?:vacation|leave|holiday)',
                re.I), 'MY_UPCOMING'),
    (re.compile(r'(?:team|my team)[\'s]* (?:vacation|leave)',  re.I), 'TEAM_UPCOMING'),
    (re.compile(r'(?:all|company) (?:vacation|leave)',          re.I), 'ALL_UPCOMING'),
    (re.compile(r'vacation.*(?:next month|this month)',         re.I), 'MY_UPCOMING'),
]


def _parse_vacation_intent(q):
    for pattern, intent in _VACATION_PATTERNS:
        if pattern.search(q):
            return intent
    return None


def _parse_org_intent(q):
    for pattern, intent in _ORG_PATTERNS:
        m = pattern.search(q)
        if m:
            named = m.group(1) if intent == 'NAMED_TEAM' and m.lastindex else None
            return intent, named
    return None, None


# ── Employee full-text search ─────────────────────────────────────────────────

def search_employees(q: str, company_id: str = None, limit: int = 10):
    if not q or len(q.strip()) < 2:
        return []

    company_filter     = "AND e.company_id = %s::uuid" if company_id else ""
    params_fts         = [q] + ([company_id] if company_id else [])

    rows = query(f"""
        SELECT e.id::text, e.first_name, e.last_name, e.job_title,
               e.email, e.employment_status,
               COALESCE(l.name,'') AS location,
               COALESCE(bu.name,'') AS business_unit
        FROM employee_search_index esi
        JOIN employees e ON e.id = esi.employee_id
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l ON l.id=oa.location_id
        LEFT JOIN business_units bu ON bu.id=oa.business_unit_id
        WHERE esi.search_text @@ plainto_tsquery('english', %s)
          AND e.employment_status = 'ACTIVE'
          {company_filter}
        ORDER BY ts_rank(esi.search_text, plainto_tsquery('english', %s)) DESC
        LIMIT %s
    """, params_fts + [q, limit])

    return [to_dict(r) for r in rows]


# ── Vacation search ───────────────────────────────────────────────────────────

def search_vacations(q: str, employee_id: str, company_id: str = None,
                     scope: str = 'mine', limit: int = 20):
    intent = _parse_vacation_intent(q)

    today     = datetime.date.today()
    nxt_month = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    end_range = (nxt_month.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

    if intent in ('MY_UPCOMING', None) and scope == 'mine':
        rows = query("""
            SELECT vr.id::text, e.first_name || ' ' || e.last_name AS employee_name,
                   vt.name AS type_name, vt.color,
                   vr.start_date, vr.end_date, vr.status, vr.working_days
            FROM vacation_requests vr
            JOIN employees e ON e.id = vr.employee_id
            JOIN vacation_types vt ON vt.id = vr.vacation_type_id
            WHERE vr.employee_id = %s::uuid
              AND vr.start_date >= %s
            ORDER BY vr.start_date LIMIT %s
        """, (employee_id, today, limit))

    elif intent == 'TEAM_UPCOMING' or scope == 'team':
        rows = query("""
            SELECT vr.id::text, e.first_name || ' ' || e.last_name AS employee_name,
                   vt.name AS type_name, vt.color,
                   vr.start_date, vr.end_date, vr.status, vr.working_days
            FROM vacation_requests vr
            JOIN employees e ON e.id = vr.employee_id
            JOIN manager_relationships mr
                 ON mr.employee_id = vr.employee_id AND mr.manager_id = %s::uuid
                 AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
            JOIN vacation_types vt ON vt.id = vr.vacation_type_id
            WHERE vr.start_date >= %s
            ORDER BY vr.start_date LIMIT %s
        """, (employee_id, today, limit))

    else:
        rows = query("""
            SELECT vr.id::text, e.first_name || ' ' || e.last_name AS employee_name,
                   vt.name AS type_name, vt.color,
                   vr.start_date, vr.end_date, vr.status, vr.working_days
            FROM vacation_requests vr
            JOIN employees e ON e.id = vr.employee_id AND e.company_id = %s::uuid
            JOIN vacation_types vt ON vt.id = vr.vacation_type_id
            WHERE vr.start_date >= %s
            ORDER BY vr.start_date LIMIT %s
        """, (company_id or '', today, limit))

    return [to_dict(r) for r in rows]


# ── Org chart intents ─────────────────────────────────────────────────────────

def search_org(q: str, employee_id: str):
    intent, named = _parse_org_intent(q)
    if intent == 'REPORTING_TO_ME':
        return {'action': 'focus_tree', 'root_id': employee_id,
                'label':  'People reporting to you'}
    if intent == 'NAMED_TEAM' and named:
        rows = query("""
            SELECT e.id::text FROM employees e
            WHERE (e.first_name || ' ' || e.last_name) ILIKE %s
              AND e.employment_status = 'ACTIVE'
            LIMIT 1
        """, (f'%{named}%',))
        if rows:
            return {'action': 'focus_tree', 'root_id': rows[0]['id'],
                    'label':  f"Team of {named}"}
    return None


# ── Unified search ─────────────────────────────────────────────────────────────

def unified_search(q: str, employee_id: str, company_id: str = None):
    results = {
        'employees': search_employees(q, company_id=company_id, limit=8),
        'vacations': search_vacations(q, employee_id=employee_id,
                                      company_id=company_id, scope='mine'),
        'org':       search_org(q, employee_id),
    }
    return results

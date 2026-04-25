import os
import uuid
import datetime

from app.db import query, to_dict

ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}

# Resolve uploads dir relative to project root (one level up from this file)
_BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_DIR  = os.path.join(_BASE_DIR, 'static', 'uploads', 'logos')


def save_logo(file_storage, old_url=None):
    """Save uploaded logo; delete old local file if present. Returns public URL or None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMG:
        return None
    filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(_LOGO_DIR, exist_ok=True)
    file_storage.save(os.path.join(_LOGO_DIR, filename))
    if old_url and old_url.startswith('/static/uploads/logos/'):
        old_path = os.path.join(_BASE_DIR, old_url.lstrip('/'))
        if os.path.isfile(old_path):
            os.remove(old_path)
    return f"/static/uploads/logos/{filename}"


def next_employee_number():
    row = query(
        "SELECT COALESCE(MAX(CAST(SPLIT_PART(employee_number,'-',2) AS INTEGER)), 0) AS n "
        "FROM employees WHERE employee_number ~ '^EMP-[0-9]+$'",
        one=True,
    )
    return f"EMP-{(row['n'] + 1):03d}"


# ── Core employee SELECT ───────────────────────────────────────────────────────

_EMP_SELECT = """
    SELECT
        e.id::text,
        e.employee_number,
        e.first_name || ' ' || e.last_name       AS full_name,
        e.first_name,
        e.last_name,
        e.email,
        COALESCE(e.phone_number, '')              AS phone_number,
        COALESCE(e.job_title, '')                 AS job_title,
        e.employment_status,
        COALESCE(e.employment_type, '')           AS employment_type,
        COALESCE(e.gender, '')                    AS gender,
        e.join_date,
        COALESCE(l.name, '')                      AS location,
        COALESCE(l.office_code, '')               AS office_code,
        COALESCE(bu.name, '')                     AS business_unit,
        COALESCE(bu.code, '')                     AS bu_code,
        COALESCE(fu.name, '')                     AS functional_unit,
        COALESCE(fu.code, '')                     AS fu_code,
        COALESCE(cc.name, '')                     AS cost_center,
        COALESCE(sm_e.first_name || ' ' || sm_e.last_name, '') AS solid_manager_name,
        COALESCE(sm_e.job_title, '')              AS solid_manager_title,
        sm_e.id::text                             AS solid_manager_id,
        COALESCE(dm_e.first_name || ' ' || dm_e.last_name, '') AS dotted_manager_name,
        COALESCE(dm_e.job_title, '')              AS dotted_manager_title,
        COALESCE(sk.skills,  '[]'::json)          AS skills,
        COALESCE(ct.cert_count, 0)                AS cert_count,
        COALESCE(ct.certs,   '[]'::json)          AS certifications
    FROM employees e
    LEFT JOIN employee_org_assignments oa  ON oa.employee_id = e.id AND oa.is_current
    LEFT JOIN locations       l  ON l.id  = oa.location_id
    LEFT JOIN business_units  bu ON bu.id = oa.business_unit_id
    LEFT JOIN functional_units fu ON fu.id = oa.functional_unit_id
    LEFT JOIN cost_centers    cc ON cc.id  = oa.cost_center_id
    LEFT JOIN LATERAL (
        SELECT manager_id FROM manager_relationships
        WHERE employee_id = e.id AND relationship_type = 'SOLID_LINE' AND is_current LIMIT 1
    ) sm ON TRUE
    LEFT JOIN employees sm_e ON sm_e.id = sm.manager_id
    LEFT JOIN LATERAL (
        SELECT manager_id FROM manager_relationships
        WHERE employee_id = e.id AND relationship_type = 'DOTTED_LINE' AND is_current LIMIT 1
    ) dm ON TRUE
    LEFT JOIN employees dm_e ON dm_e.id = dm.manager_id
    LEFT JOIN LATERAL (
        SELECT JSON_AGG(JSON_BUILD_OBJECT(
            'skill_id',      es.skill_id::text,
            'skill',         s.name,
            'category',      sc.name,
            'self_level',    pl_s.level_name,
            'self_level_id', es.self_rating_level_id::text,
            'self_order',    pl_s.level_order,
            'val_level',     COALESCE(pl_v.level_name, ''),
            'val_order',     COALESCE(pl_v.level_order, 0),
            'is_primary',    es.is_primary_skill,
            'status',        es.validation_status
        ) ORDER BY es.is_primary_skill DESC, pl_s.level_order DESC) AS skills
        FROM employee_skills es
        JOIN skills s             ON s.id  = es.skill_id
        JOIN skill_categories sc  ON sc.id = s.skill_category_id
        JOIN proficiency_levels pl_s ON pl_s.id = es.self_rating_level_id
        LEFT JOIN proficiency_levels pl_v ON pl_v.id = es.manager_validated_level_id
        WHERE es.employee_id = e.id
    ) sk ON TRUE
    LEFT JOIN LATERAL (
        SELECT COUNT(*)::int AS cert_count,
               JSON_AGG(JSON_BUILD_OBJECT(
                   'ec_id',    ec.id::text,
                   'cert_id',  ec.certification_id::text,
                   'name',     c.name,
                   'provider', c.provider,
                   'status',   ec.verification_status,
                   'issued',   ec.issued_date,
                   'expiry',   ec.expiry_date,
                   'url',      COALESCE(ec.certificate_url, '')
               )) AS certs
        FROM employee_certifications ec
        JOIN certifications c ON c.id = ec.certification_id
        WHERE ec.employee_id = e.id
    ) ct ON TRUE
"""


def fetch_employees(emp_ids=None):
    if emp_ids is None:
        sql  = _EMP_SELECT + " WHERE e.employment_status='ACTIVE' ORDER BY e.first_name, e.last_name"
        rows = query(sql)
    else:
        if not emp_ids:
            return []
        sql  = _EMP_SELECT + " WHERE e.id = ANY(%s::uuid[]) AND e.employment_status='ACTIVE' ORDER BY e.first_name, e.last_name"
        rows = query(sql, (list(emp_ids),))
    return [to_dict(r) for r in rows]


def direct_report_ids(manager_emp_id, line='SOLID_LINE'):
    rows = query(
        "SELECT employee_id::text FROM manager_relationships "
        "WHERE manager_id = %s::uuid AND relationship_type = %s AND is_current",
        (manager_emp_id, line),
    )
    return [r['employee_id'] for r in rows]


def is_direct_report(manager_emp_id, employee_id):
    row = query(
        "SELECT 1 FROM manager_relationships "
        "WHERE manager_id = %s::uuid AND employee_id = %s::uuid "
        "AND relationship_type = 'SOLID_LINE' AND is_current",
        (manager_emp_id, employee_id),
        one=True,
    )
    return row is not None


# ── Org tree ──────────────────────────────────────────────────────────────────

MGMT_ROLES = ['SYSTEM_ADMIN', 'HR_ADMIN', 'DEPARTMENT_HEAD',
               'LOCATION_HEAD', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER']

TREE_CTE = """
    WITH RECURSIVE tree AS (
        SELECT e.id,
               e.first_name, e.last_name, e.job_title,
               e.employment_type,
               COALESCE(l.name,'')  AS location,
               COALESCE(bu.name,'') AS business_unit,
               NULL::uuid           AS manager_id,
               0                    AS depth
        FROM employees e
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l       ON l.id=oa.location_id
        LEFT JOIN business_units bu ON bu.id=oa.business_unit_id
        WHERE e.id = ANY(%s::uuid[]) AND e.employment_status='ACTIVE'

        UNION ALL

        SELECT e.id,
               e.first_name, e.last_name, e.job_title,
               e.employment_type,
               COALESCE(l.name,'')  AS location,
               COALESCE(bu.name,'') AS business_unit,
               mr.manager_id,
               t.depth + 1
        FROM employees e
        JOIN manager_relationships mr
             ON mr.employee_id = e.id
             AND mr.relationship_type = 'SOLID_LINE'
             AND mr.is_current
        JOIN tree t ON t.id = mr.manager_id
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        LEFT JOIN locations l       ON l.id=oa.location_id
        LEFT JOIN business_units bu ON bu.id=oa.business_unit_id
        WHERE e.employment_status='ACTIVE' AND t.depth < 10
    )
    SELECT id::text, first_name, last_name, job_title, employment_type,
           location, business_unit, manager_id::text, depth
    FROM tree ORDER BY depth, last_name
"""


def build_nested(flat):
    nodes = {r['id']: {**r, 'children': []} for r in flat}
    roots = []
    for r in flat:
        if r['manager_id'] is None or r['manager_id'] not in nodes:
            roots.append(nodes[r['id']])
        else:
            nodes[r['manager_id']]['children'].append(nodes[r['id']])
    return roots


# ── Vacation helpers ──────────────────────────────────────────────────────────

def vacation_types_for_employee(emp_id):
    """Return vacation types the employee is eligible for (location + rules)."""
    emp_info = query(
        "SELECT e.gender, e.join_date, e.company_id::text FROM employees e WHERE e.id=%s::uuid",
        (emp_id,), one=True,
    )
    if not emp_info:
        return []

    types = [to_dict(r) for r in query("""
        SELECT vt.id::text, vt.name, vt.description, vt.max_days_per_year,
               vt.is_paid, vt.color,
               CASE WHEN COALESCE(vtl_count.cnt,0) = 0
                    THEN 'Company-wide' ELSE 'Location-specific' END AS scope
        FROM vacation_types vt
        LEFT JOIN (
            SELECT vacation_type_id, COUNT(*) AS cnt
            FROM vacation_type_locations GROUP BY vacation_type_id
        ) vtl_count ON vtl_count.vacation_type_id = vt.id
        WHERE vt.is_active AND vt.company_id = %s::uuid
          AND (
            COALESCE(vtl_count.cnt,0) = 0
            OR EXISTS (
                SELECT 1 FROM vacation_type_locations vtl2
                JOIN employee_org_assignments oa
                     ON oa.location_id = vtl2.location_id AND oa.is_current
                WHERE vtl2.vacation_type_id = vt.id AND oa.employee_id = %s::uuid
            )
          )
        ORDER BY vt.name
    """, (emp_info['company_id'], emp_id))]

    if not types:
        return []

    type_ids  = [t['id'] for t in types]
    rules_rows = query(
        "SELECT vacation_type_id::text, rule_type, rule_value "
        "FROM vacation_type_rules WHERE vacation_type_id = ANY(%s::uuid[])",
        (type_ids,),
    )

    from collections import defaultdict
    rules_by_type = defaultdict(list)
    for r in rules_rows:
        rules_by_type[r['vacation_type_id']].append(to_dict(r))

    today     = datetime.date.today()
    join_date = emp_info['join_date']
    gender    = (emp_info['gender'] or '').upper()
    tenure_mo = (today - join_date).days / 30.44  if join_date else 0
    tenure_yr = (today - join_date).days / 365.25 if join_date else 0

    eligible = []
    for t in types:
        rules  = rules_by_type.get(t['id'], [])
        passed = True
        for rule in rules:
            rt, rv = rule['rule_type'], rule['rule_value']
            if rt == 'GENDER_EQ':
                if gender != rv.upper():
                    passed = False; break
            elif rt == 'MIN_TENURE_MONTHS':
                if tenure_mo < float(rv):
                    passed = False; break
            elif rt == 'MIN_TENURE_YEARS':
                if tenure_yr < float(rv):
                    passed = False; break
        if passed:
            t['rules']       = rules
            t['rule_labels'] = [rule_label(r) for r in rules]
            eligible.append(t)
    return eligible


def rule_label(rule):
    rt, rv = rule['rule_type'], rule['rule_value']
    if rt == 'GENDER_EQ':         return f'Gender: {rv.title()}'
    if rt == 'MIN_TENURE_MONTHS': return f'Min tenure: {rv} months'
    if rt == 'MIN_TENURE_YEARS':  return f'Min tenure: {rv} year{"s" if float(rv) != 1 else ""}'
    return rt


def employee_solid_manager(emp_id):
    row = query(
        "SELECT manager_id::text FROM manager_relationships "
        "WHERE employee_id = %s::uuid AND relationship_type='SOLID_LINE' AND is_current LIMIT 1",
        (emp_id,), one=True,
    )
    return row['manager_id'] if row else None


def used_days(emp_id, vt_id, year):
    row = query(
        "SELECT COALESCE(SUM(working_days),0)::int AS used FROM vacation_requests "
        "WHERE employee_id=%s::uuid AND vacation_type_id=%s::uuid "
        "AND status IN ('PENDING','APPROVED') AND EXTRACT(YEAR FROM start_date) = %s",
        (emp_id, vt_id, year), one=True,
    )
    return row['used'] if row else 0


def company_stats(company_id):
    return query("""
        SELECT
          COUNT(*)::int                                                    AS total,
          COUNT(*) FILTER (WHERE employment_status='ACTIVE')::int         AS active,
          COUNT(*) FILTER (WHERE employment_type='PERMANENT')::int        AS permanent,
          COUNT(*) FILTER (WHERE employment_type='CONTRACTOR')::int       AS contractors,
          COUNT(DISTINCT oa.business_unit_id)::int                        AS bu_count,
          COUNT(DISTINCT oa.location_id)::int                             AS loc_count
        FROM employees e
        LEFT JOIN employee_org_assignments oa ON oa.employee_id=e.id AND oa.is_current
        WHERE e.company_id = %s::uuid
    """, (company_id,), one=True)

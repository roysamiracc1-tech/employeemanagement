"""Skills Intelligence analytics — compare company skills vs SO 2025 benchmarks."""
from app.db import query, to_dict

_SKILL_CATS = {
    'Programming Languages', 'Databases', 'Web Frameworks',
    'Cloud & DevOps', 'Dev IDEs', 'Large Language Models',
}

# Maps SO benchmark technology names → internal skill names (case-insensitive handled by ILIKE)
# Used to cross-reference employee_skills with survey_benchmarks
_TECH_TO_SKILL = {
    'Python':           'Python',
    'JavaScript':       'JavaScript',
    'TypeScript':       'TypeScript',
    'HTML/CSS':         'HTML/CSS',
    'Java':             'Java',
    'SQL':              'SQL',
    'Bash/Shell':       'Bash/Shell',
    'Go':               'Go',
    'Rust':             'Rust',
    'C#':               '.NET',
    'PHP':              'PHP',
    'Kotlin':           'Kotlin',
    'PostgreSQL':       'PostgreSQL',
    'MySQL':            'MySQL',
    'MongoDB':          'MongoDB',
    'Redis':            'Redis',
    'SQLite':           'SQLite',
    'React':            'React',
    'Node.js':          'Node.js',
    'Angular':          'Angular',
    'Vue.js':           'Vue.js',
    'Next.js':          'Next.js',
    'Django':           'Django',
    'Flask':            'Flask',
    'FastAPI':          'FastAPI',
    'Docker':           'Docker',
    'AWS':              'AWS',
    'Azure':            'Azure',
    'Kubernetes':       'Kubernetes',
    'Terraform':        'Terraform',
    'GCP':              'GCP',
    'GitHub Actions':   'GitHub Actions',
    'Machine Learning': 'Machine Learning',
}


def _scope(company_id: str | None, emp_ids: list | None):
    """Return (where_clause, param) for scoping to company or employee list."""
    if emp_ids is not None:
        return "e.id = ANY(%s::uuid[])", emp_ids
    return "e.company_id = %s::uuid", company_id


def _emp_count(company_id: str | None, emp_ids: list | None = None) -> int:
    wh, param = _scope(company_id, emp_ids)
    wh = wh.replace('e.', '')  # bare table, no alias
    r = query(f"SELECT COUNT(*)::int AS n FROM employees WHERE {wh} AND employment_status='ACTIVE'",
              (param,), one=True)
    return (r or {}).get('n', 1) or 1


# ── KPI summary ───────────────────────────────────────────────────────────────

def get_kpi_summary(company_id: str, emp_ids: list | None = None) -> dict:
    total = _emp_count(company_id, emp_ids)
    wh, sc = _scope(company_id, emp_ids)

    r = query(f"""
        SELECT
            COUNT(DISTINCT es.employee_id)::int              AS emps_with_skills,
            COUNT(*)::int                                     AS total_entries,
            COUNT(DISTINCT es.skill_id)::int                  AS unique_skills,
            COUNT(*) FILTER (WHERE es.validation_status='VALIDATED')::int AS validated,
            ROUND(
                COUNT(DISTINCT es.employee_id)::numeric / %s * 100, 1
            )                                                 AS coverage_pct,
            ROUND(
                AVG(es.years_of_experience), 1
            )                                                 AS avg_yoe
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
    """, (total, sc), one=True) or {}

    val = r.get('validated', 0) or 0
    total_entries = r.get('total_entries', 0) or 0
    return {
        'total_employees':    total,
        'emps_with_skills':   r.get('emps_with_skills', 0) or 0,
        'total_skill_entries': total_entries,
        'unique_skills':      r.get('unique_skills', 0) or 0,
        'coverage_pct':       float(r.get('coverage_pct', 0) or 0),
        'validation_rate':    round(val / total_entries * 100, 1) if total_entries else 0,
        'avg_yoe':            float(r.get('avg_yoe', 0) or 0),
    }


# ── Coverage by skill category ────────────────────────────────────────────────

def get_category_coverage(company_id: str, emp_ids: list | None = None) -> list:
    total = _emp_count(company_id, emp_ids)
    wh, sc = _scope(company_id, emp_ids)
    rows = query(f"""
        SELECT
            sc.name                                           AS category,
            COUNT(DISTINCT es.employee_id)::int               AS emps_with_skill,
            COUNT(DISTINCT es.skill_id)::int                  AS skills_covered,
            ROUND(COUNT(DISTINCT es.employee_id)::numeric / %s * 100, 1) AS coverage_pct
        FROM skill_categories sc
        JOIN skills s ON s.skill_category_id = sc.id
        JOIN employee_skills es ON es.skill_id = s.id
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
        GROUP BY sc.name
        ORDER BY coverage_pct DESC
    """, (total, sc))
    return [to_dict(r) for r in rows]


# ── Top skills (strength) ─────────────────────────────────────────────────────

def get_top_skills(company_id: str, limit: int = 20, emp_ids: list | None = None) -> list:
    total = _emp_count(company_id, emp_ids)
    wh, sc = _scope(company_id, emp_ids)
    rows = query(f"""
        SELECT
            s.name                                            AS skill,
            sc.name                                           AS category,
            COUNT(DISTINCT es.employee_id)::int               AS emp_count,
            ROUND(COUNT(DISTINCT es.employee_id)::numeric / %s * 100, 1) AS company_pct,
            ROUND(AVG(es.years_of_experience), 1)             AS avg_yoe,
            COUNT(*) FILTER (WHERE es.validation_status='VALIDATED')::int AS validated_count
        FROM employee_skills es
        JOIN skills s ON s.id = es.skill_id
        JOIN skill_categories sc ON sc.id = s.skill_category_id
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
        GROUP BY s.name, sc.name
        ORDER BY emp_count DESC
        LIMIT %s
    """, (total, sc, limit))
    return [to_dict(r) for r in rows]


# ── Benchmark gap analysis ────────────────────────────────────────────────────

def get_benchmark_gaps(company_id: str, year: int = 2025, emp_ids: list | None = None) -> list:
    """For each SO benchmark technology (skill-crossmatchable), compare company % vs industry %."""
    total = _emp_count(company_id, emp_ids)
    wh, sc = _scope(company_id, emp_ids)

    bench_rows = query("""
        SELECT technology, usage_pct, desired_pct, admired_pct,
               category, sankey_role, rank_in_category
        FROM survey_benchmarks
        WHERE survey_year = %s
          AND category IN (
            'Programming Languages','Databases','Web Frameworks',
            'Cloud & DevOps','Dev IDEs','Large Language Models'
          )
          AND context = 'all_respondents'
        ORDER BY category, rank_in_category
    """, (year,))
    bench = [to_dict(r) for r in bench_rows]

    # Build company skill counts indexed by lowercase name
    skill_counts = query(f"""
        SELECT s.name AS skill_name,
               COUNT(DISTINCT es.employee_id)::int AS emp_count
        FROM employee_skills es
        JOIN skills s ON s.id = es.skill_id
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
        GROUP BY s.name
    """, (sc,))
    company_map = {r['skill_name'].lower(): r['emp_count'] for r in skill_counts}

    result = []
    for b in bench:
        tech = b['technology']
        mapped = _TECH_TO_SKILL.get(tech, tech)
        emp_count = company_map.get(mapped.lower(), 0)
        company_pct = round(emp_count / total * 100, 1)
        bench_pct = float(b.get('usage_pct') or 0)
        gap = round(bench_pct - company_pct, 1)

        result.append({
            'technology':     tech,
            'category':       b['category'],
            'bench_pct':      bench_pct,
            'company_pct':    company_pct,
            'emp_count':      emp_count,
            'gap':            gap,
            'desired_pct':    float(b.get('desired_pct') or 0),
            'admired_pct':    float(b.get('admired_pct') or 0),
            'sankey_role':    b.get('sankey_role'),
            'rank':           b.get('rank_in_category'),
            'signal': (
                'strength'  if company_pct >= bench_pct * 0.9 else
                'near'      if company_pct >= bench_pct * 0.5 else
                'gap'       if bench_pct > 0 else
                'not_in_benchmark'
            ),
        })

    return result


# ── Proficiency heatmap (skill × proficiency_level) ──────────────────────────

def get_proficiency_heatmap(company_id: str, emp_ids: list | None = None) -> dict:
    """Returns skills × proficiency matrix for top 15 skills."""
    wh, sc = _scope(company_id, emp_ids)
    rows = query(f"""
        SELECT s.name AS skill, pl.level_name AS level,
               COUNT(DISTINCT es.employee_id)::int AS cnt
        FROM employee_skills es
        JOIN skills s ON s.id = es.skill_id
        JOIN proficiency_levels pl ON pl.id = es.self_rating_level_id
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
        GROUP BY s.name, pl.level_name, pl.level_order
        ORDER BY s.name, pl.level_order
    """, (sc,))

    # Aggregate into {skill: {level: count}}
    matrix = {}
    for r in rows:
        s, lvl, cnt = r['skill'], r['level'], r['cnt']
        matrix.setdefault(s, {'Beginner': 0, 'Intermediate': 0, 'Advanced': 0, 'Expert': 0})
        matrix[s][lvl] = cnt

    # Pick top 15 by total headcount
    ranked = sorted(matrix.items(), key=lambda x: sum(x[1].values()), reverse=True)[:15]
    skills = [s for s, _ in ranked]
    levels = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
    data = {lvl: [matrix[s].get(lvl, 0) for s in skills] for lvl in levels}

    return {'skills': skills, 'levels': levels, 'data': data}


# ── Trend alignment — desired vs company adoption ────────────────────────────

def get_trend_alignment(company_id: str, year: int = 2025, emp_ids: list | None = None) -> list:
    """Compare desired_pct (what devs want) vs company adoption — find emerging opportunities."""
    total = _emp_count(company_id, emp_ids)
    wh, sc = _scope(company_id, emp_ids)

    bench = query("""
        SELECT technology, desired_pct, usage_pct, category, sankey_role
        FROM survey_benchmarks
        WHERE survey_year = %s AND desired_pct > 0
          AND category IN (
            'Programming Languages','Databases','Web Frameworks','Cloud & DevOps'
          )
          AND context = 'all_respondents'
        ORDER BY desired_pct DESC
        LIMIT 30
    """, (year,))

    skill_counts = query(f"""
        SELECT s.name AS skill_name,
               COUNT(DISTINCT es.employee_id)::int AS emp_count
        FROM employee_skills es
        JOIN skills s ON s.id = es.skill_id
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
        GROUP BY s.name
    """, (sc,))
    company_map = {r['skill_name'].lower(): r['emp_count'] for r in skill_counts}

    result = []
    for b in [to_dict(r) for r in bench]:
        tech = b['technology']
        mapped = _TECH_TO_SKILL.get(tech, tech)
        emp_count = company_map.get(mapped.lower(), 0)
        company_pct = round(emp_count / total * 100, 1)
        desired = float(b.get('desired_pct') or 0)
        opportunity_score = round(desired - company_pct, 1)

        result.append({
            'technology':       tech,
            'category':         b['category'],
            'desired_pct':      desired,
            'company_pct':      company_pct,
            'opportunity_score': opportunity_score,
            'sankey_role':      b.get('sankey_role'),
            'quadrant': (
                'invest'       if desired >= 20 and company_pct < 20 else
                'leverage'     if desired >= 20 and company_pct >= 20 else
                'monitor'      if desired < 20  and company_pct < 10 else
                'maintain'
            ),
        })
    return sorted(result, key=lambda x: -x['opportunity_score'])


# ── Department skill coverage ─────────────────────────────────────────────────

def get_job_title_coverage(company_id: str, emp_ids: list | None = None) -> list:
    """Top 10 job titles + their skill coverage."""
    wh, sc = _scope(company_id, emp_ids)
    rows = query(f"""
        SELECT
            e.job_title,
            COUNT(DISTINCT e.id)::int                          AS headcount,
            COUNT(DISTINCT es.employee_id)::int                AS with_skills,
            COUNT(DISTINCT es.skill_id)::int                   AS unique_skills,
            ROUND(COUNT(DISTINCT es.employee_id)::numeric /
                  NULLIF(COUNT(DISTINCT e.id),0) * 100, 1)    AS coverage_pct
        FROM employees e
        LEFT JOIN employee_skills es ON es.employee_id = e.id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
          AND e.job_title IS NOT NULL
        GROUP BY e.job_title
        ORDER BY headcount DESC
        LIMIT 10
    """, (sc,))
    return [to_dict(r) for r in rows]


# ── Validation funnel ─────────────────────────────────────────────────────────

def get_validation_funnel(company_id: str, emp_ids: list | None = None) -> list:
    wh, sc = _scope(company_id, emp_ids)
    rows = query(f"""
        SELECT es.validation_status, COUNT(*)::int AS cnt
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
        GROUP BY es.validation_status
        ORDER BY cnt DESC
    """, (sc,))
    return [to_dict(r) for r in rows]


# ── Skill growth over time (entries created per month) ───────────────────────

def get_skill_growth(company_id: str, emp_ids: list | None = None) -> list:
    wh, sc = _scope(company_id, emp_ids)
    rows = query(f"""
        SELECT
            TO_CHAR(DATE_TRUNC('month', es.created_at), 'YYYY-MM') AS month,
            COUNT(*)::int AS new_entries
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        WHERE {wh} AND e.employment_status = 'ACTIVE'
          AND es.created_at >= NOW() - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', es.created_at)
        ORDER BY 1
    """, (sc,))
    return [to_dict(r) for r in rows]

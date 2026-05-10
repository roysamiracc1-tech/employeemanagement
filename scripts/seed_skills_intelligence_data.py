"""Seed realistic skills data for Skills Intelligence dashboard.

Adds ~20 new skills (aligned with SO 2025 benchmarks) and seeds:
  - Telia (100 employees): full realistic distribution
  - Acme (46 employees): supplemental skills for benchmark-aligned coverage

Run:  python3 scripts/seed_skills_intelligence_data.py
Safe to re-run (INSERT ... ON CONFLICT DO NOTHING for skills; deletes + re-inserts employee skills).
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from app.db import query, execute, to_dict

random.seed(42)

# ── Constants ─────────────────────────────────────────────────────────────────

ACME_ID  = '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c'
TELIA_ID = '05a3fddb-0add-4a76-87c7-6bf0d84d214d'

# Existing skill_category IDs (from DB)
CATS = {
    'Backend':          'd119252a-1234-0000-0000-000000000000',
    'Cloud':            '434d4b12-1234-0000-0000-000000000000',
    'DataEngineering':  '47196fba-1234-0000-0000-000000000000',
    'DevOps':           'ae4dac1a-1234-0000-0000-000000000000',
    'Frontend':         'cd2ede12-1234-0000-0000-000000000000',
    'Leadership':       '8bf65f1a-1234-0000-0000-000000000000',
    'QA':               '3c0bb20d-1234-0000-0000-000000000000',
    'Security':         '103398e4-1234-0000-0000-000000000000',
}

# ── New skills to insert (name -> category key) ───────────────────────────────

NEW_SKILLS = [
    ('JavaScript',       'Frontend'),
    ('HTML/CSS',         'Frontend'),
    ('Vue.js',           'Frontend'),
    ('Angular',          'Frontend'),
    ('Next.js',          'Frontend'),
    ('Node.js',          'Backend'),
    ('Django',           'Backend'),
    ('Flask',            'Backend'),
    ('FastAPI',          'Backend'),
    ('Go',               'Backend'),
    ('Rust',             'Backend'),
    ('SQL',              'Backend'),
    ('PostgreSQL',       'Backend'),
    ('MySQL',            'Backend'),
    ('MongoDB',          'Data Engineering'),
    ('Redis',            'Data Engineering'),
    ('Machine Learning', 'Data Engineering'),
    ('Bash/Shell',       'DevOps'),
    ('GitHub Actions',   'DevOps'),
    ('Ansible',          'DevOps'),
]

# ── Skill population model per company ────────────────────────────────────────
# Each entry: (skill_name, % of employees who have it, proficiency_weights)
# proficiency_weights: [Beginner, Intermediate, Advanced, Expert]

TELIA_DIST = [
    # Foundational — most developers have these
    ('Python',           0.68, [0.10, 0.35, 0.38, 0.17]),
    ('JavaScript',       0.72, [0.08, 0.32, 0.42, 0.18]),
    ('SQL',              0.60, [0.12, 0.38, 0.35, 0.15]),
    ('HTML/CSS',         0.65, [0.08, 0.30, 0.45, 0.17]),
    # Frontend
    ('React',            0.45, [0.12, 0.35, 0.38, 0.15]),
    ('TypeScript',       0.42, [0.15, 0.38, 0.35, 0.12]),
    ('Vue.js',           0.20, [0.20, 0.42, 0.30, 0.08]),
    ('Angular',          0.18, [0.18, 0.40, 0.32, 0.10]),
    ('Next.js',          0.25, [0.22, 0.40, 0.30, 0.08]),
    # Backend
    ('Node.js',          0.38, [0.12, 0.38, 0.38, 0.12]),
    ('Django',           0.22, [0.18, 0.40, 0.32, 0.10]),
    ('Flask',            0.20, [0.18, 0.42, 0.30, 0.10]),
    ('FastAPI',          0.18, [0.22, 0.42, 0.28, 0.08]),
    ('Java',             0.35, [0.10, 0.30, 0.40, 0.20]),
    ('Go',               0.14, [0.25, 0.40, 0.28, 0.07]),
    ('Rust',             0.08, [0.35, 0.42, 0.18, 0.05]),
    ('PostgreSQL',       0.40, [0.15, 0.38, 0.35, 0.12]),
    ('MySQL',            0.30, [0.15, 0.38, 0.35, 0.12]),
    ('MongoDB',          0.25, [0.18, 0.40, 0.32, 0.10]),
    # Cloud / DevOps
    ('Docker',           0.55, [0.10, 0.32, 0.40, 0.18]),
    ('AWS',              0.45, [0.12, 0.35, 0.38, 0.15]),
    ('Azure',            0.30, [0.15, 0.38, 0.35, 0.12]),
    ('Kubernetes',       0.30, [0.18, 0.38, 0.32, 0.12]),
    ('Terraform',        0.22, [0.20, 0.40, 0.30, 0.10]),
    ('CI/CD',            0.42, [0.12, 0.35, 0.38, 0.15]),
    ('Bash/Shell',       0.45, [0.10, 0.35, 0.38, 0.17]),
    ('GitHub Actions',   0.35, [0.15, 0.38, 0.35, 0.12]),
    ('GCP',              0.18, [0.20, 0.42, 0.28, 0.10]),
    # Data / ML
    ('Redis',            0.22, [0.20, 0.42, 0.28, 0.10]),
    ('Kafka',            0.15, [0.22, 0.42, 0.28, 0.08]),
    ('Machine Learning', 0.20, [0.25, 0.40, 0.28, 0.07]),
    # Leadership / PM
    ('Agile',            0.55, [0.08, 0.28, 0.42, 0.22]),
    ('Project Management', 0.30, [0.12, 0.32, 0.40, 0.16]),
]

ACME_SUPPLEMENT = [
    # Skills Acme likely lacks (bridge SO benchmark gaps)
    ('JavaScript',       0.55, [0.08, 0.32, 0.42, 0.18]),
    ('HTML/CSS',         0.50, [0.10, 0.32, 0.42, 0.16]),
    ('SQL',              0.55, [0.12, 0.38, 0.35, 0.15]),
    ('Node.js',          0.30, [0.15, 0.38, 0.35, 0.12]),
    ('PostgreSQL',       0.35, [0.15, 0.38, 0.35, 0.12]),
    ('Go',               0.12, [0.28, 0.42, 0.24, 0.06]),
    ('Rust',             0.06, [0.38, 0.42, 0.15, 0.05]),
    ('FastAPI',          0.15, [0.22, 0.42, 0.28, 0.08]),
    ('Machine Learning', 0.18, [0.25, 0.40, 0.28, 0.07]),
    ('GitHub Actions',   0.28, [0.18, 0.40, 0.32, 0.10]),
    ('Bash/Shell',       0.40, [0.10, 0.35, 0.38, 0.17]),
    ('MongoDB',          0.20, [0.20, 0.42, 0.28, 0.10]),
    ('MySQL',            0.25, [0.15, 0.40, 0.35, 0.10]),
]


def get_or_create_skills(skill_name_cat_map):
    """Return {name: id_str} for all skills, inserting new ones."""
    existing = {r['name']: r['id'] for r in
                [to_dict(x) for x in query("SELECT id::text AS id, name FROM skills")]}

    for name, cat_key in skill_name_cat_map:
        if name not in existing:
            # Resolve category id from DB
            cat_row = query("SELECT id::text FROM skill_categories WHERE name = %s", (cat_key,), one=True)
            if not cat_row:
                print(f"  WARN: category '{cat_key}' not found, skipping skill '{name}'")
                continue
            cat_id = cat_row['id']
            execute("""
                INSERT INTO skills (skill_category_id, name, is_active)
                VALUES (%s::uuid, %s, TRUE)
                ON CONFLICT (name) DO NOTHING
            """, (cat_id, name))
            new_row = query("SELECT id::text FROM skills WHERE name=%s", (name,), one=True)
            if new_row:
                existing[name] = new_row['id']
                print(f"  + added skill: {name}")

    return existing


def pick_proficiency(weights, prof_ids):
    """Return a proficiency_level_id sampled from weights list [B, I, A, E]."""
    levels = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
    chosen = random.choices(levels, weights=weights)[0]
    return prof_ids[chosen]


def seed_company(company_id, dist, skill_ids, prof_ids, label):
    emp_rows = query(
        "SELECT id::text FROM employees WHERE company_id=%s::uuid AND employment_status='ACTIVE'",
        (company_id,))
    emp_ids = [r['id'] for r in emp_rows]
    if not emp_ids:
        print(f"  WARN: no active employees for {label}")
        return

    # Remove existing seeded entries (keep only non-benchmark ones if any, but here we rebuild all)
    execute(
        "DELETE FROM employee_skills WHERE employee_id IN "
        "(SELECT id FROM employees WHERE company_id=%s::uuid AND employment_status='ACTIVE')",
        (company_id,))
    print(f"  Cleared existing employee_skills for {label} ({len(emp_ids)} employees)")

    inserted = 0
    for skill_name, pct, prof_w in dist:
        sid = skill_ids.get(skill_name)
        if not sid:
            print(f"  SKIP: skill '{skill_name}' not found")
            continue

        chosen = random.sample(emp_ids, k=int(len(emp_ids) * pct))
        for eid in chosen:
            prof_id = pick_proficiency(prof_w, prof_ids)
            yoe = round(random.uniform(0.5, 10.0), 1)
            is_primary = random.random() < 0.30
            val_status = random.choices(
                ['VALIDATED', 'PENDING_MANAGER_VALIDATION', 'SELF_ASSESSED', 'REJECTED'],
                weights=[0.50, 0.25, 0.20, 0.05])[0]
            execute("""
                INSERT INTO employee_skills
                    (employee_id, skill_id, self_rating_level_id,
                     years_of_experience, is_primary_skill, validation_status)
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s)
                ON CONFLICT (employee_id, skill_id) DO NOTHING
            """, (eid, sid, prof_id, yoe, is_primary, val_status))
            inserted += 1

    print(f"  {label}: inserted {inserted} employee_skill rows for {len(emp_ids)} employees")


def run():
    with app.app_context():
        print("=== Skills Intelligence Data Seed ===\n")

        # 1. Get/create all needed skills
        print("Step 1: Ensuring skills exist...")
        skill_ids = get_or_create_skills(NEW_SKILLS)
        total_skills = query("SELECT COUNT(*) AS n FROM skills", one=True)['n']
        print(f"  Skills in DB: {total_skills}")

        # 2. Build proficiency id map
        prof_rows = query("SELECT id::text AS id, level_name FROM proficiency_levels")
        prof_ids = {r['level_name']: r['id'] for r in [to_dict(p) for p in prof_rows]}
        print(f"  Proficiency levels: {list(prof_ids.keys())}")

        # 3. Seed Telia
        print("\nStep 2: Seeding Telia...")
        seed_company(TELIA_ID, TELIA_DIST, skill_ids, prof_ids, "Telia")

        # 4. Supplement Acme
        print("\nStep 3: Supplementing Acme...")
        seed_company(ACME_ID, ACME_SUPPLEMENT, skill_ids, prof_ids, "Acme")

        # 5. Summary
        print("\n=== Summary ===")
        for company_id, label in [(TELIA_ID, 'Telia'), (ACME_ID, 'Acme')]:
            r = query("""
                SELECT
                    COUNT(DISTINCT es.employee_id) AS emps_with_skills,
                    COUNT(*) AS total_entries,
                    COUNT(DISTINCT es.skill_id) AS unique_skills
                FROM employee_skills es
                JOIN employees e ON e.id = es.employee_id
                WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
            """, (company_id,), one=True)
            print(f"  {label}: {r['emps_with_skills']} employees, "
                  f"{r['total_entries']} entries, {r['unique_skills']} unique skills")


if __name__ == '__main__':
    run()

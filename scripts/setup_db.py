#!/usr/bin/env python3
"""
One-shot DB setup script — safe to run multiple times.

What it does:
  1. Apply schema migration  (add company_id to org tables, PORTAL_ADMIN role,
                               portal_features + role_feature_access tables)
  2. Backfill company_id     (set BU / location / FU → the company their employees belong to)
  3. Fix Tech Admin          (set SYSTEM_ADMIN employee's company_id = NULL)
  4. Seed Telia employees    (100 employees, using the actual Telia UUID in the DB)
  5. Seed portal_features    + default role_feature_access rows
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2, psycopg2.extras
from app.config import DB_CONFIG


def conn():
    c = psycopg2.connect(**DB_CONFIG)
    c.autocommit = False
    return c


def run(cur, sql, params=()):
    cur.execute(sql, params)


# ─────────────────────────────────────────────────────────────────────────────
def step1_migrate(cur):
    """Add company_id column to org tables + new role/feature tables."""
    cur.execute("ALTER TABLE business_units  ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE")
    cur.execute("ALTER TABLE locations        ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE")
    cur.execute("ALTER TABLE functional_units ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE")

    cur.execute("""INSERT INTO roles (name, description)
        VALUES ('PORTAL_ADMIN', 'Full administrative access within their assigned company')
        ON CONFLICT (name) DO NOTHING""")

    cur.execute("""CREATE TABLE IF NOT EXISTS portal_features (
        id         UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
        code       VARCHAR(100) UNIQUE NOT NULL,
        label      VARCHAR(150) NOT NULL,
        description TEXT,
        sort_order INT NOT NULL DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS role_feature_access (
        role_id    UUID    NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        feature_id UUID    NOT NULL REFERENCES portal_features(id) ON DELETE CASCADE,
        can_read   BOOLEAN NOT NULL DEFAULT FALSE,
        can_write  BOOLEAN NOT NULL DEFAULT FALSE,
        can_delete BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (role_id, feature_id)
    )""")
    print("  ✓ Schema migration applied")


# ─────────────────────────────────────────────────────────────────────────────
def step2_backfill(cur):
    """Set company_id on BU / location / FU rows that are still NULL,
       by looking at which company the employees assigned to them belong to."""

    for table, fk_col in [
        ('business_units',  'business_unit_id'),
        ('locations',       'location_id'),
        ('functional_units', 'functional_unit_id'),
    ]:
        cur.execute(f"""
            UPDATE {table} t
            SET company_id = (
                SELECT e.company_id
                FROM employee_org_assignments oa
                JOIN employees e ON e.id = oa.employee_id
                WHERE oa.{fk_col} = t.id AND e.company_id IS NOT NULL
                GROUP BY e.company_id ORDER BY COUNT(*) DESC LIMIT 1
            )
            WHERE t.company_id IS NULL
        """)
        print(f"  ✓ Backfilled {cur.rowcount} {table} rows")


# ─────────────────────────────────────────────────────────────────────────────
def step3_fix_tech_admin(cur):
    """Remove Tech Admin from any company (SYSTEM_ADMIN should be company-agnostic)."""
    cur.execute("""
        UPDATE employees e
        SET company_id = NULL
        WHERE e.id IN (
            SELECT u.employee_id FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id
            WHERE r.name = 'SYSTEM_ADMIN'
        )
    """)
    print(f"  ✓ Unlinked {cur.rowcount} Tech Admin employee(s) from company")


# ─────────────────────────────────────────────────────────────────────────────
def step4_seed_portal_features(cur):
    """Insert the 8 portal feature areas and default role → feature access rows."""
    features = [
        ('employee_profiles', 'Employee Profiles',      'View and manage employee personal, role and org data',      1),
        ('org_structure',     'Organisation Structure',  'Manage business units, locations and functional units',     2),
        ('user_accounts',     'User Accounts',           'Create, enable/disable and assign roles to portal users',   3),
        ('skills',            'Skills & Certifications', 'View, validate and manage skill profiles',                  4),
        ('vacations',         'Vacations & Leave',       'Manage vacation types, entitlements and leave requests',    5),
        ('reports',           'Reports & Analytics',     'Access competency dashboards and analytics',                6),
        ('company_settings',  'Company Settings',        'Edit company branding, logo, theme and metadata',           7),
        ('system_config',     'System Configuration',    'Widget settings and global platform config',                8),
    ]
    for code, label, desc, order in features:
        cur.execute(
            "INSERT INTO portal_features (code,label,description,sort_order) VALUES (%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING",
            (code, label, desc, order)
        )

    # Default access matrix
    access_map = {
        'EMPLOYEE':            [('employee_profiles', True, False, False)],
        'SOLID_LINE_MANAGER':  [('employee_profiles', True, True,  False),
                                ('skills',            True, True,  True),
                                ('reports',           True, False, False)],
        'DOTTED_LINE_MANAGER': [('employee_profiles', True, False, False),
                                ('reports',           True, False, False)],
        'HIRING_MANAGER':      [('employee_profiles', True, False, False),
                                ('reports',           True, False, False)],
        'DEPARTMENT_HEAD':     [('employee_profiles', True, True,  False),
                                ('org_structure',     True, False, False),
                                ('skills',            True, True,  False),
                                ('reports',           True, False, False)],
        'LOCATION_HEAD':       [('employee_profiles', True, False, False),
                                ('reports',           True, False, False)],
        'HR_ADMIN':            [('employee_profiles', True, True,  True),
                                ('org_structure',     True, True,  True),
                                ('skills',            True, True,  True),
                                ('vacations',         True, True,  True),
                                ('reports',           True, True,  False)],
        'PORTAL_ADMIN':        [('employee_profiles', True, True,  True),
                                ('org_structure',     True, True,  True),
                                ('user_accounts',     True, True,  True),
                                ('skills',            True, True,  True),
                                ('vacations',         True, True,  True),
                                ('reports',           True, True,  False),
                                ('company_settings',  True, True,  False)],
    }
    for role_name, perms in access_map.items():
        for feat_code, r, w, d in perms:
            cur.execute("""
                INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
                SELECT ro.id, f.id, %s, %s, %s
                FROM roles ro, portal_features f
                WHERE ro.name=%s AND f.code=%s
                ON CONFLICT (role_id, feature_id) DO NOTHING
            """, (r, w, d, role_name, feat_code))

    # SYSTEM_ADMIN gets everything
    cur.execute("""
        INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
        SELECT r.id, f.id, TRUE, TRUE, TRUE FROM roles r, portal_features f
        WHERE r.name='SYSTEM_ADMIN'
        ON CONFLICT (role_id, feature_id) DO NOTHING
    """)
    print("  ✓ Portal features and default permissions seeded")


# ─────────────────────────────────────────────────────────────────────────────
def step5_seed_telia(cur):
    """Seed 100 Telia employees using the actual Telia company UUID from the DB."""
    cur.execute("SELECT id::text FROM companies WHERE name ILIKE 'telia%' LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("  ⚠  No 'Telia' company found — skipping Telia seed")
        return
    telia_id = row['id']
    print(f"  Using Telia company: {telia_id}")

    cur.execute("SELECT COUNT(*) AS c FROM employees WHERE email LIKE '%@telia.com'")
    existing = cur.fetchone()['c']
    if existing >= 90:
        print(f"  ✓ Telia employees already seeded ({existing} found) — skipping")
        return

    # ── BUs ────────────────────────────────────────────────────────────────
    bus = [
        ('TELI-TECH', 'Technology & Innovation', 'Software engineering, data, AI and cybersecurity'),
        ('TELI-COMM', 'Commercial & Sales',       'Enterprise, consumer sales and digital marketing'),
        ('TELI-FIN',  'Finance & Administration', 'Financial control, treasury and procurement'),
        ('TELI-HR',   'People & Culture',         'Talent acquisition, L&D and employee experience'),
        ('TELI-OPS',  'Network & Operations',     'Network engineering and cloud infrastructure'),
    ]
    bu_ids = {}
    for code, name, desc in bus:
        cur.execute("""
            INSERT INTO business_units (name, code, description, company_id)
            VALUES (%s, %s, %s, %s::uuid)
            ON CONFLICT (code) DO UPDATE SET company_id = EXCLUDED.company_id
            RETURNING id::text
        """, (name, code, desc, telia_id))
        bu_ids[code] = cur.fetchone()['id']

    # ── Locations ──────────────────────────────────────────────────────────
    locs = [
        ('TELI-STO', 'Stockholm HQ', 'Sweden',  'Stockholm'),
        ('TELI-HEL', 'Helsinki',     'Finland', 'Helsinki'),
        ('TELI-OSL', 'Oslo',         'Norway',  'Oslo'),
        ('TELI-CPH', 'Copenhagen',   'Denmark', 'Copenhagen'),
        ('TELI-TLL', 'Tallinn',      'Estonia', 'Tallinn'),
    ]
    loc_ids = {}
    for code, name, country, city in locs:
        cur.execute("""
            INSERT INTO locations (name, country, city, office_code, company_id)
            VALUES (%s, %s, %s, %s, %s::uuid)
            ON CONFLICT (office_code) DO UPDATE SET company_id = EXCLUDED.company_id
            RETURNING id::text
        """, (name, country, city, code, telia_id))
        loc_ids[code] = cur.fetchone()['id']

    # ── Functional Units ───────────────────────────────────────────────────
    fus_data = [
        ('TELI-SWE', 'Software Engineering', 'Backend, frontend and mobile', 'TELI-TECH'),
        ('TELI-DAI', 'Data & AI',            'Data eng, ML and AI products', 'TELI-TECH'),
        ('TELI-SEC', 'Cybersecurity',         'Security architecture and ops','TELI-TECH'),
        ('TELI-PRD', 'Product Management',    'Product strategy and roadmap', 'TELI-TECH'),
        ('TELI-ENT', 'Enterprise Sales',      'B2B enterprise accounts',      'TELI-COMM'),
        ('TELI-CON', 'Consumer Sales',        'Consumer and SMB sales',       'TELI-COMM'),
        ('TELI-MKT', 'Digital Marketing',     'Performance and brand mktg',   'TELI-COMM'),
        ('TELI-FIN', 'Financial Control',     'Accounting and reporting',     'TELI-FIN'),
        ('TELI-PRO', 'Procurement',           'Strategic sourcing',           'TELI-FIN'),
        ('TELI-TAL', 'Talent Acquisition',    'Recruitment & employer brand', 'TELI-HR'),
        ('TELI-NET', 'Network Engineering',   '4G/5G network design',         'TELI-OPS'),
        ('TELI-INF', 'Infrastructure',        'Cloud and SRE',                'TELI-OPS'),
    ]
    fu_ids = {}
    for code, name, desc, bu_code in fus_data:
        cur.execute("""
            INSERT INTO functional_units (name, code, description, business_unit_id, company_id)
            VALUES (%s, %s, %s, %s::uuid, %s::uuid)
            ON CONFLICT (code) DO UPDATE SET company_id = EXCLUDED.company_id
            RETURNING id::text
        """, (name, code, desc, bu_ids[bu_code], telia_id))
        fu_ids[code] = cur.fetchone()['id']

    # ── Employees ──────────────────────────────────────────────────────────
    # Columns: (emp_num, first, last, email, title, join_date, bu_code, fu_code, loc_code)
    employees = [
        # C-Suite
        ('TELI-001','Erik',     'Lindqvist', 'erik.lindqvist@telia.com',    'Chief Executive Officer',       '2015-03-01', None,        None,       'TELI-STO'),
        ('TELI-002','Anna',     'Svensson',  'anna.svensson@telia.com',     'Chief Technology Officer',      '2017-06-01', None,        None,       'TELI-STO'),
        ('TELI-003','Lars',     'Bergström', 'lars.bergstrom@telia.com',    'Chief Financial Officer',       '2016-01-01', None,        None,       'TELI-STO'),
        ('TELI-004','Maria',    'Andersson', 'maria.andersson@telia.com',   'Chief People Officer',          '2018-09-01', None,        None,       'TELI-STO'),
        ('TELI-005','Johan',    'Nilsson',   'johan.nilsson@telia.com',     'Chief Commercial Officer',      '2019-02-01', None,        None,       'TELI-STO'),
        # VPs
        ('TELI-006','Sofia',    'Johansson', 'sofia.johansson@telia.com',   'VP Software Engineering',       '2018-04-01', 'TELI-TECH', 'TELI-SWE','TELI-STO'),
        ('TELI-007','Marcus',   'Pettersson','marcus.pettersson@telia.com', 'VP Data & AI',                  '2019-07-01', 'TELI-TECH', 'TELI-DAI','TELI-STO'),
        ('TELI-008','Emma',     'Eriksson',  'emma.eriksson@telia.com',     'VP Cybersecurity',              '2020-01-01', 'TELI-TECH', 'TELI-SEC','TELI-STO'),
        ('TELI-009','Oliver',   'Karlsson',  'oliver.karlsson@telia.com',   'VP Product Management',         '2019-11-01', 'TELI-TECH', 'TELI-PRD','TELI-STO'),
        ('TELI-010','Isabelle', 'Larsson',   'isabelle.larsson@telia.com',  'VP Enterprise Sales',           '2018-08-01', 'TELI-COMM', 'TELI-ENT','TELI-OSL'),
        ('TELI-011','Alexander','Olsson',    'alexander.olsson@telia.com',  'VP Consumer Sales',             '2017-10-01', 'TELI-COMM', 'TELI-CON','TELI-HEL'),
        ('TELI-012','Victoria', 'Persson',   'victoria.persson@telia.com',  'VP Digital Marketing',          '2020-03-01', 'TELI-COMM', 'TELI-MKT','TELI-STO'),
        ('TELI-013','William',  'Söderström','william.soderstrom@telia.com','VP Financial Control',          '2018-05-01', 'TELI-FIN',  'TELI-FIN','TELI-STO'),
        ('TELI-014','Charlotte','Lindström', 'charlotte.lindstrom@telia.com','VP Procurement',               '2019-04-01', 'TELI-FIN',  'TELI-PRO','TELI-STO'),
        ('TELI-015','Felix',    'Magnusson', 'felix.magnusson@telia.com',   'VP Talent & Culture',           '2020-06-01', 'TELI-HR',   'TELI-TAL','TELI-STO'),
        ('TELI-016','William',  'Tamm',      'william.tamm@telia.com',      'VP Network & Infrastructure',   '2018-02-01', 'TELI-OPS',  'TELI-NET','TELI-STO'),
        # Software Engineering
        ('TELI-017','Linnea',   'Bergström', 'linnea.bergstrom@telia.com',  'Principal Software Engineer',   '2019-09-01', 'TELI-TECH', 'TELI-SWE','TELI-STO'),
        ('TELI-018','Thomas',   'Nielsen',   'thomas.nielsen@telia.com',    'Engineering Manager',           '2020-02-01', 'TELI-TECH', 'TELI-SWE','TELI-HEL'),
        ('TELI-019','Alexander','Nilsson',   'alexander.nilsson@telia.com', 'Senior Software Engineer',      '2020-08-01', 'TELI-TECH', 'TELI-SWE','TELI-HEL'),
        ('TELI-020','Amanda',   'Svensson',  'amanda.svensson@telia.com',   'Senior Software Engineer',      '2021-01-01', 'TELI-TECH', 'TELI-SWE','TELI-STO'),
        ('TELI-021','Frida',    'Andersen',  'frida.andersen@telia.com',    'Senior Software Engineer',      '2020-05-01', 'TELI-TECH', 'TELI-SWE','TELI-HEL'),
        ('TELI-022','Daniel',   'Gustafsson','daniel.gustafsson@telia.com', 'Software Engineer',             '2021-06-01', 'TELI-TECH', 'TELI-SWE','TELI-STO'),
        ('TELI-023','Julia',    'Andersson', 'julia.andersson@telia.com',   'Software Engineer',             '2022-01-01', 'TELI-TECH', 'TELI-SWE','TELI-HEL'),
        ('TELI-024','Viktor',   'Hansson',   'viktor.hansson@telia.com',    'Software Engineer',             '2022-03-01', 'TELI-TECH', 'TELI-SWE','TELI-TLL'),
        ('TELI-025','Sebastian','Hansen',    'sebastian.hansen@telia.com',  'Software Engineer',             '2021-11-01', 'TELI-TECH', 'TELI-SWE','TELI-STO'),
        ('TELI-026','Cecilia',  'Andersen',  'cecilia.andersen@telia.com',  'Software Engineer',             '2022-06-01', 'TELI-TECH', 'TELI-SWE','TELI-TLL'),
        ('TELI-027','Mattias',  'Jakobsson', 'mattias.jakobsson@telia.com', 'Junior Developer',              '2023-01-01', 'TELI-TECH', 'TELI-SWE','TELI-STO'),
        ('TELI-028','Klara',    'Winther',   'klara.winther@telia.com',     'Junior Developer',              '2023-06-01', 'TELI-TECH', 'TELI-SWE','TELI-HEL'),
        # Data & AI
        ('TELI-029','Astrid',   'Christensen','astrid.christensen@telia.com','Principal Data Scientist',     '2019-05-01', 'TELI-TECH', 'TELI-DAI','TELI-STO'),
        ('TELI-030','Petter',   'Peltonen',  'petter.peltonen@telia.com',   'Senior Data Engineer',          '2020-09-01', 'TELI-TECH', 'TELI-DAI','TELI-TLL'),
        ('TELI-031','Oscar',    'Laine',     'oscar.laine@telia.com',       'Senior ML Engineer',            '2021-02-01', 'TELI-TECH', 'TELI-DAI','TELI-STO'),
        ('TELI-032','Eva',      'Mäkinen',   'eva.makinen@telia.com',       'Data Engineer',                 '2022-04-01', 'TELI-TECH', 'TELI-DAI','TELI-TLL'),
        ('TELI-033','Stefan',   'Korhonen',  'stefan.korhonen@telia.com',   'Data Analyst',                  '2022-07-01', 'TELI-TECH', 'TELI-DAI','TELI-STO'),
        ('TELI-034','Christian','Virtanen',  'christian.virtanen@telia.com','Data Scientist',                '2022-02-01', 'TELI-TECH', 'TELI-DAI','TELI-TLL'),
        ('TELI-035','Emil',     'Mäki',      'emil.maki@telia.com',         'Data Engineer',                 '2023-03-01', 'TELI-TECH', 'TELI-DAI','TELI-STO'),
        ('TELI-036','Sandra',   'Laine',     'sandra.laine@telia.com',      'Junior Data Analyst',           '2023-08-01', 'TELI-TECH', 'TELI-DAI','TELI-TLL'),
        # Cybersecurity
        ('TELI-037','Maria',    'Häkkinen',  'maria.hakkinen@telia.com',    'Security Architect',            '2019-10-01', 'TELI-TECH', 'TELI-SEC','TELI-STO'),
        ('TELI-038','Lars',     'Koskinen',  'lars.koskinen@telia.com',     'Senior Security Engineer',      '2020-11-01', 'TELI-TECH', 'TELI-SEC','TELI-STO'),
        ('TELI-039','Anna',     'Lehtinen',  'anna.lehtinen@telia.com',     'Security Analyst',              '2021-08-01', 'TELI-TECH', 'TELI-SEC','TELI-STO'),
        ('TELI-040','Henrik',   'Järvi',     'henrik.jarvi@telia.com',      'Security Engineer',             '2022-09-01', 'TELI-TECH', 'TELI-SEC','TELI-STO'),
        ('TELI-041','Camilla',  'Kallio',    'camilla.kallio@telia.com',    'Junior Security Analyst',       '2023-10-01', 'TELI-TECH', 'TELI-SEC','TELI-STO'),
        # Product
        ('TELI-042','Felix',    'Tamm',      'felix.tamm@telia.com',        'Senior Product Manager',        '2020-07-01', 'TELI-TECH', 'TELI-PRD','TELI-STO'),
        ('TELI-043','Petra',    'Mägi',      'petra.magi@telia.com',        'Product Manager',               '2021-10-01', 'TELI-TECH', 'TELI-PRD','TELI-STO'),
        # Enterprise Sales
        ('TELI-044','William',  'Söderberg', 'william.soderberg@telia.com', 'Senior Account Manager',        '2019-03-01', 'TELI-COMM', 'TELI-ENT','TELI-OSL'),
        ('TELI-045','Lena',     'Gustafsson','lena.gustafsson@telia.com',   'Sales Manager Enterprise',      '2020-04-01', 'TELI-COMM', 'TELI-ENT','TELI-CPH'),
        ('TELI-046','Charlotte','Lindberg',  'charlotte.lindberg@telia.com','Enterprise Account Manager',    '2021-03-01', 'TELI-COMM', 'TELI-ENT','TELI-OSL'),
        ('TELI-047','Karl',     'Gunnarsson','karl.gunnarsson@telia.com',   'Enterprise Account Manager',    '2021-07-01', 'TELI-COMM', 'TELI-ENT','TELI-CPH'),
        ('TELI-048','Maja',     'Hansen',    'maja.hansen@telia.com',       'Account Executive',             '2022-01-01', 'TELI-COMM', 'TELI-ENT','TELI-OSL'),
        ('TELI-049','Tobias',   'Andersen',  'tobias.andersen@telia.com',   'Account Executive',             '2022-05-01', 'TELI-COMM', 'TELI-ENT','TELI-CPH'),
        ('TELI-050','Cecilia',  'Christensen','cecilia.christensen@telia.com','Account Executive',           '2023-01-01', 'TELI-COMM', 'TELI-ENT','TELI-OSL'),
        # Consumer Sales
        ('TELI-051','Magnus',   'Häkkilä',   'magnus.hakkila@telia.com',    'Sales Manager Consumer',        '2019-06-01', 'TELI-COMM', 'TELI-CON','TELI-HEL'),
        ('TELI-052','Victor',   'Mäkinen',   'victor.makinen@telia.com',    'Senior Sales Manager',          '2020-08-01', 'TELI-COMM', 'TELI-CON','TELI-HEL'),
        ('TELI-053','Peter',    'Virtanen',  'peter.virtanen@telia.com',    'Senior Sales Representative',   '2021-04-01', 'TELI-COMM', 'TELI-CON','TELI-OSL'),
        ('TELI-054','Simon',    'Korhonen',  'simon.korhonen@telia.com',    'Sales Representative',          '2022-08-01', 'TELI-COMM', 'TELI-CON','TELI-HEL'),
        ('TELI-055','Robert',   'Mäki',      'robert.maki@telia.com',       'Sales Representative',          '2022-11-01', 'TELI-COMM', 'TELI-CON','TELI-OSL'),
        ('TELI-056','Björn',    'Laine',     'bjorn.laine@telia.com',       'Sales Representative',          '2023-02-01', 'TELI-COMM', 'TELI-CON','TELI-HEL'),
        ('TELI-057','Ingrid',   'Koskinen',  'ingrid.koskinen@telia.com',   'Sales Representative',          '2023-04-01', 'TELI-COMM', 'TELI-CON','TELI-OSL'),
        ('TELI-058','Elin',     'Lehtinen',  'elin.lehtinen@telia.com',     'Junior Sales Representative',   '2023-09-01', 'TELI-COMM', 'TELI-CON','TELI-HEL'),
        # Digital Marketing
        ('TELI-059','Petra',    'Kallio',    'petra.kallio@telia.com',      'Digital Marketing Manager',     '2020-10-01', 'TELI-COMM', 'TELI-MKT','TELI-STO'),
        ('TELI-060','Andreas',  'Järvi',     'andreas.jarvi@telia.com',     'Content Manager',               '2021-05-01', 'TELI-COMM', 'TELI-MKT','TELI-STO'),
        ('TELI-061','Linda',    'Mägi',      'linda.magi@telia.com',        'Social Media Manager',          '2021-12-01', 'TELI-COMM', 'TELI-MKT','TELI-CPH'),
        ('TELI-062','Sara',     'Tamm',      'sara.tamm@telia.com',         'Marketing Analyst',             '2022-10-01', 'TELI-COMM', 'TELI-MKT','TELI-STO'),
        ('TELI-063','Niklas',   'Kask',      'niklas.kask@telia.com',       'Performance Marketing Analyst', '2023-05-01', 'TELI-COMM', 'TELI-MKT','TELI-CPH'),
        ('TELI-064','Mikael',   'Lepp',      'mikael.lepp@telia.com',       'Junior Marketing Executive',    '2023-11-01', 'TELI-COMM', 'TELI-MKT','TELI-STO'),
        # Financial Control
        ('TELI-065','Helena',   'Saar',      'helena.saar@telia.com',       'Financial Controller',          '2018-11-01', 'TELI-FIN',  'TELI-FIN','TELI-STO'),
        ('TELI-066','Malin',    'Johansson', 'malin.johansson@telia.com',   'Financial Controller',          '2019-08-01', 'TELI-FIN',  'TELI-FIN','TELI-CPH'),
        ('TELI-067','Karin',    'Piir',      'karin.piir@telia.com',        'Senior Financial Analyst',      '2020-03-01', 'TELI-FIN',  'TELI-FIN','TELI-STO'),
        ('TELI-068','Fredrik',  'Nilsson',   'fredrik.nilsson@telia.com',   'Senior Financial Analyst',      '2020-06-01', 'TELI-FIN',  'TELI-FIN','TELI-CPH'),
        ('TELI-069','Niklas',   'Lindqvist', 'niklas.lindqvist@telia.com',  'Financial Analyst',             '2021-09-01', 'TELI-FIN',  'TELI-FIN','TELI-STO'),
        ('TELI-070','Emma',     'Svensson',  'emma.svensson@telia.com',     'Financial Analyst',             '2022-02-01', 'TELI-FIN',  'TELI-FIN','TELI-CPH'),
        ('TELI-071','Andreas',  'Andersson', 'andreas.andersson@telia.com', 'Financial Analyst',             '2022-08-01', 'TELI-FIN',  'TELI-FIN','TELI-STO'),
        ('TELI-072','Gustav',   'Bergström', 'gustav.bergstrom@telia.com',  'Junior Financial Analyst',      '2023-07-01', 'TELI-FIN',  'TELI-FIN','TELI-STO'),
        # Procurement
        ('TELI-073','Johanna',  'Pettersson','johanna.pettersson@telia.com','Procurement Manager',           '2019-01-01', 'TELI-FIN',  'TELI-PRO','TELI-STO'),
        ('TELI-074','Daniel',   'Eriksson',  'daniel.eriksson@telia.com',   'Procurement Specialist',        '2020-05-01', 'TELI-FIN',  'TELI-PRO','TELI-STO'),
        ('TELI-075','Sandra',   'Karlsson',  'sandra.karlsson@telia.com',   'Procurement Analyst',           '2021-10-01', 'TELI-FIN',  'TELI-PRO','TELI-STO'),
        ('TELI-076','Mattias',  'Larsson',   'mattias.larsson@telia.com',   'Procurement Analyst',           '2022-04-01', 'TELI-FIN',  'TELI-PRO','TELI-STO'),
        ('TELI-077','Julia',    'Olsson',    'julia.olsson@telia.com',      'Junior Procurement Coordinator','2023-09-01', 'TELI-FIN',  'TELI-PRO','TELI-STO'),
        # Talent Acquisition
        ('TELI-078','Axel',     'Lindström', 'axel.lindstrom@telia.com',    'Talent Acquisition Manager',    '2019-04-01', 'TELI-HR',   'TELI-TAL','TELI-STO'),
        ('TELI-079','Isabelle', 'Magnusson', 'isabelle.magnusson@telia.com','Senior Recruiter',              '2020-07-01', 'TELI-HR',   'TELI-TAL','TELI-STO'),
        ('TELI-080','Viktor',   'Winther',   'viktor.winther@telia.com',    'Senior Recruiter',              '2021-02-01', 'TELI-HR',   'TELI-TAL','TELI-CPH'),
        ('TELI-081','Linnea',   'Hansen',    'linnea.hansen@telia.com',     'Talent Partner',                '2021-08-01', 'TELI-HR',   'TELI-TAL','TELI-STO'),
        ('TELI-082','Sofia',    'Gustafsson','sofia.gustafsson@telia.com',  'Recruiter',                     '2022-03-01', 'TELI-HR',   'TELI-TAL','TELI-CPH'),
        ('TELI-083','Oliver',   'Hansson',   'oliver.hansson@telia.com',    'Recruiter',                     '2022-09-01', 'TELI-HR',   'TELI-TAL','TELI-STO'),
        ('TELI-084','Amanda',   'Jakobsson', 'amanda.jakobsson@telia.com',  'Junior Recruiter',              '2023-06-01', 'TELI-HR',   'TELI-TAL','TELI-STO'),
        # L&D
        ('TELI-085','Thomas',   'Christensen','thomas.christensen@telia.com','L&D Manager',                  '2019-09-01', 'TELI-HR',   None,       'TELI-STO'),
        ('TELI-086','Astrid',   'Nielsen',   'astrid.nielsen@telia.com',    'Senior L&D Specialist',         '2020-11-01', 'TELI-HR',   None,       'TELI-STO'),
        ('TELI-087','Christian','Korhonen',  'christian.korhonen@telia.com','L&D Partner',                   '2021-06-01', 'TELI-HR',   None,       'TELI-HEL'),
        ('TELI-088','Petter',   'Christensen','petter.christensen@telia.com','L&D Specialist',               '2022-01-01', 'TELI-HR',   None,       'TELI-STO'),
        ('TELI-089','Eva',      'Peltonen',  'eva.peltonen@telia.com',      'L&D Specialist',                '2022-07-01', 'TELI-HR',   None,       'TELI-HEL'),
        ('TELI-090','Stefan',   'Mäkinen',   'stefan.makinen@telia.com',    'L&D Coordinator',               '2023-04-01', 'TELI-HR',   None,       'TELI-STO'),
        # Network Engineering
        ('TELI-091','Maria',    'Laine',     'maria.laine@telia.com',       'Principal Network Engineer',    '2018-07-01', 'TELI-OPS',  'TELI-NET','TELI-STO'),
        ('TELI-092','Lars',     'Häkkinen',  'lars.hakkinen@telia.com',     'Senior Network Engineer',       '2019-12-01', 'TELI-OPS',  'TELI-NET','TELI-STO'),
        ('TELI-093','Camilla',  'Järvi',     'camilla.jarvi@telia.com',     'Senior Network Engineer',       '2020-06-01', 'TELI-OPS',  'TELI-NET','TELI-TLL'),
        ('TELI-094','Anna',     'Koskinen',  'anna.koskinen@telia.com',     'Network Engineer',              '2021-03-01', 'TELI-OPS',  'TELI-NET','TELI-STO'),
        ('TELI-095','Henrik',   'Lehtinen',  'henrik.lehtinen@telia.com',   'Network Engineer',              '2021-11-01', 'TELI-OPS',  'TELI-NET','TELI-TLL'),
        ('TELI-096','Karl',     'Kallio',    'karl.kallio@telia.com',       'Network Engineer',              '2022-05-01', 'TELI-OPS',  'TELI-NET','TELI-STO'),
        ('TELI-097','Maja',     'Tamm',      'maja.tamm@telia.com',         'Junior Network Engineer',       '2023-02-01', 'TELI-OPS',  'TELI-NET','TELI-TLL'),
        # Infrastructure
        ('TELI-098','Tobias',   'Mägi',      'tobias.magi@telia.com',       'Infrastructure Manager',        '2019-02-01', 'TELI-OPS',  'TELI-INF','TELI-STO'),
        ('TELI-099','Lena',     'Kask',      'lena.kask@telia.com',         'Senior Site Reliability Engineer','2020-09-01','TELI-OPS', 'TELI-INF','TELI-HEL'),
        ('TELI-100','Cecilia',  'Lepp',      'cecilia.lepp@telia.com',      'Cloud Engineer',                '2021-07-01', 'TELI-OPS',  'TELI-INF','TELI-HEL'),
    ]

    # Manager hierarchy: emp_num → manager_emp_num
    mgr_map = {
        'TELI-002': 'TELI-001', 'TELI-003': 'TELI-001', 'TELI-004': 'TELI-001',
        'TELI-005': 'TELI-001', 'TELI-016': 'TELI-001',
        'TELI-006': 'TELI-002', 'TELI-007': 'TELI-002', 'TELI-008': 'TELI-002', 'TELI-009': 'TELI-002',
        'TELI-010': 'TELI-005', 'TELI-011': 'TELI-005', 'TELI-012': 'TELI-005',
        'TELI-013': 'TELI-003', 'TELI-014': 'TELI-003',
        'TELI-015': 'TELI-004',
        'TELI-017': 'TELI-006', 'TELI-018': 'TELI-006',
        **{f'TELI-0{n:02d}': 'TELI-018' for n in range(19, 26)},
        **{f'TELI-0{n:02d}': 'TELI-017' for n in [26, 28]},
        'TELI-027': 'TELI-018',
        'TELI-029': 'TELI-007', **{f'TELI-0{n:02d}': 'TELI-029' for n in range(30, 37)},
        'TELI-037': 'TELI-008', **{f'TELI-0{n:02d}': 'TELI-037' for n in range(38, 42)},
        'TELI-042': 'TELI-009', 'TELI-043': 'TELI-009',
        'TELI-044': 'TELI-010', 'TELI-045': 'TELI-010',
        'TELI-046': 'TELI-044', 'TELI-048': 'TELI-044', 'TELI-050': 'TELI-044',
        'TELI-047': 'TELI-045', 'TELI-049': 'TELI-045',
        'TELI-051': 'TELI-011', 'TELI-052': 'TELI-011',
        'TELI-053': 'TELI-051', 'TELI-054': 'TELI-051', 'TELI-056': 'TELI-051',
        'TELI-055': 'TELI-052', 'TELI-057': 'TELI-052', 'TELI-058': 'TELI-052',
        'TELI-059': 'TELI-012', **{f'TELI-0{n:02d}': 'TELI-059' for n in range(60, 65)},
        'TELI-065': 'TELI-013', 'TELI-066': 'TELI-013',
        'TELI-067': 'TELI-065', 'TELI-069': 'TELI-065', 'TELI-071': 'TELI-065',
        'TELI-068': 'TELI-066', 'TELI-070': 'TELI-066', 'TELI-072': 'TELI-066',
        'TELI-073': 'TELI-014', **{f'TELI-0{n:02d}': 'TELI-073' for n in range(74, 78)},
        'TELI-078': 'TELI-015', **{f'TELI-0{n:02d}': 'TELI-078' for n in range(79, 85)},
        'TELI-085': 'TELI-015', **{f'TELI-0{n:02d}': 'TELI-085' for n in range(86, 91)},
        'TELI-091': 'TELI-016', **{f'TELI-0{n:02d}': 'TELI-091' for n in range(92, 98)},
        'TELI-098': 'TELI-016', 'TELI-099': 'TELI-098', 'TELI-100': 'TELI-098',
    }

    emp_ids = {}  # emp_num → employee UUID

    for emp_num, first, last, email, title, join_date, bu_code, fu_code, loc_code in employees:
        cur.execute("""
            INSERT INTO employees
              (employee_number, first_name, last_name, email, job_title,
               employment_status, employment_type, join_date, company_id)
            VALUES (%s,%s,%s,%s,%s,'ACTIVE','PERMANENT',%s,%s::uuid)
            ON CONFLICT (employee_number) DO UPDATE
              SET company_id = EXCLUDED.company_id
            RETURNING id::text
        """, (emp_num, first, last, email, title, join_date, telia_id))
        emp_id = cur.fetchone()['id']
        emp_ids[emp_num] = emp_id

        # Org assignment
        bu_id  = bu_ids[bu_code]  if bu_code  else None
        fu_id  = fu_ids[fu_code]  if fu_code  else None
        loc_id = loc_ids[loc_code] if loc_code else None
        cur.execute("""
            INSERT INTO employee_org_assignments
              (employee_id, location_id, business_unit_id, functional_unit_id, is_current)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid, TRUE)
            ON CONFLICT DO NOTHING
        """, (emp_id, loc_id, bu_id, fu_id))

        # User account
        username = email.split('@')[0]
        cur.execute("""
            INSERT INTO users (employee_id, email, username, is_active)
            VALUES (%s::uuid, %s, %s, TRUE)
            ON CONFLICT (email) DO NOTHING
        """, (emp_id, email, username))

        # EMPLOYEE role
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id FROM users u, roles r
            WHERE u.email=%s AND r.name='EMPLOYEE'
            ON CONFLICT DO NOTHING
        """, (email,))

    # VPs → DEPARTMENT_HEAD
    vp_nums = [f'TELI-0{n:02d}' for n in range(6, 17)]
    for emp_num in vp_nums:
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM users u
            JOIN employees e ON e.id = u.employee_id
            JOIN roles r ON r.name = 'DEPARTMENT_HEAD'
            WHERE e.employee_number = %s
            ON CONFLICT DO NOTHING
        """, (emp_num,))

    # Managers → SOLID_LINE_MANAGER
    mgr_nums = ['TELI-017','TELI-018','TELI-029','TELI-037',
                'TELI-044','TELI-045','TELI-051','TELI-052',
                'TELI-059','TELI-065','TELI-066','TELI-073',
                'TELI-078','TELI-085','TELI-091','TELI-098']
    for emp_num in mgr_nums:
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM users u
            JOIN employees e ON e.id = u.employee_id
            JOIN roles r ON r.name = 'SOLID_LINE_MANAGER'
            WHERE e.employee_number = %s
            ON CONFLICT DO NOTHING
        """, (emp_num,))

    # Portal Admin → Maria Andersson (TELI-004 = CPO)
    cur.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id FROM users u
        JOIN employees e ON e.id = u.employee_id
        JOIN roles r ON r.name = 'PORTAL_ADMIN'
        WHERE e.employee_number = 'TELI-004'
        ON CONFLICT DO NOTHING
    """)

    # Manager relationships
    for emp_num, mgr_num in mgr_map.items():
        if emp_num in emp_ids and mgr_num in emp_ids:
            cur.execute("""
                INSERT INTO manager_relationships
                  (employee_id, manager_id, relationship_type, is_current)
                VALUES (%s::uuid, %s::uuid, 'SOLID_LINE', TRUE)
                ON CONFLICT DO NOTHING
            """, (emp_ids[emp_num], emp_ids[mgr_num]))

    print(f"  ✓ Seeded {len(employees)} Telia employees with org assignments, users and manager hierarchy")


# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n=== HR Portal DB Setup ===\n")
    c = conn()
    try:
        with c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            print("Step 1: Applying schema migration…")
            step1_migrate(cur)
            c.commit()

            print("Step 2: Backfilling company_id on org tables…")
            step2_backfill(cur)
            c.commit()

            print("Step 3: Removing Tech Admin from company…")
            step3_fix_tech_admin(cur)
            c.commit()

            print("Step 4: Seeding portal features…")
            step4_seed_portal_features(cur)
            c.commit()

            print("Step 5: Seeding Telia employees…")
            step5_seed_telia(cur)
            c.commit()

        print("\n✓ All done. Restart the Flask server if it's running.\n")

    except Exception as e:
        c.rollback()
        print(f"\n✗ Error (rolled back): {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        c.close()


if __name__ == '__main__':
    main()

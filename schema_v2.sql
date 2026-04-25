-- =============================================================
-- HR Competency Portal — Phase 1 MVP Schema
-- Drop & recreate all new tables inside a transaction.
-- The legacy employee_directory table is left untouched.
-- =============================================================

BEGIN;

-- Enable UUID helper
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────
-- Drop tables in reverse-dependency order
-- ─────────────────────────────────────────
DROP TABLE IF EXISTS dashboard_saved_filters      CASCADE;
DROP TABLE IF EXISTS dashboard_metric_snapshots   CASCADE;
DROP TABLE IF EXISTS employee_certifications      CASCADE;
DROP TABLE IF EXISTS certifications               CASCADE;
DROP TABLE IF EXISTS employee_skills              CASCADE;
DROP TABLE IF EXISTS proficiency_levels           CASCADE;
DROP TABLE IF EXISTS skills                       CASCADE;
DROP TABLE IF EXISTS skill_categories             CASCADE;
DROP TABLE IF EXISTS employee_search_index        CASCADE;
DROP TABLE IF EXISTS saved_views                  CASCADE;
DROP TABLE IF EXISTS visibility_scopes            CASCADE;
DROP TABLE IF EXISTS role_permissions             CASCADE;
DROP TABLE IF EXISTS permissions                  CASCADE;
DROP TABLE IF EXISTS user_roles                   CASCADE;
DROP TABLE IF EXISTS roles                        CASCADE;
DROP TABLE IF EXISTS users                        CASCADE;
DROP TABLE IF EXISTS manager_relationships        CASCADE;
DROP TABLE IF EXISTS employee_org_assignments     CASCADE;
DROP TABLE IF EXISTS cost_centers                 CASCADE;
DROP TABLE IF EXISTS functional_units             CASCADE;
DROP TABLE IF EXISTS business_units               CASCADE;
DROP TABLE IF EXISTS locations                    CASCADE;
DROP TABLE IF EXISTS employees                    CASCADE;

-- =============================================================
-- EPIC 1 — EMPLOYEE MASTER DATA
-- =============================================================

CREATE TABLE employees (
    id                 UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_number    VARCHAR(50) UNIQUE NOT NULL,
    first_name         VARCHAR(100) NOT NULL,
    last_name          VARCHAR(100) NOT NULL,
    email              VARCHAR(255) UNIQUE NOT NULL,
    phone_number       VARCHAR(50),
    job_title          VARCHAR(150),
    employment_status  VARCHAR(50)  NOT NULL DEFAULT 'ACTIVE'
                           CHECK (employment_status IN ('ACTIVE','INACTIVE','RESIGNED','TERMINATED')),
    employment_type    VARCHAR(50)
                           CHECK (employment_type IN ('PERMANENT','CONTRACTOR','INTERN','PART_TIME')),
    join_date          DATE,
    exit_date          DATE,
    profile_photo_url  TEXT,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- EPIC 2 — ORGANIZATION ATTRIBUTES
-- =============================================================

CREATE TABLE locations (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(150) NOT NULL,
    country     VARCHAR(100),
    city        VARCHAR(100),
    office_code VARCHAR(50)  UNIQUE
);

CREATE TABLE business_units (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(150) NOT NULL,
    code        VARCHAR(50)  UNIQUE,
    description TEXT
);

CREATE TABLE functional_units (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_unit_id UUID        REFERENCES business_units(id) ON DELETE SET NULL,
    name             VARCHAR(150) NOT NULL,
    code             VARCHAR(50)  UNIQUE,
    description      TEXT
);

CREATE TABLE cost_centers (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_unit_id UUID        REFERENCES business_units(id) ON DELETE SET NULL,
    code             VARCHAR(50)  UNIQUE NOT NULL,
    name             VARCHAR(150) NOT NULL
);

CREATE TABLE employee_org_assignments (
    id                 UUID     PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id        UUID     NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    location_id        UUID     REFERENCES locations(id),
    business_unit_id   UUID     REFERENCES business_units(id),
    functional_unit_id UUID     REFERENCES functional_units(id),
    cost_center_id     UUID     REFERENCES cost_centers(id),
    effective_from     DATE     NOT NULL DEFAULT CURRENT_DATE,
    effective_to       DATE,
    is_current         BOOLEAN  NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- EPIC 3 — REPORTING STRUCTURE
-- =============================================================

CREATE TABLE manager_relationships (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id       UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    manager_id        UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL
                          CHECK (relationship_type IN ('SOLID_LINE','DOTTED_LINE')),
    effective_from    DATE        NOT NULL DEFAULT CURRENT_DATE,
    effective_to      DATE,
    is_current        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_not_self_manager CHECK (employee_id <> manager_id)
);

-- =============================================================
-- EPIC 4 — ROLE-BASED ACCESS CONTROL & VISIBILITY
-- =============================================================

CREATE TABLE users (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id    UUID        UNIQUE REFERENCES employees(id) ON DELETE CASCADE,
    username       VARCHAR(100) UNIQUE NOT NULL,
    email          VARCHAR(255) UNIQUE NOT NULL,
    password_hash  TEXT,
    is_active      BOOLEAN     NOT NULL DEFAULT TRUE,
    last_login_at  TIMESTAMP,
    created_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE user_roles (
    user_id     UUID NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    role_id     UUID NOT NULL REFERENCES roles(id)  ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE permissions (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_code VARCHAR(100) UNIQUE NOT NULL,
    description     TEXT
);

CREATE TABLE role_permissions (
    role_id       UUID NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE visibility_scopes (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scope_type     VARCHAR(50) NOT NULL
                       CHECK (scope_type IN (
                           'COMPANY','LOCATION','BUSINESS_UNIT',
                           'FUNCTIONAL_UNIT','COST_CENTER'
                       )),
    scope_value_id UUID,
    effective_from DATE        NOT NULL DEFAULT CURRENT_DATE,
    effective_to   DATE,
    created_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- EPIC 5 — EMPLOYEE SEARCH & SAVED VIEWS
-- =============================================================

CREATE TABLE saved_views (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    view_name   VARCHAR(150) NOT NULL,
    view_type   VARCHAR(100),
    filter_json JSONB,
    is_default  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_search_index (
    employee_id UUID      PRIMARY KEY REFERENCES employees(id) ON DELETE CASCADE,
    search_text TSVECTOR,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- EPIC 6 — SKILL PROFILE MANAGEMENT
-- =============================================================

CREATE TABLE skill_categories (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(150) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE skills (
    id                UUID     PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_category_id UUID     REFERENCES skill_categories(id) ON DELETE SET NULL,
    name              VARCHAR(150) UNIQUE NOT NULL,
    description       TEXT,
    is_active         BOOLEAN  NOT NULL DEFAULT TRUE
);

CREATE TABLE proficiency_levels (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    level_name  VARCHAR(100) UNIQUE NOT NULL,
    level_order INT          UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE employee_skills (
    id                         UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id                UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    skill_id                   UUID        NOT NULL REFERENCES skills(id)    ON DELETE CASCADE,
    self_rating_level_id       UUID        REFERENCES proficiency_levels(id),
    manager_validated_level_id UUID        REFERENCES proficiency_levels(id),
    years_of_experience        NUMERIC(4,1),
    last_used_date             DATE,
    is_primary_skill           BOOLEAN     NOT NULL DEFAULT FALSE,
    validation_status          VARCHAR(50) NOT NULL DEFAULT 'SELF_ASSESSED'
                                   CHECK (validation_status IN (
                                       'SELF_ASSESSED',
                                       'PENDING_MANAGER_VALIDATION',
                                       'VALIDATED',
                                       'REJECTED'
                                   )),
    created_at                 TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                 TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_employee_skill UNIQUE (employee_id, skill_id)
);

CREATE TABLE certifications (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(200) UNIQUE NOT NULL,
    provider    VARCHAR(150),
    description TEXT
);

CREATE TABLE employee_certifications (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id         UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    certification_id    UUID        NOT NULL REFERENCES certifications(id),
    issued_date         DATE,
    expiry_date         DATE,
    certificate_url     TEXT,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED'
                            CHECK (verification_status IN (
                                'UNVERIFIED','VERIFIED','EXPIRED','REJECTED'
                            )),
    created_at          TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- EPIC 7 — COMPETENCY ANALYTICS DASHBOARD
-- =============================================================

CREATE TABLE dashboard_metric_snapshots (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_date     DATE        NOT NULL DEFAULT CURRENT_DATE,
    dimension_type    VARCHAR(50) NOT NULL
                          CHECK (dimension_type IN (
                              'COMPANY','LOCATION','BUSINESS_UNIT',
                              'FUNCTIONAL_UNIT','COST_CENTER',
                              'SOLID_LINE_MANAGER','DOTTED_LINE_MANAGER','JOB_TITLE'
                          )),
    dimension_id      UUID,
    skill_id          UUID        REFERENCES skills(id)           ON DELETE SET NULL,
    skill_category_id UUID        REFERENCES skill_categories(id) ON DELETE SET NULL,
    average_rating    NUMERIC(4,2),
    employee_count    INT         NOT NULL DEFAULT 0,
    rating_count      INT         NOT NULL DEFAULT 0,
    created_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dashboard_saved_filters (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filter_name VARCHAR(150) NOT NULL,
    filter_json JSONB       NOT NULL,
    is_default  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- INDEXES
-- =============================================================

CREATE INDEX idx_employees_email       ON employees(email);
CREATE INDEX idx_employees_status      ON employees(employment_status);
CREATE INDEX idx_employees_job_title   ON employees(job_title);

CREATE INDEX idx_org_employee          ON employee_org_assignments(employee_id);
CREATE INDEX idx_org_location          ON employee_org_assignments(location_id);
CREATE INDEX idx_org_bu                ON employee_org_assignments(business_unit_id);
CREATE INDEX idx_org_fu                ON employee_org_assignments(functional_unit_id);
CREATE INDEX idx_org_current           ON employee_org_assignments(is_current);

CREATE INDEX idx_mgr_employee          ON manager_relationships(employee_id);
CREATE INDEX idx_mgr_manager           ON manager_relationships(manager_id);
CREATE INDEX idx_mgr_type              ON manager_relationships(relationship_type);
CREATE INDEX idx_mgr_current           ON manager_relationships(is_current);

CREATE INDEX idx_visibility_user       ON visibility_scopes(user_id);
CREATE INDEX idx_visibility_scope      ON visibility_scopes(scope_type, scope_value_id);

CREATE INDEX idx_emp_skills_employee   ON employee_skills(employee_id);
CREATE INDEX idx_emp_skills_skill      ON employee_skills(skill_id);
CREATE INDEX idx_emp_skills_status     ON employee_skills(validation_status);

CREATE INDEX idx_emp_certs_employee    ON employee_certifications(employee_id);

CREATE INDEX idx_search_text           ON employee_search_index USING GIN(search_text);

CREATE INDEX idx_dashboard_snap_date   ON dashboard_metric_snapshots(snapshot_date);
CREATE INDEX idx_dashboard_snap_dim    ON dashboard_metric_snapshots(dimension_type, dimension_id);
CREATE INDEX idx_dashboard_snap_skill  ON dashboard_metric_snapshots(skill_id);

-- =============================================================
-- SEED DATA — Roles
-- =============================================================

INSERT INTO roles (name, description) VALUES
('EMPLOYEE',            'View and manage own profile only'),
('SOLID_LINE_MANAGER',  'View and manage solid-line direct reports'),
('DOTTED_LINE_MANAGER', 'View dotted-line reports'),
('HIRING_MANAGER',      'Search employees within assigned hiring scope'),
('DEPARTMENT_HEAD',     'View all employees under their department/BU'),
('LOCATION_HEAD',       'View all employees in their location'),
('HR_ADMIN',            'Full employee record access based on HR permissions'),
('SYSTEM_ADMIN',        'Full system-wide access and configuration');

-- =============================================================
-- SEED DATA — Permissions
-- =============================================================

INSERT INTO permissions (permission_code, description) VALUES
('VIEW_OWN_PROFILE',              'View own employee profile'),
('EDIT_OWN_PROFILE',              'Edit own basic profile'),
('EDIT_OWN_SKILLS',               'Add and update own skills'),
('VIEW_DIRECT_REPORTS',           'View solid-line direct reports'),
('VIEW_DOTTED_REPORTS',           'View dotted-line reports'),
('VIEW_DEPT_EMPLOYEES',           'View employees in own department/BU'),
('VIEW_LOCATION_EMPLOYEES',       'View all employees in own location'),
('VIEW_CENTER_EMPLOYEES',         'View employees in assigned hiring center'),
('VIEW_ALL_EMPLOYEES',            'View all employees across the organisation'),
('EDIT_EMPLOYEE_DATA',            'Create and update employee records'),
('MANAGE_ORG_STRUCTURE',          'Manage locations, BUs, FUs, cost centres'),
('VALIDATE_SKILLS',               'Validate and approve employee skill ratings'),
('MANAGE_SKILL_CATALOG',          'Manage skills, categories, proficiency levels'),
('VIEW_COMPETENCY_DASHBOARD',     'Access competency analytics dashboards'),
('MANAGE_ROLES_PERMISSIONS',      'Manage roles and permission assignments'),
('MANAGE_SYSTEM_SETTINGS',        'System-level configuration');

-- =============================================================
-- SEED DATA — Role → Permission mapping
-- =============================================================

-- EMPLOYEE
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'EMPLOYEE'
  AND p.permission_code IN ('VIEW_OWN_PROFILE','EDIT_OWN_PROFILE','EDIT_OWN_SKILLS');

-- SOLID LINE MANAGER
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'SOLID_LINE_MANAGER'
  AND p.permission_code IN (
      'VIEW_OWN_PROFILE','EDIT_OWN_PROFILE','EDIT_OWN_SKILLS',
      'VIEW_DIRECT_REPORTS','VALIDATE_SKILLS','VIEW_COMPETENCY_DASHBOARD');

-- DOTTED LINE MANAGER
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'DOTTED_LINE_MANAGER'
  AND p.permission_code IN (
      'VIEW_OWN_PROFILE','EDIT_OWN_PROFILE','EDIT_OWN_SKILLS',
      'VIEW_DOTTED_REPORTS','VIEW_COMPETENCY_DASHBOARD');

-- HIRING MANAGER
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'HIRING_MANAGER'
  AND p.permission_code IN (
      'VIEW_OWN_PROFILE','VIEW_CENTER_EMPLOYEES',
      'VIEW_COMPETENCY_DASHBOARD');

-- DEPARTMENT HEAD
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'DEPARTMENT_HEAD'
  AND p.permission_code IN (
      'VIEW_OWN_PROFILE','VIEW_DEPT_EMPLOYEES',
      'VIEW_DIRECT_REPORTS','VALIDATE_SKILLS','VIEW_COMPETENCY_DASHBOARD');

-- LOCATION HEAD
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'LOCATION_HEAD'
  AND p.permission_code IN (
      'VIEW_OWN_PROFILE','VIEW_LOCATION_EMPLOYEES',
      'VIEW_COMPETENCY_DASHBOARD');

-- HR ADMIN
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'HR_ADMIN'
  AND p.permission_code IN (
      'VIEW_ALL_EMPLOYEES','EDIT_EMPLOYEE_DATA','MANAGE_ORG_STRUCTURE',
      'VALIDATE_SKILLS','MANAGE_SKILL_CATALOG','VIEW_COMPETENCY_DASHBOARD');

-- SYSTEM ADMIN (all permissions)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'SYSTEM_ADMIN';

-- =============================================================
-- SEED DATA — Proficiency levels
-- =============================================================

INSERT INTO proficiency_levels (level_name, level_order, description) VALUES
('Beginner',     1, 'Basic awareness, needs guidance to complete tasks'),
('Intermediate', 2, 'Works independently on standard tasks'),
('Advanced',     3, 'Solves complex problems, guides peers'),
('Expert',       4, 'Recognised subject matter expert, sets direction');

-- =============================================================
-- SEED DATA — Skill categories & skills
-- =============================================================

INSERT INTO skill_categories (name, description) VALUES
('Cloud',            'Cloud platforms and managed services'),
('DevOps',           'CI/CD, automation, infrastructure and operations'),
('Backend',          'Server-side development technologies'),
('Frontend',         'Client-side and UI development technologies'),
('Quality Assurance','Testing, quality engineering and automation'),
('Security',         'Application, cloud and infrastructure security'),
('Data Engineering', 'Data pipelines, warehousing and analytics'),
('Leadership',       'People management, coaching, and strategy');

INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'AWS',           'Amazon Web Services'         FROM skill_categories WHERE name = 'Cloud';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Azure',         'Microsoft Azure'             FROM skill_categories WHERE name = 'Cloud';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'GCP',           'Google Cloud Platform'       FROM skill_categories WHERE name = 'Cloud';

INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Docker',        'Containerisation platform'   FROM skill_categories WHERE name = 'DevOps';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Kubernetes',    'Container orchestration'     FROM skill_categories WHERE name = 'DevOps';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Terraform',     'Infrastructure as Code'      FROM skill_categories WHERE name = 'DevOps';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'CI/CD',         'Continuous integration and delivery pipelines' FROM skill_categories WHERE name = 'DevOps';

INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Python',        'Python programming language' FROM skill_categories WHERE name = 'Backend';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, '.NET',          'Microsoft .NET platform'     FROM skill_categories WHERE name = 'Backend';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Java',          'Java programming language'   FROM skill_categories WHERE name = 'Backend';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Kafka',         'Event streaming platform'    FROM skill_categories WHERE name = 'Backend';

INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'React',         'React JavaScript library'    FROM skill_categories WHERE name = 'Frontend';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'TypeScript',    'Typed JavaScript'            FROM skill_categories WHERE name = 'Frontend';

INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Agile',         'Agile delivery methodology'  FROM skill_categories WHERE name = 'Leadership';
INSERT INTO skills (skill_category_id, name, description)
SELECT id, 'Project Management', 'End-to-end project delivery' FROM skill_categories WHERE name = 'Leadership';

-- =============================================================
-- SEED DATA — Locations, BUs, FUs, Cost Centres
-- =============================================================

INSERT INTO locations (name, country, city, office_code) VALUES
('Tallinn IT Center', 'Estonia',  'Tallinn', 'TLL'),
('Porto IT Center',   'Portugal', 'Porto',   'OPO'),
('Hamburg Office',    'Germany',  'Hamburg', 'HAM');

INSERT INTO business_units (name, code, description) VALUES
('Platform Engineering', 'PE', 'Platform and engineering enablement'),
('Logistics Solutions',  'LS', 'Logistics product and solution delivery'),
('Corporate',            'CO', 'Corporate functions (HR, Finance, Legal)');

INSERT INTO functional_units (business_unit_id, name, code, description)
SELECT id, 'DevOps Engineering',    'PE-DEVOPS', 'DevOps and infrastructure'     FROM business_units WHERE code = 'PE';
INSERT INTO functional_units (business_unit_id, name, code, description)
SELECT id, 'Backend Engineering',   'PE-BE',     'Backend services and APIs'     FROM business_units WHERE code = 'PE';
INSERT INTO functional_units (business_unit_id, name, code, description)
SELECT id, 'Frontend Engineering',  'PE-FE',     'Frontend and UX engineering'   FROM business_units WHERE code = 'PE';
INSERT INTO functional_units (business_unit_id, name, code, description)
SELECT id, 'Data & Analytics',      'PE-DA',     'Data engineering and analytics'FROM business_units WHERE code = 'PE';
INSERT INTO functional_units (business_unit_id, name, code, description)
SELECT id, 'Product Management',    'LS-PM',     'Product ownership and roadmap' FROM business_units WHERE code = 'LS';

INSERT INTO cost_centers (business_unit_id, code, name)
SELECT id, 'CC-PE-001', 'Platform Engineering Cost Center' FROM business_units WHERE code = 'PE';
INSERT INTO cost_centers (business_unit_id, code, name)
SELECT id, 'CC-LS-001', 'Logistics Solutions Cost Center'  FROM business_units WHERE code = 'LS';
INSERT INTO cost_centers (business_unit_id, code, name)
SELECT id, 'CC-CO-001', 'Corporate Cost Center'            FROM business_units WHERE code = 'CO';

COMMIT;

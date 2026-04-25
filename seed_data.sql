-- =============================================================
-- HR Competency Portal — Seed Data
-- ~45 employees across 3 locations, 3 BUs, 5 FUs
-- Org hierarchy: CTO → VPs → Managers → ICs
-- =============================================================

BEGIN;

-- ─────────────────────────────────────────
-- Reference IDs (from schema_v2 seed)
-- ─────────────────────────────────────────
DO $$ BEGIN
  RAISE NOTICE 'Seeding employees and all related tables...';
END $$;

-- =============================================================
-- 1. EMPLOYEES  (45 records)
-- Levels: L1=IC Junior, L2=IC Mid, L3=IC Senior,
--         L4=Lead/Manager, L5=Director/VP, L6=C-Level
-- =============================================================

INSERT INTO employees
    (id, employee_number, first_name, last_name, email, phone_number,
     job_title, employment_status, employment_type, join_date)
VALUES
-- ── C-Level ────────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000001','EMP-001','Oliver','Hartmann',
 'oliver.hartmann@company.com','+49-40-1001','Chief Technology Officer',
 'ACTIVE','PERMANENT','2018-03-01'),

-- ── HR Director ────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000002','EMP-002','Ingrid','Mäkinen',
 'ingrid.makinen@company.com','+372-5001-0002','HR Director',
 'ACTIVE','PERMANENT','2019-01-15'),

-- ── VP Platform Engineering ────────────────────────────────
('e0000001-0000-0000-0000-000000000003','EMP-003','Sofia','Andrade',
 'sofia.andrade@company.com','+351-22-3001','VP Platform Engineering',
 'ACTIVE','PERMANENT','2019-06-01'),

-- ── VP Logistics Solutions ─────────────────────────────────
('e0000001-0000-0000-0000-000000000004','EMP-004','Markus','Leppänen',
 'markus.leppanen@company.com','+372-5001-0004','VP Logistics Solutions',
 'ACTIVE','PERMANENT','2020-02-01'),

-- ── Location Head — Tallinn ────────────────────────────────
('e0000001-0000-0000-0000-000000000005','EMP-005','Katrin','Tamm',
 'katrin.tamm@company.com','+372-5001-0005','Tallinn IT Center Head',
 'ACTIVE','PERMANENT','2019-09-01'),

-- ── Location Head — Porto ──────────────────────────────────
('e0000001-0000-0000-0000-000000000006','EMP-006','Diogo','Ferreira',
 'diogo.ferreira@company.com','+351-22-3006','Porto IT Center Head',
 'ACTIVE','PERMANENT','2020-04-01'),

-- ── DevOps Manager ─────────────────────────────────────────
('e0000001-0000-0000-0000-000000000007','EMP-007','Lars','Eriksson',
 'lars.eriksson@company.com','+372-5001-0007','DevOps Engineering Manager',
 'ACTIVE','PERMANENT','2020-07-01'),

-- ── Backend Manager ────────────────────────────────────────
('e0000001-0000-0000-0000-000000000008','EMP-008','Ana','Costa',
 'ana.costa@company.com','+351-22-3008','Backend Engineering Manager',
 'ACTIVE','PERMANENT','2020-09-01'),

-- ── Frontend Manager ───────────────────────────────────────
('e0000001-0000-0000-0000-000000000009','EMP-009','Mihkel','Kask',
 'mihkel.kask@company.com','+372-5001-0009','Frontend Engineering Manager',
 'ACTIVE','PERMANENT','2021-01-10'),

-- ── Data Manager ───────────────────────────────────────────
('e0000001-0000-0000-0000-000000000010','EMP-010','Claudia','Nunes',
 'claudia.nunes@company.com','+351-22-3010','Data & Analytics Manager',
 'ACTIVE','PERMANENT','2021-03-01'),

-- ── Product Manager ────────────────────────────────────────
('e0000001-0000-0000-0000-000000000011','EMP-011','Juhan','Sepp',
 'juhan.sepp@company.com','+372-5001-0011','Product Management Lead',
 'ACTIVE','PERMANENT','2021-05-01'),

-- ── HR Manager ─────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000012','EMP-012','Liisa','Virtanen',
 'liisa.virtanen@company.com','+49-40-1012','HR Manager',
 'ACTIVE','PERMANENT','2021-07-01'),

-- ── DevOps ICs ─────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000013','EMP-013','Tõnis','Rebane',
 'tonis.rebane@company.com','+372-5001-0013','Senior DevOps Engineer',
 'ACTIVE','PERMANENT','2021-02-15'),
('e0000001-0000-0000-0000-000000000014','EMP-014','Risto','Korhonen',
 'risto.korhonen@company.com','+372-5001-0014','DevOps Engineer',
 'ACTIVE','PERMANENT','2022-01-10'),
('e0000001-0000-0000-0000-000000000015','EMP-015','Peeter','Mägi',
 'peeter.magi@company.com','+372-5001-0015','DevOps Engineer',
 'ACTIVE','PERMANENT','2022-06-01'),
('e0000001-0000-0000-0000-000000000016','EMP-016','Annika','Saar',
 'annika.saar@company.com','+372-5001-0016','Junior DevOps Engineer',
 'ACTIVE','PERMANENT','2023-03-01'),

-- ── Backend ICs ────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000017','EMP-017','Bruno','Oliveira',
 'bruno.oliveira@company.com','+351-22-3017','Senior Backend Engineer',
 'ACTIVE','PERMANENT','2020-11-01'),
('e0000001-0000-0000-0000-000000000018','EMP-018','Inês','Rodrigues',
 'ines.rodrigues@company.com','+351-22-3018','Backend Engineer',
 'ACTIVE','PERMANENT','2021-08-01'),
('e0000001-0000-0000-0000-000000000019','EMP-019','Tiago','Santos',
 'tiago.santos@company.com','+351-22-3019','Backend Engineer',
 'ACTIVE','PERMANENT','2022-02-14'),
('e0000001-0000-0000-0000-000000000020','EMP-020','Filipa','Sousa',
 'filipa.sousa@company.com','+351-22-3020','Junior Backend Engineer',
 'ACTIVE','PERMANENT','2023-06-01'),
('e0000001-0000-0000-0000-000000000021','EMP-021','Carlos','Mendes',
 'carlos.mendes@company.com','+351-22-3021','Senior Backend Engineer',
 'ACTIVE','PERMANENT','2021-04-01'),

-- ── Frontend ICs ───────────────────────────────────────────
('e0000001-0000-0000-0000-000000000022','EMP-022','Kadri','Laan',
 'kadri.laan@company.com','+372-5001-0022','Senior Frontend Engineer',
 'ACTIVE','PERMANENT','2021-03-15'),
('e0000001-0000-0000-0000-000000000023','EMP-023','Marta','Alves',
 'marta.alves@company.com','+351-22-3023','Frontend Engineer',
 'ACTIVE','PERMANENT','2022-05-01'),
('e0000001-0000-0000-0000-000000000024','EMP-024','Siim','Kallas',
 'siim.kallas@company.com','+372-5001-0024','Frontend Engineer',
 'ACTIVE','PERMANENT','2022-08-15'),
('e0000001-0000-0000-0000-000000000025','EMP-025','Nora','Tamme',
 'nora.tamme@company.com','+372-5001-0025','Junior Frontend Engineer',
 'ACTIVE','PERMANENT','2023-09-01'),

-- ── Data & Analytics ICs ───────────────────────────────────
('e0000001-0000-0000-0000-000000000026','EMP-026','Pedro','Lima',
 'pedro.lima@company.com','+351-22-3026','Senior Data Engineer',
 'ACTIVE','PERMANENT','2020-10-01'),
('e0000001-0000-0000-0000-000000000027','EMP-027','Anu','Põld',
 'anu.pold@company.com','+372-5001-0027','Data Engineer',
 'ACTIVE','PERMANENT','2022-01-17'),
('e0000001-0000-0000-0000-000000000028','EMP-028','Vasco','Pinto',
 'vasco.pinto@company.com','+351-22-3028','Data Analyst',
 'ACTIVE','PERMANENT','2022-11-01'),
('e0000001-0000-0000-0000-000000000029','EMP-029','Kertu','Rand',
 'kertu.rand@company.com','+372-5001-0029','Junior Data Analyst',
 'ACTIVE','PERMANENT','2023-07-01'),

-- ── Product ICs ────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000030','EMP-030','Marek','Pärn',
 'marek.parn@company.com','+372-5001-0030','Senior Product Owner',
 'ACTIVE','PERMANENT','2021-06-01'),
('e0000001-0000-0000-0000-000000000031','EMP-031','Joana','Cruz',
 'joana.cruz@company.com','+351-22-3031','Product Owner',
 'ACTIVE','PERMANENT','2022-03-01'),
('e0000001-0000-0000-0000-000000000032','EMP-032','Taavi','Ots',
 'taavi.ots@company.com','+372-5001-0032','Business Analyst',
 'ACTIVE','PERMANENT','2022-09-01'),

-- ── HR ICs ─────────────────────────────────────────────────
('e0000001-0000-0000-0000-000000000033','EMP-033','Hanna','Müller',
 'hanna.muller@company.com','+49-40-1033','HR Business Partner',
 'ACTIVE','PERMANENT','2021-10-01'),
('e0000001-0000-0000-0000-000000000034','EMP-034','Sven','Becker',
 'sven.becker@company.com','+49-40-1034','Recruiter',
 'ACTIVE','PERMANENT','2022-04-01'),
('e0000001-0000-0000-0000-000000000035','EMP-035','Jana','Wolf',
 'jana.wolf@company.com','+49-40-1035','HR Coordinator',
 'ACTIVE','PERMANENT','2023-01-01'),

-- ── Cross-BU / Shared ──────────────────────────────────────
('e0000001-0000-0000-0000-000000000036','EMP-036','Erik','Tamberg',
 'erik.tamberg@company.com','+372-5001-0036','Site Reliability Engineer',
 'ACTIVE','PERMANENT','2021-11-01'),
('e0000001-0000-0000-0000-000000000037','EMP-037','Rita','Gonçalves',
 'rita.goncalves@company.com','+351-22-3037','Security Engineer',
 'ACTIVE','PERMANENT','2022-07-01'),
('e0000001-0000-0000-0000-000000000038','EMP-038','Andres','Kukk',
 'andres.kukk@company.com','+372-5001-0038','Platform Architect',
 'ACTIVE','PERMANENT','2020-05-01'),
('e0000001-0000-0000-0000-000000000039','EMP-039','Marco','Bianchi',
 'marco.bianchi@company.com','+49-40-1039','Solutions Architect',
 'ACTIVE','PERMANENT','2020-08-01'),
('e0000001-0000-0000-0000-000000000040','EMP-040','Piret','Lepik',
 'piret.lepik@company.com','+372-5001-0040','QA Engineer',
 'ACTIVE','PERMANENT','2022-10-01'),
('e0000001-0000-0000-0000-000000000041','EMP-041','Rafael','Ferreira',
 'rafael.ferreira@company.com','+351-22-3041','QA Automation Engineer',
 'ACTIVE','PERMANENT','2022-12-01'),
('e0000001-0000-0000-0000-000000000042','EMP-042','Moonika','Kivi',
 'moonika.kivi@company.com','+372-5001-0042','Scrum Master',
 'ACTIVE','PERMANENT','2021-09-01'),
('e0000001-0000-0000-0000-000000000043','EMP-043','Thomas','Schmidt',
 'thomas.schmidt@company.com','+49-40-1043','IT Operations Engineer',
 'ACTIVE','PERMANENT','2022-02-01'),
('e0000001-0000-0000-0000-000000000044','EMP-044','Leena','Heikkinen',
 'leena.heikkinen@company.com','+372-5001-0044','Cloud Engineer',
 'ACTIVE','PERMANENT','2023-04-01'),
('e0000001-0000-0000-0000-000000000045','EMP-045','Paulo','Barbosa',
 'paulo.barbosa@company.com','+351-22-3045','Backend Engineer',
 'ACTIVE','CONTRACTOR','2023-05-01');

-- =============================================================
-- 2. EMPLOYEE ORG ASSIGNMENTS
-- =============================================================

INSERT INTO employee_org_assignments
    (employee_id, location_id, business_unit_id, functional_unit_id, cost_center_id, is_current)
SELECT
    e.id,
    l.id,
    bu.id,
    fu.id,
    cc.id,
    TRUE
FROM (VALUES
-- (emp_number, location_code, bu_code, fu_code, cc_code)
('EMP-001','HAM','PE',  NULL,       'CC-PE-001'),
('EMP-002','HAM','CO',  NULL,       'CC-CO-001'),
('EMP-003','OPO','PE',  NULL,       'CC-PE-001'),
('EMP-004','TLL','LS',  NULL,       'CC-LS-001'),
('EMP-005','TLL','PE',  NULL,       'CC-PE-001'),
('EMP-006','OPO','PE',  NULL,       'CC-PE-001'),
('EMP-007','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-008','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-009','TLL','PE',  'PE-FE',    'CC-PE-001'),
('EMP-010','OPO','PE',  'PE-DA',    'CC-PE-001'),
('EMP-011','TLL','LS',  'LS-PM',    'CC-LS-001'),
('EMP-012','HAM','CO',  NULL,       'CC-CO-001'),
('EMP-013','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-014','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-015','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-016','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-017','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-018','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-019','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-020','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-021','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-022','TLL','PE',  'PE-FE',    'CC-PE-001'),
('EMP-023','OPO','PE',  'PE-FE',    'CC-PE-001'),
('EMP-024','TLL','PE',  'PE-FE',    'CC-PE-001'),
('EMP-025','TLL','PE',  'PE-FE',    'CC-PE-001'),
('EMP-026','OPO','PE',  'PE-DA',    'CC-PE-001'),
('EMP-027','TLL','PE',  'PE-DA',    'CC-PE-001'),
('EMP-028','OPO','PE',  'PE-DA',    'CC-PE-001'),
('EMP-029','TLL','PE',  'PE-DA',    'CC-PE-001'),
('EMP-030','TLL','LS',  'LS-PM',    'CC-LS-001'),
('EMP-031','OPO','LS',  'LS-PM',    'CC-LS-001'),
('EMP-032','TLL','LS',  'LS-PM',    'CC-LS-001'),
('EMP-033','HAM','CO',  NULL,       'CC-CO-001'),
('EMP-034','HAM','CO',  NULL,       'CC-CO-001'),
('EMP-035','HAM','CO',  NULL,       'CC-CO-001'),
('EMP-036','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-037','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-038','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-039','HAM','PE',  NULL,       'CC-PE-001'),
('EMP-040','TLL','PE',  'PE-FE',    'CC-PE-001'),
('EMP-041','OPO','PE',  'PE-BE',    'CC-PE-001'),
('EMP-042','TLL','LS',  'LS-PM',    'CC-LS-001'),
('EMP-043','HAM','PE',  NULL,       'CC-PE-001'),
('EMP-044','TLL','PE',  'PE-DEVOPS','CC-PE-001'),
('EMP-045','OPO','PE',  'PE-BE',    'CC-PE-001')
) AS v(emp_num, loc_code, bu_code, fu_code, cc_code)
JOIN employees      e  ON e.employee_number = v.emp_num
JOIN locations      l  ON l.office_code     = v.loc_code
JOIN business_units bu ON bu.code           = v.bu_code
LEFT JOIN functional_units fu ON fu.code    = v.fu_code
JOIN cost_centers   cc ON cc.code           = v.cc_code;

-- =============================================================
-- 3. MANAGER RELATIONSHIPS
-- =============================================================

INSERT INTO manager_relationships
    (employee_id, manager_id, relationship_type, is_current)
SELECT e.id, m.id, v.rel_type, TRUE
FROM (VALUES
-- (employee_num, manager_num, relationship)
-- CTO manages VPs and location heads
('EMP-003','EMP-001','SOLID_LINE'),
('EMP-004','EMP-001','SOLID_LINE'),
('EMP-005','EMP-001','SOLID_LINE'),
('EMP-006','EMP-001','SOLID_LINE'),
('EMP-002','EMP-001','SOLID_LINE'),
-- HR Director manages HR Manager
('EMP-012','EMP-002','SOLID_LINE'),
-- VP PE manages Managers
('EMP-007','EMP-003','SOLID_LINE'),
('EMP-008','EMP-003','SOLID_LINE'),
('EMP-009','EMP-003','SOLID_LINE'),
('EMP-010','EMP-003','SOLID_LINE'),
('EMP-038','EMP-003','SOLID_LINE'),
('EMP-039','EMP-003','SOLID_LINE'),
-- VP LS manages Product Lead
('EMP-011','EMP-004','SOLID_LINE'),
-- DevOps Manager manages DevOps ICs
('EMP-013','EMP-007','SOLID_LINE'),
('EMP-014','EMP-007','SOLID_LINE'),
('EMP-015','EMP-007','SOLID_LINE'),
('EMP-016','EMP-007','SOLID_LINE'),
('EMP-036','EMP-007','SOLID_LINE'),
('EMP-044','EMP-007','SOLID_LINE'),
-- Backend Manager manages Backend ICs
('EMP-017','EMP-008','SOLID_LINE'),
('EMP-018','EMP-008','SOLID_LINE'),
('EMP-019','EMP-008','SOLID_LINE'),
('EMP-020','EMP-008','SOLID_LINE'),
('EMP-021','EMP-008','SOLID_LINE'),
('EMP-037','EMP-008','SOLID_LINE'),
('EMP-041','EMP-008','SOLID_LINE'),
('EMP-045','EMP-008','SOLID_LINE'),
-- Frontend Manager manages Frontend ICs
('EMP-022','EMP-009','SOLID_LINE'),
('EMP-023','EMP-009','SOLID_LINE'),
('EMP-024','EMP-009','SOLID_LINE'),
('EMP-025','EMP-009','SOLID_LINE'),
('EMP-040','EMP-009','SOLID_LINE'),
-- Data Manager manages Data ICs
('EMP-026','EMP-010','SOLID_LINE'),
('EMP-027','EMP-010','SOLID_LINE'),
('EMP-028','EMP-010','SOLID_LINE'),
('EMP-029','EMP-010','SOLID_LINE'),
-- Product Lead manages Product ICs
('EMP-030','EMP-011','SOLID_LINE'),
('EMP-031','EMP-011','SOLID_LINE'),
('EMP-032','EMP-011','SOLID_LINE'),
('EMP-042','EMP-011','SOLID_LINE'),
-- HR Manager manages HR ICs
('EMP-033','EMP-012','SOLID_LINE'),
('EMP-034','EMP-012','SOLID_LINE'),
('EMP-035','EMP-012','SOLID_LINE'),
-- IT Ops under CTO dotted
('EMP-043','EMP-001','SOLID_LINE'),
-- DOTTED LINE — cross-team collaboration
('EMP-036','EMP-038','DOTTED_LINE'),  -- SRE dotted to Architect
('EMP-013','EMP-038','DOTTED_LINE'),  -- Senior DevOps dotted to Architect
('EMP-044','EMP-039','DOTTED_LINE'),  -- Cloud Eng dotted to Solutions Architect
('EMP-037','EMP-039','DOTTED_LINE'),  -- Security Eng dotted to Solutions Arch
('EMP-040','EMP-011','DOTTED_LINE'),  -- QA dotted to Product Lead
('EMP-041','EMP-011','DOTTED_LINE'),  -- QA Automation dotted to Product Lead
('EMP-042','EMP-007','DOTTED_LINE'),  -- Scrum Master dotted to DevOps Mgr
('EMP-042','EMP-008','DOTTED_LINE'),  -- Scrum Master dotted to Backend Mgr
('EMP-026','EMP-004','DOTTED_LINE'),  -- Senior Data Eng dotted to VP LS
('EMP-032','EMP-003','DOTTED_LINE')   -- BA dotted to VP PE
) AS v(emp_num, mgr_num, rel_type)
JOIN employees e ON e.employee_number = v.emp_num
JOIN employees m ON m.employee_number = v.mgr_num;

-- =============================================================
-- 4. USERS
-- =============================================================

INSERT INTO users (employee_id, username, email, is_active)
SELECT
    e.id,
    LOWER(SPLIT_PART(e.email,'@',1)),
    e.email,
    TRUE
FROM employees e;

-- =============================================================
-- 5. USER ROLES
-- =============================================================

-- Everyone gets EMPLOYEE role
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE r.name = 'EMPLOYEE';

-- Solid-line managers
INSERT INTO user_roles (user_id, role_id)
SELECT DISTINCT u.id, r.id
FROM manager_relationships mr
JOIN employees e ON e.id = mr.manager_id
JOIN users u     ON u.employee_id = e.id
JOIN roles r     ON r.name = 'SOLID_LINE_MANAGER'
WHERE mr.relationship_type = 'SOLID_LINE'
ON CONFLICT DO NOTHING;

-- Dotted-line managers
INSERT INTO user_roles (user_id, role_id)
SELECT DISTINCT u.id, r.id
FROM manager_relationships mr
JOIN employees e ON e.id = mr.manager_id
JOIN users u     ON u.employee_id = e.id
JOIN roles r     ON r.name = 'DOTTED_LINE_MANAGER'
WHERE mr.relationship_type = 'DOTTED_LINE'
ON CONFLICT DO NOTHING;

-- Location heads
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM employees e
JOIN users u ON u.employee_id = e.id
JOIN roles r  ON r.name = 'LOCATION_HEAD'
WHERE e.employee_number IN ('EMP-005','EMP-006')
ON CONFLICT DO NOTHING;

-- Department / VP level = DEPARTMENT_HEAD
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM employees e
JOIN users u ON u.employee_id = e.id
JOIN roles r  ON r.name = 'DEPARTMENT_HEAD'
WHERE e.employee_number IN ('EMP-003','EMP-004')
ON CONFLICT DO NOTHING;

-- HR team
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM employees e
JOIN users u ON u.employee_id = e.id
JOIN roles r  ON r.name = 'HR_ADMIN'
WHERE e.employee_number IN ('EMP-002','EMP-012','EMP-033')
ON CONFLICT DO NOTHING;

-- Hiring managers (Product Lead, VP LS, VP PE)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM employees e
JOIN users u ON u.employee_id = e.id
JOIN roles r  ON r.name = 'HIRING_MANAGER'
WHERE e.employee_number IN ('EMP-003','EMP-004','EMP-011')
ON CONFLICT DO NOTHING;

-- System Admin = CTO
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM employees e
JOIN users u ON u.employee_id = e.id
JOIN roles r  ON r.name = 'SYSTEM_ADMIN'
WHERE e.employee_number = 'EMP-001'
ON CONFLICT DO NOTHING;

-- =============================================================
-- 6. VISIBILITY SCOPES
-- =============================================================

-- CTO → COMPANY wide
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'COMPANY', NULL
FROM employees e JOIN users u ON u.employee_id = e.id
WHERE e.employee_number = 'EMP-001';

-- HR Director & HR Manager → COMPANY wide
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'COMPANY', NULL
FROM employees e JOIN users u ON u.employee_id = e.id
WHERE e.employee_number IN ('EMP-002','EMP-012');

-- VP PE → Business Unit PE
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'BUSINESS_UNIT', bu.id
FROM employees e
JOIN users u        ON u.employee_id = e.id
JOIN business_units bu ON bu.code   = 'PE'
WHERE e.employee_number = 'EMP-003';

-- VP LS → Business Unit LS
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'BUSINESS_UNIT', bu.id
FROM employees e
JOIN users u        ON u.employee_id = e.id
JOIN business_units bu ON bu.code   = 'LS'
WHERE e.employee_number = 'EMP-004';

-- Tallinn Location Head → Location TLL
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'LOCATION', l.id
FROM employees e
JOIN users u    ON u.employee_id = e.id
JOIN locations l ON l.office_code = 'TLL'
WHERE e.employee_number = 'EMP-005';

-- Porto Location Head → Location OPO
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'LOCATION', l.id
FROM employees e
JOIN users u    ON u.employee_id = e.id
JOIN locations l ON l.office_code = 'OPO'
WHERE e.employee_number = 'EMP-006';

-- Functional managers → their FU
INSERT INTO visibility_scopes (user_id, scope_type, scope_value_id)
SELECT u.id, 'FUNCTIONAL_UNIT', fu.id
FROM (VALUES
    ('EMP-007','PE-DEVOPS'),
    ('EMP-008','PE-BE'),
    ('EMP-009','PE-FE'),
    ('EMP-010','PE-DA'),
    ('EMP-011','LS-PM')
) AS v(emp_num, fu_code)
JOIN employees       e  ON e.employee_number = v.emp_num
JOIN users           u  ON u.employee_id     = e.id
JOIN functional_units fu ON fu.code          = v.fu_code;

-- =============================================================
-- 7. CERTIFICATIONS CATALOG
-- =============================================================

INSERT INTO certifications (id, name, provider, description) VALUES
('c0000001-0000-0000-0000-000000000001','AWS Solutions Architect – Associate','Amazon Web Services','Validates ability to design distributed systems on AWS'),
('c0000001-0000-0000-0000-000000000002','AWS Solutions Architect – Professional','Amazon Web Services','Advanced AWS architecture design'),
('c0000001-0000-0000-0000-000000000003','Certified Kubernetes Administrator (CKA)','CNCF','Validates Kubernetes administration skills'),
('c0000001-0000-0000-0000-000000000004','Certified Kubernetes Application Developer (CKAD)','CNCF','Validates Kubernetes application development skills'),
('c0000001-0000-0000-0000-000000000005','HashiCorp Certified: Terraform Associate','HashiCorp','Validates Terraform IaC skills'),
('c0000001-0000-0000-0000-000000000006','Microsoft Certified: Azure Developer Associate','Microsoft','Azure application development'),
('c0000001-0000-0000-0000-000000000007','Google Professional Cloud Architect','Google','GCP architecture design'),
('c0000001-0000-0000-0000-000000000008','Professional Scrum Master I (PSM I)','Scrum.org','Scrum framework and practices'),
('c0000001-0000-0000-0000-000000000009','ISTQB Certified Tester Foundation Level','ISTQB','Software testing fundamentals'),
('c0000001-0000-0000-0000-000000000010','Certified Information Systems Security Professional (CISSP)','ISC2','Information security');

-- =============================================================
-- 8. EMPLOYEE SKILLS
-- =============================================================

INSERT INTO employee_skills
    (employee_id, skill_id, self_rating_level_id, manager_validated_level_id,
     years_of_experience, is_primary_skill, validation_status)
SELECT e.id, s.id, sl.id, vl.id, v.yoe, v.is_primary,
    CASE WHEN vl.id IS NOT NULL THEN 'VALIDATED' ELSE 'SELF_ASSESSED' END
FROM (VALUES
-- (emp_num, skill_name, self_level, validated_level, yoe, is_primary)
('EMP-001','AWS',          'Expert',       'Expert',       10.0, true),
('EMP-001','Agile',        'Expert',       'Expert',       12.0, true),
('EMP-001','Kubernetes',   'Advanced',     'Advanced',      7.0, false),

('EMP-003','AWS',          'Expert',       'Expert',        8.0, true),
('EMP-003','Kubernetes',   'Expert',       'Expert',        6.0, true),
('EMP-003','Terraform',    'Advanced',     'Advanced',      5.0, false),
('EMP-003','Agile',        'Advanced',     'Advanced',      8.0, false),

('EMP-004','Agile',        'Expert',       'Expert',        9.0, true),
('EMP-004','Project Management','Expert',  'Expert',        9.0, true),
('EMP-004','AWS',          'Intermediate', NULL,            4.0, false),

('EMP-007','Kubernetes',   'Expert',       'Expert',        7.0, true),
('EMP-007','Docker',       'Expert',       'Expert',        7.0, true),
('EMP-007','Terraform',    'Expert',       'Expert',        6.0, true),
('EMP-007','AWS',          'Advanced',     'Advanced',      6.0, false),
('EMP-007','CI/CD',        'Expert',       'Expert',        7.0, false),

('EMP-008','Java',         'Expert',       'Expert',        9.0, true),
('EMP-008','Python',       'Advanced',     'Advanced',      5.0, true),
('EMP-008','Kafka',        'Advanced',     'Advanced',      4.0, false),
('EMP-008','AWS',          'Intermediate', NULL,            3.0, false),

('EMP-009','React',        'Expert',       'Expert',        7.0, true),
('EMP-009','TypeScript',   'Expert',       'Expert',        6.0, true),
('EMP-009','Agile',        'Advanced',     'Advanced',      5.0, false),

('EMP-010','Python',       'Expert',       'Expert',        8.0, true),
('EMP-010','AWS',          'Advanced',     'Advanced',      5.0, true),
('EMP-010','Kafka',        'Advanced',     NULL,            4.0, false),

('EMP-011','Agile',        'Expert',       'Expert',        8.0, true),
('EMP-011','Project Management','Expert',  'Expert',        8.0, true),

-- DevOps ICs
('EMP-013','Kubernetes',   'Advanced',     'Advanced',      5.0, true),
('EMP-013','Docker',       'Advanced',     'Advanced',      5.0, true),
('EMP-013','Terraform',    'Advanced',     'Advanced',      4.0, false),
('EMP-013','AWS',          'Advanced',     'Advanced',      5.0, false),
('EMP-013','CI/CD',        'Advanced',     NULL,            4.0, false),

('EMP-014','Docker',       'Intermediate', 'Intermediate',  3.0, true),
('EMP-014','Kubernetes',   'Intermediate', NULL,            2.0, false),
('EMP-014','CI/CD',        'Intermediate', 'Intermediate',  3.0, false),
('EMP-014','AWS',          'Beginner',     NULL,            1.0, false),

('EMP-015','Docker',       'Intermediate', 'Intermediate',  3.0, true),
('EMP-015','Terraform',    'Intermediate', NULL,            2.0, true),
('EMP-015','AWS',          'Intermediate', 'Intermediate',  2.0, false),

('EMP-016','Docker',       'Beginner',     'Beginner',      1.0, true),
('EMP-016','CI/CD',        'Beginner',     NULL,            0.5, false),

-- Backend ICs
('EMP-017','Java',         'Expert',       'Expert',        8.0, true),
('EMP-017','Kafka',        'Advanced',     'Advanced',      5.0, true),
('EMP-017','Python',       'Intermediate', 'Intermediate',  3.0, false),
('EMP-017','AWS',          'Intermediate', NULL,            3.0, false),

('EMP-018','Python',       'Advanced',     'Advanced',      4.0, true),
('EMP-018','Java',         'Intermediate', 'Intermediate',  3.0, false),
('EMP-018','Kafka',        'Intermediate', NULL,            2.0, false),

('EMP-019','.NET',         'Advanced',     'Advanced',      4.0, true),
('EMP-019','Python',       'Intermediate', NULL,            2.0, false),
('EMP-019','Azure',        'Intermediate', 'Intermediate',  2.0, false),

('EMP-020','Java',         'Beginner',     'Beginner',      1.0, true),
('EMP-020','Python',       'Beginner',     NULL,            0.5, false),

('EMP-021','Java',         'Advanced',     'Advanced',      6.0, true),
('EMP-021','.NET',         'Intermediate', NULL,            3.0, false),
('EMP-021','Kafka',        'Intermediate', 'Intermediate',  3.0, false),

-- Frontend ICs
('EMP-022','React',        'Advanced',     'Advanced',      5.0, true),
('EMP-022','TypeScript',   'Advanced',     'Advanced',      4.0, true),

('EMP-023','React',        'Advanced',     'Advanced',      3.0, true),
('EMP-023','TypeScript',   'Intermediate', 'Intermediate',  2.0, false),

('EMP-024','React',        'Intermediate', 'Intermediate',  2.0, true),
('EMP-024','TypeScript',   'Intermediate', NULL,            2.0, false),

('EMP-025','React',        'Beginner',     NULL,            0.5, true),
('EMP-025','TypeScript',   'Beginner',     NULL,            0.5, false),

-- Data ICs
('EMP-026','Python',       'Expert',       'Expert',        7.0, true),
('EMP-026','AWS',          'Advanced',     'Advanced',      5.0, false),
('EMP-026','Kafka',        'Advanced',     'Advanced',      4.0, false),

('EMP-027','Python',       'Intermediate', 'Intermediate',  3.0, true),
('EMP-027','AWS',          'Intermediate', NULL,            2.0, false),

('EMP-028','Python',       'Intermediate', 'Intermediate',  2.0, true),
('EMP-028','AWS',          'Beginner',     NULL,            1.0, false),

('EMP-029','Python',       'Beginner',     NULL,            0.5, true),

-- Product ICs
('EMP-030','Agile',        'Advanced',     'Advanced',      6.0, true),
('EMP-030','Project Management','Advanced','Advanced',      5.0, false),

('EMP-031','Agile',        'Intermediate', 'Intermediate',  3.0, true),

('EMP-032','Agile',        'Intermediate', NULL,            3.0, false),

-- Cross-BU
('EMP-036','Kubernetes',   'Advanced',     'Advanced',      4.0, true),
('EMP-036','AWS',          'Advanced',     'Advanced',      4.0, false),
('EMP-036','CI/CD',        'Advanced',     NULL,            3.0, false),

('EMP-037','AWS',          'Advanced',     'Advanced',      4.0, true),
('EMP-037','Kubernetes',   'Intermediate', NULL,            2.0, false),

('EMP-038','AWS',          'Expert',       'Expert',        9.0, true),
('EMP-038','Kubernetes',   'Expert',       'Expert',        7.0, true),
('EMP-038','Terraform',    'Expert',       'Expert',        7.0, true),
('EMP-038','GCP',          'Advanced',     NULL,            4.0, false),

('EMP-039','AWS',          'Expert',       'Expert',        8.0, true),
('EMP-039','Azure',        'Advanced',     'Advanced',      5.0, true),
('EMP-039','GCP',          'Advanced',     NULL,            4.0, false),

('EMP-040','Agile',        'Intermediate', 'Intermediate',  2.0, false),

('EMP-041','Agile',        'Intermediate', NULL,            2.0, false),
('EMP-041','CI/CD',        'Intermediate', 'Intermediate',  2.0, true),

('EMP-042','Agile',        'Expert',       'Expert',        6.0, true),
('EMP-042','Project Management','Advanced','Advanced',      5.0, false),

('EMP-044','AWS',          'Intermediate', 'Intermediate',  1.5, true),
('EMP-044','Terraform',    'Beginner',     NULL,            0.5, false),

('EMP-045','Java',         'Intermediate', NULL,            3.0, true),
('EMP-045','Python',       'Intermediate', NULL,            2.0, false)
) AS v(emp_num, skill_name, self_lvl, val_lvl, yoe, is_primary)
JOIN employees e        ON e.employee_number = v.emp_num
JOIN skills s           ON s.name            = v.skill_name
JOIN proficiency_levels sl ON sl.level_name  = v.self_lvl
LEFT JOIN proficiency_levels vl ON vl.level_name = v.val_lvl;

-- =============================================================
-- 9. EMPLOYEE CERTIFICATIONS
-- =============================================================

INSERT INTO employee_certifications
    (employee_id, certification_id, issued_date, expiry_date, verification_status)
SELECT e.id, c.id, v.issued::date, v.expiry::date, v.status
FROM (VALUES
('EMP-007','Certified Kubernetes Administrator (CKA)',       '2021-06-01','2024-06-01','VERIFIED'),
('EMP-007','HashiCorp Certified: Terraform Associate',       '2022-03-01','2025-03-01','VERIFIED'),
('EMP-007','AWS Solutions Architect – Associate',            '2020-09-01','2023-09-01','EXPIRED'),
('EMP-008','AWS Solutions Architect – Associate',            '2021-11-01','2024-11-01','VERIFIED'),
('EMP-009','Professional Scrum Master I (PSM I)',            '2022-01-15','2025-01-15','VERIFIED'),
('EMP-013','Certified Kubernetes Administrator (CKA)',       '2022-08-01','2025-08-01','VERIFIED'),
('EMP-013','HashiCorp Certified: Terraform Associate',       '2023-01-01','2026-01-01','VERIFIED'),
('EMP-017','AWS Solutions Architect – Associate',            '2022-05-01','2025-05-01','VERIFIED'),
('EMP-019','Microsoft Certified: Azure Developer Associate', '2023-02-01','2026-02-01','VERIFIED'),
('EMP-026','AWS Solutions Architect – Associate',            '2021-07-01','2024-07-01','VERIFIED'),
('EMP-036','Certified Kubernetes Administrator (CKA)',       '2023-03-01','2026-03-01','VERIFIED'),
('EMP-037','Certified Information Systems Security Professional (CISSP)','2022-10-01',NULL,'VERIFIED'),
('EMP-038','AWS Solutions Architect – Professional',         '2021-04-01','2024-04-01','VERIFIED'),
('EMP-038','Certified Kubernetes Administrator (CKA)',       '2020-11-01','2023-11-01','EXPIRED'),
('EMP-038','HashiCorp Certified: Terraform Associate',       '2022-06-01','2025-06-01','VERIFIED'),
('EMP-039','AWS Solutions Architect – Professional',         '2022-01-01','2025-01-01','VERIFIED'),
('EMP-039','Google Professional Cloud Architect',            '2022-09-01','2025-09-01','VERIFIED'),
('EMP-039','Microsoft Certified: Azure Developer Associate', '2021-06-01','2024-06-01','VERIFIED'),
('EMP-040','ISTQB Certified Tester Foundation Level',        '2023-05-01',NULL,'VERIFIED'),
('EMP-041','ISTQB Certified Tester Foundation Level',        '2023-07-01',NULL,'VERIFIED'),
('EMP-042','Professional Scrum Master I (PSM I)',            '2021-03-01','2024-03-01','VERIFIED')
) AS v(emp_num, cert_name, issued, expiry, status)
JOIN employees     e ON e.employee_number = v.emp_num
JOIN certifications c ON c.name           = v.cert_name;

-- =============================================================
-- 10. SAVED VIEWS
-- =============================================================

INSERT INTO saved_views (user_id, view_name, view_type, filter_json, is_default)
SELECT u.id, v.vname, v.vtype, v.fjson::jsonb, v.is_def
FROM (VALUES
('EMP-002','All Active Employees',      'EMPLOYEE_LIST',
  '{"employment_status":"ACTIVE"}', true),
('EMP-002','Tallinn Headcount',         'EMPLOYEE_LIST',
  '{"location":"TLL"}', false),
('EMP-002','Platform Engineering Team', 'EMPLOYEE_LIST',
  '{"business_unit":"PE"}', false),
('EMP-007','My DevOps Team',            'TEAM_VIEW',
  '{"functional_unit":"PE-DEVOPS","manager":"EMP-007"}', true),
('EMP-008','Backend Team Skills',       'SKILL_VIEW',
  '{"functional_unit":"PE-BE","skill_categories":["Backend"]}', true),
('EMP-003','PE Cloud Skills Overview',  'SKILL_VIEW',
  '{"business_unit":"PE","skill_categories":["Cloud","DevOps"]}', true),
('EMP-011','Product Team – Porto & Tallinn','TEAM_VIEW',
  '{"functional_unit":"LS-PM"}', true)
) AS v(emp_num, vname, vtype, fjson, is_def)
JOIN employees e ON e.employee_number = v.emp_num
JOIN users     u ON u.employee_id     = e.id;

-- =============================================================
-- 11. EMPLOYEE SEARCH INDEX
-- =============================================================

INSERT INTO employee_search_index (employee_id, search_text)
SELECT
    e.id,
    TO_TSVECTOR('english',
        COALESCE(e.first_name,'')     || ' ' ||
        COALESCE(e.last_name,'')      || ' ' ||
        COALESCE(e.job_title,'')      || ' ' ||
        COALESCE(e.email,'')          || ' ' ||
        COALESCE(l.name,'')           || ' ' ||
        COALESCE(bu.name,'')          || ' ' ||
        COALESCE(fu.name,'')
    )
FROM employees e
LEFT JOIN employee_org_assignments oa ON oa.employee_id = e.id AND oa.is_current
LEFT JOIN locations      l  ON l.id  = oa.location_id
LEFT JOIN business_units bu ON bu.id = oa.business_unit_id
LEFT JOIN functional_units fu ON fu.id = oa.functional_unit_id;

-- =============================================================
-- 12. DASHBOARD METRIC SNAPSHOTS
-- =============================================================

INSERT INTO dashboard_metric_snapshots
    (snapshot_date, dimension_type, dimension_id, skill_id, skill_category_id,
     average_rating, employee_count, rating_count)
-- Average skill rating per functional unit per skill (using proficiency level_order as proxy rating)
SELECT
    CURRENT_DATE,
    'FUNCTIONAL_UNIT',
    oa.functional_unit_id,
    es.skill_id,
    s.skill_category_id,
    ROUND(AVG(pl.level_order), 2),
    COUNT(DISTINCT es.employee_id),
    COUNT(es.id)
FROM employee_skills es
JOIN proficiency_levels pl ON pl.id = es.self_rating_level_id
JOIN skills s              ON s.id  = es.skill_id
JOIN employee_org_assignments oa ON oa.employee_id = es.employee_id AND oa.is_current
WHERE oa.functional_unit_id IS NOT NULL
GROUP BY oa.functional_unit_id, es.skill_id, s.skill_category_id;

-- Per location
INSERT INTO dashboard_metric_snapshots
    (snapshot_date, dimension_type, dimension_id, skill_id, skill_category_id,
     average_rating, employee_count, rating_count)
SELECT
    CURRENT_DATE,
    'LOCATION',
    oa.location_id,
    es.skill_id,
    s.skill_category_id,
    ROUND(AVG(pl.level_order), 2),
    COUNT(DISTINCT es.employee_id),
    COUNT(es.id)
FROM employee_skills es
JOIN proficiency_levels pl ON pl.id = es.self_rating_level_id
JOIN skills s              ON s.id  = es.skill_id
JOIN employee_org_assignments oa ON oa.employee_id = es.employee_id AND oa.is_current
GROUP BY oa.location_id, es.skill_id, s.skill_category_id;

-- =============================================================
-- 13. DASHBOARD SAVED FILTERS
-- =============================================================

INSERT INTO dashboard_saved_filters (user_id, filter_name, filter_json, is_default)
SELECT u.id, v.fname, v.fjson::jsonb, v.is_def
FROM (VALUES
('EMP-003','Cloud Skills — All PE',
  '{"business_unit":"PE","skill_category":"Cloud"}', true),
('EMP-003','Kubernetes Proficiency by FU',
  '{"skill":"Kubernetes","group_by":"functional_unit"}', false),
('EMP-007','DevOps Team Skill Heatmap',
  '{"functional_unit":"PE-DEVOPS","group_by":"skill"}', true),
('EMP-010','Data Engineering Competency',
  '{"functional_unit":"PE-DA","group_by":"skill"}', true),
('EMP-002','Company-wide Expert Count by Skill',
  '{"scope":"COMPANY","proficiency":"Expert","group_by":"skill"}', true),
('EMP-002','Certification Coverage by Location',
  '{"scope":"COMPANY","group_by":"location"}', false)
) AS v(emp_num, fname, fjson, is_def)
JOIN employees e ON e.employee_number = v.emp_num
JOIN users     u ON u.employee_id     = e.id;

COMMIT;

-- Quick verification
SELECT 'employees'               AS tbl, COUNT(*) FROM employees
UNION ALL SELECT 'org_assignments',              COUNT(*) FROM employee_org_assignments
UNION ALL SELECT 'manager_relationships',        COUNT(*) FROM manager_relationships
UNION ALL SELECT 'users',                        COUNT(*) FROM users
UNION ALL SELECT 'user_roles',                   COUNT(*) FROM user_roles
UNION ALL SELECT 'visibility_scopes',            COUNT(*) FROM visibility_scopes
UNION ALL SELECT 'certifications',               COUNT(*) FROM certifications
UNION ALL SELECT 'employee_certifications',      COUNT(*) FROM employee_certifications
UNION ALL SELECT 'employee_skills',              COUNT(*) FROM employee_skills
UNION ALL SELECT 'saved_views',                  COUNT(*) FROM saved_views
UNION ALL SELECT 'search_index',                 COUNT(*) FROM employee_search_index
UNION ALL SELECT 'dashboard_snapshots',          COUNT(*) FROM dashboard_metric_snapshots
UNION ALL SELECT 'dashboard_saved_filters',      COUNT(*) FROM dashboard_saved_filters
ORDER BY tbl;

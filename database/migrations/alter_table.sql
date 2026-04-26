-- Add columns without NOT NULL first
ALTER TABLE employees ADD COLUMN designation TEXT;
ALTER TABLE employees ADD COLUMN skills TEXT[];

-- ── Two-tier admin: PORTAL_ADMIN role + company ownership on org tables ───────

-- New role: Portal Admin (company-scoped full admin)
INSERT INTO roles (name, description)
VALUES ('PORTAL_ADMIN', 'Full administrative access within their assigned company')
ON CONFLICT (name) DO NOTHING;

-- Grant Portal Admin the same broad permissions as HR_ADMIN + org management
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'PORTAL_ADMIN'
  AND p.name IN (
    'VIEW_ALL_EMPLOYEES', 'EDIT_EMPLOYEE_BASIC', 'EDIT_EMPLOYEE_FULL',
    'VIEW_COMPENSATION', 'MANAGE_ORG_STRUCTURE', 'MANAGE_VACATIONS',
    'MANAGE_ROLES_PERMISSIONS', 'VIEW_REPORTS'
  )
ON CONFLICT DO NOTHING;

-- Tie org structure tables to companies so Portal Admin data is isolated
ALTER TABLE business_units  ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE;
ALTER TABLE locations        ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE;
ALTER TABLE functional_units ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE;

-- ── Feature-level permission matrix (read / write / delete per feature area) ─

CREATE TABLE IF NOT EXISTS portal_features (
    id         UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    code       VARCHAR(100) UNIQUE NOT NULL,
    label      VARCHAR(150) NOT NULL,
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS role_feature_access (
    role_id    UUID    NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    feature_id UUID    NOT NULL REFERENCES portal_features(id) ON DELETE CASCADE,
    can_read   BOOLEAN NOT NULL DEFAULT FALSE,
    can_write  BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (role_id, feature_id)
);

INSERT INTO portal_features (code, label, description, sort_order) VALUES
  ('employee_profiles', 'Employee Profiles',      'View and manage employee personal, role and org data',      1),
  ('org_structure',     'Organisation Structure',  'Manage business units, locations and functional units',     2),
  ('user_accounts',     'User Accounts',           'Create, enable/disable and assign roles to portal users',   3),
  ('skills',            'Skills & Certifications', 'View, validate and manage skill profiles',                  4),
  ('vacations',         'Vacations & Leave',       'Manage vacation types, entitlements and leave requests',    5),
  ('reports',           'Reports & Analytics',     'Access competency dashboards and analytics',                6),
  ('company_settings',  'Company Settings',        'Edit company branding, logo, theme and metadata',           7),
  ('system_config',     'System Configuration',    'Widget settings, global platform config',                   8)
ON CONFLICT (code) DO NOTHING;

-- EMPLOYEE: own profile only
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, FALSE, FALSE FROM roles r, portal_features f
WHERE r.name='EMPLOYEE' AND f.code='employee_profiles' ON CONFLICT DO NOTHING;

-- SOLID_LINE_MANAGER
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id,
  TRUE,
  CASE WHEN f.code IN ('employee_profiles','skills') THEN TRUE ELSE FALSE END,
  CASE WHEN f.code='skills' THEN TRUE ELSE FALSE END
FROM roles r, portal_features f WHERE r.name='SOLID_LINE_MANAGER'
  AND f.code IN ('employee_profiles','skills','reports') ON CONFLICT DO NOTHING;

-- DOTTED_LINE_MANAGER
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, FALSE, FALSE FROM roles r, portal_features f
WHERE r.name='DOTTED_LINE_MANAGER' AND f.code IN ('employee_profiles','reports') ON CONFLICT DO NOTHING;

-- HIRING_MANAGER
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, FALSE, FALSE FROM roles r, portal_features f
WHERE r.name='HIRING_MANAGER' AND f.code IN ('employee_profiles','reports') ON CONFLICT DO NOTHING;

-- DEPARTMENT_HEAD
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE,
  CASE WHEN f.code IN ('employee_profiles','skills') THEN TRUE ELSE FALSE END, FALSE
FROM roles r, portal_features f WHERE r.name='DEPARTMENT_HEAD'
  AND f.code IN ('employee_profiles','org_structure','skills','reports') ON CONFLICT DO NOTHING;

-- LOCATION_HEAD
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, FALSE, FALSE FROM roles r, portal_features f
WHERE r.name='LOCATION_HEAD' AND f.code IN ('employee_profiles','reports') ON CONFLICT DO NOTHING;

-- HR_ADMIN
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE,
  CASE WHEN f.code IN ('employee_profiles','org_structure','skills','vacations','reports') THEN TRUE ELSE FALSE END,
  CASE WHEN f.code IN ('employee_profiles','org_structure','skills','vacations') THEN TRUE ELSE FALSE END
FROM roles r, portal_features f WHERE r.name='HR_ADMIN'
  AND f.code IN ('employee_profiles','org_structure','skills','vacations','reports') ON CONFLICT DO NOTHING;

-- PORTAL_ADMIN: everything except system_config
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, TRUE,
  CASE WHEN f.code IN ('employee_profiles','org_structure','user_accounts','skills','vacations') THEN TRUE ELSE FALSE END
FROM roles r, portal_features f WHERE r.name='PORTAL_ADMIN' AND f.code != 'system_config' ON CONFLICT DO NOTHING;

-- SYSTEM_ADMIN (Tech Admin): all features, full access
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, TRUE, TRUE FROM roles r, portal_features f
WHERE r.name='SYSTEM_ADMIN' ON CONFLICT DO NOTHING;

-- Per-company roles migration.
-- SYSTEM_ADMIN and PORTAL_ADMIN remain global (company_id IS NULL).
-- All other roles become company-specific; each company gets seeded copies.

-- Step 1: add company_id column to roles
ALTER TABLE roles ADD COLUMN IF NOT EXISTS company_id UUID
    REFERENCES companies(id) ON DELETE CASCADE;

-- Step 2: replace the global unique-name constraint with two partial indexes
ALTER TABLE roles DROP CONSTRAINT IF EXISTS roles_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS roles_global_name_uniq
    ON roles (name) WHERE company_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS roles_company_name_uniq
    ON roles (name, company_id) WHERE company_id IS NOT NULL;

-- Step 3: for every existing company create company-specific copies of the 7 non-system roles
INSERT INTO roles (name, description, company_id)
SELECT r.name, r.description, c.id
FROM roles r
CROSS JOIN companies c
WHERE r.company_id IS NULL
  AND r.name NOT IN ('SYSTEM_ADMIN', 'PORTAL_ADMIN')
ON CONFLICT DO NOTHING;

-- Step 4: seed role_feature_access for the new company-specific roles (copy from global)
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT cr.id, rfa.feature_id, rfa.can_read, rfa.can_write, rfa.can_delete
FROM role_feature_access rfa
JOIN roles gr ON gr.id = rfa.role_id AND gr.company_id IS NULL
JOIN roles cr ON cr.name = gr.name AND cr.company_id IS NOT NULL
ON CONFLICT (role_id, feature_id) DO NOTHING;

-- Step 5: point user_roles to company-specific role copies for non-system roles
UPDATE user_roles ur
SET role_id = cr.id
FROM users u
JOIN employees e  ON e.id  = u.employee_id
JOIN roles    gr  ON gr.id = ur.role_id
JOIN roles    cr  ON cr.name = gr.name AND cr.company_id = e.company_id
WHERE ur.user_id      = u.id
  AND gr.company_id   IS NULL
  AND gr.name         NOT IN ('SYSTEM_ADMIN', 'PORTAL_ADMIN')
  AND e.company_id    IS NOT NULL;

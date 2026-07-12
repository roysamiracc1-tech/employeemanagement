-- ─────────────────────────────────────────────────────────────────────────────
-- 06_org_change_workflow.sql
-- Drag-and-drop position change with a company-configurable, multi-level,
-- sequential approval workflow.
--
-- Adds:
--   * org_change_workflows        — one active approval chain per company
--   * org_change_workflow_steps   — ordered approval levels (role OR person)
--   * org_change_requests         — a proposed move (BU/FU/location/manager)
--   * org_change_approvals        — per-step audit trail of decisions
--   * portal feature 'org_change' + default role_feature_access
-- Idempotent: safe to re-run.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Workflow header — one chain per company ----------------------------------
CREATE TABLE IF NOT EXISTS org_change_workflows (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    name       VARCHAR(150) NOT NULL DEFAULT 'Position Change Approval',
    is_active  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Ordered approval levels --------------------------------------------------
CREATE TABLE IF NOT EXISTS org_change_workflow_steps (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id          UUID NOT NULL REFERENCES org_change_workflows(id) ON DELETE CASCADE,
    step_order           INT  NOT NULL,
    approver_type        VARCHAR(10) NOT NULL CHECK (approver_type IN ('ROLE','EMPLOYEE')),
    approver_role        VARCHAR(50),                       -- role NAME (roles are per-company)
    approver_employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    label                VARCHAR(120),
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workflow_id, step_order),
    CHECK (
        (approver_type = 'ROLE'     AND approver_role IS NOT NULL AND approver_employee_id IS NULL) OR
        (approver_type = 'EMPLOYEE' AND approver_employee_id IS NOT NULL AND approver_role IS NULL)
    )
);

-- 3. The proposed move --------------------------------------------------------
CREATE TABLE IF NOT EXISTS org_change_requests (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id                  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id                 UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,  -- subject
    requested_by_user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason                      TEXT,
    -- audit snapshot of the placement at request time
    from_business_unit_id       UUID REFERENCES business_units(id) ON DELETE SET NULL,
    from_functional_unit_id     UUID REFERENCES functional_units(id) ON DELETE SET NULL,
    from_location_id            UUID REFERENCES locations(id) ON DELETE SET NULL,
    from_manager_id             UUID REFERENCES employees(id) ON DELETE SET NULL,
    -- the proposed placement
    proposed_business_unit_id   UUID REFERENCES business_units(id) ON DELETE SET NULL,
    proposed_functional_unit_id UUID REFERENCES functional_units(id) ON DELETE SET NULL,
    proposed_location_id        UUID REFERENCES locations(id) ON DELETE SET NULL,
    proposed_manager_id         UUID REFERENCES employees(id) ON DELETE SET NULL,
    workflow_id                 UUID REFERENCES org_change_workflows(id) ON DELETE SET NULL,
    current_step                INT NOT NULL DEFAULT 1,
    status                      VARCHAR(12) NOT NULL DEFAULT 'PENDING'
                                CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED')),
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at                  TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ocr_company_status ON org_change_requests (company_id, status);
CREATE INDEX IF NOT EXISTS idx_ocr_employee       ON org_change_requests (employee_id);
CREATE INDEX IF NOT EXISTS idx_ocr_requester      ON org_change_requests (requested_by_user_id);

-- 4. Per-step decision audit trail --------------------------------------------
CREATE TABLE IF NOT EXISTS org_change_approvals (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id           UUID NOT NULL REFERENCES org_change_requests(id) ON DELETE CASCADE,
    step_order           INT  NOT NULL,
    approver_type        VARCHAR(10) NOT NULL,
    approver_role        VARCHAR(50),
    approver_employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    decided_by_user_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    decision             VARCHAR(10) CHECK (decision IN ('APPROVED','REJECTED')),
    note                 TEXT,
    decided_at           TIMESTAMP,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (request_id, step_order)
);

CREATE INDEX IF NOT EXISTS idx_oca_request ON org_change_approvals (request_id);

-- 5. Register the portal feature + default access -----------------------------
INSERT INTO portal_features (code, label, description, sort_order)
VALUES ('org_change', 'Position Change Requests',
        'Raise and approve employee business unit / department / manager changes', 10)
ON CONFLICT (code) DO NOTHING;

-- Default access: managers + HR + Portal admins can raise and approve
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, f.id, TRUE, TRUE, FALSE
FROM roles ro, portal_features f
WHERE f.code = 'org_change'
  AND ro.name IN ('SOLID_LINE_MANAGER','HR_ADMIN','PORTAL_ADMIN')
ON CONFLICT (role_id, feature_id) DO NOTHING;

-- SYSTEM_ADMIN gets everything (mirrors setup_db)
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, TRUE, TRUE
FROM roles r, portal_features f
WHERE r.name = 'SYSTEM_ADMIN' AND f.code = 'org_change'
ON CONFLICT (role_id, feature_id) DO NOTHING;

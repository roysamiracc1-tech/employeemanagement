-- Per-company role-feature access overrides.
-- PORTAL_ADMIN can restrict or re-enable roles for their company,
-- within the ceiling set by role_feature_access (SYSTEM_ADMIN).
-- No row = inherit global role_feature_access setting.

CREATE TABLE IF NOT EXISTS company_role_feature_access (
    company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role_id     UUID        NOT NULL REFERENCES roles(id)     ON DELETE CASCADE,
    feature_id  UUID        NOT NULL REFERENCES portal_features(id) ON DELETE CASCADE,
    is_enabled  BOOLEAN     NOT NULL DEFAULT TRUE,
    updated_by  UUID        REFERENCES users(id),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (company_id, role_id, feature_id)
);

CREATE INDEX IF NOT EXISTS idx_crfa_company_feature
    ON company_role_feature_access (company_id, feature_id);

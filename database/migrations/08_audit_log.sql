-- ─────────────────────────────────────────────────────────────────────────────
-- 08_audit_log.sql
-- EP38 / KAN-187 — the audit subsystem (ADR-009).
--
-- A single append-only, company-scoped audit trail shared by every subsystem
-- (EP38 lifecycle, EP35 import, EP39 accruals). It answers, for one row:
-- WHO did WHAT to WHOM, WHEN, from WHAT state to WHAT state, WHY, and with WHAT
-- OUTCOME — and rows produced by one unit of work share a correlation id so the
-- operation reads as one story.
--
-- Adds:
--   * audit_log                     — the trail itself (BIGSERIAL, TIMESTAMPTZ)
--   * audit_log_immutable()         — trigger function, raises on UPDATE
--   * trg_audit_log_no_update       — BEFORE UPDATE guard (append-only)
--   * three indexes (entity / company-time / correlation)
--   * portal feature 'audit_log' + default role_feature_access (read-only)
--
-- Idempotent: safe to re-run. Reverse with 08_audit_log_down.sql.
--
-- Deliberate design points — do NOT "fix" these (ADR-009 §3.1–§3.2):
--   * BIGSERIAL, not UUID. Append + range-scan-by-time only; a monotonic key
--     keeps inserts at the B-tree right edge and the row narrow.
--   * TIMESTAMPTZ, not TIMESTAMP. Every other table uses `timestamp without time
--     zone`; an audit trail is the one place "when" must be unambiguous. TD-12.
--   * before_state / after_state hold FIELD-LEVEL DIFFS ONLY — never whole rows,
--     never a password hash, token or free-text PII narrative.
--   * The subject is recorded as id + employee number ONLY. Never the name: an
--     audit row must survive a GDPR erasure without re-leaking the erased data.
--   * DELETE is deliberately NOT blocked. Retention purge must be able to delete
--     and this deployment has no DB role separation to distinguish a purge job
--     from the app user; blocking DELETE would either make retention impossible
--     or force a SET LOCAL escape hatch any code path could set. TD-13.
--   * No GIN index on the JSONB columns — nothing queries inside the blobs yet.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. The trail ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id                      BIGSERIAL PRIMARY KEY,

    -- Tenant scope (R4.1 #6). Mandatory, taken from the AFFECTED ENTITY, never
    -- from the session and never from request input. No ON DELETE clause: an
    -- audit trail must not be removable by deleting the company it describes.
    company_id              UUID         NOT NULL REFERENCES companies(id),

    -- Actor (R4.1 #3). The ids may be nulled by a later user/employee delete,
    -- so the label and the roles held AT THE TIME are denormalised — an audit
    -- trail that forgets who acted is not an audit trail.
    actor_user_id           UUID             NULL REFERENCES users(id)     ON DELETE SET NULL,
    actor_employee_id       UUID             NULL REFERENCES employees(id) ON DELETE SET NULL,
    actor_label             VARCHAR(255) NOT NULL,
    actor_roles             JSONB        NOT NULL DEFAULT '[]'::jsonb,

    -- Actor context (R4.1 #4, Should). Nullable — only becomes meaningful once
    -- real authentication lands (EP28/KAN-148).
    actor_ip                VARCHAR(45)      NULL,
    actor_session_id        VARCHAR(64)      NULL,

    -- Subject (R4.1 #5). Id plus an employee-number snapshot. NAME IS NEVER
    -- STORED — it would survive erasure and defeat it.
    subject_employee_id     UUID             NULL REFERENCES employees(id) ON DELETE SET NULL,
    subject_employee_number VARCHAR(50)      NULL,

    -- What happened (R4.1 #7, #8). `action` is a closed enumeration held in
    -- app/services/audit_service.py, not a DB CHECK, so EP35/EP39 extend the
    -- vocabulary without a migration. entity_id is polymorphic — no FK.
    action                  VARCHAR(60)  NOT NULL,
    entity_type             VARCHAR(50)  NOT NULL,
    entity_id               UUID         NOT NULL,

    -- Field-level diff (R4.1 #9). Same key set on both sides; changed fields only.
    before_state            JSONB            NULL,
    after_state             JSONB            NULL,

    -- Why (R4.1 #10). Mandatory and non-blank — every row answers "why".
    reason                  TEXT         NOT NULL,

    -- One unit of work = one correlation id (R4.1 #11).
    correlation_id          UUID         NOT NULL,

    -- Outcome (R4.1 #12). A FAILED row can only be written AFTER the failed
    -- transaction has rolled back — see audit_service.record().
    outcome                 VARCHAR(10)  NOT NULL DEFAULT 'SUCCESS',
    error_code              VARCHAR(60)      NULL,

    metadata                JSONB        NOT NULL DEFAULT '{}'::jsonb,
    retention_class         VARCHAR(20)  NOT NULL DEFAULT 'STANDARD',
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_audit_reason_not_blank CHECK (btrim(reason) <> ''),
    CONSTRAINT chk_audit_outcome          CHECK (outcome IN ('SUCCESS','FAILED')),
    CONSTRAINT chk_audit_retention_class  CHECK (retention_class IN ('STANDARD','EMPLOYMENT','SECURITY'))
);

CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON audit_log (company_id, entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_company_time
    ON audit_log (company_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_correlation
    ON audit_log (company_id, correlation_id);

-- 2. Append-only, enforced in the database and not by convention --------------
-- Application code issues INSERT only; conventions decay, triggers do not.
CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (attempted %)', TG_OP
        USING ERRCODE = 'restrict_violation';
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_log_no_update ON audit_log;
CREATE TRIGGER trg_audit_log_no_update
    BEFORE UPDATE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();

-- 3. Register the portal feature + default access -----------------------------
-- Read surface only (the viewer itself is Wave 3 work). sort_order 13 leaves
-- 11/12 free for `onboarding` / `offboarding` per the technical design §9.1.
INSERT INTO portal_features (code, label, description, sort_order)
VALUES ('audit_log', 'Audit Log',
        'View the immutable audit trail of changes within the company', 13)
ON CONFLICT (code) DO NOTHING;

-- Default: PORTAL_ADMIN and HR_ADMIN may READ their own company's trail.
-- Write and delete are FALSE for every tenant role — the table is append-only
-- and there is no legitimate audit write or delete outside audit_service.
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, f.id, TRUE, FALSE, FALSE
FROM roles ro, portal_features f
WHERE f.code = 'audit_log'
  AND ro.name IN ('PORTAL_ADMIN','HR_ADMIN')
ON CONFLICT (role_id, feature_id) DO NOTHING;

-- SYSTEM_ADMIN gets everything (mirrors setup_db's blanket grant; the bypass in
-- _load_feature_access() makes this row belt-and-braces rather than load-bearing).
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, TRUE, TRUE
FROM roles r, portal_features f
WHERE r.name = 'SYSTEM_ADMIN' AND f.code = 'audit_log'
ON CONFLICT (role_id, feature_id) DO NOTHING;

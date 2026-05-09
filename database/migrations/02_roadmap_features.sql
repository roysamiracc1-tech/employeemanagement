-- ── Roadmap features migration ───────────────────────────────────────────────
-- Run once.  All statements are idempotent (IF NOT EXISTS / ON CONFLICT).

-- ── 1. Notification settings ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_settings (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    event_type      VARCHAR(50) NOT NULL,   -- VACATION_REQUESTED | APPROVED | REJECTED | CANCELLED | EMPLOYEE_CREATED | SKILL_VALIDATED
    recipient_role  VARCHAR(50) NOT NULL,   -- role name (EMPLOYEE, SOLID_LINE_MANAGER, HR_ADMIN …)
    is_enabled      BOOLEAN     NOT NULL DEFAULT TRUE,
    allow_mute      BOOLEAN     NOT NULL DEFAULT TRUE,  -- can the recipient silence this?
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (company_id, event_type, recipient_role)
);

-- Per-user mute preferences (only effective when allow_mute = true)
CREATE TABLE IF NOT EXISTS notification_mutes (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    event_type  VARCHAR(50) NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, event_type)
);

-- ── 2. Employee search index trigger ────────────────────────────────────────
-- Ensure the search index table has employee_id as unique key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'employee_search_index'
          AND constraint_type = 'UNIQUE'
    ) THEN
        ALTER TABLE employee_search_index
            ADD CONSTRAINT employee_search_index_employee_id_key UNIQUE (employee_id);
    END IF;
END $$;

CREATE OR REPLACE FUNCTION fn_update_employee_search()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO employee_search_index (employee_id, search_text)
    VALUES (
        NEW.id,
        to_tsvector('english',
            COALESCE(NEW.first_name, '')  || ' ' ||
            COALESCE(NEW.last_name,  '')  || ' ' ||
            COALESCE(NEW.job_title,  '')  || ' ' ||
            COALESCE(NEW.email,      '')
        )
    )
    ON CONFLICT (employee_id) DO UPDATE
        SET search_text = EXCLUDED.search_text;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_employee_search ON employees;
CREATE TRIGGER trg_employee_search
    AFTER INSERT OR UPDATE OF first_name, last_name, job_title, email
    ON employees FOR EACH ROW
    EXECUTE FUNCTION fn_update_employee_search();

-- Backfill existing employees
INSERT INTO employee_search_index (employee_id, search_text)
SELECT id,
       to_tsvector('english',
           COALESCE(first_name,'') || ' ' ||
           COALESCE(last_name, '') || ' ' ||
           COALESCE(job_title, '') || ' ' ||
           COALESCE(email,     ''))
FROM employees
ON CONFLICT (employee_id) DO UPDATE
    SET search_text = EXCLUDED.search_text;

-- ── 3. Bulk employee import ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employee_imports (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by     UUID        NOT NULL REFERENCES users(id),
    status          VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    -- PENDING_REVIEW | APPROVED | REJECTED | PROCESSING | COMPLETED | FAILED
    filename        VARCHAR(255),
    row_count       INTEGER     NOT NULL DEFAULT 0,
    valid_count     INTEGER     NOT NULL DEFAULT 0,
    error_count     INTEGER     NOT NULL DEFAULT 0,
    imported_count  INTEGER     NOT NULL DEFAULT 0,
    approved_by     UUID        REFERENCES users(id),
    approved_at     TIMESTAMP,
    processed_at    TIMESTAMP,
    reject_reason   TEXT,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employee_import_rows (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id         UUID        NOT NULL REFERENCES employee_imports(id) ON DELETE CASCADE,
    row_number        INTEGER     NOT NULL,
    raw_data          JSONB       NOT NULL,
    validation_errors JSONB,      -- null = valid; array of error strings = invalid
    status            VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- PENDING | VALID | INVALID | IMPORTED | SKIPPED
    employee_id       UUID        REFERENCES employees(id),
    created_at        TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_rows_import ON employee_import_rows(import_id);
CREATE INDEX IF NOT EXISTS idx_import_rows_status ON employee_import_rows(status);
CREATE INDEX IF NOT EXISTS idx_imports_company    ON employee_imports(company_id);
CREATE INDEX IF NOT EXISTS idx_imports_status     ON employee_imports(status);

-- ── 4. Seed default notification settings for existing companies ─────────────
-- Fired once; ON CONFLICT DO NOTHING keeps it idempotent
DO $$ DECLARE rec RECORD; BEGIN
    FOR rec IN SELECT id FROM companies LOOP
        -- Vacation requested → notify employee's solid-line manager + HR_ADMIN
        INSERT INTO notification_settings (company_id, event_type, recipient_role, is_enabled, allow_mute)
        VALUES
          (rec.id, 'VACATION_REQUESTED',  'SOLID_LINE_MANAGER', TRUE, FALSE),
          (rec.id, 'VACATION_REQUESTED',  'HR_ADMIN',           TRUE, TRUE),
          (rec.id, 'VACATION_APPROVED',   'EMPLOYEE',           TRUE, TRUE),
          (rec.id, 'VACATION_REJECTED',   'EMPLOYEE',           TRUE, FALSE),
          (rec.id, 'VACATION_CANCELLED',  'SOLID_LINE_MANAGER', TRUE, TRUE),
          (rec.id, 'VACATION_CANCELLED',  'HR_ADMIN',           TRUE, TRUE),
          (rec.id, 'EMPLOYEE_CREATED',    'HR_ADMIN',           TRUE, TRUE),
          (rec.id, 'EMPLOYEE_CREATED',    'SOLID_LINE_MANAGER', TRUE, TRUE),
          (rec.id, 'SKILL_VALIDATED',     'EMPLOYEE',           TRUE, TRUE)
        ON CONFLICT (company_id, event_type, recipient_role) DO NOTHING;
    END LOOP;
END $$;

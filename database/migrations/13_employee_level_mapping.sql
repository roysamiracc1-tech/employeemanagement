-- ─────────────────────────────────────────────────────────────────────────────
-- 13 · KAN-191 — everyone on a level (EP42 W1 · R6 · R2 · D7)
--
-- Two halves, and they are different jobs:
--
--   A. THE MAPPING PROJECT — every employee gets a LEVEL. Driven from their
--      existing free-text `job_title`: 41 distinct titles at Acme and 75 at
--      Telia for 146 people (risk R-2). The screen is the deliverable; the
--      tenant's own effort is theirs and is NOT in the estimate.
--
--   B. STEP ASSESSMENT — a manager assesses each direct report's STEP against
--      the expectations authored in KAN-190. Moved here by amendment A6, which
--      forbids deriving a step from a salary.
--
-- `employee_job_assignments` was created in migration 12 (its trigger had to
-- exist before anything could write). This adds the mapping table and the two
-- constraints that make the effective-dated history trustworthy.
--
-- Down migration: 13_employee_level_mapping_down.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- ── The persisted output of the mapping screen ───────────────────────────────
-- NOT a scratch pad. It has to survive the sitting (146 people is not one
-- afternoon), round-trip through CSV, and be re-applied to people hired later —
-- otherwise every new joiner restarts the exercise by hand.
--
-- Keyed on the RAW title text, because that is the only key the source data has.
-- `employees.job_title` stays exactly as it is (ADR-017d / CFL-42-4): kept,
-- relabelled "Working title" in the UI, and never a grouping key for anything
-- that matters. Its index and the search trigger are untouched.
CREATE TABLE IF NOT EXISTS job_title_level_map (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id    UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_title     VARCHAR(200) NOT NULL,   -- the raw free-text title, verbatim
    job_level_id  UUID         NOT NULL,
    mapped_by_user_id UUID     NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    -- One mapping per title per company. Re-mapping updates in place, so the
    -- history of "what we decided this title means" is the audit trail's job
    -- rather than a pile of rows here.
    UNIQUE (company_id, job_title),
    CONSTRAINT fk_jtlm_level
        FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_jtlm_company ON job_title_level_map (company_id, job_title);

COMMENT ON TABLE job_title_level_map IS
    'Title -> level decisions from the KAN-191 mapping screen. Survives the '
    'sitting, round-trips through CSV, and is re-applied to later joiners. '
    'NOTE: there is deliberately no algorithmic title->level suggestion in this '
    'cycle — a wrong guess accepted in bulk is worse than an empty field.';


-- ── Making the effective-dated history trustworthy ───────────────────────────
--
-- 1. AT MOST ONE CURRENT ROW PER EMPLOYEE. Two would make "which level is this
--    person on?" ambiguous, and every downstream read — pay point, equity
--    check, promotion — picks one arbitrarily and disagrees with the next.
CREATE UNIQUE INDEX IF NOT EXISTS uq_eja_one_current
    ON employee_job_assignments (employee_id)
    WHERE is_current;

-- 2. NO OVERLAPPING PERIODS, on ADR-020's half-open `[from, to)` convention —
--    the same one KAN-189 made project-wide. Enforced by the DATABASE rather
--    than by service code, because an overlap means an employee was on two
--    levels on one day, and "as at date X they were on level Y" then has two
--    answers. That question is exactly what the equity check and any historical
--    pay explanation ask.
--
--    `daterange(from, to, '[)')` — half-open, so closing one period on the same
--    date the next opens is adjacent and legal, which is precisely what
--    `assign()` does. This needs btree_gist (migration 12 creates it).
ALTER TABLE employee_job_assignments
    DROP CONSTRAINT IF EXISTS excl_eja_no_overlap;
ALTER TABLE employee_job_assignments
    ADD CONSTRAINT excl_eja_no_overlap
    EXCLUDE USING gist (
        employee_id WITH =,
        daterange(effective_from, effective_to, '[)') WITH &&
    );


DO $$
DECLARE n INT;
BEGIN
    SELECT COUNT(*) INTO n FROM employees WHERE employment_status = 'ACTIVE';
    RAISE NOTICE 'KAN-191: mapping table ready. % ACTIVE employees to place; '
                 'coverage is reported with its denominator, never as a bare '
                 'percentage, and the unplaced are listed rather than dropped.', n;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 12 · KAN-190 — job families, levels and steps (EP42 W1 · R6 · ADR-017)
--
-- The ladder itself: a company defines its own job families, ordinal levels
-- within a family (each carrying THE canonical title), and steps within a level
-- with an authored description of what each step expects.
--
-- Everything downstream hangs off this shape — pay points (KAN-206), step
-- assessment (KAN-191), the equity check (KAN-200), promotions (KAN-192) — so
-- the constraints here are deliberately strict. It is cheap now and expensive
-- once occupied.
--
-- NOTE ON NUMBERING: the technical design (§3.2, §9.3 T-190-2) calls this
-- migration `11_job_architecture.sql`. KAN-188's tenant switch shipped first and
-- took 11, so job architecture is **12**. Same reason KAN-189 took 10.
--
-- Down migration: 12_job_architecture_down.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- T-190-1: exclusion constraints need btree_gist, and the effective-dated pay
-- tables in W2 will use them. Created here rather than there so every
-- environment has it before the first table that needs it, and so a fresh
-- database built from schema.sql alone can create one.
CREATE EXTENSION IF NOT EXISTS btree_gist;


-- ── Job families ─────────────────────────────────────────────────────────────
-- Company-scoped. There is deliberately NO global/default family: a tenant with
-- no ladder must see an empty state, never another company's ladder and never a
-- "starter" one somebody then has to undo (CLAUDE.md — company rows are only
-- ever `company_id = that company`).
CREATE TABLE IF NOT EXISTS job_families (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id   UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code         VARCHAR(50)  NOT NULL,
    name         VARCHAR(150) NOT NULL,
    description  TEXT,
    sort_order   INT          NOT NULL DEFAULT 0,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (company_id, code),
    UNIQUE (company_id, name),
    -- Target of the composite FK from job_levels. This is what makes a
    -- cross-tenant level impossible in the DATABASE rather than in a service
    -- somebody might bypass.
    UNIQUE (id, company_id)
);
CREATE INDEX IF NOT EXISTS idx_job_families_company
    ON job_families (company_id, is_active, sort_order);


-- ── Job levels ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_levels (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id     UUID         NOT NULL,
    job_family_id  UUID         NOT NULL,
    ordinal        INT          NOT NULL,
    title          VARCHAR(150) NOT NULL,   -- THE canonical job title (D3)
    short_code     VARCHAR(20),             -- "L1", "P3" — display only
    -- ⚠ NO DEFAULT, ON PURPOSE (§12.4.1). `step_count` is the number of
    -- increments ABOVE entry, so 5 yields SIX discrete values (.0 … .5) —
    -- matching the owner's own "2.0 … 2.5" example.
    --
    -- Trainee→Junior and Junior→Mid are genuinely different distances, so the
    -- configurator must REQUIRE an answer. A column default is how "we never
    -- decided" becomes indistinguishable from "we decided five" — and this is
    -- the last moment it is free to omit, because the table is empty today.
    step_count     INT          NOT NULL,
    description    TEXT,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_job_levels_ordinal    CHECK (ordinal BETWEEN 1 AND 30),
    CONSTRAINT chk_job_levels_step_count CHECK (step_count BETWEEN 1 AND 12),
    CONSTRAINT fk_job_levels_family
        FOREIGN KEY (job_family_id, company_id)
        REFERENCES job_families (id, company_id) ON DELETE RESTRICT,
    UNIQUE (job_family_id, ordinal),
    UNIQUE (job_family_id, title),
    UNIQUE (id, company_id)
);
CREATE INDEX IF NOT EXISTS idx_job_levels_family
    ON job_levels (company_id, job_family_id, ordinal);

COMMENT ON COLUMN job_levels.step_count IS
    'Number of increments ABOVE entry (§12.4.1). step_count = 5 means SIX steps: '
    '.0 .1 .2 .3 .4 .5. Never defaulted — the configurator must require an answer.';


-- ── Step expectations — the biggest thing A1 added ────────────────────────────
-- Content about THE JOB, not guidance about pay. (It replaces the withdrawn
-- `job_level_step_targets`, which was a percentile target — the wrong object.)
--
-- SPARSE ON PURPOSE. A level may be defined before its expectations are
-- authored; an unauthored step renders "Expectations not yet defined" — an
-- explicit empty state, never a blank and NEVER inherited from another step.
-- Authoring is a real content exercise per tenant (six blocks of text per level)
-- and blocking the ladder on it would stall W1.
--
-- ⚠ NO RATINGS, NO SCORES, NO ASSESSMENT COLUMNS — AND THERE MUST NEVER BE ONE.
-- No `score`, no `rating`, no `achieved`, no `met_expectations`. That is the
-- §14.5 / R-17 boundary written where it is enforceable instead of as a note in
-- a design document: a PR adding an assessment column here is the first
-- increment of a performance-management module arriving through an
-- entirely reasonable-sounding change. Performance management is EP44 and has
-- its own tables. `TestNoAssessmentColumnsOnTheLadder` fails the build.
CREATE TABLE IF NOT EXISTS job_step_expectations (
    job_level_id       UUID         NOT NULL,
    company_id         UUID         NOT NULL,
    step_no            INT          NOT NULL,
    summary            VARCHAR(200) NOT NULL,  -- one line, shown in lists/roadmaps
    description        TEXT         NOT NULL,  -- the responsibilities and expectations
    -- "Drafted by", because in most companies this content is written by
    -- engineering managers and transcribed by HR — the person who typed it is
    -- not the author, and attribution to the typist would be a false claim.
    drafted_by         VARCHAR(150),
    updated_by_user_id UUID         NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (job_level_id, step_no),
    -- step_no starts at 0 — entry. NOT 1: `.0` is a real step a person occupies.
    CONSTRAINT chk_jse_step CHECK (step_no >= 0 AND step_no <= 12),
    -- Whitespace is not an expectation. Enforced in the DB so an empty string
    -- cannot masquerade as authored content and defeat the empty state.
    CONSTRAINT chk_jse_text CHECK (btrim(summary) <> '' AND btrim(description) <> ''),
    CONSTRAINT fk_jse_level
        FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_jse_company ON job_step_expectations (company_id, job_level_id, step_no);


-- ── Employee placement on the ladder ─────────────────────────────────────────
-- Created here, POPULATED by KAN-191. It exists now because two KAN-190 rules
-- need it: a level's ordinal is immutable once an assignment exists, and the
-- step-bound trigger below must be in place before anything can ever write.
--
-- Effective-dated on ADR-020's half-open `[effective_from, effective_to)` — the
-- convention KAN-189 made project-wide. `effective_to` is the first day NOT
-- covered; never render it raw (use `fmt_period`).
CREATE TABLE IF NOT EXISTS employee_job_assignments (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id     UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id    UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    job_level_id   UUID        NOT NULL,
    -- NULL = STEP_NOT_ASSESSED, and that is a DISTINCT STATE from step 0 (A6).
    -- "Everyone defaults to .0" was itself a claim that a person is at entry
    -- level. An employee with no assessed step has no derived base pay, is not
    -- evaluable by the equity check, and renders "Step not yet assessed" —
    -- never `2.0`, never a dash, never blank.
    step_no        INT         NULL,
    effective_from DATE        NOT NULL DEFAULT CURRENT_DATE,
    effective_to   DATE        NULL,
    is_current     BOOLEAN     NOT NULL DEFAULT TRUE,
    assigned_by_user_id UUID   NULL REFERENCES users(id) ON DELETE SET NULL,
    reason         TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_eja_level
        FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE RESTRICT,
    CONSTRAINT chk_eja_step  CHECK (step_no IS NULL OR (step_no >= 0 AND step_no <= 12)),
    CONSTRAINT chk_eja_dates CHECK (effective_to IS NULL OR effective_to > effective_from)
);
CREATE INDEX IF NOT EXISTS idx_eja_employee ON employee_job_assignments (employee_id, is_current);
CREATE INDEX IF NOT EXISTS idx_eja_level    ON employee_job_assignments (company_id, job_level_id);

COMMENT ON COLUMN employee_job_assignments.step_no IS
    'NULL = STEP_NOT_ASSESSED, a distinct state and NOT step 0 (A6). No derived '
    'base pay, not evaluable, renders "Step not yet assessed".';


-- ── The step bound, as a CONSTRAINT rather than a convention (§12.4.1) ───────
-- `step_no` lives here and `step_count` lives on `job_levels`, so a single-table
-- CHECK cannot express the bound. §3.2 accepted that gap as TD-21 on
-- proportionality grounds; A1 withdrew that judgement because **the bound is
-- load-bearing on money**.
--
-- A step_no of 6 on a step_count = 5 level is not a cosmetic error. It produces
-- a pay point compounded six times, a PAY_BELOW_STEP finding against a rate
-- nobody is entitled to, and a "Propose adjustment" button pre-filled from a
-- number that should not exist. TD-21 is therefore CLOSED, not accepted.
CREATE OR REPLACE FUNCTION employee_job_assignment_step_valid() RETURNS trigger AS $$
DECLARE max_step INT;
BEGIN
    -- NULL is STEP_NOT_ASSESSED and always legal; it is the absence of a claim.
    IF NEW.step_no IS NULL THEN
        RETURN NEW;
    END IF;
    SELECT step_count INTO max_step FROM job_levels WHERE id = NEW.job_level_id;
    IF max_step IS NULL THEN
        RAISE EXCEPTION 'job level % does not exist', NEW.job_level_id;
    END IF;
    IF NEW.step_no < 0 OR NEW.step_no > max_step THEN
        RAISE EXCEPTION 'step_no % is outside level %''s ladder: valid steps are 0..% '
                        '(step_count counts increments ABOVE entry, so a step_count of % '
                        'yields % discrete values). EP42 ADR-017 §12.4.1.',
                        NEW.step_no, NEW.job_level_id, max_step, max_step, max_step + 1;
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_eja_step_valid ON employee_job_assignments;
CREATE TRIGGER trg_eja_step_valid
    BEFORE INSERT OR UPDATE OF step_no, job_level_id ON employee_job_assignments
    FOR EACH ROW EXECUTE FUNCTION employee_job_assignment_step_valid();


-- ── The fourth feature code ──────────────────────────────────────────────────
-- `job_architecture`. Registered here AND in seed_rbac.sql AND setup_db.py —
-- a feature row is DATA, a fresh CI database is schema.sql + seed_rbac.sql, and
-- migrations are never replayed (CLAUDE.md; this broke CI on 9 Aug 2026).
--
-- default_enabled = TRUE: the ladder is core product, not a licensed add-on.
INSERT INTO portal_features (code, label, description, sort_order, default_enabled)
VALUES ('job_architecture', 'Job Architecture',
        'Read the job ladder — families, levels, steps and what each step expects; '
        'write step roadmaps for your reports',
        11, TRUE)
ON CONFLICT (code) DO UPDATE
   SET label = EXCLUDED.label, description = EXCLUDED.description;

-- ⚠ THE LABEL AND DESCRIPTION ABOVE ARE PART OF THE ACCEPTANCE CRITERIA, not
-- decoration. `job_architecture:w` does NOT grant ladder editing — it grants
-- ROADMAP AUTHORING (KAN-207). Ladder configuration is `org_structure:w`. A
-- grant that reads "Job Architecture: write" would mislead the PORTAL_ADMIN at
-- the exact moment they make it, so the text says what it actually does
-- (CFL-42-35).

-- `r` to EVERY role: an employee must be able to read their own step and the
-- next one. That is the transparency the owner asked for twice, so it is the
-- default rather than a grant somebody has to remember to make.
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, pf.id, TRUE, FALSE, FALSE
  FROM roles ro
 CROSS JOIN portal_features pf
 WHERE pf.code = 'job_architecture'
ON CONFLICT (role_id, feature_id) DO NOTHING;

-- `w` — roadmap authoring — to the manager who must write them, plus HR/Portal.
-- Deliberately NOT a ladder-editing grant; see the note above.
UPDATE role_feature_access rfa
   SET can_write = TRUE
  FROM roles ro, portal_features pf
 WHERE rfa.role_id = ro.id AND rfa.feature_id = pf.id
   AND pf.code = 'job_architecture'
   AND ro.name IN ('SOLID_LINE_MANAGER', 'HR_ADMIN', 'PORTAL_ADMIN');


DO $$
DECLARE n INT;
BEGIN
    SELECT COUNT(*) INTO n FROM role_feature_access rfa
      JOIN portal_features pf ON pf.id = rfa.feature_id
     WHERE pf.code = 'job_architecture' AND rfa.can_read;
    RAISE NOTICE 'KAN-190: job_architecture readable by % role(s); ladder tables created.', n;
END $$;

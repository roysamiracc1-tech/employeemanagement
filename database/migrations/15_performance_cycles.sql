-- ─────────────────────────────────────────────────────────────────────────────
-- 15 · KAN-219 + KAN-220 — review cycles and who is in them (EP44 P0 · A7 · D-010)
--
-- The foundation of performance management: nothing else in the epic can exist
-- without a round to hang it on.
--
-- ⚠ NO PAY REFERENCE ANYWHERE IN THIS MIGRATION (AC-219-09). A cycle is
-- independent of the pay round (D-009(1)), which keeps the compensation
-- dependency one-directional and stops a rating ever reaching an amount by way
-- of a shared key. There is no currency, no amount, and no pay-period column.
--
-- Down migration: 15_performance_cycles_down.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- ── The fifth feature code ───────────────────────────────────────────────────
--
-- `performance:r` — read. Seeded to EVERY role, because an employee must be able
--   to read their own review. Row scoping decides WHOSE, not whether.
-- `performance:w` — **administer the company's review rounds**: open, configure,
--   close. HR_ADMIN + PORTAL_ADMIN only, deliberately **NOT** a manager: a line
--   manager must not be able to open or close the company's annual round.
--
-- ⚠ AN OPEN DESIGN QUESTION IS DELIBERATELY LEFT OPEN, not answered early.
-- A manager writing an assessment and an employee writing a self-assessment are
-- also WRITES, and they must not require this admin grant. That is the same shape
-- as CFL-42-35 (where `job_architecture:w` turned out to mean "author for your
-- own reports" while ladder configuration needed `org_structure:w`). It is raised
-- in BACKLOG.md against KAN-224/KAN-225 rather than pre-empted here, because
-- inventing a sixth feature code before the story that needs it is how a
-- permission model acquires codes nobody can explain.
INSERT INTO portal_features (code, label, description, sort_order, default_enabled)
VALUES ('performance', 'Performance Reviews',
        'Read your own performance review; administer the company''s review rounds',
        12, TRUE)
ON CONFLICT (code) DO UPDATE
   SET label = EXCLUDED.label, description = EXCLUDED.description;

INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, pf.id, TRUE, FALSE, FALSE
  FROM roles ro CROSS JOIN portal_features pf
 WHERE pf.code = 'performance'
ON CONFLICT (role_id, feature_id) DO NOTHING;

UPDATE role_feature_access rfa
   SET can_write = TRUE
  FROM roles ro, portal_features pf
 WHERE rfa.role_id = ro.id AND rfa.feature_id = pf.id
   AND pf.code = 'performance'
   AND ro.name IN ('HR_ADMIN', 'PORTAL_ADMIN');


-- ── Review cycles ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS performance_cycles (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id   UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name         VARCHAR(150) NOT NULL,

    -- ANNUAL, and therefore no `period_type` column (D-009(1), AC-219-01). A
    -- configurable field with one legal value is a lie about what the product
    -- supports; adding quarterly later is a migration and should look like one.
    -- `period_year` is the year the cycle is ABOUT; the window can straddle a
    -- calendar boundary for a company whose year starts in April.
    period_year  INT          NOT NULL,

    -- Half-open `[opens_on, closes_on)` on ADR-020's project-wide convention:
    -- `closes_on` is the first day the cycle does NOT cover. Never render it raw —
    -- `fmt_period()` subtracts the day.
    opens_on     DATE         NOT NULL,
    closes_on    DATE         NOT NULL,

    -- OQ-10. The employee's submission gates the manager's rating, so a deadline
    -- is the only thing that prevents a silent employee deadlocking their own
    -- review and the whole round. Nullable so a DRAFT cycle can be built up in
    -- any order; required before evaluation opens (enforced in the service, and
    -- checked here for the window bound).
    self_assessment_deadline DATE NULL,

    -- ── The eligibility POLICY the cycle ran under ──────────────────────────
    -- Stored ON THE CYCLE rather than in a company settings table, deliberately.
    -- A 2027 cycle's exclusions must still be explicable in 2029 even if the
    -- company's policy changed in between; a settings table would answer "what is
    -- the policy now?" when the question is "what was it then?". Same reasoning
    -- as versioning the rating scale.
    joiner_cutoff_days INT NOT NULL DEFAULT 90,
    excluded_employment_types TEXT[] NOT NULL DEFAULT ARRAY['CONTRACTOR'],

    status       VARCHAR(16)  NOT NULL DEFAULT 'DRAFT',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by_user_id UUID   NULL REFERENCES users(id) ON DELETE SET NULL,
    opened_at    TIMESTAMPTZ  NULL,
    closed_at    TIMESTAMPTZ  NULL,

    CONSTRAINT chk_pc_status CHECK (status IN
        ('DRAFT', 'OPEN', 'IN_REVIEW', 'CALIBRATION', 'CLOSED')),
    CONSTRAINT chk_pc_window CHECK (closes_on > opens_on),
    -- The deadline must fall inside the window. A deadline after the cycle closes
    -- is not a deadline; one before it opens is unmeetable.
    CONSTRAINT chk_pc_deadline CHECK (
        self_assessment_deadline IS NULL
        OR (self_assessment_deadline >= opens_on AND self_assessment_deadline < closes_on)),
    CONSTRAINT chk_pc_cutoff CHECK (joiner_cutoff_days >= 0 AND joiner_cutoff_days <= 365),
    UNIQUE (company_id, period_year),
    UNIQUE (id, company_id)
);

-- ⚠ AT MOST ONE CYCLE PER COMPANY THAT IS NOT CLOSED (AC-219-03).
-- Annual cadence makes this a real constraint rather than an arbitrary cap. Two
-- open rounds make "which cycle am I in?" ambiguous, and every downstream reader
-- — the participant list, the assessment surface, calibration — would pick one
-- arbitrarily and disagree with the next. Enforced by the DATABASE, for the same
-- reason `uq_eja_one_current` is.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_one_active
    ON performance_cycles (company_id) WHERE status <> 'CLOSED';

CREATE INDEX IF NOT EXISTS idx_pc_company ON performance_cycles (company_id, period_year DESC);

COMMENT ON COLUMN performance_cycles.status IS
    'DRAFT -> OPEN -> IN_REVIEW -> CALIBRATION -> CLOSED, FORWARD ONLY. A CLOSED '
    'cycle can never be reopened (AC-219-05): assessments, calibration outcomes '
    'and step changes point at it, so reopening silently changes what those '
    'records mean. A correction is an amendment with an actor and a reason.';


-- ── Who is in the cycle ──────────────────────────────────────────────────────
--
-- ⚠ A SNAPSHOT, NOT A LIVE QUERY (AC-220-01). This is the load-bearing decision
-- in KAN-220. If participation were resolved live:
--   • somebody joining mid-cycle would silently appear in a manager's list,
--   • a leaver would silently vanish from it,
--   • and the completion meter would move for reasons nobody did —
-- which is indistinguishable from a bug, and destroys trust in the number that
-- HR uses to chase the round. Re-evaluation is an explicit, audited action that
-- reports what changed.
CREATE TABLE IF NOT EXISTS performance_cycle_participants (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cycle_id     UUID         NOT NULL,
    company_id   UUID         NOT NULL,
    employee_id  UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    -- INCLUDED or EXCLUDED, and an exclusion ALWAYS carries a named reason
    -- (AC-220-02). A silent exclusion from a review round is the defect this
    -- story exists to prevent — and it is exactly what a works council or a
    -- tribunal asks about.
    state        VARCHAR(12)  NOT NULL,
    exclusion_reason VARCHAR(32) NULL,

    -- A shorter period, flagged so the manager knows they are assessing less
    -- than a year (AC-220-05). Shown at the point of assessment, never only in
    -- a report.
    is_partial   BOOLEAN      NOT NULL DEFAULT FALSE,

    -- Who was expected to assess them, AS AT THE SNAPSHOT. Recorded because
    -- `NO_MANAGER` blocks the round from opening and that judgement must be
    -- reconstructable. The assessment surface resolves the CURRENT manager — if
    -- Ana leaves and Bob takes over mid-cycle, Bob assesses — so this column is
    -- the record of who it was, not the authority on who acts.
    manager_employee_id UUID  NULL REFERENCES employees(id) ON DELETE SET NULL,

    -- An HR override, which needs a mandatory reason (AC-220-09).
    overridden_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    override_reason TEXT       NULL,

    snapshot_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_pcp_state CHECK (state IN ('INCLUDED', 'EXCLUDED')),
    -- An exclusion without a reason, or a reason without an exclusion, are both
    -- incoherent records.
    CONSTRAINT chk_pcp_reason CHECK (
        (state = 'EXCLUDED') = (exclusion_reason IS NOT NULL)),
    CONSTRAINT chk_pcp_reason_vocab CHECK (
        exclusion_reason IS NULL OR exclusion_reason IN
        ('NEW_JOINER', 'LEAVER', 'EXCLUDED_EMPLOYMENT_TYPE', 'NO_MANAGER', 'HR_EXCLUDED')),
    -- An HR override must say why. HR is overriding a rule, so the reason IS the
    -- record.
    CONSTRAINT chk_pcp_override CHECK (
        overridden_by_user_id IS NULL OR btrim(COALESCE(override_reason, '')) <> ''),
    CONSTRAINT fk_pcp_cycle FOREIGN KEY (cycle_id, company_id)
        REFERENCES performance_cycles (id, company_id) ON DELETE CASCADE,
    UNIQUE (cycle_id, employee_id)
);

CREATE INDEX IF NOT EXISTS idx_pcp_cycle ON performance_cycle_participants (cycle_id, state);
CREATE INDEX IF NOT EXISTS idx_pcp_manager
    ON performance_cycle_participants (cycle_id, manager_employee_id) WHERE state = 'INCLUDED';
CREATE INDEX IF NOT EXISTS idx_pcp_employee ON performance_cycle_participants (employee_id);

COMMENT ON TABLE performance_cycle_participants IS
    'A SNAPSHOT of who is in a review round, taken when it opens (KAN-220). Never '
    'a live query: live participation means a mid-cycle joiner silently appears, a '
    'leaver silently vanishes, and the completion meter moves for reasons nobody '
    'did. Re-evaluation is an explicit audited action that reports what changed.';


DO $$
DECLARE n INT;
BEGIN
    SELECT COUNT(*) INTO n FROM role_feature_access rfa
      JOIN portal_features pf ON pf.id = rfa.feature_id
     WHERE pf.code = 'performance' AND rfa.can_write;
    RAISE NOTICE 'EP44 P0: review cycles ready. performance:w held by % role row(s) '
                 '(HR + Portal admin only — a line manager must not open or close '
                 'the company''s round).', n;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 14 · KAN-207 — step roadmaps, and the step-disclosure switch (EP42 W1 · A1)
--
-- **The object the owner actually asked for**, and it is NOT KAN-190's step
-- expectation. The distinction is the whole story:
--
--   EXPECTATION (KAN-190)  what step 1.2 means *here*, for anybody
--   ROADMAP     (KAN-207)  what *you, specifically* need to do to get there
--
-- ⚠ NO RATINGS, NO SCORES, NO ASSESSMENT OF ANY KIND. A roadmap is a statement
-- of expectations, and that boundary is what keeps it out of GDPR Art. 22 and
-- EU AI Act territory — an automated or scored judgement about a person is a
-- different legal object with different obligations. There is no `score`,
-- `rating`, `readiness`, `likelihood` or `percent_complete` column here and
-- there must never be one. `TestNoAssessmentColumnsOnTheLadder` covers it.
--
-- Down migration: 14_step_roadmaps_down.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- ── The step-disclosure switch (A2 §6, corrected by A3-4 / CFL-42-58) ────────
--
-- ⚠ THIS BELONGED TO KAN-190 AND WAS MISSED. Recorded plainly rather than
-- quietly folded in: KAN-190's criteria included a first-run prompt asking
-- whether an employee's own STEP is displayed to them, and it was not built. It
-- is added here because KAN-207 is the first surface that CONSUMES it, and a
-- switch with no reader would have been untestable.
--
-- It governs the STEP, not the level. In the owner's own example the title
-- *Junior Software Fullstack Engineer* **is** level 2, and he has said the title
-- is always visible — so a switch claiming to hide the level would hide nothing
-- while claiming to (standing rule 6: a label is a claim).
--
-- Named `display_step_to_employee` and DEFAULT TRUE: he asked for
-- level-expectation transparency twice, so withholding is the exception a
-- company invokes, not the default it has to switch off.
ALTER TABLE companies
    ADD COLUMN IF NOT EXISTS display_step_to_employee BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN companies.display_step_to_employee IS
    'Whether an employee is shown their own STEP NUMBER (KAN-190/207, A2 §6). '
    'Governs display only, never inference: the employee still reads the whole '
    'ladder and their own expectations either way. Labelled "do not display", '
    'never "hide" — the ladder remains readable, so it prevents display, not '
    'inference. Default TRUE.';


-- ── Roadmaps ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employee_step_roadmaps (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id        UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id       UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    version           INT         NOT NULL,

    -- Where they were, and what this points at. **Denormalised from the
    -- assignment ON PURPOSE**: the target must survive the employee moving, so
    -- "what did we agree in March" still reads correctly after a level change.
    -- Reading it back through the live assignment would silently re-target every
    -- historical roadmap the moment somebody is promoted.
    from_job_level_id   UUID      NOT NULL,
    from_step_no        INT       NOT NULL,
    target_job_level_id UUID      NOT NULL,
    target_step_no      INT       NOT NULL,

    content           TEXT        NOT NULL,

    -- §14.5: RECORD the review context, do NOT build the review. EP44 makes this
    -- point at a real closed cycle (KAN-236); until then it is an honest label.
    review_context    VARCHAR(24) NOT NULL,
    review_date       DATE        NULL,

    authored_by_user_id UUID      NOT NULL REFERENCES users(id),
    -- The author's name AT THE TIME, because a roadmap outlives a job change and
    -- "authored by their manager" must still read correctly when that person is
    -- no longer their manager.
    authored_by_label VARCHAR(255) NOT NULL,
    authored_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- ⚠ ACKNOWLEDGEMENT IS "WE DISCUSSED THIS", NOT "I AGREE" (CFL-42-50).
    -- Recording agreement when somebody merely read it is a false record about a
    -- person. The column name says `acknowledged`, the button says
    -- "Confirm we discussed this", and the rendered state says "Discussed with
    -- Ravi on 14 March" — never "agreed".
    --
    -- An unacknowledged roadmap is STILL LIVE. Nothing is blocked by
    -- non-acknowledgement: a non-responsive employee must not be able to freeze
    -- their own development plan. It is surfaced back to the manager instead —
    -- no blocking workflow for a conversation that happens in a room.
    acknowledged_at   TIMESTAMPTZ NULL,
    acknowledged_by_user_id UUID  NULL REFERENCES users(id) ON DELETE SET NULL,

    -- Versioned, NOT overwritten. Roadmaps are re-agreed at each review, and
    -- "what did we agree in March" is the question this object exists to answer.
    superseded_at     TIMESTAMPTZ NULL,
    correlation_id    UUID        NOT NULL,

    CONSTRAINT chk_esr_version CHECK (version >= 1),
    CONSTRAINT chk_esr_content CHECK (btrim(content) <> ''),
    CONSTRAINT chk_esr_steps   CHECK (from_step_no >= 0 AND target_step_no >= 0),
    CONSTRAINT chk_esr_context CHECK (review_context IN
        ('PROBATION_REVIEW', 'MID_TERM_GOAL_REVIEW', 'PERFORMANCE_REVIEW', 'OFF_CYCLE')),
    -- Both acknowledgement columns or neither — a timestamp with no actor is an
    -- unattributable claim that somebody confirmed something.
    CONSTRAINT chk_esr_ack     CHECK ((acknowledged_at IS NULL) = (acknowledged_by_user_id IS NULL)),
    CONSTRAINT fk_esr_target FOREIGN KEY (target_job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE RESTRICT,
    CONSTRAINT fk_esr_from FOREIGN KEY (from_job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE RESTRICT,
    UNIQUE (employee_id, version)
);

-- Exactly one LIVE roadmap per employee. A new version supersedes the previous
-- one inside the same transaction; the previous one stays READABLE, which is the
-- entire reason this table is versioned rather than updated in place.
CREATE UNIQUE INDEX IF NOT EXISTS uq_esr_one_live
    ON employee_step_roadmaps (employee_id) WHERE superseded_at IS NULL;

-- "Which of the roadmaps I wrote has nobody confirmed?" — the manager's own
-- follow-up list, which is what replaces a blocking workflow.
CREATE INDEX IF NOT EXISTS idx_esr_unacknowledged
    ON employee_step_roadmaps (company_id, authored_by_user_id)
    WHERE acknowledged_at IS NULL AND superseded_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_esr_employee
    ON employee_step_roadmaps (employee_id, version DESC);


DO $$
DECLARE n INT;
BEGIN
    SELECT COUNT(*) INTO n FROM companies WHERE display_step_to_employee;
    RAISE NOTICE 'KAN-207: roadmaps ready. % company(ies) display the step to '
                 'employees (the default). The switch prevents DISPLAY, not '
                 'inference — the ladder stays readable either way.', n;
END $$;

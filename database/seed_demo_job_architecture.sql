-- ─────────────────────────────────────────────────────────────────────────────
-- DEMO DATA — one worked example job ladder (KAN-190 · T-190-6)
--
-- ⚠ DEV AND DEMO ONLY. **Never run in CI, and never referenced from
-- `seed_rbac.sql`.** The product ships a CONFIGURATOR, not a ladder: an
-- opinionated default would be a claim about how a customer organises work, and
-- they would have to undo it before they could start. `seed_rbac.sql` therefore
-- registers the feature and its permissions and stops there.
--
-- This file exists so a demo has something real to walk through — the ladder
-- reading as a genuine description of the work is on the Demo Readiness Gate's
-- must-be-walked-by-a-human list (R-18), and that is impossible to rehearse
-- against "Level 1 / Level 2 / Level 3".
--
-- ⚠ NO PAY DATA. Not one amount, not one percentage, not one currency. Pay
-- points arrive with KAN-206 on `compensation:w`, and a demo seed carrying money
-- would put figures in front of anyone who can read the ladder — which is
-- everybody, by design.
--
-- Idempotent: re-running changes nothing.
--
--   psql -d employee -f database/seed_demo_job_architecture.sql
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    co   UUID;
    fam  UUID;
    lvl  UUID;
BEGIN
    SELECT id INTO co FROM companies WHERE name = 'Acme Corp' LIMIT 1;
    IF co IS NULL THEN
        RAISE NOTICE 'Demo ladder skipped: no Acme Corp in this database.';
        RETURN;
    END IF;

    -- ── Engineering ───────────────────────────────────────────────────────────
    INSERT INTO job_families (company_id, code, name, description, sort_order)
    VALUES (co, 'ENG', 'Engineering',
            'Builds and runs the product — software, platform and quality.', 1)
    ON CONFLICT (company_id, code) DO NOTHING;
    SELECT id INTO fam FROM job_families WHERE company_id = co AND code = 'ENG';

    -- Level 1 — Trainee. THREE steps above entry, not five: the distance from
    -- trainee to junior is genuinely shorter than junior to mid, which is the
    -- whole reason `step_count` is per level and has no default.
    INSERT INTO job_levels (company_id, job_family_id, ordinal, title, short_code, step_count, description)
    VALUES (co, fam, 1, 'Trainee Software Engineer', 'L1', 3,
            'Learning the codebase and the craft with close support.')
    ON CONFLICT (job_family_id, ordinal) DO NOTHING;
    SELECT id INTO lvl FROM job_levels WHERE job_family_id = fam AND ordinal = 1;

    INSERT INTO job_step_expectations (job_level_id, company_id, step_no, summary, description, drafted_by)
    VALUES
      (lvl, co, 0, 'Learning the codebase with close support',
       'Works on small, well-defined tasks chosen by their mentor. Asks questions '
       'early rather than staying stuck. Can run the app locally, find their way '
       'around the repository and open a pull request that passes CI.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 1, 'Completes small defined tasks with review',
       'Picks up a ticket that has already been scoped and finishes it without '
       'day-to-day prompting. Writes a test alongside the change. Responds to '
       'review comments and understands why they were made.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 2, 'Works through a ticket independently',
       'Takes a scoped ticket from start to merged without needing the work broken '
       'down further. Spots when a ticket is ambiguous and asks before building the '
       'wrong thing. Reviews a peer''s small change usefully.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 3, 'Ready to own a feature end to end',
       'Consistently delivers scoped work at the quality the team expects. Has '
       'begun contributing to how work is shaped rather than only executing it. '
       'The step at which a move to Junior is a conversation worth having.', 'Priya Raman, Head of Engineering')
    ON CONFLICT (job_level_id, step_no) DO NOTHING;

    -- Level 2 — Junior. FIVE steps above entry, so `.0 … .5` — the owner's own
    -- worked example, so a demo can be walked against exactly what he described.
    INSERT INTO job_levels (company_id, job_family_id, ordinal, title, short_code, step_count, description)
    VALUES (co, fam, 2, 'Junior Software Fullstack Engineer', 'L2', 5,
            'Delivers features across the stack with review.')
    ON CONFLICT (job_family_id, ordinal) DO NOTHING;
    SELECT id INTO lvl FROM job_levels WHERE job_family_id = fam AND ordinal = 2;

    INSERT INTO job_step_expectations (job_level_id, company_id, step_no, summary, description, drafted_by)
    VALUES
      (lvl, co, 0, 'Delivers well-scoped features with review',
       'Owns a feature that has been specified for them, front to back, and ships '
       'it behind review. Writes tests without being asked. Knows which parts of '
       'the system they do not yet understand.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 1, 'Shapes the how, given the what',
       'Given a goal rather than a design, proposes an approach and checks it '
       'before building. Breaks their own work into reviewable pieces. Handles the '
       'unhappy paths without being reminded.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 2, 'Trusted with production changes',
       'Ships changes that touch live data or customer-visible behaviour, having '
       'thought about migration, rollback and what happens if it is wrong. '
       'On call-adjacent work they can diagnose before escalating.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 3, 'Improves the codebase around the task',
       'Leaves the area they worked in better than they found it, without turning '
       'every ticket into a refactor. Reviews others'' work substantively, '
       'including designs and not only diffs.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 4, 'Owns a slice of the system',
       'Is the person the team asks about one area. Anticipates the consequences '
       'of a change beyond their own component. Mentors a trainee without being '
       'asked to.', 'Priya Raman, Head of Engineering'),
      (lvl, co, 5, 'Operating beyond the level',
       'Consistently doing work that would be unremarkable from a mid-level '
       'engineer. The step at which a level change is overdue rather than '
       'aspirational.', 'Priya Raman, Head of Engineering')
    ON CONFLICT (job_level_id, step_no) DO NOTHING;

    -- Level 3 — Mid. Deliberately left with NO expectations authored, so the
    -- incomplete state is demoable. An empty ladder and a complete ladder are
    -- both easy; the half-authored one is where the product has to be honest,
    -- and it is what KAN-191's step assessment will refuse to work against.
    INSERT INTO job_levels (company_id, job_family_id, ordinal, title, short_code, step_count, description)
    VALUES (co, fam, 3, 'Software Engineer', 'L3', 5,
            'Owns significant work with limited direction.')
    ON CONFLICT (job_family_id, ordinal) DO NOTHING;

    -- ── Commercial — a second family, so "per family" is visible ─────────────
    INSERT INTO job_families (company_id, code, name, description, sort_order)
    VALUES (co, 'COM', 'Commercial',
            'Wins and keeps customers — sales, partnerships and success.', 2)
    ON CONFLICT (company_id, code) DO NOTHING;
    SELECT id INTO fam FROM job_families WHERE company_id = co AND code = 'COM';

    -- TWO steps above entry. A different shape again, on purpose.
    INSERT INTO job_levels (company_id, job_family_id, ordinal, title, short_code, step_count, description)
    VALUES (co, fam, 1, 'Account Executive', 'C1', 2,
            'Runs a defined book of business.')
    ON CONFLICT (job_family_id, ordinal) DO NOTHING;

    RAISE NOTICE 'Demo ladder seeded for Acme Corp: 2 families, 4 levels, '
                 'L3 deliberately left undescribed so the incomplete state is demoable.';
END $$;

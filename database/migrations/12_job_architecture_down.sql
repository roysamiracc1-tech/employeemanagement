-- ─────────────────────────────────────────────────────────────────────────────
-- 12 · DOWN — KAN-190 job architecture
--
-- ⚠ THIS DESTROYS AUTHORED CONTENT. `job_step_expectations` holds text a
-- customer's engineering managers wrote — six blocks per level — and it is not
-- derivable from anything. `employee_job_assignments` holds who is on which
-- level and step, which is a governed record, not a cache.
--
-- Ordered children-first so the composite FKs and the CASCADE do not fight.
-- btree_gist is deliberately NOT dropped: other things will use it, and dropping
-- a shared extension to undo one migration is the destructive direction.
--
-- The `job_architecture` feature row and its role grants ARE removed, because a
-- feature code pointing at absent tables is worse than no feature code — it
-- renders a nav link to a 500.
-- ─────────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trg_eja_step_valid ON employee_job_assignments;
DROP FUNCTION IF EXISTS employee_job_assignment_step_valid();

DROP TABLE IF EXISTS employee_job_assignments;
DROP TABLE IF EXISTS job_step_expectations;
DROP TABLE IF EXISTS job_levels;
DROP TABLE IF EXISTS job_families;

DELETE FROM role_feature_access
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'job_architecture');
DELETE FROM company_role_feature_access
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'job_architecture');
DELETE FROM company_features
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'job_architecture');
DELETE FROM portal_features WHERE code = 'job_architecture';

-- ─────────────────────────────────────────────────────────────────────────────
-- 13 · DOWN — KAN-191 employee level mapping
--
-- Drops the mapping table and the two integrity constraints. It does NOT touch
-- `employee_job_assignments` rows: those are who is on which level, a governed
-- record and not a cache, and they are still readable by migration 12's schema.
--
-- ⚠ Dropping `excl_eja_no_overlap` and `uq_eja_one_current` makes overlapping
-- and duplicate-current rows possible again. If this is rolled back and rolled
-- forward, re-check for overlaps before re-adding them — the constraint will
-- refuse to be created over data that already violates it, which is the correct
-- and useful failure:
--     SELECT a.employee_id FROM employee_job_assignments a
--       JOIN employee_job_assignments b ON b.employee_id = a.employee_id AND b.id <> a.id
--      WHERE daterange(a.effective_from, a.effective_to, '[)')
--         && daterange(b.effective_from, b.effective_to, '[)');
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE employee_job_assignments DROP CONSTRAINT IF EXISTS excl_eja_no_overlap;
DROP INDEX IF EXISTS uq_eja_one_current;
DROP TABLE IF EXISTS job_title_level_map;

-- ─────────────────────────────────────────────────────────────────────────────
-- 10 · DOWN — KAN-189 effective dating
--
-- Dropping the column loses every effective date ever chosen, which is real
-- history and not derivable from anything else: once it is gone there is no way
-- to tell whether a move was backdated to the 1st or applied on the 17th.
-- `_apply_change` then falls back to CURRENT_DATE, so the system keeps working
-- and the RECORD of intent is what is destroyed.
--
-- Rows already written to employee_org_assignments / manager_relationships are
-- NOT touched — their dates stay as applied. That is deliberate: rewriting
-- applied history to undo a schema change would be the destructive direction.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE org_change_requests
    DROP COLUMN IF EXISTS effective_date;

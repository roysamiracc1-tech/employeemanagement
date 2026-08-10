-- ─────────────────────────────────────────────────────────────────────────────
-- 14 · DOWN — KAN-207 step roadmaps
--
-- ⚠ DROPPING THE TABLE DESTROYS WHAT WAS AGREED WITH PEOPLE. A roadmap is text a
-- manager wrote for a named individual, and its acknowledgement is a record that
-- a conversation happened on a date. Neither is derivable from anything else, and
-- "what did we agree in March" is the question the table exists to answer.
--
-- `companies.display_step_to_employee` is dropped too, which silently returns
-- every tenant to the default (display ON). A company that deliberately switched
-- it OFF would have that decision reversed without anybody being told — so if
-- this is ever run in anger, record which companies had it off FIRST:
--     SELECT name FROM companies WHERE NOT display_step_to_employee;
-- ─────────────────────────────────────────────────────────────────────────────

DROP INDEX IF EXISTS idx_esr_employee;
DROP INDEX IF EXISTS idx_esr_unacknowledged;
DROP INDEX IF EXISTS uq_esr_one_live;
DROP TABLE IF EXISTS employee_step_roadmaps;

ALTER TABLE companies DROP COLUMN IF EXISTS display_step_to_employee;

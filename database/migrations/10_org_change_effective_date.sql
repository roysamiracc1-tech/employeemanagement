-- ─────────────────────────────────────────────────────────────────────────────
-- 10 · KAN-189 — effective dating for position changes (ADR-020, closes CFL-4)
--
-- Carries the DATE a position change takes effect, so placement and pay can move
-- on the same day instead of "whenever the last approver happened to click".
--
-- NULLABLE ON PURPOSE, and it is not laziness:
--   • it cannot fail on the rows already in the table, and
--   • a request raised BEFORE this migration keeps its original meaning —
--     "apply on the day it is approved". A NOT NULL default of CURRENT_DATE
--     would have back-stamped every historical request with the migration date,
--     inventing an effective date that nobody ever chose.
-- `create_request()` defaults it to today from KAN-189 onward, so new rows are
-- always populated; readers still tolerate NULL for the historical ones.
--
-- NOTE ON NUMBERING: the technical design (§9.2 T-189-2, §14 migration table)
-- bundles this column into `10_tenant_feature_switch.sql` alongside KAN-188's
-- tenant switch. KAN-189 shipped first and alone, so bundling would have meant
-- committing a half-written migration named after work that does not exist yet.
-- This file carries KAN-189 only; **KAN-188 takes 11**.
--
-- Down migration: 10_org_change_effective_date_down.sql
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE org_change_requests
    ADD COLUMN IF NOT EXISTS effective_date DATE NULL;

COMMENT ON COLUMN org_change_requests.effective_date IS
    'The date the move takes effect (ADR-020). Drives BOTH the effective_to of '
    'the outgoing assignment and the effective_from of the incoming one, so the '
    'two cannot disagree. NULL only on requests raised before KAN-189, which '
    'mean "apply on approval". Half-open [from, to) — see TECHNICAL_DOCUMENTATION.';


-- ─────────────────────────────────────────────────────────────────────────────
-- DEF-42-2 REPAIR — close the reporting lines that were closed without a date.
--
-- `_apply_change` used to set `is_current = FALSE` and nothing else on the
-- superseded SOLID_LINE row, leaving it with a NULL `effective_to`: closed by the
-- flag, open-ended by the dates. Anything that trusts the dates rather than the
-- flag reads it as still in force. The code no longer does this; these are the
-- rows it already left behind (2 in the dev database at the time of writing).
--
-- THE END DATE IS DERIVED, NOT INVENTED. Under half-open `[from, to)` a
-- relationship ended exactly when its successor began, so the successor's
-- `effective_from` IS the missing value — it is recovered from data that was
-- always there, not guessed.
--
-- Deliberately conservative:
--   • only rows that HAVE a successor are touched. With no successor there is
--     nothing to derive from, and a guess is worse than an honest NULL;
--   • `is_current = FALSE` only — a current row is supposed to have a NULL end;
--   • `IS NULL` only — an existing date is never overwritten;
--   • idempotent: re-running matches nothing, because the rows now have dates.
--
-- Not mirrored into schema.sql or the seeds, and that is correct rather than an
-- oversight: schema.sql is structure, and `seed_data.sql` / `telia_seed.sql`
-- insert only `is_current = TRUE` rows, so a fresh CI database has none of this
-- shape to repair. This is a one-off repair of history on databases that already
-- ran the old code.
-- ─────────────────────────────────────────────────────────────────────────────

UPDATE manager_relationships mr
   SET effective_to = s.starts
  FROM (
        SELECT m.id,
               MIN(n.effective_from) AS starts
          FROM manager_relationships m
          JOIN manager_relationships n
            ON n.employee_id       = m.employee_id
           AND n.relationship_type = m.relationship_type
           AND n.id               <> m.id
           AND n.effective_from   >= m.effective_from
         WHERE m.is_current = FALSE
           AND m.effective_to IS NULL
         GROUP BY m.id
       ) s
 WHERE mr.id = s.id;

-- Anything still NULL after this has no successor to derive from and is LEFT
-- ALONE on purpose. Surfaced rather than hidden, so it is a known quantity:
DO $$
DECLARE n INT;
BEGIN
    SELECT COUNT(*) INTO n
      FROM manager_relationships
     WHERE is_current = FALSE AND effective_to IS NULL;
    IF n > 0 THEN
        RAISE NOTICE 'DEF-42-2: % closed reporting line(s) still have no end date '
                     '(no successor to derive one from). Left as NULL deliberately.', n;
    END IF;
END $$;

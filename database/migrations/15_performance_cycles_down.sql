-- ─────────────────────────────────────────────────────────────────────────────
-- 15 · DOWN — EP44 P0 review cycles and participants
--
-- ⚠ THIS DESTROYS REVIEW ROUNDS AND WHO WAS IN THEM. A participant row is the
-- record of a decision about a named person — including every exclusion and the
-- reason for it, which is precisely what somebody would later be asked to
-- justify. None of it is derivable from anything else.
--
-- Ordered children-first. The `performance` feature row and its grants go too:
-- a feature code pointing at absent tables renders a nav link to a 500.
-- ─────────────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS performance_cycle_participants;
DROP INDEX IF EXISTS uq_pc_one_active;
DROP TABLE IF EXISTS performance_cycles;

DELETE FROM role_feature_access
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'performance');
DELETE FROM company_role_feature_access
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'performance');
DELETE FROM company_features
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'performance');
DELETE FROM portal_features WHERE code = 'performance';

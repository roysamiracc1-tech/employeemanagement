-- ─────────────────────────────────────────────────────────────────────────────
-- 11 · DOWN — KAN-188 tenant feature switch
--
-- Drops the column ONLY. The materialised `company_features` rows are LEFT IN
-- PLACE, deliberately, and this is the important half of the file.
--
-- Deleting them would be the destructive direction twice over:
--   • a row that was deliberately switched OFF by an administrator after this
--     migration is a real decision, and it is indistinguishable by then from a
--     row this migration created;
--   • with the code rolled back, surplus rows are INERT — the pre-KAN-188
--     resolver never reads `company_features` at all, and the two hand-rolled
--     checks only ever look at `reports` and `skills_intelligence`.
--
-- So leaving them costs nothing and removing them could destroy an intent
-- nobody can reconstruct. The repair in step 2 of the up-migration is likewise
-- NOT reversed: it made stored values match behaviour that was already true.
--
-- If rows genuinely must go, do it deliberately and with the list in front of
-- you — it is not something a rollback should do on your behalf:
--     SELECT c.name, pf.code, cf.is_enabled
--       FROM company_features cf
--       JOIN companies c ON c.id = cf.company_id
--       JOIN portal_features pf ON pf.id = cf.feature_id
--      ORDER BY c.name, pf.code;
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE portal_features
    DROP COLUMN IF EXISTS default_enabled;

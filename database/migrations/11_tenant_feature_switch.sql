-- ─────────────────────────────────────────────────────────────────────────────
-- 11 · KAN-188 — the per-company feature switch (R7 · ADR-016c)
--
-- Makes `company_features.is_enabled` a real term in effective access:
--
--     effective access = tenant switch AND role grant
--
-- Today the column exists but only TWO features consult it, via hand-rolled
-- checks inside `analytics.py` and `skills_intelligence.py`. This migration
-- makes the data safe to read centrally; the resolver change does the reading.
--
-- ⚠ THE DANGEROUS PART, AND WHY THIS IS A REPAIR-THEN-MATERIALISE:
--
-- 18 rows exist. 14 of them are `is_enabled = FALSE`, for features that NOTHING
-- CURRENTLY READS — company_settings, employee_profiles, org_structure, skills,
-- system_config, user_accounts, vacations, across Acme and Telia. They are
-- FALSE because nobody ever set them TRUE, not because anyone decided those
-- companies should not have those features. Their real, observable effect today
-- is nil: every one of those features is fully available.
--
-- Start reading them centrally without repairing them first and most of the
-- product switches off for two of the three companies, instantly. A green test
-- suite would not notice — no test asserts "HR_ADMIN can still reach vacations
-- at Acme". `tests/fixtures/feature_matrix_before.json` was captured through the
-- real resolver before any of this, precisely so that it does get noticed.
--
-- So, in order:
--   1. REPAIR   — set TRUE the rows whose FALSE has no effect today, so the
--                 stored value finally matches observed behaviour. `reports`
--                 and `skills_intelligence` are EXCLUDED: their values are
--                 live, honoured by the hand-rolled checks, and a genuine
--                 administrative decision that must survive.
--   2. MATERIALISE — insert a row for every (company, feature) pair that has
--                 none, defaulting from `portal_features.default_enabled`, so
--                 the resolver never has to reason about a missing row and the
--                 admin UI has something to toggle for every feature.
--
-- Down migration: 11_tenant_feature_switch_down.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 1. The default for a feature nobody has decided about ────────────────────
-- A COLUMN, not a Python constant: the answer to "is this feature on for a
-- brand-new company?" is product data that a SYSTEM_ADMIN should be able to
-- change, and a constant would make it a code deploy. TRUE by default, because
-- every existing feature is currently available to every company — a FALSE
-- default here would turn this migration into a product-wide blackout.
ALTER TABLE portal_features
    ADD COLUMN IF NOT EXISTS default_enabled BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN portal_features.default_enabled IS
    'Whether a company with no company_features row gets this feature (KAN-188). '
    'Data, not a constant, so onboarding defaults are administrable. After this '
    'migration every (company, feature) pair is materialised, so this governs '
    'NEW companies and NEW features only.';

-- ⚠ THE TWO LICENSED FEATURES DEFAULT TO **OFF**, and getting this wrong is how
-- the migration silently GRANTS access instead of preserving it.
--
-- `reports` and `skills_intelligence` are the only two features that were ever
-- actually gated, by the hand-rolled checks in `analytics.py` and
-- `skills_intelligence.py`. Those checks read "no company_features row" as
-- **DENIED**. Every other feature was ungated, i.e. effectively always on.
--
-- So the historical default is genuinely different for these two, and a blanket
-- TRUE would hand them to any company that never had a row. That is not
-- hypothetical: 'Sam Cpmapny' had no row for either, and a blanket default
-- switched both ON for them — caught only because the old gates were compared
-- directly, since they lived OUTSIDE the resolver and so were invisible to the
-- 330-cell matrix.
--
-- Preserving behaviour means these two default OFF and everything else ON.
UPDATE portal_features
   SET default_enabled = FALSE
 WHERE code IN ('reports', 'skills_intelligence');


-- ── 2. REPAIR — make the stored value match the observed behaviour ───────────
-- Only rows that are FALSE *and* belong to a feature nothing consults. Anything
-- already TRUE is untouched, and the two live features are excluded by name.
--
-- Idempotent: after this runs there are no matching rows left.
UPDATE company_features cf
   SET is_enabled = TRUE,
       enabled_at = COALESCE(cf.enabled_at, NOW())
  FROM portal_features pf
 WHERE pf.id = cf.feature_id
   AND cf.is_enabled = FALSE
   AND pf.code NOT IN ('reports', 'skills_intelligence');

-- ── 3. MATERIALISE — one row per (company, feature), no gaps ─────────────────
-- After this the resolver's LEFT JOIN always finds a row for an existing
-- company, so "no row" stops being a state anybody has to think about. The
-- COALESCE in the resolver remains as a guard for companies created later.
INSERT INTO company_features (company_id, feature_id, is_enabled, enabled_at)
SELECT c.id, pf.id, pf.default_enabled, NOW()
  FROM companies c
 CROSS JOIN portal_features pf
 WHERE NOT EXISTS (
        SELECT 1 FROM company_features x
         WHERE x.company_id = c.id AND x.feature_id = pf.id);

-- ── 4. Report what happened, so this is not a silent bulk write ──────────────
DO $$
DECLARE tot INT; off_ct INT; cos INT; feats INT;
BEGIN
    SELECT COUNT(*) INTO tot    FROM company_features;
    SELECT COUNT(*) INTO off_ct FROM company_features WHERE is_enabled = FALSE;
    SELECT COUNT(*) INTO cos    FROM companies;
    SELECT COUNT(*) INTO feats  FROM portal_features;
    RAISE NOTICE 'KAN-188: % company_features rows for % companies x % features '
                 '(expected %); % switched OFF.', tot, cos, feats, cos * feats, off_ct;
    IF tot <> cos * feats THEN
        RAISE EXCEPTION 'KAN-188: materialise incomplete — % rows, expected %',
                        tot, cos * feats;
    END IF;
END $$;

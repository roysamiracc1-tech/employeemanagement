-- ─────────────────────────────────────────────────────────────────────────────
-- 08_audit_log_down.sql
-- Reverses 08_audit_log.sql (EP38 / KAN-187, ADR-009).
--
-- Idempotent: safe to re-run, and safe to run against a database where the up
-- migration never applied.
--
-- ⚠ RUNBOOK CAVEAT — read before running in any environment with tenant data.
-- Rollback is clean and total ONLY while audit_log is empty. Once tenant audit
-- rows exist, DROP TABLE audit_log is a DATA-LOSS event that destroys audit
-- history, and audit history is by definition unreproducible. Take a dump of
-- audit_log first, or do not run this. (Technical design §8.1.)
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Feature access rows, then the feature itself.
--    role_feature_access.feature_id and company_role_feature_access.feature_id
--    are ON DELETE CASCADE, so the child grants go with the parent; the explicit
--    DELETE below simply makes the intent visible and keeps the file readable if
--    the cascade is ever changed.
DELETE FROM role_feature_access
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'audit_log');

DELETE FROM company_role_feature_access
 WHERE feature_id IN (SELECT id FROM portal_features WHERE code = 'audit_log');

DELETE FROM portal_features WHERE code = 'audit_log';

-- 2. The trail. DROP TABLE takes its indexes AND the BEFORE UPDATE trigger with
--    it, so there is no separate DROP TRIGGER — `DROP TRIGGER IF EXISTS ... ON
--    audit_log` would itself fail once the table is gone, breaking re-runs.
--    The trigger function is table-independent and is dropped after.
DROP TABLE IF EXISTS audit_log;
DROP FUNCTION IF EXISTS audit_log_immutable();

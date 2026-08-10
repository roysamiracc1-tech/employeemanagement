-- ─────────────────────────────────────────────────────────────────────────────
-- 09_notification_related_entity_down.sql
-- Reverses 09_notification_related_entity.sql (DEF-001 / DEF-003).
--
-- Idempotent: safe to re-run, and safe against a database where the up
-- migration never applied.
--
-- Rollback is non-destructive to notifications themselves — only the linkage is
-- lost. The consequence is that "awaiting your approval" notifications stop
-- being resolved when a request is decided and start accumulating in the bell
-- again, which is exactly the defect this migration exists to fix.
-- ─────────────────────────────────────────────────────────────────────────────

DROP INDEX IF EXISTS idx_user_notifications_related_unread;

ALTER TABLE user_notifications
    DROP COLUMN IF EXISTS related_id,
    DROP COLUMN IF EXISTS related_type;

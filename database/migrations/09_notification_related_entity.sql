-- ─────────────────────────────────────────────────────────────────────────────
-- 09_notification_related_entity.sql
-- DEF-001 / DEF-003 — give an in-app notification a link back to the thing it
-- is about, so a notification can be RESOLVED when that thing is decided.
--
-- Why this is needed: `user_notifications` held only (event_type, message, link).
-- A message such as "Position change requested for X — awaiting your approval
-- (level 1 of 2)" therefore had no way to know which request it referred to, so
-- it survived in the bell for ever — including after that request was rejected
-- and the approver could no longer act on it. Matching on message TEXT was the
-- alternative and was rejected: it breaks the moment the copy is reworded or
-- translated, and two employees with the same name would collide.
--
-- Adds:
--   * user_notifications.related_type — polymorphic discriminator (no FK, the
--     column must be able to point at requests, leave, imports … without this
--     table growing a foreign key per subsystem)
--   * user_notifications.related_id   — the entity's id
--   * a PARTIAL index over the unread rows only, which is the only set the
--     resolve query and the bell ever touch
--
-- Idempotent: safe to re-run. Reverse with 09_notification_related_entity_down.sql.
--
-- Deliberate design points — do NOT "fix" these:
--   * NULLable, with no backfill. Every notification written before this
--     migration genuinely has no known subject; inventing one would be a lie in
--     the data. Un-tagged rows keep the old behaviour (they are cleared by the
--     user reading them) and that is correct.
--   * No FOREIGN KEY on related_id. It is polymorphic by design. A notification
--     must also outlive the row it describes — a cascade delete would silently
--     rewrite a user's notification history when an entity is purged.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE user_notifications
    ADD COLUMN IF NOT EXISTS related_type VARCHAR(40) NULL,
    ADD COLUMN IF NOT EXISTS related_id   UUID        NULL;

-- The resolve path looks up (related_type, related_id) among UNREAD rows only;
-- read rows are already resolved by definition. Partial keeps it small.
CREATE INDEX IF NOT EXISTS idx_user_notifications_related_unread
    ON user_notifications (related_type, related_id)
    WHERE NOT is_read;

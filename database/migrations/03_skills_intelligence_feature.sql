-- Add skills_intelligence to portal_features and seed default role access.
-- Safe to re-run (all statements use ON CONFLICT DO NOTHING).

INSERT INTO portal_features (code, label, description, sort_order)
VALUES ('skills_intelligence', 'Skills Intelligence', 'Benchmark company skills against industry trends', 9)
ON CONFLICT (code) DO NOTHING;

-- Default access: PORTAL_ADMIN (read+write), HR_ADMIN (read only)
-- SYSTEM_ADMIN is handled separately below.
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, f.id, TRUE, TRUE, FALSE
FROM roles ro, portal_features f
WHERE ro.name = 'PORTAL_ADMIN' AND f.code = 'skills_intelligence'
ON CONFLICT (role_id, feature_id) DO NOTHING;

INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, f.id, TRUE, FALSE, FALSE
FROM roles ro, portal_features f
WHERE ro.name = 'HR_ADMIN' AND f.code = 'skills_intelligence'
ON CONFLICT (role_id, feature_id) DO NOTHING;

-- SYSTEM_ADMIN gets full access to all features
INSERT INTO role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT r.id, f.id, TRUE, TRUE, TRUE
FROM roles r, portal_features f
WHERE r.name = 'SYSTEM_ADMIN' AND f.code = 'skills_intelligence'
ON CONFLICT (role_id, feature_id) DO NOTHING;

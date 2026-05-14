# CLAUDE.md — Project Rules

## Access Control — NEVER hardcode role checks for feature visibility

**Access to features is controlled entirely by two tables:**

- `role_feature_access` — global ceiling, set by SYSTEM_ADMIN via Roles & Permissions
- `company_role_feature_access` — per-company overrides, set by PORTAL_ADMIN via Feature Access tab

**The rules:**

1. Route guards use `@require_feature_access('feature_code')` — never `@require_roles(...)` for feature pages.
2. Nav links use `{% if has_feature_access('feature_code') %}` — never hardcoded `has_role(...)` for feature links.
3. Do NOT add extra per-feature role checks inside routes (e.g. `_si_enabled_for_hr`, `enabled_for_hr` checks). These bypass the permission system and block roles that have been correctly granted access.
4. SYSTEM_ADMIN always has full access — handled automatically in `_load_feature_access()`.
5. If a role has access in `role_feature_access` and is not overridden by `company_role_feature_access`, they get access. Period.

**Adding a new feature:**
- Add it to `portal_features` in `setup_db.py` and a migration SQL under `database/migrations/`
- Seed default `role_feature_access` rows for the roles that should have it by default
- Use `@require_feature_access('your_feature_code')` on routes
- Use `{% if has_feature_access('your_feature_code') %}` in nav

**Past mistakes to never repeat:**
- Skills Intelligence had a legacy `enabled_for_hr` flag that blocked HR_ADMIN even after they were granted access via `role_feature_access`. This was removed. Never add sub-flags like this again.
- Skills Intelligence routes used `@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')` hardcoded — this broke when the admin granted access to other roles (e.g. Solid Line Manager). Hardcoded role lists on feature routes are forbidden.

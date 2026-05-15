# CLAUDE.md — Project Rules

## BEFORE CONFIRMING ANY CHANGE TO THE USER

**Run `python -m pytest -q` and verify 0 failures. Then manually check these 5 things:**

1. Does the UI show data ONLY scoped to the correct company / role? (No global template roles bleeding in.)
2. Does a company with NO custom roles show an empty state — not global roles like EMPLOYEE, DEPARTMENT_HEAD?
3. Does `role_feature_access` and `company_role_feature_access` only query `company_id = specific UUID` — never `OR company_id IS NULL` when showing a company's own roles?
4. Does every feature route use `@require_feature_access(...)` — never a hardcoded `@require_roles(...)` list?
5. Does SYSTEM_ADMIN bypass all feature checks automatically?

**Only confirm to the user AFTER all 5 pass. No exceptions.**



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

**Company roles are ONLY roles with `company_id = that company's UUID`.** Never query `OR company_id IS NULL` when showing a company's roles — that pulls in global template roles (EMPLOYEE, DEPARTMENT_HEAD, etc.) which the company has NOT created. Every query that lists or shows roles for a specific company must filter `WHERE company_id = %s::uuid` only.

**Past mistakes to never repeat:**
- Skills Intelligence had a legacy `enabled_for_hr` flag that blocked HR_ADMIN even after they were granted access via `role_feature_access`. This was removed. Never add sub-flags like this again.
- Skills Intelligence routes used `@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')` hardcoded — this broke when the admin granted access to other roles (e.g. Solid Line Manager). Hardcoded role lists on feature routes are forbidden.

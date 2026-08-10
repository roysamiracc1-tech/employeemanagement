-- ─────────────────────────────────────────────────────────────────────────────
-- 07_perf_indexes.sql
-- Architecture-review performance fixes (KAN-154, KAN-157 / findings F6, F23).
--
-- Adds indexes on the columns the app filters/joins on most heavily. `company_id`
-- is the single most-filtered column across dashboard/directory/analytics/org
-- queries but was previously unindexed on `employees` (seq-scan per request).
-- Idempotent: safe to re-run.
-- ─────────────────────────────────────────────────────────────────────────────

-- F6/KAN-154 — the ubiquitous `company_id [+ ACTIVE]` predicate on employees.
-- Composite supersedes the low-cardinality single-column status index.
CREATE INDEX IF NOT EXISTS idx_employees_company_status
    ON employees (company_id, employment_status);
DROP INDEX IF EXISTS idx_employees_status;

-- F23/KAN-157 — org tables filtered by company on every admin/org-change form.
CREATE INDEX IF NOT EXISTS idx_business_units_company
    ON business_units (company_id);
CREATE INDEX IF NOT EXISTS idx_locations_company
    ON locations (company_id);
CREATE INDEX IF NOT EXISTS idx_functional_units_company
    ON functional_units (company_id);

-- F23/KAN-157 — vacation_requests joined/subqueried by vacation_type_id
-- (used-days aggregation, type listings). Only employee/manager/status existed.
CREATE INDEX IF NOT EXISTS idx_vacation_requests_type
    ON vacation_requests (vacation_type_id);

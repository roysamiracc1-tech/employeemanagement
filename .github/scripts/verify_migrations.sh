#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# verify_migrations.sh — migration apply / reverse / drift verification.
#
# Owned by DevOps (Engineering Charter §9: CI/CD pipelines). Invoked by the
# `migrations` job in .github/workflows/ci.yml, and runnable locally against any
# throwaway Postgres:
#
#     PGDATABASE=mig_check .github/scripts/verify_migrations.sh
#
# What it proves (each step prints PASS/FAIL and the job fails on the first FAIL):
#
#   1. database/schema.sql applies to an empty database.
#   2. Every forward migration in database/migrations/ replays onto that schema
#      without error and WITHOUT CHANGING IT — i.e. schema.sql is not missing
#      anything the migrations add, and every migration is idempotent.
#   3. The 08 audit-log migration reverses cleanly: down leaves no audit_log
#      table, function, feature row or grant behind.
#   4. Re-applying 08 after the reverse restores a structure byte-identical to
#      schema.sql — the upgrade path and the fresh-install path converge.
#   5. down is safe to run twice and safe to run where up never applied.
#   6. The append-only trigger actually rejects UPDATE.
#   7. THE DATA-LOSS BOUNDARY IS REAL: with rows present, down destroys them.
#      This is asserted deliberately so the runbook's warning cannot go stale —
#      if someone ever makes the down migration data-safe, this check goes red
#      and the runbook gets updated in the same PR.
#
# Structure comparison is done on a CANONICALISED dump (schema-only dump, reloaded
# into a scratch database, dumped again). The round-trip is required, not
# decoration: Postgres re-renders CHECK constraint expressions depending on how
# they were written (`x IN ('A','B')` vs `x::text = ANY(ARRAY[...]::text[])` dump
# to different — but semantically identical — text). One reload converges both
# renderings, so a raw text diff would false-positive without it.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MIG_DIR="$REPO_ROOT/database/migrations"
DB="${PGDATABASE:-employee_mig}"
SCRATCH="${DB}_canon"
TMP="$(mktemp -d)"
FAILURES=0

# ── Migrations that are KNOWN BROKEN and cannot currently be replayed ─────────
# Each entry needs a reason and an owner. A quarantined file that starts passing
# FAILS this script on purpose, so the entry cannot be left here forever.
#
#   05_per_company_roles.sql — step 5 (`UPDATE user_roles ur ... FROM users u
#   JOIN roles gr ON gr.id = ur.role_id`) references the UPDATE target inside its
#   own FROM clause. Postgres rejects this at plan time on every version:
#   `ERROR: invalid reference to FROM-clause entry for table "ur"` (psql exit 3).
#   The file has therefore never run to completion. Owner: Senior SWE (schema).
QUARANTINE=("05_per_company_roles.sql")

psql_q()  { psql -d "$DB" -v ON_ERROR_STOP=1 -tAc "$1"; }
psql_f()  { psql -d "$DB" -v ON_ERROR_STOP=1 -q -f "$1"; }

pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1"; FAILURES=$((FAILURES + 1)); }

# Canonical schema fingerprint: dump -> reload into a scratch DB -> dump again.
canonical_dump() {
    local out="$1"
    pg_dump --schema-only --no-owner --no-privileges -d "$DB" > "$TMP/raw.sql"
    dropdb --if-exists "$SCRATCH" >/dev/null 2>&1
    createdb "$SCRATCH"
    psql -d "$SCRATCH" -q -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' >/dev/null 2>&1
    psql -d "$SCRATCH" -q -f "$TMP/raw.sql" >/dev/null 2>&1
    pg_dump --schema-only --no-owner --no-privileges -d "$SCRATCH" \
        | grep -v '^--' | grep -v '^$' | grep -v '^\\\(un\)\?restrict ' > "$out"
    dropdb --if-exists "$SCRATCH" >/dev/null 2>&1
}

is_quarantined() {
    local name="$1"
    for q in "${QUARANTINE[@]}"; do [ "$q" = "$name" ] && return 0; done
    return 1
}

echo "=============================================================="
echo " Migration verification — database: $DB"
echo "=============================================================="

# ── 1. Authoritative schema ──────────────────────────────────────────────────
echo
echo "1. Build from database/schema.sql (+ RBAC seed)"
dropdb --if-exists "$DB" >/dev/null 2>&1
createdb "$DB"
psql -d "$DB" -q -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
if psql_f "$REPO_ROOT/database/schema.sql" >/dev/null 2>&1; then
    pass "schema.sql applied"
else
    fail "schema.sql did NOT apply"; exit 1
fi
psql_f "$REPO_ROOT/database/seed_rbac.sql" >/dev/null 2>&1 \
    && pass "seed_rbac.sql applied" || fail "seed_rbac.sql did NOT apply"
canonical_dump "$TMP/A.sql"

# ── 2. Replay every forward migration; assert it changes nothing ─────────────
echo
echo "2. Replay forward migrations onto the authoritative schema"
for f in "$MIG_DIR"/[0-9]*.sql; do
    name="$(basename "$f")"
    case "$name" in *_down.sql) continue ;; esac
    if is_quarantined "$name"; then
        if psql_f "$f" >/dev/null 2>&1; then
            fail "$name is in QUARANTINE but now applies cleanly — remove it from QUARANTINE in this script"
        else
            echo "  SKIP  $name (quarantined — known broken, see header)"
        fi
        continue
    fi
    if psql_f "$f" >/dev/null 2>&1; then
        pass "$name replayed"
    else
        fail "$name failed to replay onto schema.sql"
        psql -d "$DB" -v ON_ERROR_STOP=1 -f "$f" 2>&1 | grep -i '^psql.*ERROR' | head -3
    fi
done
canonical_dump "$TMP/B.sql"
if diff -u "$TMP/A.sql" "$TMP/B.sql" > "$TMP/drift_replay.diff"; then
    pass "replaying every migration left schema.sql's structure unchanged (no drift)"
else
    fail "migration replay CHANGED the structure — schema.sql and the migrations disagree"
    head -60 "$TMP/drift_replay.diff"
fi

# ── 3. Reverse 08 ────────────────────────────────────────────────────────────
echo
echo "3. Reverse 08_audit_log.sql"
if psql_f "$MIG_DIR/08_audit_log_down.sql" >/dev/null 2>&1; then
    pass "08_audit_log_down.sql ran"
else
    fail "08_audit_log_down.sql errored"
fi
[ "$(psql_q "SELECT to_regclass('public.audit_log') IS NULL")" = "t" ] \
    && pass "audit_log table removed"  || fail "audit_log table still present after down"
[ "$(psql_q "SELECT count(*) FROM pg_proc WHERE proname='audit_log_immutable'")" = "0" ] \
    && pass "audit_log_immutable() removed" || fail "trigger function survived down"
[ "$(psql_q "SELECT count(*) FROM portal_features WHERE code='audit_log'")" = "0" ] \
    && pass "portal_features row removed" || fail "portal_features row survived down"
[ "$(psql_q "SELECT count(*) FROM role_feature_access rfa JOIN portal_features f ON f.id=rfa.feature_id WHERE f.code='audit_log'")" = "0" ] \
    && pass "role_feature_access grants removed" || fail "grants survived down"

# ── 4. down is idempotent / safe where up never ran ──────────────────────────
echo
echo "4. Re-run down (idempotency / never-applied case)"
psql_f "$MIG_DIR/08_audit_log_down.sql" >/dev/null 2>&1 \
    && pass "down is re-runnable against a database that has no audit_log" \
    || fail "second down errored"

# ── 5. Re-apply up; assert convergence with schema.sql ───────────────────────
echo
echo "5. Re-apply 08_audit_log.sql and compare with the fresh-install structure"
psql_f "$MIG_DIR/08_audit_log.sql" >/dev/null 2>&1 && pass "up applied" || fail "up errored"
psql_f "$MIG_DIR/08_audit_log.sql" >/dev/null 2>&1 && pass "up is idempotent" || fail "second up errored"
[ "$(psql_q "SELECT count(*) FROM portal_features WHERE code='audit_log'")" = "1" ] \
    && pass "exactly one portal_features row after two applies" \
    || fail "portal_features row count wrong after re-apply"
canonical_dump "$TMP/C.sql"
if diff -u "$TMP/A.sql" "$TMP/C.sql" > "$TMP/drift_updown.diff"; then
    pass "down+up round-trip is structurally identical to schema.sql"
else
    fail "down+up round-trip DIVERGED from schema.sql"
    head -60 "$TMP/drift_updown.diff"
fi

# ── 6. Append-only enforcement ──────────────────────────────────────────────
echo
echo "6. Append-only enforcement"
CO="$(psql_q "SELECT id FROM companies LIMIT 1")"
if [ -z "$CO" ]; then
    fail "no company row available to write a probe audit row"
else
    psql_q "INSERT INTO audit_log (company_id, actor_label, action, entity_type, entity_id, reason, correlation_id)
            VALUES ('$CO','ci-probe <ci@local>','EMPLOYEE_STATUS_CHANGED','employee',
                    uuid_generate_v4(),'ci migration probe', uuid_generate_v4())" >/dev/null \
        && pass "INSERT accepted" || fail "INSERT rejected"
    if psql -d "$DB" -tAc "UPDATE audit_log SET reason='tampered'" >/dev/null 2>&1; then
        fail "UPDATE on audit_log SUCCEEDED — the append-only trigger is not doing its job"
    else
        pass "UPDATE on audit_log rejected by trg_audit_log_no_update"
    fi
fi

# ── 7. The data-loss boundary — asserted, so the runbook cannot go stale ────
echo
echo "7. Data-loss boundary (runbook: docs/runbooks/MIGRATIONS.md §4)"
BEFORE="$(psql_q "SELECT count(*) FROM audit_log")"
psql_f "$MIG_DIR/08_audit_log_down.sql" >/dev/null 2>&1
psql_f "$MIG_DIR/08_audit_log.sql"      >/dev/null 2>&1
AFTER="$(psql_q "SELECT count(*) FROM audit_log")"
if [ "$BEFORE" -gt 0 ] && [ "$AFTER" = "0" ]; then
    pass "confirmed: down destroys $BEFORE audit row(s) — runbook §4 STOP condition is accurate"
else
    fail "down no longer destroys audit rows (before=$BEFORE after=$AFTER). This is a BEHAVIOUR CHANGE: update docs/runbooks/MIGRATIONS.md §4 in the same PR."
fi

# ── Result ──────────────────────────────────────────────────────────────────
dropdb --if-exists "$SCRATCH" >/dev/null 2>&1
rm -rf "$TMP"
echo
echo "=============================================================="
if [ "$FAILURES" -eq 0 ]; then
    echo " MIGRATION VERIFICATION: PASS"
    exit 0
fi
echo " MIGRATION VERIFICATION: $FAILURES FAILURE(S)"
exit 1

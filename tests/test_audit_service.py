"""EP38 / KAN-187 — the audit subsystem (ADR-009).

Three tiers:

1. **Contract** (always run) — validation rules of `audit_service._build_row`,
   which is pure and needs no database.
2. **Transaction mechanics** (always run) — the fake connection from
   `test_transactions` proves the load-bearing property: `record()` writes into
   the caller's open transaction, opens none of its own, and commits nothing.
3. **Real Postgres** (skipped when no DB is reachable) — atomicity with the
   change being audited, the append-only trigger, the NOT NULL tenant scope,
   cross-tenant isolation, and a full up/down migration cycle on a genuinely
   fresh database.

All data is synthetic. Real-DB rows are written with a unique correlation id and
deleted afterwards (DELETE is deliberately not blocked — ADR-009 §3.2a / TD-13).
"""
import json
import os
import subprocess
import uuid

import psycopg2
import pytest

from app import app as flask_app
from app.db import execute, query, transaction
from app.services import audit_service as audit
from app.services.audit_service import AuditError

from tests.test_transactions import FakeConnection


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATION_UP = os.path.join(REPO, 'database', 'migrations', '08_audit_log.sql')
MIGRATION_DOWN = os.path.join(REPO, 'database', 'migrations', '08_audit_log_down.sql')

ACTOR = {
    'user_id': str(uuid.uuid4()),
    'employee_id': str(uuid.uuid4()),
    'roles': ['HR_ADMIN', 'EMPLOYEE'],
    'company_id': str(uuid.uuid4()),
    'user_name': 'Ada Synthetic',
    'user_email': 'ada@example.test',
}


def _args(**over):
    base = dict(
        action='EMPLOYEE_STATUS_CHANGED',
        entity_type='employee',
        entity_id=str(uuid.uuid4()),
        company_id=str(uuid.uuid4()),
        actor=ACTOR,
        reason='End of fixed-term contract',
    )
    base.update(over)
    return base


def _build(**over):
    a = _args(**over)
    return audit._build_row(a.pop('action'), a.pop('entity_type'),
                            a.pop('entity_id'), **a)


# ── Tier 1: the contract ──────────────────────────────────────────────────────

class TestRequiredFields:
    """BA D4 R4.1 — the twelve fields, asserted individually."""

    def test_a_minimal_row_carries_all_twelve_fields(self):
        row = _build()
        # 1 event id is BIGSERIAL, 2 occurred_at is a server DEFAULT — neither is
        # a bind parameter, which is the point: they cannot be client-supplied.
        (company_id, actor_user_id, actor_employee_id, actor_label, actor_roles,
         actor_ip, actor_session_id, subject_id, subject_number, action,
         entity_type, entity_id, before, after, reason, correlation_id,
         outcome, error_code, metadata, retention_class) = row

        assert company_id                                   # 6  tenant scope
        assert actor_user_id and actor_employee_id          # 3  actor identity
        assert actor_label == 'Ada Synthetic <ada@example.test>'
        assert json.loads(actor_roles) == ['HR_ADMIN', 'EMPLOYEE']   # 3  roles snapshot
        assert action == 'EMPLOYEE_STATUS_CHANGED'          # 7  action code
        assert entity_type == 'employee' and entity_id      # 8  entity affected
        assert reason == 'End of fixed-term contract'       # 10 reason
        assert uuid.UUID(correlation_id)                    # 11 correlation id
        assert outcome == 'SUCCESS'                         # 12 outcome
        assert retention_class == 'STANDARD'

    def test_actor_roles_are_snapshotted_as_at_the_time(self):
        actor = dict(ACTOR, roles=['PORTAL_ADMIN'])
        assert json.loads(_build(actor=actor)[4]) == ['PORTAL_ADMIN']

    def test_actor_label_falls_back_when_the_name_is_unknown(self):
        uid = str(uuid.uuid4())
        assert _build(actor={'user_id': uid, 'roles': []})[3] == f'user:{uid}'
        assert _build(actor={'roles': []})[3] == 'system'

    def test_a_correlation_id_is_generated_when_the_caller_omits_one(self):
        assert uuid.UUID(_build()[15])

    def test_a_supplied_correlation_id_groups_rows_into_one_story(self):
        cid = audit.new_correlation_id()
        assert _build(correlation_id=cid)[15] == cid
        assert _build(correlation_id=cid, action='USER_ACCESS_REVOKED')[15] == cid

    def test_outcome_failed_carries_an_error_code(self):
        row = _build(outcome='FAILED', error_code='LAST_PORTAL_ADMIN')
        assert row[16] == 'FAILED' and row[17] == 'LAST_PORTAL_ADMIN'


class TestSubjectIsNeverNamed:
    """The subject is id + employee number only — never a name (BA D4 R4.1 #5)."""

    def test_subject_is_recorded_as_id_and_employee_number(self):
        sid = str(uuid.uuid4())
        row = _build(subject_employee_id=sid, subject_employee_number='E-4711')
        assert row[7] == sid
        assert row[8] == 'E-4711'

    def test_no_bind_parameter_can_carry_a_subject_name(self):
        """There is no column for it, so an erasure cannot be defeated by one."""
        with pytest.raises(TypeError):
            _build(subject_name='Ada Synthetic')

    def test_a_name_smuggled_into_the_diff_is_still_only_a_diff_field(self):
        """The guard is the diff-only rule plus review, not a name blocklist —
        assert the shape we DO enforce so the boundary is explicit."""
        row = _build(before={'employment_status': 'ACTIVE'},
                     after={'employment_status': 'TERMINATED'})
        assert json.loads(row[12]) == {'employment_status': 'ACTIVE'}
        assert json.loads(row[13]) == {'employment_status': 'TERMINATED'}


class TestValidation:
    def test_company_id_is_mandatory(self):
        for bad in (None, '', 'not-a-uuid'):
            with pytest.raises(AuditError, match='company_id'):
                _build(company_id=bad)

    def test_company_id_is_not_defaulted_from_the_actor(self):
        """It comes from the AFFECTED ENTITY, never the session (ADR-009 §3.3)."""
        with pytest.raises(AuditError, match='company_id'):
            _build(company_id=None)
        # and when supplied it is used verbatim, not overridden by the actor's
        affected = str(uuid.uuid4())
        assert _build(company_id=affected)[0] == affected
        assert affected != ACTOR['company_id']

    def test_reason_is_mandatory_and_non_blank(self):
        for bad in (None, '', '   ', 5):
            with pytest.raises(AuditError, match='reason'):
                _build(reason=bad)

    def test_action_must_be_in_the_closed_enumeration(self):
        with pytest.raises(AuditError, match='unknown audit action'):
            _build(action='EMPLOYEE_DELETED_SOMEHOW')

    def test_retention_class_and_outcome_are_enumerated(self):
        with pytest.raises(AuditError, match='retention_class'):
            _build(retention_class='FOREVER')
        with pytest.raises(AuditError, match='outcome'):
            _build(outcome='MAYBE')

    def test_entity_id_must_be_a_uuid(self):
        with pytest.raises(AuditError, match='entity_id'):
            _build(entity_id='12345')


class TestDiffsOnlyNeverFullRows:
    def test_before_and_after_must_describe_the_same_fields(self):
        with pytest.raises(AuditError, match='SAME fields'):
            _build(before={'employment_status': 'ACTIVE'},
                   after={'employment_status': 'TERMINATED', 'exit_date': '2026-09-30'})

    def test_a_one_sided_diff_is_allowed(self):
        assert json.loads(_build(after={'status': 'IN_PROGRESS'})[13]) == {'status': 'IN_PROGRESS'}
        assert _build(after={'status': 'IN_PROGRESS'})[12] is None

    def test_nested_structures_are_refused(self):
        """Nesting is how a whole row gets smuggled into the trail."""
        with pytest.raises(AuditError, match='field-level'):
            _build(after={'employee': {'first_name': 'Ada', 'email': 'a@b.test'}})

    @pytest.mark.parametrize('key', [
        'password', 'password_hash', 'reset_token', 'api_key', 'client_secret',
    ])
    def test_secrets_are_refused_in_the_diff(self, key):
        with pytest.raises(AuditError, match='secrets and credentials'):
            _build(after={key: 'whatever'})

    def test_secrets_are_refused_in_metadata_too(self):
        with pytest.raises(AuditError, match='secrets and credentials'):
            _build(metadata={'auth_token': 'abc'})

    def test_dates_decimals_and_uuids_are_serialised_not_rejected(self):
        import datetime
        import decimal
        row = _build(before={'exit_date': None},
                     after={'exit_date': datetime.date(2026, 9, 30)})
        assert json.loads(row[13]) == {'exit_date': '2026-09-30'}

        row = _build(before={'manager_id': None},
                     after={'manager_id': uuid.UUID(int=7)})
        assert json.loads(row[13]) == {'manager_id': '00000000-0000-0000-0000-000000000007'}

        row = _build(before={'fte': decimal.Decimal('1.0')},
                     after={'fte': decimal.Decimal('0.5')})
        assert json.loads(row[13]) == {'fte': 0.5}


class TestRecordMany:
    def test_the_whole_batch_is_validated_before_anything_is_written(self, monkeypatch):
        written = []
        monkeypatch.setattr(audit, 'execute', lambda sql, params: written.append(params))
        cid = audit.new_correlation_id()
        good = _args(correlation_id=cid)
        bad = _args(correlation_id=cid, action='NOT_A_REAL_ACTION')
        with pytest.raises(AuditError):
            audit.record_many([good, bad])
        assert written == [], 'a bad entry left a half-written batch behind'

    def test_a_valid_batch_shares_one_correlation_id(self, monkeypatch):
        written = []
        monkeypatch.setattr(audit, 'execute', lambda sql, params: written.append(params))
        cid = audit.new_correlation_id()
        audit.record_many([
            _args(correlation_id=cid, action='EMPLOYEE_STATUS_CHANGED'),
            _args(correlation_id=cid, action='USER_ACCESS_REVOKED'),
            _args(correlation_id=cid, action='MANAGER_RELATIONSHIP_CLOSED'),
        ])
        assert len(written) == 3
        assert {params[15] for params in written} == {cid}


# ── Tier 2: transaction mechanics, no database ────────────────────────────────

@pytest.fixture
def fake_db():
    from flask import g

    def _make(fail_on=None):
        conn = FakeConnection(fail_on=fail_on)
        conn.autocommit = True
        g.db = conn
        return conn

    with flask_app.test_request_context():
        yield _make


class TestJoinsTheCallersTransaction:
    """The single most important property (ADR-009 §3.3 + KAN-155)."""

    def test_record_does_not_commit_inside_the_callers_block(self, fake_db):
        conn = fake_db()
        with transaction():
            audit.record(**_args())
            assert conn.commits == 0, 'audit committed independently of its caller'
            assert conn.durable == [], 'the audit row was durable before the caller committed'
        assert conn.commits == 1
        assert len(conn.durable) == 1

    def test_record_never_opens_its_own_transaction(self, fake_db):
        """transaction() refuses to nest (RuntimeError). Reaching the end of the
        caller's block proves record() opened none of its own."""
        conn = fake_db()
        with transaction():
            audit.record(**_args())
            audit.record(**_args(action='USER_ACCESS_REVOKED'))
        assert conn.commits == 1, 'more than one commit boundary was created'
        assert conn.rollbacks == 0

    def test_a_rolled_back_change_takes_the_audit_row_with_it(self, fake_db):
        conn = fake_db()
        with pytest.raises(ValueError):
            with transaction():
                execute("UPDATE employees SET employment_status='TERMINATED'")
                audit.record(**_args())
                raise ValueError('last PORTAL_ADMIN — refused')
        assert conn.durable == [], 'a false audit entry survived a rolled-back change'
        assert conn.commits == 0
        assert conn.rollbacks == 1

    def test_record_many_writes_inside_one_commit_boundary(self, fake_db):
        conn = fake_db()
        cid = audit.new_correlation_id()
        with transaction():
            audit.record_many([_args(correlation_id=cid),
                               _args(correlation_id=cid, action='ORG_ASSIGNMENT_CLOSED')])
            assert conn.commits == 0
        assert conn.commits == 1
        assert len(conn.durable) == 2

    def test_a_standalone_record_outside_a_transaction_still_works(self, fake_db):
        """Needed for the R4.1 #12 FAILED row, which is written AFTER the failed
        transaction has already rolled back."""
        conn = fake_db()
        audit.record(**_args(outcome='FAILED', error_code='LAST_PORTAL_ADMIN'))
        assert len(conn.durable) == 1
        assert conn.pending == []


class TestReadsAreCompanyScoped:
    def test_neither_timeline_ever_matches_a_null_company(self, fake_db):
        seen = []
        with flask_app.test_request_context():
            import app.services.audit_service as mod
            original = mod.query
            mod.query = lambda sql, params=(), one=False: (seen.append(sql) or [])
            try:
                mod.entity_timeline(str(uuid.uuid4()), 'employee', str(uuid.uuid4()))
                mod.company_timeline(str(uuid.uuid4()), action='EMPLOYEE_STATUS_CHANGED')
            finally:
                mod.query = original
        assert seen and all('company_id = %s::uuid' in sql for sql in seen)
        assert not any('IS NULL' in sql.upper() for sql in seen)

    def test_the_page_size_is_bounded(self, fake_db):
        assert audit._paging(10_000, -5) == (500, 0)


# ── Tier 3: real Postgres ─────────────────────────────────────────────────────

def _db_reachable():
    try:
        from app.config import DB_CONFIG
        psycopg2.connect(**DB_CONFIG).close()
        return True
    except Exception:
        return False


real_db = pytest.mark.skipif(
    not _db_reachable(),
    reason='no PostgreSQL reachable with the configured DB_CONFIG')


@pytest.fixture
def live_db():
    from app.db import close_db
    with flask_app.test_request_context():
        yield
        close_db(None)


def _a_company():
    row = query("SELECT id::text FROM companies ORDER BY created_at LIMIT 1", one=True)
    if not row:
        pytest.skip('seeded dev DB has no companies')
    return row['id']


def _live_actor():
    """ACTOR with ids that satisfy the FKs on the live schema.

    `actor_user_id` / `actor_employee_id` are real foreign keys, so a synthetic
    UUID is (correctly) refused. The ids come from the dev DB; the name and email
    stay synthetic — no real PII in tests.
    """
    row = query("""
        SELECT u.id::text AS user_id, u.employee_id::text AS employee_id
        FROM users u WHERE u.employee_id IS NOT NULL LIMIT 1
    """, one=True)
    return dict(ACTOR,
                user_id=(row or {}).get('user_id'),
                employee_id=(row or {}).get('employee_id'))


def _purge(correlation_id):
    """Remove this test's rows. DELETE is deliberately unblocked (TD-13)."""
    execute("DELETE FROM audit_log WHERE correlation_id = %s::uuid", (correlation_id,))


@real_db
class TestRealPostgresAudit:

    def test_the_audit_row_commits_atomically_with_its_change(self, live_db):
        company = _a_company()
        cid = audit.new_correlation_id()
        probe = f'kan187_probe_{uuid.uuid4().hex[:8]}'
        execute(f"CREATE TEMP TABLE {probe} (id int PRIMARY KEY)")
        try:
            with transaction():
                execute(f"INSERT INTO {probe} VALUES (1)")
                audit.record('EMPLOYEE_STATUS_CHANGED', 'employee', str(uuid.uuid4()),
                             company_id=company, actor=_live_actor(),
                             reason='Resignation accepted',
                             before={'employment_status': 'ACTIVE'},
                             after={'employment_status': 'RESIGNED'},
                             correlation_id=cid)
            assert [r['id'] for r in query(f"SELECT id FROM {probe}")] == [1]
            rows = audit.company_timeline(company, correlation_id=cid)
            assert len(rows) == 1, 'the change committed without its audit row'
            assert rows[0]['before_state'] == {'employment_status': 'ACTIVE'}
            assert rows[0]['after_state'] == {'employment_status': 'RESIGNED'}
            assert rows[0]['reason'] == 'Resignation accepted'
            assert rows[0]['actor_roles'] == ['HR_ADMIN', 'EMPLOYEE']
        finally:
            _purge(cid)

    def test_a_rolled_back_change_leaves_no_audit_row(self, live_db):
        company = _a_company()
        cid = audit.new_correlation_id()
        probe = f'kan187_probe_{uuid.uuid4().hex[:8]}'
        execute(f"CREATE TEMP TABLE {probe} (id int PRIMARY KEY)")

        with pytest.raises(psycopg2.IntegrityError):
            with transaction():
                execute(f"INSERT INTO {probe} VALUES (1)")
                audit.record('EMPLOYEE_OFFBOARD_COMPLETED', 'employee',
                             str(uuid.uuid4()), company_id=company, actor=_live_actor(),
                             reason='Termination', correlation_id=cid)
                execute(f"INSERT INTO {probe} VALUES (1)")     # PK violation

        assert query(f"SELECT id FROM {probe}") == []
        assert audit.company_timeline(company, correlation_id=cid) == [], \
            'a false audit entry survived a rolled-back change'

    def test_the_append_only_trigger_rejects_an_update(self, live_db):
        company = _a_company()
        cid = audit.new_correlation_id()
        try:
            audit.record('EMPLOYEE_SUSPENDED', 'employee', str(uuid.uuid4()),
                         company_id=company, actor=_live_actor(),
                         reason='Suspended pending investigation', correlation_id=cid)
            row_id = audit.company_timeline(company, correlation_id=cid)[0]['id']

            with pytest.raises(psycopg2.Error) as exc:
                execute("UPDATE audit_log SET reason = 'rewritten' WHERE id = %s", (row_id,))
            assert 'append-only' in str(exc.value)

            after = audit.company_timeline(company, correlation_id=cid)[0]
            assert after['reason'] == 'Suspended pending investigation'
        finally:
            _purge(cid)

    def test_the_trigger_also_blocks_a_blanket_update(self, live_db):
        company = _a_company()
        cid = audit.new_correlation_id()
        try:
            audit.record('EMPLOYEE_REINSTATED', 'employee', str(uuid.uuid4()),
                         company_id=company, actor=_live_actor(), reason='Returned from leave',
                         correlation_id=cid)
            with pytest.raises(psycopg2.Error):
                execute("UPDATE audit_log SET retention_class = 'SECURITY'")
        finally:
            _purge(cid)

    def test_company_id_cannot_be_null(self, live_db):
        """Enforced in the database, not only by the service."""
        with pytest.raises(psycopg2.errors.NotNullViolation):
            execute("""
                INSERT INTO audit_log (company_id, actor_label, action, entity_type,
                                       entity_id, reason, correlation_id)
                VALUES (NULL, 'x', 'EMPLOYEE_STATUS_CHANGED', 'employee',
                        %s::uuid, 'why', %s::uuid)
            """, (str(uuid.uuid4()), str(uuid.uuid4())))

    def test_a_blank_reason_is_rejected_by_the_database(self, live_db):
        company = _a_company()
        with pytest.raises(psycopg2.errors.CheckViolation):
            execute("""
                INSERT INTO audit_log (company_id, actor_label, action, entity_type,
                                       entity_id, reason, correlation_id)
                VALUES (%s::uuid, 'x', 'EMPLOYEE_STATUS_CHANGED', 'employee',
                        %s::uuid, '   ', %s::uuid)
            """, (company, str(uuid.uuid4()), str(uuid.uuid4())))

    def test_one_tenant_never_sees_another_tenants_rows(self, live_db):
        companies = query("SELECT id::text FROM companies ORDER BY created_at LIMIT 2")
        if len(companies) < 2:
            pytest.skip('need two companies to prove tenant isolation')
        a, b = companies[0]['id'], companies[1]['id']
        cid = audit.new_correlation_id()
        entity = str(uuid.uuid4())
        try:
            audit.record('CHECKLIST_STARTED', 'employee_checklist', entity,
                         company_id=a, actor=_live_actor(), reason='Offboarding started',
                         correlation_id=cid)
            audit.record('CHECKLIST_STARTED', 'employee_checklist', entity,
                         company_id=b, actor=_live_actor(), reason='Offboarding started',
                         correlation_id=cid)

            a_rows = audit.entity_timeline(a, 'employee_checklist', entity)
            b_rows = audit.entity_timeline(b, 'employee_checklist', entity)
            assert [r['company_id'] for r in a_rows] == [a]
            assert [r['company_id'] for r in b_rows] == [b]
            assert len(audit.company_timeline(a, correlation_id=cid)) == 1
        finally:
            _purge(cid)

    def test_the_timeline_is_newest_first_and_pageable(self, live_db):
        company = _a_company()
        cid = audit.new_correlation_id()
        entity = str(uuid.uuid4())
        try:
            for action in ('EMPLOYEE_OFFBOARD_INITIATED', 'USER_ACCESS_REVOKED',
                           'EMPLOYEE_OFFBOARD_COMPLETED'):
                audit.record(action, 'employee', entity, company_id=company,
                             actor=_live_actor(), reason='Offboarding', correlation_id=cid)
            rows = audit.entity_timeline(company, 'employee', entity)
            assert len(rows) == 3
            assert rows[0]['action'] == 'EMPLOYEE_OFFBOARD_COMPLETED'
            assert audit.entity_timeline(company, 'employee', entity, limit=1)[0]['id'] == rows[0]['id']
            assert audit.entity_timeline(company, 'employee', entity, limit=1, offset=2)[0]['id'] == rows[2]['id']
        finally:
            _purge(cid)

    def test_the_audit_log_feature_is_registered_read_only(self, live_db):
        feat = query("SELECT code, sort_order FROM portal_features WHERE code='audit_log'", one=True)
        assert feat, "'audit_log' is missing from portal_features"
        grants = query("""
            SELECT DISTINCT ro.name, rfa.can_read, rfa.can_write, rfa.can_delete
            FROM role_feature_access rfa
            JOIN roles ro ON ro.id = rfa.role_id
            JOIN portal_features f ON f.id = rfa.feature_id
            WHERE f.code = 'audit_log'
        """)
        by_role = {g['name']: g for g in grants}
        assert by_role['PORTAL_ADMIN']['can_read'] is True
        assert by_role['HR_ADMIN']['can_read'] is True
        for role in ('PORTAL_ADMIN', 'HR_ADMIN'):
            assert by_role[role]['can_write'] is False
            assert by_role[role]['can_delete'] is False
        assert 'EMPLOYEE' not in by_role, 'EMPLOYEE must never read the audit trail'


# ── Tier 3b: the migration, on a genuinely fresh database ─────────────────────

def _pg_tools_available():
    from shutil import which
    return all(which(t) for t in ('createdb', 'dropdb', 'psql'))


@pytest.mark.skipif(not _db_reachable() or not _pg_tools_available(),
                    reason='needs a reachable PostgreSQL plus createdb/dropdb/psql')
def test_the_migration_applies_and_reverses_on_a_fresh_database():
    """Reversible means tested, not assumed (Engineering Charter §4 DoD)."""
    from app.config import DB_CONFIG
    dbname = f'kan187_migration_{uuid.uuid4().hex[:8]}'
    env = dict(os.environ, PGHOST=str(DB_CONFIG['host']),
               PGPORT=str(DB_CONFIG['port']), PGUSER=str(DB_CONFIG['user']))
    if DB_CONFIG.get('password'):
        env['PGPASSWORD'] = DB_CONFIG['password']

    def psql(*args):
        return subprocess.run(['psql', '-q', '-d', dbname, '-v', 'ON_ERROR_STOP=1', *args],
                              env=env, capture_output=True, text=True)

    def scalar(sql):
        out = psql('-tAc', sql)
        assert out.returncode == 0, out.stderr
        return out.stdout.strip()

    subprocess.run(['createdb', dbname], env=env, check=True, capture_output=True)
    try:
        for path in (os.path.join(REPO, 'database', 'schema.sql'),
                     os.path.join(REPO, 'database', 'seed_rbac.sql')):
            res = psql('-f', path)
            assert res.returncode == 0, res.stderr

        # The baseline already carries audit_log (schema.sql and the migrations
        # must not diverge — F9 / KAN-166). Start from a reversed state.
        down = psql('-f', MIGRATION_DOWN)
        assert down.returncode == 0, down.stderr
        assert scalar("SELECT to_regclass('public.audit_log') IS NULL") == 't'

        # UP
        up = psql('-f', MIGRATION_UP)
        assert up.returncode == 0, up.stderr
        assert scalar("SELECT to_regclass('public.audit_log') IS NOT NULL") == 't'
        assert scalar("SELECT count(*) FROM portal_features WHERE code='audit_log'") == '1'
        assert scalar("""SELECT count(*) FROM pg_trigger
                         WHERE tgname='trg_audit_log_no_update'""") == '1'
        assert scalar("""SELECT count(*) FROM pg_indexes WHERE tablename='audit_log'
                         AND indexname IN ('idx_audit_entity','idx_audit_company_time',
                                           'idx_audit_correlation')""") == '3'

        # Re-applying is a no-op, not an error.
        again = psql('-f', MIGRATION_UP)
        assert again.returncode == 0, again.stderr
        assert scalar("SELECT count(*) FROM portal_features WHERE code='audit_log'") == '1'

        # DOWN — and it must leave nothing behind.
        down2 = psql('-f', MIGRATION_DOWN)
        assert down2.returncode == 0, down2.stderr
        assert scalar("SELECT to_regclass('public.audit_log') IS NULL") == 't'
        assert scalar("SELECT count(*) FROM pg_proc WHERE proname='audit_log_immutable'") == '0'
        assert scalar("SELECT count(*) FROM portal_features WHERE code='audit_log'") == '0'
        assert scalar("""SELECT count(*) FROM role_feature_access rfa
                         LEFT JOIN portal_features f ON f.id = rfa.feature_id
                         WHERE f.id IS NULL""") == '0'

        # Re-running down is also a no-op, and up still works afterwards.
        down3 = psql('-f', MIGRATION_DOWN)
        assert down3.returncode == 0, down3.stderr
        up2 = psql('-f', MIGRATION_UP)
        assert up2.returncode == 0, up2.stderr
        assert scalar("SELECT to_regclass('public.audit_log') IS NOT NULL") == 't'
    finally:
        subprocess.run(['dropdb', '--if-exists', dbname], env=env, capture_output=True)

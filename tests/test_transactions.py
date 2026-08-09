"""
KAN-155 / ADR-006 — atomic composite writes.

Two tiers:

1. **Mechanics** (always run) — a fake connection that models Postgres's
   durability rules closely enough to prove the contract: statements issued
   inside `transaction()` are NOT durable until the single commit, and a failure
   part-way through retracts every earlier write in the block.
2. **Real Postgres** (skipped when no DB is reachable) — the same guarantee
   against the live schema, including the vacation-type composite write named in
   the KAN-155 acceptance criteria.

All data is synthetic; the real-DB tests only ever create rows inside a
transaction they then force to roll back, plus a session-scoped TEMP table.
"""
import uuid

import psycopg2
import pytest

from app import app as flask_app
from app.db import (execute, insert_returning, query, transaction,
                    _in_transaction)


# ── Tier 1: fake connection ───────────────────────────────────────────────────

class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self._row = {'id': 'generated-id'}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=()):
        self.conn._run(sql)

    def fetchone(self):
        return self._row

    def fetchall(self):
        return []


class FakeConnection:
    """Models the only DB behaviour these tests care about: what is durable.

    A statement run while `autocommit` is on is durable immediately. Otherwise it
    is pending until `commit()`, and `rollback()` discards it — exactly the
    property KAN-155 depends on.
    """

    def __init__(self, fail_on=None):
        self.autocommit = False
        self.durable = []
        self.pending = []
        self.commits = 0
        self.rollbacks = 0
        self.fail_on = fail_on

    def _run(self, sql):
        if self.fail_on and self.fail_on in sql:
            raise psycopg2.IntegrityError(f'simulated failure on {self.fail_on}')
        (self.durable if self.autocommit else self.pending).append(sql)

    def cursor(self, cursor_factory=None):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1
        self.durable.extend(self.pending)
        self.pending = []

    def rollback(self):
        self.rollbacks += 1
        self.pending = []

    def close(self):
        self.pending = []


@pytest.fixture
def fake_db():
    """Request context with a FakeConnection installed as this request's `g.db`."""
    from flask import g

    def _make(fail_on=None):
        conn = FakeConnection(fail_on=fail_on)
        conn.autocommit = True          # what get_db() sets on a fresh connection
        g.db = conn
        return conn

    with flask_app.test_request_context():
        yield _make


class TestStandaloneWrites:
    def test_write_outside_transaction_is_durable_immediately(self, fake_db):
        conn = fake_db()
        execute("INSERT INTO a VALUES (1)")
        execute("INSERT INTO b VALUES (2)")
        assert conn.durable == ["INSERT INTO a VALUES (1)", "INSERT INTO b VALUES (2)"]
        assert conn.pending == []

    def test_reads_do_not_leave_an_open_transaction(self, fake_db):
        conn = fake_db()
        query("SELECT 1")
        assert conn.autocommit is True      # read path never sits idle-in-transaction
        assert conn.pending == []
        assert _in_transaction() is False


class TestTransactionCommits:
    def test_statements_are_not_durable_until_the_block_exits(self, fake_db):
        conn = fake_db()
        with transaction():
            execute("INSERT INTO a VALUES (1)")
            execute("INSERT INTO b VALUES (2)")
            # THE critical semantic: nothing has committed yet, so a failure on the
            # next statement could still retract both.
            assert conn.durable == []
            assert conn.commits == 0
        assert conn.commits == 1
        assert conn.durable == ["INSERT INTO a VALUES (1)", "INSERT INTO b VALUES (2)"]

    def test_insert_returning_does_not_commit_inside_the_block(self, fake_db):
        conn = fake_db()
        with transaction():
            row = insert_returning("INSERT INTO a VALUES (1) RETURNING id")
            assert row == {'id': 'generated-id'}
            assert conn.commits == 0
        assert conn.commits == 1

    def test_autocommit_is_restored_after_the_block(self, fake_db):
        conn = fake_db()
        with transaction():
            assert conn.autocommit is False
        assert conn.autocommit is True
        assert _in_transaction() is False


class TestTransactionRollsBack:
    def test_failure_part_way_retracts_earlier_writes(self, fake_db):
        conn = fake_db(fail_on='vacation_type_rules')
        with pytest.raises(psycopg2.IntegrityError):
            with transaction():
                execute("INSERT INTO vacation_types VALUES (1)")
                execute("INSERT INTO vacation_type_locations VALUES (1, 2)")
                execute("INSERT INTO vacation_type_rules VALUES (1, 'MAX', '5')")
        assert conn.durable == []           # no partial data whatsoever
        assert conn.pending == []
        assert conn.rollbacks == 1
        assert conn.commits == 0

    def test_rollback_restores_autocommit_for_the_rest_of_the_request(self, fake_db):
        conn = fake_db(fail_on='boom')
        with pytest.raises(psycopg2.IntegrityError):
            with transaction():
                execute("INSERT INTO boom VALUES (1)")
        assert conn.autocommit is True
        assert _in_transaction() is False
        execute("INSERT INTO after VALUES (1)")
        assert conn.durable == ["INSERT INTO after VALUES (1)"]

    def test_non_db_exception_also_rolls_back(self, fake_db):
        conn = fake_db()
        with pytest.raises(ValueError):
            with transaction():
                execute("INSERT INTO a VALUES (1)")
                raise ValueError('business rule violated')
        assert conn.durable == []
        assert conn.rollbacks == 1


class TestNesting:
    def test_nested_transaction_is_refused(self, fake_db):
        conn = fake_db()
        with pytest.raises(RuntimeError, match='must not be nested'):
            with transaction():
                with transaction():
                    pass
        # the outer block was aborted, so nothing committed
        assert conn.commits == 0
        assert conn.rollbacks == 1
        assert conn.durable == []


# ── Tier 2: real Postgres ─────────────────────────────────────────────────────

def _db_reachable():
    try:
        from app.config import DB_CONFIG
        psycopg2.connect(**DB_CONFIG).close()
        return True
    except Exception:
        return False


real_db = pytest.mark.skipif(not _db_reachable(),
                             reason='no PostgreSQL reachable with the configured DB_CONFIG')


@pytest.fixture
def live_db():
    """Real connection for one request, discarded afterwards."""
    from app.db import close_db
    with flask_app.test_request_context():
        yield
        close_db(None)


@real_db
class TestRealPostgresAtomicity:
    def test_composite_write_failure_leaves_no_rows(self, live_db):
        probe = f'kan155_probe_{uuid.uuid4().hex[:8]}'
        execute(f"CREATE TEMP TABLE {probe} (id int PRIMARY KEY)")

        with pytest.raises(psycopg2.IntegrityError):
            with transaction():
                execute(f"INSERT INTO {probe} VALUES (1)")
                execute(f"INSERT INTO {probe} VALUES (2)")
                execute(f"INSERT INTO {probe} VALUES (1)")   # PK violation

        assert query(f"SELECT id FROM {probe}") == []       # rows 1 and 2 retracted
        # and the connection is usable — no aborted-transaction cascade (F8)
        execute(f"INSERT INTO {probe} VALUES (9)")
        assert [r['id'] for r in query(f"SELECT id FROM {probe}")] == [9]

    def test_successful_transaction_commits_once(self, live_db):
        probe = f'kan155_probe_{uuid.uuid4().hex[:8]}'
        execute(f"CREATE TEMP TABLE {probe} (id int PRIMARY KEY)")
        with transaction():
            execute(f"INSERT INTO {probe} VALUES (1)")
            execute(f"INSERT INTO {probe} VALUES (2)")
        assert [r['id'] for r in query(f"SELECT id FROM {probe} ORDER BY id")] == [1, 2]

    def test_vacation_type_create_rolls_back_whole_unit(self, live_db):
        """The KAN-155 acceptance case, on the real schema.

        A vacation type plus a bad location row: the type must not survive.
        """
        company = query("SELECT id::text FROM companies LIMIT 1", one=True)
        if not company:
            pytest.skip('seeded dev DB has no companies')

        name = f'KAN155 rollback probe {uuid.uuid4().hex[:8]}'
        orphan_location = str(uuid.uuid4())      # no such location → FK violation

        with pytest.raises(psycopg2.IntegrityError):
            with transaction():
                vt = insert_returning("""
                    INSERT INTO vacation_types (company_id, name, is_paid, color)
                    VALUES (%s::uuid,%s,%s,%s) RETURNING id::text
                """, (company['id'], name, True, '#3b82f6'))
                execute("INSERT INTO vacation_type_locations VALUES (%s::uuid,%s::uuid)",
                        (vt['id'], orphan_location))

        left_behind = query("SELECT id::text FROM vacation_types WHERE name=%s", (name,))
        assert left_behind == [], 'the vacation type survived a failed composite write'

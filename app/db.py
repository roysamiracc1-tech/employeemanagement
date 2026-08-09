import contextlib
import decimal
import datetime

import psycopg2
import psycopg2.extras
from flask import g, has_app_context

from app.config import DB_CONFIG

# Key on `g` holding the depth of the currently open transaction() block.
_TXN_KEY = '_db_txn_depth'


def get_db():
    if 'db' not in g:
        conn = psycopg2.connect(**DB_CONFIG)
        # ADR-006: connections are autocommit by default so read paths never hold
        # an open transaction (F8: "read paths sit idle-in-transaction"), and a
        # failed statement cannot poison the rest of the request with
        # "current transaction is aborted". Composite writes opt IN to a single
        # transaction via transaction() below.
        conn.autocommit = True
        g.db = conn
    return g.db


def close_db(_):
    db = g.pop('db', None)
    if db:
        db.close()


def _in_transaction():
    """True while a transaction() block is open on this request's connection."""
    return has_app_context() and getattr(g, _TXN_KEY, 0) > 0


def _restore_autocommit(db, value):
    """Put the connection back into its previous autocommit mode.

    psycopg2 refuses to change autocommit while a transaction is open, so if the
    commit/rollback above did not fully close it, roll back once and retry. A
    dead connection is left alone — close_db will discard it.
    """
    try:
        db.autocommit = value
    except psycopg2.Error:
        try:
            db.rollback()
            db.autocommit = value
        except psycopg2.Error:
            pass


@contextlib.contextmanager
def transaction():
    """Run a composite write as ONE unit of work — single commit, single rollback.

    ADR-006 / KAN-155. Statements issued inside the block (execute,
    insert_returning) do **not** commit individually, so a failure at any point
    retracts every earlier write in the block:

        with transaction():
            vt = insert_returning("INSERT INTO vacation_types ... RETURNING id::text", ...)
            for lid in location_ids:
                execute("INSERT INTO vacation_type_locations ...", (vt['id'], lid))

    Rules (EP38 technical design §5.4):
      * one transaction() per public entry point — not per cascade, not per table;
      * side effects that cannot be rolled back (notifications, email) go AFTER
        the block, never inside it;
      * never nest — a helper that needs the transaction runs inside the caller's
        open block rather than opening its own. Nesting raises RuntimeError so
        the mistake is loud instead of silently creating a false commit boundary.
    """
    db = get_db()
    if _in_transaction():
        raise RuntimeError(
            'transaction() must not be nested (ADR-006). The inner call would '
            'commit or roll back independently of the outer unit of work — let '
            'the helper run inside the caller\'s open transaction instead.')

    previous_autocommit = db.autocommit
    db.autocommit = False
    setattr(g, _TXN_KEY, 1)
    try:
        yield db
    except BaseException:
        try:
            db.rollback()
        except psycopg2.Error:
            pass
        raise
    else:
        db.commit()
    finally:
        setattr(g, _TXN_KEY, 0)
        _restore_autocommit(db, previous_autocommit)


def query(sql, params=(), one=False):
    with get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()


def _commit_unless_in_transaction(db):
    """Commit a standalone statement; inside transaction() the caller commits.

    Committing here while a transaction() block is open would defeat its single
    commit/rollback boundary — earlier writes could no longer be retracted.
    """
    if _in_transaction():
        return
    if not db.autocommit:
        db.commit()


def execute(sql, params=()):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
    _commit_unless_in_transaction(db)


def insert_returning(sql, params=()):
    db = get_db()
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    _commit_unless_in_transaction(db)
    return dict(row) if row else None


def serialize(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def to_dict(row):
    return {k: serialize(v) for k, v in dict(row).items()}

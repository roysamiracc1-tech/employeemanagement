import decimal
import datetime

import psycopg2
import psycopg2.extras
from flask import g

from app.config import DB_CONFIG


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
    return g.db


def close_db(_):
    db = g.pop('db', None)
    if db:
        db.close()


def query(sql, params=(), one=False):
    with get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()


def execute(sql, params=()):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
    db.commit()


def insert_returning(sql, params=()):
    db = get_db()
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    db.commit()
    return dict(row) if row else None


def serialize(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def to_dict(row):
    return {k: serialize(v) for k, v in dict(row).items()}

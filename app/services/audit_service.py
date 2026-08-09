"""Audit trail service — EP38 / KAN-187 (ADR-009).

The one write path into `audit_log`. Every subsystem that changes tenant data
records it here; nothing else INSERTs into the table and nothing at all UPDATEs
it (a BEFORE UPDATE trigger raises).

Public API::

    record(action, entity_type, entity_id, *, company_id, actor, reason, ...) -> None
    record_many(entries)                                                      -> None
    entity_timeline(company_id, entity_type, entity_id, limit=50, offset=0)   -> list[dict]
    company_timeline(company_id, *, action=None, actor_user_id=None,
                     correlation_id=None, since=None, until=None,
                     limit=50, offset=0)                                      -> list[dict]
    new_correlation_id()                                                      -> str

`actor` is the same light dict the org-change engine already uses —
``{'user_id', 'employee_id', 'roles', 'company_id'}`` — optionally carrying
``user_name`` / ``user_email`` so the label can be built. Do not invent a second
actor shape.

────────────────────────────────────────────────────────────────────────────────
THE LOAD-BEARING PROPERTY — read this before changing anything below.

`record()` NEVER opens a connection and NEVER commits. It writes through
``app.db.execute`` on the request-scoped ``g.db``, so it joins whatever
transaction the caller already has open (KAN-155 / ADR-006). Two consequences,
both intentional:

  * An audit row commits atomically with the change it describes. If the change
    rolls back, the audit row vanishes with it. **A false audit entry is worse
    than a missing one.**
  * `transaction()` refuses to nest — it raises RuntimeError — so this module
    must never open one. It runs inside the caller's block. Callers wrap the
    business operation; audit is a participant, not an owner.

Corollary: failed and rejected *attempts* are not written from inside the failing
transaction — they roll back with it. Authorisation denials and validation
failures belong in the application log. If a caller genuinely needs the R4.1 #12
`FAILED` row it must call `record(..., outcome='FAILED', error_code=...)`
**after** the failed transaction has already rolled back, where `execute()` is
back in autocommit and the row stands alone.
────────────────────────────────────────────────────────────────────────────────

PII rules — compliance requirements, not style preferences:

  * `before_state` / `after_state` hold **field-level diffs only**, never whole
    rows. Storing a whole `employees` row would copy name, email, phone and job
    title into a permanently retained table on every edit.
  * Never a password hash, token, secret or free-text PII narrative in the diff
    or in `metadata`. `_SECRETISH_KEYS` rejects the obvious ones at runtime so
    this is test-enforced rather than review-only.
  * The subject is recorded as **employee id + employee number only. Never the
    name.** An audit row must survive an erasure request without re-leaking the
    erased data.
"""
import json
import re
import uuid

from app.db import execute, query, serialize, to_dict


class AuditError(ValueError):
    """A caller supplied an audit row that must not be written."""


# ── Action vocabulary ─────────────────────────────────────────────────────────
# Closed enumeration, held here rather than in a DB CHECK so EP35/EP39 extend it
# by editing one frozenset instead of shipping a migration. Verbs are past tense
# and describe WHAT HAPPENED TO THE ENTITY. Frozen for EP38 (technical design
# §3.4); later epics extend the list, they do not redefine the shape.
ACTIONS = frozenset({
    'EMPLOYEE_STATUS_CHANGED',
    'EMPLOYEE_OFFBOARD_INITIATED',
    'EMPLOYEE_OFFBOARD_COMPLETED',
    'EMPLOYEE_OFFBOARD_CANCELLED',
    'EMPLOYEE_SUSPENDED',
    'EMPLOYEE_REINSTATED',
    'EMPLOYEE_EXIT_TYPE_CORRECTED',
    'USER_ACCESS_REVOKED',
    'MANAGER_RELATIONSHIP_CLOSED',
    'MANAGER_REPORTS_REASSIGNED',
    'ORG_ASSIGNMENT_CLOSED',
    'VACATION_REQUEST_CANCELLED_BY_LIFECYCLE',
    'ORG_CHANGE_CANCELLED_BY_LIFECYCLE',
    'CHECKLIST_STARTED',
    'CHECKLIST_TASK_COMPLETED',
    'CHECKLIST_COMPLETED',
})

RETENTION_CLASSES = frozenset({'STANDARD', 'EMPLOYMENT', 'SECURITY'})
OUTCOMES = frozenset({'SUCCESS', 'FAILED'})

# Diff/metadata keys that must never reach the trail. Matched case-insensitively
# as substrings, so `password_hash`, `reset_token` and `api_key` are all caught.
_SECRETISH_KEYS = ('password', 'token', 'secret', 'api_key', 'apikey',
                   'private_key', 'session_key', 'salt', 'credential')

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)

_INSERT_SQL = """
    INSERT INTO audit_log (
        company_id, actor_user_id, actor_employee_id, actor_label, actor_roles,
        actor_ip, actor_session_id,
        subject_employee_id, subject_employee_number,
        action, entity_type, entity_id,
        before_state, after_state,
        reason, correlation_id, outcome, error_code,
        metadata, retention_class
    ) VALUES (
        %s::uuid, %s::uuid, %s::uuid, %s, %s::jsonb,
        %s, %s,
        %s::uuid, %s,
        %s, %s, %s::uuid,
        %s::jsonb, %s::jsonb,
        %s, %s::uuid, %s, %s,
        %s::jsonb, %s
    )
"""

_SELECT_COLS = """
    id, company_id::text AS company_id,
    actor_user_id::text AS actor_user_id,
    actor_employee_id::text AS actor_employee_id,
    actor_label, actor_roles, actor_ip, actor_session_id,
    subject_employee_id::text AS subject_employee_id, subject_employee_number,
    action, entity_type, entity_id::text AS entity_id,
    before_state, after_state,
    reason, correlation_id::text AS correlation_id, outcome, error_code,
    metadata, retention_class, created_at
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def new_correlation_id():
    """A fresh correlation id. One per unit of work — pass it to every row."""
    return str(uuid.uuid4())


def _require_uuid(value, field):
    if not value or not _UUID_RE.match(str(value)):
        raise AuditError(f'{field} must be a UUID (got {value!r})')
    return str(value)


def _optional_uuid(value, field):
    return None if value in (None, '') else _require_uuid(value, field)


def _check_no_secrets(payload, where):
    for key in payload:
        low = str(key).lower()
        if any(bad in low for bad in _SECRETISH_KEYS):
            raise AuditError(
                f"{where} may not contain '{key}' — secrets and credentials are "
                f'never written to audit_log (ADR-009 §3.2b)')


def _clean_diff(payload, where):
    """Validate one side of a field-level diff and return it as a plain dict.

    A diff is a FLAT mapping of ``field -> scalar``. Nested structures are how a
    whole row gets smuggled in, so they are refused.
    """
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise AuditError(f'{where} must be a dict of changed fields, not '
                         f'{type(payload).__name__}')
    _check_no_secrets(payload, where)
    clean = {}
    for key, value in payload.items():
        if isinstance(value, uuid.UUID):
            value = str(value)
        else:
            # serialize() already normalises date/datetime -> ISO and Decimal ->
            # float, which is exactly what the read path expects back.
            value = serialize(value)
        if not isinstance(value, (str, bool, int, float, type(None))):
            raise AuditError(
                f'{where}[{key!r}] must be a scalar — audit diffs are '
                f'field-level, never nested rows (got {type(value).__name__})')
        clean[str(key)] = value
    return clean


def _actor_label(actor):
    """"Firstname Lastname <email>" as it was at the time of the action."""
    name = (actor.get('user_name') or actor.get('name') or '').strip()
    email = (actor.get('user_email') or actor.get('email') or '').strip()
    if name and email:
        return f'{name} <{email}>'[:255]
    if name or email:
        return (name or email)[:255]
    uid = actor.get('user_id') or actor.get('employee_id')
    return (f'user:{uid}' if uid else 'system')[:255]


def _client_ip():
    """Best-effort caller IP. Absent outside a request context — that is fine."""
    try:
        from flask import has_request_context, request
        if has_request_context():
            return (request.remote_addr or None)
    except Exception:                                   # pragma: no cover
        pass
    return None


def _build_row(action, entity_type, entity_id, *, company_id, actor, reason,
               before=None, after=None, subject_employee_id=None,
               subject_employee_number=None, correlation_id=None,
               outcome='SUCCESS', error_code=None, metadata=None,
               retention_class='STANDARD', actor_ip=None, actor_session_id=None):
    """Validate one entry and return the positional params for `_INSERT_SQL`.

    Pure — issues no SQL — so the validation rules are unit-testable without a
    database and `record_many()` can validate the whole batch before writing any
    of it.
    """
    if action not in ACTIONS:
        raise AuditError(
            f'unknown audit action {action!r}. The vocabulary is a closed '
            f'enumeration — add the code to audit_service.ACTIONS deliberately.')
    if not entity_type or not str(entity_type).strip():
        raise AuditError('entity_type is required')
    if retention_class not in RETENTION_CLASSES:
        raise AuditError(f'retention_class must be one of '
                         f'{sorted(RETENTION_CLASSES)} (got {retention_class!r})')
    if outcome not in OUTCOMES:
        raise AuditError(f'outcome must be one of {sorted(OUTCOMES)} '
                         f'(got {outcome!r})')
    if not isinstance(reason, str) or not reason.strip():
        raise AuditError(
            'reason is mandatory and must be non-blank — an audit row that '
            'cannot say WHY is not defensible (BA D4 R4.1 #10)')
    if not isinstance(actor, dict):
        raise AuditError('actor must be the light dict '
                         "{'user_id','employee_id','roles','company_id'}")

    # company_id comes from the AFFECTED ENTITY, never from the session and
    # never from request input — when a SYSTEM_ADMIN acts across tenants the row
    # must land in the affected tenant's trail (ADR-009 §3.3).
    company_id = _require_uuid(company_id, 'company_id')
    entity_id = _require_uuid(entity_id, 'entity_id')

    roles = actor.get('roles') or []
    if isinstance(roles, (str, bytes)):
        roles = [roles]
    roles = [str(r) for r in roles]

    meta = metadata or {}
    if not isinstance(meta, dict):
        raise AuditError('metadata must be a dict')
    _check_no_secrets(meta, 'metadata')

    before = _clean_diff(before, 'before')
    after = _clean_diff(after, 'after')
    if before is not None and after is not None and set(before) != set(after):
        raise AuditError(
            'before and after must describe the SAME fields — audit rows hold a '
            f'field-level diff, not two snapshots (before={sorted(before)}, '
            f'after={sorted(after)})')

    return (
        company_id,
        _optional_uuid(actor.get('user_id'), 'actor.user_id'),
        _optional_uuid(actor.get('employee_id'), 'actor.employee_id'),
        _actor_label(actor),
        json.dumps(roles),
        (actor_ip if actor_ip is not None else _client_ip()),
        actor_session_id,
        _optional_uuid(subject_employee_id, 'subject_employee_id'),
        (str(subject_employee_number)[:50] if subject_employee_number else None),
        action,
        str(entity_type),
        entity_id,
        json.dumps(before) if before is not None else None,
        json.dumps(after) if after is not None else None,
        reason.strip(),
        _require_uuid(correlation_id or new_correlation_id(), 'correlation_id'),
        outcome,
        error_code,
        json.dumps(meta),
        retention_class,
    )


# ── Write ─────────────────────────────────────────────────────────────────────

def record(action, entity_type, entity_id, **kwargs):
    """Append one audit row **inside the caller's open transaction**.

    Does not open a transaction and does not commit — see the module docstring.
    Call it from within the caller's ``with transaction():`` block so the row
    commits with the change it describes, and disappears with it on rollback.

    Required keyword arguments: ``company_id`` (from the affected entity),
    ``actor`` (the light dict), ``reason`` (non-blank).
    """
    execute(_INSERT_SQL, _build_row(action, entity_type, entity_id, **kwargs))


def record_many(entries):
    """Append several rows as one batch, in the caller's open transaction.

    ``entries`` is a list of dicts shaped like ``record()``'s arguments. The
    WHOLE batch is validated before ANY row is written, so a malformed entry
    cannot leave a half-written set behind even if the caller has no transaction
    open. Rows that belong to one unit of work should share a ``correlation_id``
    — generate it once with ``new_correlation_id()`` and pass it to each.
    """
    rows = []
    for i, entry in enumerate(entries or []):
        entry = dict(entry)
        try:
            action = entry.pop('action')
            entity_type = entry.pop('entity_type')
            entity_id = entry.pop('entity_id')
        except KeyError as exc:
            raise AuditError(
                f'entry {i} is missing {exc.args[0]!r}') from exc
        rows.append(_build_row(action, entity_type, entity_id, **entry))
    for params in rows:
        execute(_INSERT_SQL, params)


# ── Read ──────────────────────────────────────────────────────────────────────
# Both readers filter `company_id = %s::uuid` ONLY — never `OR company_id IS
# NULL`. There is no global/template audit trail and one tenant must never see
# another's rows (CLAUDE.md; BA D4 R4.2 / CC-14).

def _paging(limit, offset):
    return max(1, min(int(limit), 500)), max(0, int(offset))


def entity_timeline(company_id, entity_type, entity_id, limit=50, offset=0):
    """Newest-first trail for one entity within one company."""
    company_id = _require_uuid(company_id, 'company_id')
    entity_id = _require_uuid(entity_id, 'entity_id')
    limit, offset = _paging(limit, offset)
    return [to_dict(r) for r in query(f"""
        SELECT {_SELECT_COLS}
        FROM audit_log
        WHERE company_id = %s::uuid
          AND entity_type = %s
          AND entity_id = %s::uuid
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s
    """, (company_id, str(entity_type), entity_id, limit, offset))]


def company_timeline(company_id, *, action=None, actor_user_id=None,
                     correlation_id=None, since=None, until=None,
                     limit=50, offset=0):
    """Newest-first trail for one company, optionally narrowed.

    `correlation_id` is the one that matters operationally: it returns every row
    produced by a single unit of work, so an offboarding reads as one story
    rather than eleven scattered rows (BA D4 R4.1 #11).
    """
    company_id = _require_uuid(company_id, 'company_id')
    limit, offset = _paging(limit, offset)

    sql = [f'SELECT {_SELECT_COLS} FROM audit_log WHERE company_id = %s::uuid']
    params = [company_id]
    if action:
        sql.append('AND action = %s')
        params.append(action)
    if actor_user_id:
        sql.append('AND actor_user_id = %s::uuid')
        params.append(_require_uuid(actor_user_id, 'actor_user_id'))
    if correlation_id:
        sql.append('AND correlation_id = %s::uuid')
        params.append(_require_uuid(correlation_id, 'correlation_id'))
    if since:
        sql.append('AND created_at >= %s')
        params.append(since)
    if until:
        sql.append('AND created_at <= %s')
        params.append(until)
    sql.append('ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s')
    params += [limit, offset]

    return [to_dict(r) for r in query('\n'.join(sql), tuple(params))]

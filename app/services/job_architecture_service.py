"""Job architecture — families, levels and step expectations (KAN-190 · EP42 W1).

The ladder a company defines for itself: job **families**, ordinal **levels**
within a family (each carrying THE canonical title), and **steps** within a level
with an authored description of what each step expects.

Public API (used by app/routes/compensation.py):
    list_families(company_id)                        -> list[dict]
    create_family(company_id, code, name, ..., actor)
    update_family(company_id, family_id, ..., actor)
    list_levels(company_id, family_id=None)          -> list[dict]
    create_level(company_id, family_id, ordinal, title, step_count, ..., actor)
    update_level(company_id, level_id, ..., actor)   -> refuses an ordinal change once occupied
    level_steps(company_id, level_id)                -> every step, authored or not
    save_step_expectation(company_id, level_id, step_no, summary, description, ..., actor)
    ladder(company_id)                               -> families -> levels -> steps, for one render

Every function is **company-scoped** (`company_id = %s::uuid`, never
`OR company_id IS NULL`): a tenant with no ladder gets an empty list, never
another company's and never a global default.

**Save is publish.** There is no draft state and no review cycle — the screen
says so. A half-authored ladder is visible as a half-authored ladder, which is
honest; a draft that silently is not live is not.
"""
import datetime
import logging

from app.db import query, execute, insert_returning, to_dict, transaction
from app.services import audit_service

logger = logging.getLogger(__name__)

# §12.4.1 — `step_count` counts increments ABOVE entry, so the count of DISCRETE
# steps is always `step_count + 1`. The bound is 1..12 as a sanity limit; there
# is deliberately no default, because "we never decided" must not be
# indistinguishable from "we decided five".
MIN_STEP_COUNT = 1
MAX_STEP_COUNT = 12
MAX_ORDINAL = 30

# The empty state for a step nobody has authored yet. Never a blank, never
# inherited from the step below — an inherited expectation is a false claim about
# what this step asks of somebody.
UNAUTHORED = 'Expectations not yet defined'


class LadderError(Exception):
    """A business-rule refusal, carrying a message meant for the user."""


def _actor(user):
    """The light actor dict `audit_service` wants, from a session-ish dict."""
    return {'user_id': (user or {}).get('user_id'),
            'employee_id': (user or {}).get('employee_id'),
            'roles': (user or {}).get('roles') or []}


# ── Families ──────────────────────────────────────────────────────────────────

def list_families(company_id, include_inactive=False):
    """This company's families. Empty list when it has no ladder — never a default."""
    where = '' if include_inactive else ' AND is_active'
    rows = query(f"""
        SELECT id::text, code, name, description, sort_order, is_active,
               (SELECT COUNT(*)::int FROM job_levels l
                 WHERE l.job_family_id = f.id AND l.is_active) AS level_count
        FROM job_families f
        WHERE company_id = %s::uuid{where}
        ORDER BY sort_order, name
    """, (company_id,))
    return [to_dict(r) for r in rows]


def create_family(company_id, code, name, description=None, sort_order=0, actor=None):
    code = (code or '').strip().upper()
    name = (name or '').strip()
    if not code or not name:
        raise LadderError('A family needs both a short code and a name.')

    with transaction():
        row = insert_returning("""
            INSERT INTO job_families (company_id, code, name, description, sort_order)
            VALUES (%s::uuid, %s, %s, %s, %s)
            RETURNING id::text
        """, (company_id, code, name, (description or None), sort_order))
        audit_service.record(
            'JOB_FAMILY_CREATED', 'job_family', row['id'],
            company_id=company_id, actor=_actor(actor),
            reason=f'Job family {code} — {name} created.',
            metadata={'code': code, 'name': name})
    return row['id']


def update_family(company_id, family_id, name=None, description=None,
                  sort_order=None, is_active=None, actor=None):
    """Rename / re-describe / re-order / deactivate. The CODE is immutable.

    A family code is quoted in exports, CSV round-trips (KAN-191) and anything a
    customer has built around them, so renaming the *display* name is free while
    changing the identifier is not.
    """
    before = query("SELECT code, name, is_active FROM job_families "
                   "WHERE id=%s::uuid AND company_id=%s::uuid",
                   (family_id, company_id), one=True)
    if not before:
        raise LadderError('That job family does not exist in this company.')
    before = to_dict(before)

    sets, params = [], []
    if name is not None:
        if not name.strip():
            raise LadderError('A family name cannot be empty.')
        sets.append('name = %s'); params.append(name.strip())
    if description is not None:
        sets.append('description = %s'); params.append(description or None)
    if sort_order is not None:
        sets.append('sort_order = %s'); params.append(int(sort_order))
    if is_active is not None:
        sets.append('is_active = %s'); params.append(bool(is_active))
    if not sets:
        return
    sets.append('updated_at = NOW()')

    with transaction():
        execute(f"UPDATE job_families SET {', '.join(sets)} "
                f"WHERE id=%s::uuid AND company_id=%s::uuid",
                tuple(params) + (family_id, company_id))
        audit_service.record(
            'JOB_FAMILY_UPDATED', 'job_family', family_id,
            company_id=company_id, actor=_actor(actor),
            reason=f"Job family {before['code']} updated.",
            metadata={'code': before['code'],
                      'name_before': before['name'], 'name_after': name})


# ── Levels ────────────────────────────────────────────────────────────────────

def list_levels(company_id, family_id=None, include_inactive=False):
    clauses = ['l.company_id = %s::uuid']
    params = [company_id]
    if family_id:
        clauses.append('l.job_family_id = %s::uuid'); params.append(family_id)
    if not include_inactive:
        clauses.append('l.is_active')
    rows = query(f"""
        SELECT l.id::text, l.job_family_id::text AS job_family_id,
               f.code AS family_code, f.name AS family_name,
               l.ordinal, l.title, l.short_code, l.step_count, l.description,
               l.is_active,
               (SELECT COUNT(*)::int FROM job_step_expectations e
                 WHERE e.job_level_id = l.id) AS authored_steps,
               (SELECT COUNT(*)::int FROM employee_job_assignments a
                 WHERE a.job_level_id = l.id AND a.is_current) AS headcount
        FROM job_levels l
        JOIN job_families f ON f.id = l.job_family_id
        WHERE {' AND '.join(clauses)}
        ORDER BY f.sort_order, f.name, l.ordinal
    """, tuple(params))
    out = []
    for r in rows:
        d = to_dict(r)
        # `step_count` counts increments above entry, so the number of steps a
        # person can occupy is one more. Computed here so no template or JS ever
        # does this arithmetic — an off-by-one here is a wrong salary (§12.4.1).
        d['step_total'] = (d['step_count'] or 0) + 1
        d['top_step_label'] = f"{d['ordinal']}.{d['step_count']}"
        d['fully_authored'] = d['authored_steps'] >= d['step_total']
        out.append(d)
    return out


def _validate_step_count(step_count):
    try:
        n = int(step_count)
    except (TypeError, ValueError):
        raise LadderError('How many steps this level has must be a whole number.')
    if not MIN_STEP_COUNT <= n <= MAX_STEP_COUNT:
        raise LadderError(
            f'A level must have between {MIN_STEP_COUNT} and {MAX_STEP_COUNT} '
            f'steps above entry. You gave {n}.')
    return n


def create_level(company_id, family_id, ordinal, title, step_count,
                 short_code=None, description=None, actor=None):
    """Add a level to a family.

    `step_count` is **required** — there is no default, by design. The
    configurator has to ask, because Trainee→Junior and Junior→Mid are genuinely
    different distances and a default would record a decision nobody made.
    """
    title = (title or '').strip()
    if not title:
        raise LadderError('A level needs a title — it is the canonical job title.')
    n = _validate_step_count(step_count)
    try:
        ordinal = int(ordinal)
    except (TypeError, ValueError):
        raise LadderError('A level needs a position in the ladder.')
    if not 1 <= ordinal <= MAX_ORDINAL:
        raise LadderError(f'A level position must be between 1 and {MAX_ORDINAL}.')

    fam = query("SELECT code FROM job_families WHERE id=%s::uuid AND company_id=%s::uuid",
                (family_id, company_id), one=True)
    if not fam:
        raise LadderError('That job family does not exist in this company.')

    with transaction():
        row = insert_returning("""
            INSERT INTO job_levels
              (company_id, job_family_id, ordinal, title, short_code, step_count, description)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s)
            RETURNING id::text
        """, (company_id, family_id, ordinal, title, (short_code or None), n,
              (description or None)))
        audit_service.record(
            'JOB_LEVEL_CREATED', 'job_level', row['id'],
            company_id=company_id, actor=_actor(actor),
            reason=(f'Level {ordinal} "{title}" created in family '
                    f'{to_dict(fam)["code"]} with {n} steps above entry '
                    f'({n + 1} steps in total, .0 to .{n}).'),
            metadata={'ordinal': ordinal, 'title': title, 'step_count': n})
    return row['id']


def level_occupancy(company_id, level_id):
    """How many people are currently on this level — ever, not just now.

    Deliberately counts **historic** assignments too. An ordinal is a coordinate
    that past records point at; if anybody has EVER been on this level,
    renumbering it silently rewrites what those records mean.
    """
    row = query("""
        SELECT COUNT(*)::int AS n
        FROM employee_job_assignments
        WHERE job_level_id = %s::uuid AND company_id = %s::uuid
    """, (level_id, company_id), one=True)
    return (to_dict(row) if row else {}).get('n') or 0


def update_level(company_id, level_id, title=None, short_code=None,
                 description=None, ordinal=None, step_count=None,
                 is_active=None, actor=None):
    """Edit a level. Renaming is always allowed; **renumbering is not, once occupied.**

    ADR-017b. A level's `ordinal` is part of how every step is written down —
    `2.3` means "level 2, step 3" — so changing it after somebody has been placed
    silently rewrites history: last year's `2.3` now points at a different level.
    Inserting a level mid-ladder has no path once occupied, and the configurator
    says so **before** the ladder is built rather than at the moment it refuses.

    Reducing `step_count` below an occupied step is refused for the same reason
    it exists as a trigger: the top step would become a pay point nobody is
    entitled to.
    """
    before = query("""
        SELECT ordinal, title, step_count, job_family_id::text AS job_family_id
        FROM job_levels WHERE id=%s::uuid AND company_id=%s::uuid
    """, (level_id, company_id), one=True)
    if not before:
        raise LadderError('That level does not exist in this company.')
    before = to_dict(before)

    occupied = level_occupancy(company_id, level_id)

    if ordinal is not None and int(ordinal) != before['ordinal']:
        if occupied:
            raise LadderError(
                f"Level {before['ordinal']} can't be renumbered — "
                f"{occupied} assignment(s) already point at it, and a step is "
                f"written as level.step (for example {before['ordinal']}.2), so "
                f"renumbering would change what those records mean. Create a new "
                f"level and deactivate this one instead.")
        sets_ordinal = int(ordinal)
        if not 1 <= sets_ordinal <= MAX_ORDINAL:
            raise LadderError(f'A level position must be between 1 and {MAX_ORDINAL}.')
    else:
        sets_ordinal = None

    new_count = None
    if step_count is not None:
        new_count = _validate_step_count(step_count)
        if new_count < before['step_count']:
            highest = query("""
                SELECT MAX(step_no) AS s FROM employee_job_assignments
                WHERE job_level_id=%s::uuid AND company_id=%s::uuid AND is_current
            """, (level_id, company_id), one=True)
            highest = (to_dict(highest) if highest else {}).get('s')
            if highest is not None and highest > new_count:
                raise LadderError(
                    f"This level can't drop to {new_count} steps — somebody is "
                    f"currently on step {before['ordinal']}.{highest}. Move them "
                    f"first, or keep at least {highest} steps.")

    sets, params = [], []
    if title is not None:
        if not title.strip():
            raise LadderError('A level title cannot be empty.')
        sets.append('title = %s'); params.append(title.strip())
    if short_code is not None:
        sets.append('short_code = %s'); params.append(short_code or None)
    if description is not None:
        sets.append('description = %s'); params.append(description or None)
    if sets_ordinal is not None:
        sets.append('ordinal = %s'); params.append(sets_ordinal)
    if new_count is not None:
        sets.append('step_count = %s'); params.append(new_count)
    if is_active is not None:
        sets.append('is_active = %s'); params.append(bool(is_active))
    if not sets:
        return
    sets.append('updated_at = NOW()')

    with transaction():
        execute(f"UPDATE job_levels SET {', '.join(sets)} "
                f"WHERE id=%s::uuid AND company_id=%s::uuid",
                tuple(params) + (level_id, company_id))
        audit_service.record(
            'JOB_LEVEL_UPDATED', 'job_level', level_id,
            company_id=company_id, actor=_actor(actor),
            reason=(f"Level {before['ordinal']} \"{before['title']}\" updated"
                    + (f"; steps {before['step_count']} → {new_count}" if new_count is not None else '')
                    + '.'),
            metadata={'ordinal': before['ordinal'],
                      'title_before': before['title'], 'title_after': title,
                      'step_count_before': before['step_count'],
                      'step_count_after': new_count,
                      'occupied': occupied})


# ── Step expectations ─────────────────────────────────────────────────────────

def level_steps(company_id, level_id):
    """EVERY step of the level — `.0` through `.step_count` — authored or not.

    Returns the unauthored ones too, each flagged, because the point of the
    screen is to show what is still missing. A query that returned only authored
    rows would make an incomplete ladder look complete.
    """
    lvl = query("""
        SELECT ordinal, title, step_count FROM job_levels
        WHERE id=%s::uuid AND company_id=%s::uuid
    """, (level_id, company_id), one=True)
    if not lvl:
        raise LadderError('That level does not exist in this company.')
    lvl = to_dict(lvl)

    authored = {}
    for r in query("""
        SELECT step_no, summary, description, drafted_by, updated_at
        FROM job_step_expectations
        WHERE job_level_id=%s::uuid AND company_id=%s::uuid
        ORDER BY step_no
    """, (level_id, company_id)):
        d = to_dict(r)
        authored[d['step_no']] = d

    steps = []
    for n in range(0, (lvl['step_count'] or 0) + 1):
        a = authored.get(n)
        steps.append({
            'step_no': n,
            'label': f"{lvl['ordinal']}.{n}",
            'is_entry': n == 0,
            'authored': a is not None,
            'summary': a['summary'] if a else UNAUTHORED,
            'description': a['description'] if a else None,
            'drafted_by': a.get('drafted_by') if a else None,
            'updated_at': a.get('updated_at') if a else None,
        })
    return {'level': lvl, 'steps': steps}


def save_step_expectation(company_id, level_id, step_no, summary, description,
                          drafted_by=None, actor=None):
    """Author (or re-author) one step's expectations. **Save is publish.**

    Refuses a `step_no` outside the level's ladder here as well as in the trigger:
    the trigger guards `employee_job_assignments`, and expectations are a
    different table with the same off-by-one risk.
    """
    summary = (summary or '').strip()
    description = (description or '').strip()
    if not summary or not description:
        raise LadderError('A step needs both a one-line summary and the '
                          'responsibilities and expectations behind it.')
    if len(summary) > 200:
        raise LadderError('The one-line summary must be 200 characters or fewer.')

    lvl = query("SELECT ordinal, step_count FROM job_levels "
                "WHERE id=%s::uuid AND company_id=%s::uuid",
                (level_id, company_id), one=True)
    if not lvl:
        raise LadderError('That level does not exist in this company.')
    lvl = to_dict(lvl)
    try:
        n = int(step_no)
    except (TypeError, ValueError):
        raise LadderError('Which step this describes must be a whole number.')
    if n < 0 or n > lvl['step_count']:
        raise LadderError(
            f"Step {n} is not on this level: it runs {lvl['ordinal']}.0 to "
            f"{lvl['ordinal']}.{lvl['step_count']} "
            f"({lvl['step_count'] + 1} steps — the count is increments above entry).")

    existed = query("""
        SELECT 1 FROM job_step_expectations
        WHERE job_level_id=%s::uuid AND step_no=%s
    """, (level_id, n), one=True) is not None

    with transaction():
        execute("""
            INSERT INTO job_step_expectations
              (job_level_id, company_id, step_no, summary, description,
               drafted_by, updated_by_user_id, updated_at)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s::uuid, NOW())
            ON CONFLICT (job_level_id, step_no) DO UPDATE
              SET summary = EXCLUDED.summary,
                  description = EXCLUDED.description,
                  drafted_by = EXCLUDED.drafted_by,
                  updated_by_user_id = EXCLUDED.updated_by_user_id,
                  updated_at = NOW()
        """, (level_id, company_id, n, summary, description,
              (drafted_by or None), (actor or {}).get('user_id')))
        audit_service.record(
            'JOB_STEP_EXPECTATION_UPDATED' if existed else 'JOB_STEP_EXPECTATION_AUTHORED',
            'job_step_expectation', level_id,
            company_id=company_id, actor=_actor(actor),
            reason=(f"Expectations for step {lvl['ordinal']}.{n} "
                    f"{'updated' if existed else 'authored'}."),
            metadata={'step_no': n, 'summary': summary,
                      'drafted_by': drafted_by or None})


# ── The whole ladder, for one render ──────────────────────────────────────────

def ladder(company_id):
    """families → levels → step summaries, in one shape, for the configurator.

    One call rather than N+1 per level: the screen shows the whole ladder and its
    completeness at once, and the authored-step counts come from `list_levels`.
    """
    fams = list_families(company_id)
    levels = list_levels(company_id)
    by_family = {}
    for l in levels:
        by_family.setdefault(l['job_family_id'], []).append(l)
    for f in fams:
        f['levels'] = by_family.get(f['id'], [])
        f['authored_steps'] = sum(l['authored_steps'] for l in f['levels'])
        f['total_steps'] = sum(l['step_total'] for l in f['levels'])
    return fams


def ladder_completeness(company_id):
    """A named figure with its denominator (D7's rule), for the configurator.

    Reported rather than hidden because a ladder whose expectations are unwritten
    delivers none of the transparency this epic is for — and because KAN-191's
    step assessment has the authored expectations as a **hard dependency**, not a
    nicety. It cannot judge whether the text is any good; only a human can, which
    is why *"the ladder reads as a real description of the work"* is on the Demo
    Readiness Gate's must-be-walked list (R-18).
    """
    levels = list_levels(company_id)
    total = sum(l['step_total'] for l in levels)
    authored = sum(min(l['authored_steps'], l['step_total']) for l in levels)
    return {
        'levels': len(levels),
        'steps_total': total,
        'steps_authored': authored,
        'pct': round(authored * 100.0 / total, 1) if total else None,
        'levels_incomplete': [l['title'] for l in levels if not l['fully_authored']],
    }

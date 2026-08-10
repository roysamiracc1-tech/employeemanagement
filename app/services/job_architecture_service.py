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
from app.helpers import as_date
from app.services import audit_service
from app.services import notification_service as notif

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


# ══════════════════════════════════════════════════════════════════════════════
# KAN-191 — everyone on a level
#
# Two jobs that look similar and are not:
#
#   A. THE MAPPING PROJECT — every employee gets a LEVEL, driven from their
#      existing free-text `job_title`. 41 distinct titles at Acme, 75 at Telia,
#      for 146 people (R-2). Bulk, HR-driven, one sitting or several.
#
#   B. STEP ASSESSMENT — a MANAGER judges each direct report against the step
#      expectations authored in KAN-190. Distributed, per person, and it is the
#      only legitimate way a step is decided (amendment A6: a step may never be
#      derived from a salary).
#
# Keeping them apart matters. One HR person assessing 146 people is a project
# nobody finishes; forty managers assessing three or four each is a ten-minute
# task, and they are the only people who can do it correctly.
# ══════════════════════════════════════════════════════════════════════════════

# `step_no IS NULL` — a DISTINCT state, and NOT step 0 (A6). "Everyone defaults
# to .0" was itself a claim that a person is at entry level. Somebody in this
# state has no derived base pay, is not evaluable by the equity check, and is
# listed for assessment.
STEP_NOT_ASSESSED_LABEL = 'Step not yet assessed'


def step_label(ordinal, step_no):
    """`2.3`, or the honest empty state — never `2.0`, a dash, or a blank.

    One implementation, because a step rendered as `2.0` when nobody has assessed
    it is a false claim, and D7's empty-state rule applies to steps too.
    """
    if ordinal is None:
        return '—'
    if step_no is None:
        return STEP_NOT_ASSESSED_LABEL
    return f'{ordinal}.{step_no}'


# ── A. The mapping project ────────────────────────────────────────────────────

def title_counts(company_id):
    """Every distinct working title for ACTIVE employees, with headcount.

    One `GROUP BY`, company-scoped. Ordered by headcount descending so the
    titles that place the most people are at the top — that ordering is the
    difference between a screen somebody finishes and one they abandon.
    """
    rows = query("""
        SELECT COALESCE(NULLIF(btrim(e.job_title), ''), '(no title recorded)') AS job_title,
               COUNT(*)::int AS headcount,
               COUNT(a.id)::int AS already_placed,
               MAX(m.job_level_id::text) AS mapped_level_id,
               MAX(l.title)   AS mapped_level_title,
               MAX(l.ordinal) AS mapped_level_ordinal,
               MAX(f.name)    AS mapped_family_name
        FROM employees e
        LEFT JOIN job_title_level_map m
               ON m.company_id = e.company_id
              AND m.job_title = COALESCE(NULLIF(btrim(e.job_title), ''), '(no title recorded)')
        LEFT JOIN job_levels  l ON l.id = m.job_level_id
        LEFT JOIN job_families f ON f.id = l.job_family_id
        LEFT JOIN employee_job_assignments a
               ON a.employee_id = e.id AND a.is_current
        WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
        GROUP BY 1
        ORDER BY 2 DESC, 1
    """, (company_id,))
    return [to_dict(r) for r in rows]


def save_title_map(company_id, mappings, actor=None):
    """Record title -> level decisions. Does NOT place anybody.

    Deliberately separate from `apply_title_map`: deciding what a title means and
    changing 146 people's records are different acts, and somebody mapping titles
    over an afternoon must be able to save and come back.

    `mappings` is [{'job_title': str, 'job_level_id': str}, ...]. A NULL or empty
    level clears that title's mapping.
    """
    if not mappings:
        return 0
    n = 0
    with transaction():
        for m in mappings:
            title = (m.get('job_title') or '').strip()
            if not title:
                continue
            level_id = m.get('job_level_id') or None
            if level_id:
                execute("""
                    INSERT INTO job_title_level_map
                      (company_id, job_title, job_level_id, mapped_by_user_id, updated_at)
                    VALUES (%s::uuid, %s, %s::uuid, %s::uuid, NOW())
                    ON CONFLICT (company_id, job_title) DO UPDATE
                      SET job_level_id = EXCLUDED.job_level_id,
                          mapped_by_user_id = EXCLUDED.mapped_by_user_id,
                          updated_at = NOW()
                """, (company_id, title, level_id, (actor or {}).get('user_id')))
            else:
                execute("DELETE FROM job_title_level_map "
                        "WHERE company_id=%s::uuid AND job_title=%s",
                        (company_id, title))
            n += 1
        # ONE audit row for the sitting, carrying counts — not one per title
        # (ADR-009 §3.5). 75 rows saying "a title was mapped" is noise that
        # buries the rows somebody actually needs to find.
        # entity_id is the COMPANY: this is one decision about the company's
        # mapping, not 75 decisions about 75 rows. `audit_service` requires a
        # real UUID rather than accepting None — it refuses to write a row that
        # points at nothing, which is the correct strictness.
        audit_service.record(
            'JOB_TITLE_MAP_SAVED', 'company_job_title_map', company_id,
            company_id=company_id, actor=_actor(actor),
            reason=f'{n} working title(s) mapped to levels.',
            metadata={'titles': n})
    return n


def apply_title_map(company_id, actor=None, dry_run=True, effective_date=None):
    """Place every ACTIVE employee whose working title has a mapping.

    **Dry run first, always.** The screen shows what WOULD happen before anything
    is written, because this touches everybody at once and "undo" is not a thing.

    Employees already on a level are **skipped, never silently overwritten** — a
    bulk re-run must not quietly undo a manager's or HR's deliberate correction.
    Their step is left as it is: this story places people on LEVELS, and the step
    is a manager's judgement (A6), not a side effect of a bulk apply.

    Returns {'create': [...], 'skip': [...], 'error': [...], 'applied': bool}.
    """
    eff = effective_date or datetime.date.today()
    rows = query("""
        SELECT e.id::text AS employee_id,
               e.first_name || ' ' || e.last_name AS name,
               COALESCE(NULLIF(btrim(e.job_title), ''), '(no title recorded)') AS job_title,
               m.job_level_id::text AS job_level_id,
               l.ordinal, l.title AS level_title,
               a.id::text AS existing_assignment
        FROM employees e
        JOIN job_title_level_map m
          ON m.company_id = e.company_id
         AND m.job_title = COALESCE(NULLIF(btrim(e.job_title), ''), '(no title recorded)')
        JOIN job_levels l ON l.id = m.job_level_id
        LEFT JOIN employee_job_assignments a
               ON a.employee_id = e.id AND a.is_current
        WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
        ORDER BY e.last_name, e.first_name
    """, (company_id,))

    create, skip = [], []
    for r in rows:
        d = to_dict(r)
        target = {'employee_id': d['employee_id'], 'name': d['name'],
                  'job_title': d['job_title'], 'job_level_id': d['job_level_id'],
                  'level': f"{d['ordinal']} — {d['level_title']}"}
        if d['existing_assignment']:
            target['reason'] = 'already on a level'
            skip.append(target)
        else:
            create.append(target)

    if dry_run:
        return {'create': create, 'skip': skip, 'error': [], 'applied': False,
                'effective_date': eff.isoformat()}

    # ONE transaction for the whole apply. A failure part-way through must leave
    # ZERO assignments and ZERO audit rows — a half-placed workforce is worse
    # than an unplaced one, because nobody can tell which half is real.
    errors = []
    with transaction():
        for c in create:
            execute("""
                INSERT INTO employee_job_assignments
                  (company_id, employee_id, job_level_id, step_no,
                   effective_from, is_current, assigned_by_user_id, reason)
                VALUES (%s::uuid, %s::uuid, %s::uuid, NULL, %s, TRUE, %s::uuid, %s)
            """, (company_id, c['employee_id'], c['job_level_id'], eff,
                  (actor or {}).get('user_id'),
                  f"Bulk placement from working title \"{c['job_title']}\"."))
        # One audit row with counts, not 146 rows (ADR-009 §3.5).
        # One row for the whole apply, so the entity is the company's workforce
        # rather than any single assignment (ADR-009 §3.5).
        audit_service.record(
            'JOB_LEVEL_BULK_ASSIGNED', 'company_job_level_assignments', company_id,
            company_id=company_id, actor=_actor(actor),
            reason=(f'{len(create)} employee(s) placed on a level from their '
                    f'working title; {len(skip)} already placed and skipped. '
                    f'Steps left unassessed — a step is a manager judgement.'),
            metadata={'placed': len(create), 'skipped': len(skip),
                      'effective_date': eff.isoformat()})
    return {'create': create, 'skip': skip, 'error': errors, 'applied': True,
            'effective_date': eff.isoformat()}


def assign(company_id, employee_id, job_level_id, step_no=None,
           effective_date=None, reason=None, actor=None):
    """Place or move ONE employee, closing their current row on the same date.

    ADR-020's half-open `[from, to)`: the outgoing row's `effective_to` and the
    incoming row's `effective_from` are the SAME date, so the periods abut with
    no overlap and no gap. The database enforces that independently
    (`excl_eja_no_overlap`), so a bug here fails loudly rather than quietly
    producing two answers to "which level was she on in March?".
    """
    eff = effective_date or datetime.date.today()
    lvl = query("""
        SELECT ordinal, title, step_count FROM job_levels
        WHERE id = %s::uuid AND company_id = %s::uuid
    """, (job_level_id, company_id), one=True)
    if not lvl:
        raise LadderError('That level does not exist in this company.')
    lvl = to_dict(lvl)

    if step_no is not None:
        try:
            step_no = int(step_no)
        except (TypeError, ValueError):
            raise LadderError('A step must be a whole number.')
        if step_no < 0 or step_no > lvl['step_count']:
            raise LadderError(
                f"Step {step_no} is not on {lvl['title']}: it runs "
                f"{lvl['ordinal']}.0 to {lvl['ordinal']}.{lvl['step_count']}.")

    current = query("""
        SELECT id::text, job_level_id::text AS job_level_id, step_no, effective_from
        FROM employee_job_assignments
        WHERE employee_id = %s::uuid AND company_id = %s::uuid AND is_current
    """, (employee_id, company_id), one=True)
    current = to_dict(current) if current else None

    if current and as_date(current['effective_from']) and as_date(current['effective_from']) > eff:
        raise LadderError(
            'That date is before this employee\'s current level started. '
            'Correct the existing record rather than inserting behind it.')

    with transaction():
        if current:
            execute("""
                UPDATE employee_job_assignments
                SET is_current = FALSE, effective_to = %s
                WHERE id = %s::uuid
            """, (eff, current['id']))
        new_row = insert_returning("""
            INSERT INTO employee_job_assignments
              (company_id, employee_id, job_level_id, step_no,
               effective_from, is_current, assigned_by_user_id, reason)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, TRUE, %s::uuid, %s)
            RETURNING id::text
        """, (company_id, employee_id, job_level_id, step_no, eff,
              (actor or {}).get('user_id'), (reason or None)))
        audit_service.record(
            'JOB_LEVEL_CHANGED' if current else 'JOB_LEVEL_ASSIGNED',
            'employee_job_assignment', new_row['id'],
            company_id=company_id, actor=_actor(actor),
            subject_employee_id=employee_id,
            reason=(reason or
                    f"Placed on level {lvl['ordinal']} \"{lvl['title']}\" "
                    f"at step {step_label(lvl['ordinal'], step_no)}."),
            metadata={'level_ordinal': lvl['ordinal'], 'step_no': step_no,
                      'effective_date': eff.isoformat(),
                      'previous_step_no': (current or {}).get('step_no')})


def coverage(company_id):
    """Level coverage as a named figure WITH its denominator (D7).

    The unplaced are **counted and listed**, never silently dropped — an
    unplaced employee is invisible to the equity check, so a coverage figure
    without its remainder hides exactly the population that matters.
    """
    row = query("""
        SELECT COUNT(*)::int AS total,
               COUNT(a.id)::int AS placed,
               COUNT(a.id) FILTER (WHERE a.step_no IS NOT NULL)::int AS step_assessed
        FROM employees e
        LEFT JOIN employee_job_assignments a
               ON a.employee_id = e.id AND a.is_current
        WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
    """, (company_id,), one=True)
    d = to_dict(row) if row else {'total': 0, 'placed': 0, 'step_assessed': 0}

    unplaced = [to_dict(r) for r in query("""
        SELECT e.id::text AS employee_id,
               e.first_name || ' ' || e.last_name AS name,
               COALESCE(NULLIF(btrim(e.job_title), ''), '(no title recorded)') AS job_title
        FROM employees e
        LEFT JOIN employee_job_assignments a
               ON a.employee_id = e.id AND a.is_current
        WHERE e.company_id = %s::uuid AND e.employment_status = 'ACTIVE'
          AND a.id IS NULL
        ORDER BY e.last_name, e.first_name
        LIMIT 200
    """, (company_id,))]

    total = d['total'] or 0
    return {
        'total': total,
        'placed': d['placed'] or 0,
        'unplaced': total - (d['placed'] or 0),
        'step_assessed': d['step_assessed'] or 0,
        # NOT assessed is derived from PLACED, not from total: you cannot assess
        # a step for somebody who is not on a level yet.
        'step_not_assessed': (d['placed'] or 0) - (d['step_assessed'] or 0),
        'level_pct': round((d['placed'] or 0) * 100.0 / total, 1) if total else None,
        'step_pct': round((d['step_assessed'] or 0) * 100.0 / total, 1) if total else None,
        'unplaced_sample': unplaced,
    }


# ── B. Step assessment — a manager's judgement, never a derivation ────────────

def pending_assessments(company_id, manager_employee_id):
    """This manager's direct reports who are on a level but have no step.

    Scoped to their own reports on purpose. They are the only people who can do
    this correctly, and distributing it is the difference between the exercise
    finishing and not.
    """
    rows = query("""
        SELECT e.id::text AS employee_id,
               e.first_name || ' ' || e.last_name AS name,
               COALESCE(NULLIF(btrim(e.job_title), ''), '') AS job_title,
               a.id::text AS assignment_id, a.step_no,
               l.id::text AS job_level_id, l.ordinal, l.title AS level_title,
               l.step_count, f.name AS family_name
        FROM manager_relationships mr
        JOIN employees e ON e.id = mr.employee_id AND e.employment_status = 'ACTIVE'
        JOIN employee_job_assignments a ON a.employee_id = e.id AND a.is_current
        JOIN job_levels   l ON l.id = a.job_level_id
        JOIN job_families f ON f.id = l.job_family_id
        WHERE mr.manager_id = %s::uuid
          AND mr.relationship_type = 'SOLID_LINE' AND mr.is_current
          AND e.company_id = %s::uuid
        ORDER BY (a.step_no IS NOT NULL), e.last_name, e.first_name
    """, (manager_employee_id, company_id))
    out = []
    for r in rows:
        d = to_dict(r)
        d['step_display'] = step_label(d['ordinal'], d['step_no'])
        d['assessed'] = d['step_no'] is not None
        out.append(d)
    return out


def assess_step(company_id, employee_id, step_no, actor=None, reason=None,
                is_hr_override=False):
    """Record a manager's assessment of a report's step. A6's core rule.

    **NOTHING is pre-selected, nothing is suggested, and nothing is derived from
    pay.** A pre-selection is a system claim about somebody's job content, and
    D4c's discipline — mandatory to answer, nothing pre-selected — applies to the
    one field amendment A6 exists to protect.

    HR may override, and then a reason is **mandatory**: HR is not the person who
    can judge the work, so an override has to say why it was made anyway.
    """
    if step_no is None or step_no == '':
        raise LadderError('Choose the step this person is at — there is nothing '
                          'pre-selected, because only you can judge it.')
    if is_hr_override and not (reason or '').strip():
        raise LadderError('An HR override needs a reason: you are recording a '
                          'judgement that is normally the manager\'s to make.')

    row = query("""
        SELECT a.id::text, a.step_no, a.job_level_id::text AS job_level_id,
               l.ordinal, l.title, l.step_count
        FROM employee_job_assignments a
        JOIN job_levels l ON l.id = a.job_level_id
        WHERE a.employee_id = %s::uuid AND a.company_id = %s::uuid AND a.is_current
    """, (employee_id, company_id), one=True)
    if not row:
        raise LadderError('This employee is not on a level yet, so there is no '
                          'ladder to assess them against.')
    row = to_dict(row)

    try:
        n = int(step_no)
    except (TypeError, ValueError):
        raise LadderError('A step must be a whole number.')
    if n < 0 or n > row['step_count']:
        raise LadderError(
            f"Step {n} is not on {row['title']}: it runs {row['ordinal']}.0 to "
            f"{row['ordinal']}.{row['step_count']}.")

    # The step must have DESCRIBED expectations. A6 makes the authored text the
    # only legitimate input to an assessment, so assessing against an undescribed
    # step is assessing against nothing — a hard dependency, not a nicety (R-18).
    described = query("""
        SELECT 1 FROM job_step_expectations
        WHERE job_level_id = %s::uuid AND step_no = %s
    """, (row['job_level_id'], n), one=True)
    if not described:
        raise LadderError(
            f"Step {row['ordinal']}.{n} has no description yet, so there is "
            f"nothing to assess against. Ask HR to describe it first.")

    before = row['step_no']
    with transaction():
        execute("""
            UPDATE employee_job_assignments
            SET step_no = %s, assigned_by_user_id = %s::uuid,
                reason = COALESCE(%s, reason)
            WHERE id = %s::uuid
        """, (n, (actor or {}).get('user_id'), (reason or None), row['id']))
        audit_service.record(
            'EMPLOYEE_STEP_ASSESSED', 'employee_job_assignment', row['id'],
            company_id=company_id, actor=_actor(actor),
            subject_employee_id=employee_id,
            reason=(reason or
                    f"Assessed at step {row['ordinal']}.{n} against the "
                    f"described expectations for that step."),
            # The step, never a pay figure — amounts stay out of the trail
            # entirely (ADR-009). The pay consequence is derived on read by a
            # `compensation:r` holder.
            metadata={'step_before': before, 'step_after': n,
                      'level_ordinal': row['ordinal'],
                      'hr_override': bool(is_hr_override)},
            retention_class='EMPLOYMENT')
    return {'step_no': n, 'label': f"{row['ordinal']}.{n}",
            'was_first_assessment': before is None}


# ══════════════════════════════════════════════════════════════════════════════
# KAN-207 — step roadmaps
#
# **The object the owner actually asked for**, and it is NOT KAN-190's step
# expectation. The distinction is the whole story:
#
#   EXPECTATION (KAN-190)  what step 1.2 means *here*, for anybody
#   ROADMAP     (KAN-207)  what *you, specifically* need to do to get there
#
# ⚠ NO RATINGS, NO SCORES, NO ASSESSMENT OF ANY KIND. A roadmap is a statement of
# expectations. That boundary is what keeps it out of GDPR Art. 22 and EU AI Act
# territory: a scored or automated judgement about a person is a different legal
# object with different obligations. Nothing here computes, ranks or predicts.
# ══════════════════════════════════════════════════════════════════════════════

REVIEW_CONTEXTS = ('PROBATION_REVIEW', 'MID_TERM_GOAL_REVIEW',
                   'PERFORMANCE_REVIEW', 'OFF_CYCLE')

REVIEW_CONTEXT_LABELS = {
    'PROBATION_REVIEW':     'Probation review',
    'MID_TERM_GOAL_REVIEW': 'Mid-term goal review',
    'PERFORMANCE_REVIEW':   'Performance review',
    'OFF_CYCLE':            'Off-cycle conversation',
}


def displays_step(company_id):
    """Does this company show an employee their own STEP NUMBER? (A2 §6)

    Governs **display, not inference** — the employee reads the whole ladder and
    their own expectations either way, which is why the setting is labelled
    *do not display* and never *hide* (standing rule 6: a label is a claim).

    It governs the STEP, not the level: in the owner's own example the title
    *Junior Software Fullstack Engineer* **is** level 2, and the title is always
    visible, so a switch claiming to hide the level would hide nothing.
    """
    row = query("SELECT display_step_to_employee AS on FROM companies WHERE id=%s::uuid",
                (company_id,), one=True)
    # Absent company → assume the transparent default rather than the restrictive
    # one: the owner asked for this twice, so withholding is the exception.
    return True if row is None else bool(to_dict(row)['on'])


def next_step_target(company_id, employee_id):
    """Where this person is, and the next rung up. None if they are not placed.

    "Next" is the next STEP in the same level, or the entry step of the next
    level once they are at the top of theirs. Returned as data so the caller
    renders it; nothing here decides whether they are *ready* — that would be an
    assessment, which this object must never make.
    """
    cur = query("""
        SELECT a.job_level_id::text AS job_level_id, a.step_no,
               l.ordinal, l.title, l.step_count, l.job_family_id::text AS job_family_id,
               f.name AS family_name
        FROM employee_job_assignments a
        JOIN job_levels   l ON l.id = a.job_level_id
        JOIN job_families f ON f.id = l.job_family_id
        WHERE a.employee_id=%s::uuid AND a.company_id=%s::uuid AND a.is_current
    """, (employee_id, company_id), one=True)
    if not cur:
        return None
    cur = to_dict(cur)

    # A step that has never been assessed has no "next": proposing one would be
    # asserting where they are, which is exactly the claim STEP_NOT_ASSESSED
    # exists to refuse to make (A6).
    if cur['step_no'] is None:
        return {'current': cur, 'target': None,
                'reason': 'Their step has not been assessed yet, so there is no '
                          'next step to point at. Assess it first under Team Steps.'}

    if cur['step_no'] < cur['step_count']:
        target = {'job_level_id': cur['job_level_id'], 'step_no': cur['step_no'] + 1,
                  'ordinal': cur['ordinal'], 'level_title': cur['title'],
                  'same_level': True}
    else:
        nxt = query("""
            SELECT id::text, ordinal, title, step_count FROM job_levels
            WHERE company_id=%s::uuid AND job_family_id=%s::uuid
              AND ordinal > %s AND is_active
            ORDER BY ordinal LIMIT 1
        """, (company_id, cur['job_family_id'], cur['ordinal']), one=True)
        if not nxt:
            return {'current': cur, 'target': None,
                    'reason': 'They are at the top step of the highest level in '
                              'this family, so there is no next step defined.'}
        nxt = to_dict(nxt)
        target = {'job_level_id': nxt['id'], 'step_no': 0,
                  'ordinal': nxt['ordinal'], 'level_title': nxt['title'],
                  'same_level': False}
    return {'current': cur, 'target': target, 'reason': None}


def live_roadmap(company_id, employee_id):
    """The one live roadmap, or None. Superseded versions are read separately."""
    row = query("""
        SELECT r.id::text, r.version, r.content, r.review_context, r.review_date,
               r.authored_by_label, r.authored_at, r.acknowledged_at,
               r.from_step_no, r.target_step_no,
               fl.ordinal AS from_ordinal, fl.title AS from_title,
               tl.ordinal AS target_ordinal, tl.title AS target_title,
               f.name AS family_name
        FROM employee_step_roadmaps r
        JOIN job_levels fl ON fl.id = r.from_job_level_id
        JOIN job_levels tl ON tl.id = r.target_job_level_id
        JOIN job_families f ON f.id = tl.job_family_id
        WHERE r.employee_id=%s::uuid AND r.company_id=%s::uuid
          AND r.superseded_at IS NULL
    """, (employee_id, company_id), one=True)
    return _decorate_roadmap(to_dict(row), company_id) if row else None


def roadmap_history(company_id, employee_id):
    """Every version, newest first. "What did we agree in March" is the point."""
    rows = query("""
        SELECT r.id::text, r.version, r.content, r.review_context, r.review_date,
               r.authored_by_label, r.authored_at, r.acknowledged_at, r.superseded_at,
               r.from_step_no, r.target_step_no,
               fl.ordinal AS from_ordinal, fl.title AS from_title,
               tl.ordinal AS target_ordinal, tl.title AS target_title,
               f.name AS family_name
        FROM employee_step_roadmaps r
        JOIN job_levels fl ON fl.id = r.from_job_level_id
        JOIN job_levels tl ON tl.id = r.target_job_level_id
        JOIN job_families f ON f.id = tl.job_family_id
        WHERE r.employee_id=%s::uuid AND r.company_id=%s::uuid
        ORDER BY r.version DESC
    """, (employee_id, company_id))
    return [_decorate_roadmap(to_dict(r), company_id) for r in rows]


def _decorate_roadmap(d, company_id):
    """Render-ready labels, including the disclosure-off variant.

    ⚠ THE ACKNOWLEDGEMENT LABEL IS THE POINT (CFL-42-50). "Discussed with Ravi on
    14 March", never "agreed" — recording agreement when somebody merely read it
    is a false record about a person.
    """
    show_step = displays_step(company_id)
    d['review_context_label'] = REVIEW_CONTEXT_LABELS.get(d.get('review_context'),
                                                          d.get('review_context'))
    d['acknowledged'] = d.get('acknowledged_at') is not None
    d['is_live'] = d.get('superseded_at') is None
    if show_step:
        d['from_label'] = step_label(d['from_ordinal'], d['from_step_no'])
        d['target_label'] = step_label(d['target_ordinal'], d['target_step_no'])
        d['target_heading'] = (f"Towards {d['target_label']} — {d['target_title']}")
    else:
        # A2 option (b). The roadmap still reads, in full — hiding it would
        # discard the transparency he asked for twice in order to hide a label.
        # But NO step number and NO "you are here" marker: showing "your next
        # step is 2.4" would disclose the very thing the switch is for.
        d['from_label'] = None
        d['target_label'] = None
        d['target_heading'] = 'What the next set of expectations looks like'
    d['shows_step'] = show_step
    return d


def author_roadmap(company_id, employee_id, content, review_context,
                   review_date=None, actor=None, author_label=None):
    """Write a roadmap for one person. Supersedes the previous version.

    **Versioned, never overwritten.** Roadmaps are re-agreed at each review, and
    the previous version stays readable — that is the entire reason this is a
    version chain rather than an `UPDATE`.

    The from/target coordinates are **denormalised on purpose**: the target must
    survive the employee moving, so "what did we agree in March" still reads
    correctly after a level change. Resolving it through the live assignment
    instead would silently re-target every historical roadmap on promotion.
    """
    content = (content or '').strip()
    if not content:
        raise LadderError('A roadmap needs to say what they need to do — that is '
                          'the whole object.')
    if review_context not in REVIEW_CONTEXTS:
        raise LadderError('Say which conversation this came out of.')

    where = next_step_target(company_id, employee_id)
    if where is None:
        raise LadderError('This person is not on a level yet, so there is no next '
                          'step to write a roadmap towards.')
    if where['target'] is None:
        raise LadderError(where['reason'])

    cur, tgt = where['current'], where['target']
    prev = query("""
        SELECT id::text, version FROM employee_step_roadmaps
        WHERE employee_id=%s::uuid AND company_id=%s::uuid AND superseded_at IS NULL
    """, (employee_id, company_id), one=True)
    prev = to_dict(prev) if prev else None
    version = (prev['version'] + 1) if prev else 1

    corr = audit_service.new_correlation_id()
    with transaction():
        if prev:
            # Superseded in the SAME transaction as the new version is written, so
            # `uq_esr_one_live` can never see two live rows.
            execute("UPDATE employee_step_roadmaps SET superseded_at=NOW() "
                    "WHERE id=%s::uuid", (prev['id'],))
        row = insert_returning("""
            INSERT INTO employee_step_roadmaps
              (company_id, employee_id, version,
               from_job_level_id, from_step_no, target_job_level_id, target_step_no,
               content, review_context, review_date,
               authored_by_user_id, authored_by_label, correlation_id)
            VALUES (%s::uuid, %s::uuid, %s,
                    %s::uuid, %s, %s::uuid, %s,
                    %s, %s, %s,
                    %s::uuid, %s, %s::uuid)
            RETURNING id::text
        """, (company_id, employee_id, version,
              cur['job_level_id'], cur['step_no'], tgt['job_level_id'], tgt['step_no'],
              content, review_context, review_date,
              (actor or {}).get('user_id'), (author_label or 'Their manager'), corr))
        audit_service.record(
            'STEP_ROADMAP_AUTHORED', 'employee_step_roadmap', row['id'],
            company_id=company_id, actor=_actor(actor),
            subject_employee_id=employee_id,
            reason=(f'Step roadmap v{version} written towards '
                    f"{tgt['ordinal']}.{tgt['step_no']}, out of a "
                    f"{REVIEW_CONTEXT_LABELS[review_context].lower()}."),
            correlation_id=corr,
            # The step coordinates and the context — never the CONTENT, which is
            # free text about a named person, and never a pay figure (ADR-009).
            metadata={'version': version, 'from_step_no': cur['step_no'],
                      'target_step_no': tgt['step_no'],
                      'review_context': review_context,
                      'superseded_version': (prev or {}).get('version')},
            retention_class='EMPLOYMENT')

    # ── Tell the employee, once, in-app ──────────────────────────────────────
    #
    # ⚠ THE OWNER OVERRULED THE BA'S AND UX'S "NO" HERE, and his reasoning is
    # the reason this exists: **a roadmap the employee does not know about
    # delivers exactly zero transparency**, and "it appears on their profile"
    # assumes they visit their profile.
    #
    # Sent AFTER the unit of work has committed — a notification cannot be rolled
    # back (EP38 technical design §5.4), so announcing before the commit risks
    # telling somebody about a roadmap that does not exist.
    #
    # No email (his constraint). Retires on view — it is an FYI, not a call to
    # action, so it must not sit in the bell like an approval waiting to be
    # decided. And it carries NO pay information and no step number: the message
    # is deliberately readable whether or not the company displays steps.
    try:
        for uid in _subject_user_ids_for(employee_id):
            notif.create_user_notification(
                uid, 'STEP_ROADMAP_AUTHORED',
                'Your manager has written what your next step needs from you.',
                link='/my-ladder',
                related_type='STEP_ROADMAP', related_id=row['id'])
    except Exception:
        # A failed notification must not undo a written roadmap — the roadmap is
        # the thing of value and it has already committed.
        logger.exception('KAN-207: failed to notify employee about roadmap %s', row['id'])

    return {'id': row['id'], 'version': version, 'correlation_id': corr}


def _subject_user_ids_for(employee_id):
    rows = query("SELECT id::text FROM users WHERE employee_id=%s::uuid AND is_active",
                 (employee_id,))
    return [r['id'] for r in rows]


def acknowledge_roadmap(company_id, employee_id, actor=None):
    """The employee confirms **the conversation happened**. Not agreement.

    ⚠ CFL-42-50. Recording "agreed" when somebody merely read it is a false
    record about a person, so nothing here stores agreement, the button says
    *Confirm we discussed this*, and the rendered state says *Discussed with Ravi
    on 14 March*.

    Idempotent: confirming twice is not an error and does not move the date — the
    first confirmation is when the conversation happened.
    """
    row = query("""
        SELECT id::text, version, acknowledged_at FROM employee_step_roadmaps
        WHERE employee_id=%s::uuid AND company_id=%s::uuid AND superseded_at IS NULL
    """, (employee_id, company_id), one=True)
    if not row:
        raise LadderError('There is no current roadmap to confirm.')
    row = to_dict(row)
    if row['acknowledged_at']:
        return {'already': True, 'at': row['acknowledged_at']}

    with transaction():
        execute("""
            UPDATE employee_step_roadmaps
            SET acknowledged_at = NOW(), acknowledged_by_user_id = %s::uuid
            WHERE id = %s::uuid
        """, ((actor or {}).get('user_id'), row['id']))
        audit_service.record(
            'STEP_ROADMAP_DISCUSSION_CONFIRMED', 'employee_step_roadmap', row['id'],
            company_id=company_id, actor=_actor(actor),
            subject_employee_id=employee_id,
            # The wording matters in the trail too: this row must not later be
            # read as the employee agreeing with the content.
            reason=(f'Employee confirmed the roadmap conversation took place '
                    f'(v{row["version"]}). This records the DISCUSSION, not '
                    f'agreement with its content.'),
            metadata={'version': row['version']},
            retention_class='EMPLOYMENT')
    return {'already': False}


def mark_roadmap_seen(roadmap_id):
    """Retire the FYI notification once the employee has looked at the roadmap.

    It is an FYI, not a call to action, so it must **not** sit in the bell like an
    approval waiting to be decided (DEF-003's lesson applied to the other
    direction). Never raises: failing to tidy the bell must not break the page.
    """
    try:
        notif.resolve_related('STEP_ROADMAP', roadmap_id, ['STEP_ROADMAP_AUTHORED'])
    except Exception:
        logger.exception('KAN-207: failed to retire the roadmap notification')


def unacknowledged_roadmaps(company_id, author_user_id):
    """Roadmaps this manager wrote that nobody has confirmed discussing.

    **This is what replaces a blocking workflow.** An unacknowledged roadmap is
    still live and nothing is blocked by it — a non-responsive employee must not
    be able to freeze their own development plan — so the follow-up is surfaced
    to the person who can have the conversation instead.
    """
    rows = query("""
        SELECT r.id::text, r.version, r.authored_at,
               e.first_name || ' ' || e.last_name AS name,
               e.id::text AS employee_id
        FROM employee_step_roadmaps r
        JOIN employees e ON e.id = r.employee_id
        WHERE r.company_id=%s::uuid AND r.authored_by_user_id=%s::uuid
          AND r.acknowledged_at IS NULL AND r.superseded_at IS NULL
        ORDER BY r.authored_at
    """, (company_id, author_user_id))
    return [to_dict(r) for r in rows]

"""Capture the (company × feature × role) effective-access matrix — KAN-188.

**This is the acceptance criterion for KAN-188, and it only works if it is run
BEFORE the code changes.** The story rewires `_load_feature_access()` to make
`company_features.is_enabled` a term in effective access. The risk is not that
the switch fails to work — it is that it silently changes somebody's access as a
side effect, in a product where 14 of 18 existing `company_features` rows are
`FALSE` for features that nothing currently reads.

Wire those in naively and most of the product switches off for two of the three
companies. Nobody would notice from a green test suite, because no test asserts
"HR_ADMIN can still reach vacations at Acme".

So: capture the truth through the REAL resolver, diff it after, and require the
two to be identical except where a change is intended and named.

Usage (needs a live database — it walks the real code path, not a mock):

    PGDATABASE=employee python3 tests/fixtures/capture_feature_matrix.py before
    #  … make the change, run the migration …
    PGDATABASE=employee python3 tests/fixtures/capture_feature_matrix.py after
    PGDATABASE=employee python3 tests/fixtures/capture_feature_matrix.py diff

`before`/`after` write JSON beside this file. `diff` exits non-zero on any cell
that moved, printing each one — so it is usable as a gate, not just a report.

It calls `_load_feature_access()` with a faked session rather than re-implementing
the resolver's SQL. A re-implementation would drift from the thing it is meant to
be checking, and would happily agree with a bug in either copy.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

HERE = os.path.dirname(os.path.abspath(__file__))

# Every role NAME in the product. Deliberately the full list rather than "the
# interesting ones": the cell that moves unnoticed is always one nobody thought
# was interesting.
ROLES = ['COMPANY_ADMIN', 'DEPARTMENT_HEAD', 'DOTTED_LINE_MANAGER', 'EMPLOYEE',
         'HIRING_MANAGER', 'HR_ADMIN', 'LOCATION_HEAD', 'PORTAL_ADMIN',
         'SOLID_LINE_MANAGER', 'SYSTEM_ADMIN']


def capture():
    """{company_name: {role: {feature: 'rwd' flags}}} via the real resolver."""
    from app import app as flask_app
    from app.db import query
    from app.auth import _load_feature_access

    # `query()` needs an app context for its `g`-cached connection.
    with flask_app.app_context():
        companies = [dict(r) for r in query(
            "SELECT id::text AS id, name FROM companies WHERE is_active ORDER BY name")]
        features = sorted(r['code'] for r in query("SELECT code FROM portal_features"))

    matrix = {'_features': features, '_roles': ROLES, 'cells': {}}
    for co in companies:
        matrix['cells'][co['name']] = {}
        for role in ROLES:
            with flask_app.test_request_context('/'):
                from flask import session, g
                session['roles'] = [role]
                session['company_id'] = co['id']
                session['user_id'] = '00000000-0000-0000-0000-000000000001'
                # `g` is per-context, so each iteration resolves fresh rather
                # than reading the previous role's cached answer.
                if hasattr(g, '_feature_access'):
                    del g._feature_access
                access = _load_feature_access()
            matrix['cells'][co['name']][role] = {
                f: ''.join(k for k in 'rwd' if access.get(f, {}).get(k))
                for f in features
            }
    return matrix


# ── The only changes KAN-188 is allowed to make ───────────────────────────────
#
# The `before` snapshot measures `_load_feature_access()`, which BEFORE KAN-188
# never consulted `company_features` at all. The two hand-rolled gates that did
# — `_analytics_enabled` and `_si_enabled` — lived OUTSIDE the resolver, inside
# `analytics.py` and `skills_intelligence.py`, so their denials were invisible to
# this snapshot.
#
# That blind spot is precisely where the one real defect in this story hid. A
# blanket `default_enabled = TRUE` materialised `reports` and
# `skills_intelligence` as ON for 'Sam Cpmapny', which had no row for either —
# and the old gates read "no row" as DENIED. The matrix said IDENTICAL while the
# migration was quietly granting two features to a company that never had them.
#
# So the resolver now (correctly) denies those cells, which registers here as a
# change. It is a change in the SNAPSHOT, not in what any user can reach:
# effective access before was `resolver AND hand-rolled gate` = denied, and
# after is `resolver (including the switch)` = denied.
#
# Encoded as an explicit allow-list rather than eyeballed, so the diff stays a
# real gate: anything outside this list still fails.
LICENSED_FEATURES = {'reports', 'skills_intelligence'}

# Companies that had NO company_features row for a licensed feature before the
# migration, and were therefore already denied it by the old hand-rolled gate.
COMPANIES_WITHOUT_LICENCE = {'Sam Cpmapny'}


def _is_expected(company, role, feature, before_flags, after_flags):
    """Is this cell's movement one KAN-188 intends?

    Exactly one shape qualifies: a licensed feature, at a company that never had
    a row for it, losing access it only ever had ON PAPER — the resolver granted
    it while the hand-rolled gate denied it. Access may only be REMOVED here,
    never added: `after` must be empty. A cell that gains access is always a
    defect, whatever else is true about it.
    """
    return (feature in LICENSED_FEATURES
            and company in COMPANIES_WITHOUT_LICENCE
            and role != 'SYSTEM_ADMIN'      # the bypass must never move
            and after_flags == ''           # removal only
            and before_flags != '')


def cells(m):
    for co, roles in m['cells'].items():
        for role, feats in roles.items():
            for feat, flags in feats.items():
                yield (co, role, feat), flags


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'before'

    if mode in ('before', 'after'):
        m = capture()
        path = os.path.join(HERE, f'feature_matrix_{mode}.json')
        with open(path, 'w') as fh:
            json.dump(m, fh, indent=1, sort_keys=True)
        total = sum(1 for _ in cells(m))
        granted = sum(1 for _, f in cells(m) if f)
        print(f'{mode}: {total} cells ({len(m["cells"])} companies × '
              f'{len(m["_features"])} features × {len(m["_roles"])} roles), '
              f'{granted} with any access → {path}')
        return 0

    if mode == 'diff':
        with open(os.path.join(HERE, 'feature_matrix_before.json')) as fh:
            before = dict(cells(json.load(fh)))
        with open(os.path.join(HERE, 'feature_matrix_after.json')) as fh:
            after = dict(cells(json.load(fh)))
        moved = [(k, before.get(k), after.get(k))
                 for k in sorted(set(before) | set(after))
                 if before.get(k) != after.get(k)]

        expected = [m for m in moved if _is_expected(*m[0], m[1], m[2])]
        unexpected = [m for m in moved if m not in expected]

        if expected:
            print(f'{len(expected)} EXPECTED change(s) — see EXPECTED_CHANGES:')
            for (co, role, feat), b, a in expected:
                print(f'  ✓ {co:<12} {role:<22} {feat:<22} {b!r} -> {a!r}')
        if not unexpected:
            print(f'NO UNEXPECTED CHANGES — {len(before) - len(expected)} of '
                  f'{len(before)} cells identical, {len(expected)} changed as designed.')
            return 0
        print(f'{len(unexpected)} of {len(before)} cells moved UNEXPECTEDLY:')
        for (co, role, feat), b, a in unexpected:
            print(f'  ✗ {co:<12} {role:<22} {feat:<22} {b!r} -> {a!r}')
        return 1

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())

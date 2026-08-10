"""KAN-190 — job families, levels and step expectations (EP42 W1).

The ladder is the foundation everything in EP42 stands on: pay points (KAN-206),
step assessment (KAN-191), the equity check (KAN-200), promotions (KAN-192). The
rules worth testing are the ones that are expensive to get wrong later:

* **`step_count` counts increments ABOVE entry.** 5 means SIX steps, `.0` … `.5`.
  An off-by-one here is not cosmetic — it is a pay point compounded once too
  often, a finding raised against a rate nobody is entitled to, and a pre-filled
  pay rise from a number that should not exist (§12.4.1).
* **No default for `step_count`.** "We never decided" must not be
  indistinguishable from "we decided five".
* **An ordinal is immutable once occupied.** A step is written `2.3`; renumbering
  level 2 silently rewrites what every historical record means (ADR-017b).
* **Two different gates on one screen** — reading the ladder is
  `job_architecture:r` (everyone), configuring it is `org_structure:w`. And
  `job_architecture:w` is roadmap authoring, NOT ladder editing (CFL-42-35).
* **No ratings anywhere near the ladder.** The §14.5 / R-17 boundary.

All DB interaction is mocked; data is synthetic.
"""
import json
import re

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session, FakeTransaction, recording_execute


CO = 'co-1'
FAM = 'fam-eng'
LVL = 'lvl-2'


@pytest.fixture
def hr_client(client):
    """HR_ADMIN — holds `org_structure:w`, so may configure the ladder."""
    _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'],
                 employee_id='emp-hr', user_id='u-hr')
    with client.session_transaction() as s:
        s['company_id'] = CO
    return client


@pytest.fixture
def employee_client(client):
    """A plain employee — may READ the ladder and configure nothing."""
    _set_session(client, roles=['EMPLOYEE'], employee_id='emp-e', user_id='u-e')
    with client.session_transaction() as s:
        s['company_id'] = CO
    return client


def _post(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type='application/json')


def _put(client, path, payload):
    return client.put(path, data=json.dumps(payload), content_type='application/json')


# ── The step-count semantics — the expensive one ──────────────────────────────

class TestStepCountCountsIncrementsAboveEntry:
    """§12.4.1. The owner's own example is `2.0 … 2.5` — six values."""

    def _levels(self, step_count):
        from app.services import job_architecture_service as svc
        row = {'id': LVL, 'job_family_id': FAM, 'family_code': 'ENG',
               'family_name': 'Engineering', 'ordinal': 2,
               'title': 'Junior Software Fullstack Engineer', 'short_code': 'L2',
               'step_count': step_count, 'description': None, 'is_active': True,
               'authored_steps': 0, 'headcount': 0}
        with patch.object(svc, 'query', return_value=[row]):
            return svc.list_levels(CO)[0]

    def test_five_means_six_steps(self):
        l = self._levels(5)
        assert l['step_total'] == 6, 'step_count counts increments ABOVE entry'
        assert l['top_step_label'] == '2.5'

    def test_three_means_four_steps(self):
        l = self._levels(3)
        assert l['step_total'] == 4
        assert l['top_step_label'] == '2.3'

    def test_one_means_two_steps(self):
        """The minimum: entry plus one increment."""
        l = self._levels(1)
        assert l['step_total'] == 2
        assert l['top_step_label'] == '2.1'

    def test_the_arithmetic_is_done_once_in_the_service(self):
        """No template or JS may recompute it — an off-by-one is a wrong salary."""
        import os
        for path in ('templates/admin/job_architecture.html',):
            with open(path) as f:
                src = f.read()
            # The dialog's live preview is the ONE place the client does it, and
            # it is a preview of the user's own unsaved input, not of stored data.
            assert 'step_count + 1' not in src, (
                'the client is recomputing the step total; use step_total from '
                'the service so there is one implementation')

    def test_every_step_is_listed_including_the_unauthored_ones(self):
        """A query returning only authored rows makes an incomplete ladder look
        complete — which is exactly what KAN-191 then depends on."""
        from app.services import job_architecture_service as svc
        lvl = {'ordinal': 2, 'title': 'Junior', 'step_count': 5}
        authored = [{'step_no': 0, 'summary': 'Entry', 'description': 'Does X',
                     'drafted_by': None, 'updated_at': None}]
        with patch.object(svc, 'query', side_effect=[lvl, authored]):
            out = svc.level_steps(CO, LVL)
        assert [s['step_no'] for s in out['steps']] == [0, 1, 2, 3, 4, 5]
        assert [s['label'] for s in out['steps']][-1] == '2.5'
        assert out['steps'][0]['authored'] is True
        assert all(not s['authored'] for s in out['steps'][1:])

    def test_an_unauthored_step_says_so_and_never_inherits(self):
        """An inherited expectation is a false claim about what a step asks."""
        from app.services import job_architecture_service as svc
        lvl = {'ordinal': 1, 'title': 'L1', 'step_count': 2}
        authored = [{'step_no': 0, 'summary': 'Entry summary',
                     'description': 'Entry detail', 'drafted_by': None,
                     'updated_at': None}]
        with patch.object(svc, 'query', side_effect=[lvl, authored]):
            steps = svc.level_steps(CO, LVL)['steps']
        assert steps[1]['summary'] == svc.UNAUTHORED
        assert steps[1]['description'] is None, 'it inherited the step below'
        assert 'not yet defined' in svc.UNAUTHORED.lower()


class TestStepCountHasNoDefault:
    """"We never decided" must not look like "we decided five"."""

    def test_the_column_has_no_default_in_the_migration(self):
        with open('database/migrations/12_job_architecture.sql') as f:
            sql = f.read()
        block = sql[sql.index('CREATE TABLE IF NOT EXISTS job_levels'):]
        block = block[:block.index(');')]
        # Comments in this block explain the no-default rule and mention the
        # column by name, so match the DECLARATION only.
        code = [l for l in block.splitlines() if not l.strip().startswith('--')]
        line = [l for l in code if 'step_count' in l and 'CONSTRAINT' not in l][0]
        assert 'NOT NULL' in line
        assert 'DEFAULT' not in line.upper(), (
            'step_count gained a default — the configurator must require an answer')

    def test_the_schema_matches_the_migration(self):
        """A fresh CI database is built from schema.sql, not the migration."""
        with open('database/schema.sql') as f:
            schema = f.read()
        block = schema[schema.index('CREATE TABLE public.job_levels'):]
        block = block[:block.index(');')]
        line = [l for l in block.splitlines() if 'step_count' in l][0]
        assert 'NOT NULL' in line and 'DEFAULT' not in line.upper()

    def test_the_api_refuses_a_level_with_no_step_count(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True):
            r = _post(hr_client, '/api/job-architecture/levels',
                      {'job_family_id': FAM, 'ordinal': 1, 'title': 'L1'})
        assert r.status_code == 400
        assert 'no default' in r.get_json()['error'].lower()

    def test_the_form_field_ships_empty(self):
        """A pre-filled 5 would record a decision nobody made."""
        with open('templates/admin/job_architecture.html') as f:
            src = f.read()
        field = src[src.index('id="ja-lvl-steps"'):]
        field = field[:field.index('>')]
        assert 'value=' not in field, 'the steps field is pre-filled'

    def test_out_of_range_step_counts_are_refused_with_the_bound(self):
        from app.services import job_architecture_service as svc
        for bad in (0, 13, -1, 'five', None):
            with pytest.raises(svc.LadderError) as exc:
                svc._validate_step_count(bad)
            assert str(exc.value)


class TestOrdinalIsImmutableOnceOccupied:
    """ADR-017b. `2.3` means level 2 step 3 — renumbering rewrites history."""

    def _update(self, occupancy, **kw):
        from app.services import job_architecture_service as svc
        before = {'ordinal': 2, 'title': 'Junior', 'step_count': 5,
                  'job_family_id': FAM}
        with patch.object(svc, 'query', side_effect=[before, {'n': occupancy}]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service'):
            svc.update_level(CO, LVL, actor={'user_id': 'u-hr'}, **kw)
        return exe

    def test_renumbering_an_occupied_level_is_refused(self):
        from app.services import job_architecture_service as svc
        with pytest.raises(svc.LadderError) as exc:
            self._update(4, ordinal=3)
        msg = str(exc.value)
        assert 'renumbered' in msg
        assert '4 assignment' in msg, 'the refusal does not say how many'
        assert '2.2' in msg or 'level.step' in msg, 'it does not explain WHY'

    def test_renumbering_an_empty_level_is_allowed(self):
        exe = self._update(0, ordinal=3)
        assert any('ordinal' in str(c.args[0]) for c in exe.call_args_list)

    def test_renaming_an_occupied_level_is_always_allowed(self):
        """Only the coordinate is frozen. The title is a label."""
        exe = self._update(9, title='Software Engineer II')
        assert any('title' in str(c.args[0]) for c in exe.call_args_list)

    def test_occupancy_counts_historic_assignments_not_just_current(self):
        """A past record still points at the ordinal, so 'nobody is on it now'
        is not the question."""
        import inspect
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc.level_occupancy)
        assert 'is_current' not in src, (
            'occupancy filters to current assignments — a historic record still '
            'points at this ordinal and renumbering would rewrite it')

    def test_reducing_steps_below_an_occupied_step_is_refused(self):
        from app.services import job_architecture_service as svc
        before = {'ordinal': 2, 'title': 'Junior', 'step_count': 5,
                  'job_family_id': FAM}
        with patch.object(svc, 'query', side_effect=[before, {'n': 3}, {'s': 4}]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'audit_service'):
            with pytest.raises(svc.LadderError) as exc:
                svc.update_level(CO, LVL, step_count=2, actor={'user_id': 'u-hr'})
        assert '2.4' in str(exc.value), 'it does not name who is affected'

    def test_the_empty_state_warns_before_the_ladder_is_built(self):
        """The configurator must say so BEFORE, not at the moment it refuses."""
        with open('templates/admin/job_architecture.html') as f:
            src = f.read()
        empty = src[src.index('No ladder yet'):]
        empty = empty[:empty.index('{% endif %}')]
        assert "can't be renumbered" in empty


# ── The two gates ─────────────────────────────────────────────────────────────

class TestTheTwoGatesAreDifferent:
    """CFL-42-35, both halves: a manager must author roadmaps, and a manager must
    NOT be able to edit the company's job architecture."""

    def test_reading_the_ladder_is_gated_on_job_architecture_read(self):
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod)
        assert "@require_feature_access('job_architecture')" in src

    def test_configuring_the_ladder_is_gated_on_org_structure_write(self):
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod)
        assert "@require_feature_access('org_structure', 'w')" in src

    def test_no_ladder_config_route_is_gated_on_job_architecture_write(self):
        """`job_architecture:w` means "author roadmaps and steps FOR YOUR OWN
        REPORTS" (KAN-207 / KAN-191), **not** "edit the company's ladder".

        Stated per endpoint rather than as "the string must not appear", because
        the string legitimately DOES appear on the step-assessment routes — that
        is the grant working as intended. What must never happen is a
        LADDER-CONFIG endpoint accepting it, which would hand every
        SOLID_LINE_MANAGER the company's job architecture. That is the half of
        CFL-42-35 people forget.
        """
        from app import app as flask_app
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod)

        # Every endpoint that changes the SHARED ladder or the company-wide
        # title mapping must be org_structure:w.
        CONFIG = ('api_create_family', 'api_update_family', 'api_create_level',
                  'api_update_level', 'api_save_step', 'admin_job_mapping',
                  'api_title_counts', 'api_save_title_map', 'api_apply_title_map',
                  'api_export_title_map', 'api_import_title_map')
        for name in CONFIG:
            fn_src = src[:src.index(f'def {name}(')]
            decorators = fn_src[fn_src.rindex('@app.route'):]
            assert "require_feature_access('org_structure', 'w')" in decorators, (
                f'{name} configures the shared ladder but is not gated on '
                f'org_structure:w — job_architecture:w is a per-report grant')

        # And the per-report ones are allowed to use it, because that IS the grant.
        for name in ('my_team_steps', 'api_step_reports', 'api_assess_step'):
            fn_src = src[:src.index(f'def {name}(')]
            decorators = fn_src[fn_src.rindex('@app.route'):]
            assert "require_feature_access('job_architecture', 'w')" in decorators

    def test_assessing_somebody_else_s_report_is_refused(self):
        """The feature gate says "may assess"; this says "may assess THIS PERSON".
        Same shape as the org-change initiator rule — the flag is not sufficient."""
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod.api_assess_step)
        assert 'is_own_report' in src
        assert 'only assess your own direct reports' in src

    def test_the_module_has_no_hardcoded_role_list(self):
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod)
        assert '@require_roles(' not in src, 'CLAUDE.md — forbidden on feature routes'
        assert not hasattr(mod, 'require_roles')

    def test_an_employee_may_read_the_ladder(self, employee_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.compensation.svc.ladder', return_value=[]), \
             patch('app.routes.compensation.svc.ladder_completeness', return_value=None):
            r = employee_client.get('/api/job-architecture/ladder')
        assert r.status_code == 200

    def test_the_page_hides_the_editing_affordances_without_org_structure_write(
            self, employee_client):
        """Hiding is never the control — but it must agree with the control."""
        def gate(code, action='r'):
            return not (code == 'org_structure' and action == 'w')
        with patch('app.auth.can_access_feature', side_effect=gate), \
             patch('app.routes.compensation.can_access_feature', side_effect=gate), \
             patch('app.routes.compensation.svc.ladder', return_value=[]), \
             patch('app.routes.compensation.svc.ladder_completeness',
                   return_value={'levels': 0, 'steps_total': 0, 'steps_authored': 0,
                                 'pct': None, 'levels_incomplete': []}):
            r = employee_client.get('/admin/job-architecture')
        html = r.data.decode()
        assert r.status_code == 200
        assert 'Add your first family' not in html
        assert 'const JA_CAN_CONFIGURE = false' in html

    def test_the_feature_description_says_what_write_actually_grants(self):
        """A grant reading "Job Architecture: write" misleads at the moment it is
        made, so the text has to say roadmaps."""
        with open('database/seed_rbac.sql') as f:
            seed = f.read()
        row = seed[seed.index("'job_architecture', 'Job Architecture'"):]
        # The description contains a semicolon ("...expects; write step roadmaps"),
        # so slice to the end of the VALUES row rather than the first ';'.
        row = row[:row.index('11, true)')]
        assert 'roadmap' in row.lower()
        assert 'read the job ladder' in row.lower()

    def test_read_is_seeded_to_every_role(self):
        """An employee must be able to read their own step and the next one —
        the default, not a grant somebody has to remember."""
        with open('database/seed_rbac.sql') as f:
            seed = f.read()
        block = seed[seed.index('KAN-190 — the `job_architecture` feature code'):]
        assert 'CROSS JOIN public.portal_features' in block
        assert 'TRUE, FALSE, FALSE' in block

    def test_write_is_seeded_only_to_the_three_roles_that_author_roadmaps(self):
        with open('database/seed_rbac.sql') as f:
            seed = f.read()
        block = seed[seed.index('KAN-190 — the `job_architecture` feature code'):]
        assert "'SOLID_LINE_MANAGER', 'HR_ADMIN', 'PORTAL_ADMIN'" in block


# ── Company scoping ──────────────────────────────────────────────────────────

class TestCompanyScoping:
    """CLAUDE.md — a company's rows are only ever `company_id = that company`."""

    def test_no_query_uses_or_company_id_is_null(self):
        import inspect, re
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc)
        # Remove the module docstring and comments: both NAME the forbidden
        # pattern in order to forbid it, which is not the same as using it.
        code = re.sub(r'"""(?:.|\n)*?"""', '', src)
        code = '\n'.join(l for l in code.splitlines() if not l.strip().startswith('#'))
        assert 'company_id is null' not in code.lower(), (
            'that pulls in another tenant or a global default')

    def test_a_company_with_no_ladder_gets_an_empty_list(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', return_value=[]):
            assert svc.list_families(CO) == []
            assert svc.list_levels(CO) == []

    def test_every_read_is_parameterised_on_the_company(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', return_value=[]) as q:
            svc.list_families(CO)
        assert q.call_args.args[1] == (CO,)

    def test_cross_tenant_levels_are_refused_by_a_composite_foreign_key(self):
        """In the DATABASE, not in a service somebody can bypass."""
        with open('database/migrations/12_job_architecture.sql') as f:
            sql = f.read()
        assert 'FOREIGN KEY (job_family_id, company_id)' in sql
        assert 'REFERENCES job_families (id, company_id)' in sql
        assert 'UNIQUE (id, company_id)' in sql, 'the composite FK has no target'


# ── The boundary that keeps performance management out ───────────────────────

class TestNoAssessmentColumnsOnTheLadder:
    """§14.5 / R-17, expressed where it is enforceable.

    A PR adding a score to the ladder is the first increment of a
    performance-management module arriving through a reasonable-sounding change.
    Performance management is EP44 and has its own tables.
    """

    FORBIDDEN = ('score', 'rating', 'achieved', 'met_expectations',
                 'performance', 'assessment_result')

    def _ladder_ddl(self, path):
        with open(path) as f:
            src = f.read()
        out = []
        for table in ('job_step_expectations', 'job_levels', 'job_families'):
            for marker in (f'CREATE TABLE IF NOT EXISTS {table}',
                           f'CREATE TABLE public.{table}'):
                if marker in src:
                    block = src[src.index(marker):]
                    out.append(block[:block.index(');')])
        return '\n'.join(out)

    def test_the_migration_defines_no_assessment_column(self):
        ddl = self._ladder_ddl('database/migrations/12_job_architecture.sql')
        # Strip comments — the ban is explained in prose right there.
        code = '\n'.join(l for l in ddl.splitlines() if not l.strip().startswith('--'))
        for word in self.FORBIDDEN:
            assert word not in code.lower(), (
                f'{word!r} appears in the ladder DDL — that is EP44, not EP42')

    def test_the_schema_defines_no_assessment_column(self):
        ddl = self._ladder_ddl('database/schema.sql')
        code = '\n'.join(l for l in ddl.splitlines() if not l.strip().startswith('--'))
        for word in self.FORBIDDEN:
            assert word not in code.lower()

    def test_the_ban_is_written_where_somebody_would_add_one(self):
        with open('database/migrations/12_job_architecture.sql') as f:
            sql = f.read()
        assert 'NO RATINGS' in sql.upper()


# ── Audit ────────────────────────────────────────────────────────────────────

class TestEveryLadderChangeIsAudited:
    """The ladder is what later decides somebody's pay point: a level renamed or
    a step rewritten changes what a person is measured against."""

    def test_the_actions_are_registered(self):
        from app.services import audit_service
        for a in ('JOB_FAMILY_CREATED', 'JOB_FAMILY_UPDATED', 'JOB_LEVEL_CREATED',
                  'JOB_LEVEL_UPDATED', 'JOB_STEP_EXPECTATION_AUTHORED',
                  'JOB_STEP_EXPECTATION_UPDATED'):
            assert a in audit_service.ACTIONS

    def test_creating_a_level_audits_the_step_arithmetic_it_recorded(self):
        """So "5 steps" can never be read back ambiguously."""
        from app.services import job_architecture_service as svc
        txn = FakeTransaction()
        with patch.object(svc, 'query', return_value={'code': 'ENG'}), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'insert_returning', return_value={'id': LVL}), \
             patch.object(svc, 'audit_service') as aud:
            svc.create_level(CO, FAM, 2, 'Junior', 5, actor={'user_id': 'u-hr'})
        aud.record.assert_called_once()
        kwargs = aud.record.call_args.kwargs
        assert '6 steps in total' in kwargs['reason']
        assert '.0 to .5' in kwargs['reason']
        assert kwargs['metadata']['step_count'] == 5

    def test_the_audit_row_joins_the_same_transaction_as_the_write(self):
        """ADR-006 — a ladder change with no record of who made it must not commit."""
        from app.services import job_architecture_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        before = {'ordinal': 2, 'title': 'Junior', 'step_count': 5, 'job_family_id': FAM}
        with patch.object(svc, 'query', side_effect=[before, {'n': 0}]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'audit_service'):
            svc.update_level(CO, LVL, title='Renamed', actor={'user_id': 'u-hr'})
        assert txn.opened == 1 and txn.committed == 1
        assert exe.inside and all(exe.inside)


# ── Completeness reporting ───────────────────────────────────────────────────

class TestCompletenessIsReportedWithItsDenominator:
    """D7 — a named figure, not a bare percentage. R-18: nothing here can test
    whether the CONTENT is any good, which is why it is on the Demo Gate's
    must-be-walked-by-a-human list."""

    def test_it_reports_authored_over_total_and_names_the_gaps(self):
        from app.services import job_architecture_service as svc
        levels = [
            {'id': 'a', 'job_family_id': FAM, 'ordinal': 1, 'title': 'L1',
             'step_count': 2, 'authored_steps': 3, 'headcount': 0,
             'step_total': 3, 'top_step_label': '1.2', 'fully_authored': True},
            {'id': 'b', 'job_family_id': FAM, 'ordinal': 2, 'title': 'L2',
             'step_count': 5, 'authored_steps': 1, 'headcount': 0,
             'step_total': 6, 'top_step_label': '2.5', 'fully_authored': False},
        ]
        with patch.object(svc, 'list_levels', return_value=levels):
            c = svc.ladder_completeness(CO)
        assert c['steps_total'] == 9 and c['steps_authored'] == 4
        assert c['levels_incomplete'] == ['L2']
        assert c['pct'] == 44.4

    def test_an_empty_ladder_reports_no_percentage_rather_than_zero(self):
        """0% of nothing invites "we are 0% done" when there is nothing to do."""
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'list_levels', return_value=[]):
            assert svc.ladder_completeness(CO)['pct'] is None

    def test_the_screen_shows_which_levels_are_incomplete(self):
        with open('templates/admin/job_architecture.html') as f:
            src = f.read()
        assert 'levels_incomplete' in src
        assert 'cannot assess somebody against a step that has not been described' in src


# ── Save is publish ──────────────────────────────────────────────────────────

class TestSaveIsPublish:
    def test_there_is_no_draft_state_in_the_schema(self):
        with open('database/migrations/12_job_architecture.sql') as f:
            sql = f.read().lower()
        block = sql[sql.index('create table if not exists job_step_expectations'):]
        block = block[:block.index(');')]
        for word in ('is_draft', 'published', 'status'):
            assert word not in block, f'{word} suggests a draft cycle; save is publish'

    def test_the_screen_says_so(self):
        with open('templates/admin/job_architecture.html') as f:
            src = f.read()
        assert 'Saving publishes immediately' in src

    def test_the_save_button_says_publish(self):
        with open('templates/admin/job_architecture.html') as f:
            src = f.read()
        assert 'Save &amp; publish' in src


# ── Accessibility: the shell primitives are reused, not reinvented ───────────

class TestUsesTheSharedShellPrimitives:
    """KAN-204 exists so a new screen calls a primitive instead of reinventing it.
    This is the first EP42 screen; if it reinvents them, all ten will."""

    def setup_method(self):
        with open('templates/admin/job_architecture.html') as f:
            self.src = f.read()

    def test_it_declares_no_live_region_of_its_own(self):
        assert 'aria-live' not in self.src, 'use announce() from base.html'

    def test_it_announces_saves_and_errors(self):
        assert 'announce(' in self.src
        assert "'assertive'" in self.src, 'errors must interrupt'

    def test_every_dom_builder_escapes(self):
        """Scoped to the innerHTML builders, on purpose.

        `textContent` and `announce()` do not interpret markup, so a check that
        flagged those too would be a lint people suppress rather than a real
        guard. Only `jaRender` and `jaLevelRow` assign innerHTML.
        """
        import re
        assert 'escH(' in self.src
        builders = ''
        for fn in ('function jaRender()', 'function jaLevelRow(l)'):
            block = self.src[self.src.index(fn):]
            builders += block[:block.index('\n}')]
        # `${expr}` where expr is a bare dotted path — i.e. its value is written
        # straight into the markup. The closing brace is required so a ternary
        # CONDITION (`${l.short_code ? …escH(l.short_code)… : ''}`) is not
        # mistaken for output: the condition is never rendered, the escaped
        # branch is.
        raw = set(re.findall(r'\$\{(?!escH)([a-z]\w*(?:\.\w+)+)\}', builders))
        # Numbers cannot carry markup; every STRING must go through escH.
        numeric = {'l.ordinal', 'l.headcount', 'l.authored_steps', 'l.step_total',
                   'f.levels.length'}
        assert not (raw - numeric), (
            f'unescaped string interpolated into innerHTML: {raw - numeric}')

    def test_the_dialogs_have_dialog_semantics_and_return_focus(self):
        assert self.src.count('role="dialog"') == 3
        assert self.src.count('aria-modal="true"') == 3
        assert 'jaOpener.focus()' in self.src, 'focus is not returned on close'
        assert "e.key !== 'Escape'" in self.src, 'Esc does not close'

    def test_the_required_fields_are_labelled_and_described(self):
        for fid in ('ja-lvl-steps', 'ja-step-summary', 'ja-step-desc', 'ja-fam-code'):
            assert f'for="{fid}"' in self.src, f'{fid} has no label'
        assert 'aria-describedby="ja-lvl-steps-help"' in self.src


# ══════════════════════════════════════════════════════════════════════════════
# KAN-191 — everyone on a level
#
# Two jobs, and the tests keep them apart because the product does:
#   A. the MAPPING project — bulk, HR, title-driven, everyone gets a LEVEL
#   B. STEP ASSESSMENT — a manager's judgement against KAN-190's authored text,
#      which amendment A6 makes the ONLY legitimate way a step is decided.
# ══════════════════════════════════════════════════════════════════════════════

class TestStepNotAssessedIsNotStepZero:
    """A6. "Everyone defaults to .0" was itself a claim that a person is at entry
    level, and D7's empty-state rule applies to steps too."""

    def test_the_column_is_nullable_and_says_why(self):
        with open('database/migrations/12_job_architecture.sql') as f:
            sql = f.read()
        block = sql[sql.index('CREATE TABLE IF NOT EXISTS employee_job_assignments'):]
        block = block[:block.index(');')]
        line = [l for l in block.splitlines()
                if 'step_no' in l and not l.strip().startswith('--')][0]
        assert 'NULL' in line and 'NOT NULL' not in line
        assert 'STEP_NOT_ASSESSED' in block, 'the state is not named in the schema'

    def test_it_renders_as_itself_never_as_a_step(self):
        from app.services import job_architecture_service as svc
        assert svc.step_label(2, None) == svc.STEP_NOT_ASSESSED_LABEL
        assert svc.step_label(2, None) != '2.0'
        assert svc.step_label(2, None) not in ('—', '', None)
        assert 'not yet assessed' in svc.STEP_NOT_ASSESSED_LABEL.lower()

    def test_an_assessed_step_renders_as_the_coordinate(self):
        from app.services import job_architecture_service as svc
        assert svc.step_label(2, 0) == '2.0'
        assert svc.step_label(2, 3) == '2.3'

    def test_step_coverage_is_measured_against_the_PLACED_not_the_total(self):
        """You cannot assess a step for somebody who is not on a level yet, so
        counting them as "unassessed" would blame the wrong gap."""
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query',
                          side_effect=[{'total': 10, 'placed': 6, 'step_assessed': 2}, []]):
            c = svc.coverage(CO)
        assert c['unplaced'] == 4
        assert c['step_not_assessed'] == 4, 'placed(6) - assessed(2)'


class TestCoverageNamesTheRemainder:
    """D7 — a named figure with its denominator, and the remainder LISTED."""

    def _coverage(self, total, placed, assessed, unplaced_rows=()):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', side_effect=[
                {'total': total, 'placed': placed, 'step_assessed': assessed},
                list(unplaced_rows)]):
            return svc.coverage(CO)

    def test_it_reports_placed_over_total(self):
        c = self._coverage(147, 100, 40)
        assert (c['placed'], c['total'], c['unplaced']) == (100, 147, 47)
        assert c['level_pct'] == 68.0

    def test_the_unplaced_are_listed_not_just_counted(self):
        """An unplaced employee is invisible to the equity check, so a coverage
        figure without its remainder hides exactly the population that matters."""
        rows = [{'employee_id': 'e1', 'name': 'Ann Ark', 'job_title': 'Widget Wrangler'}]
        c = self._coverage(2, 1, 0, rows)
        assert c['unplaced_sample'][0]['name'] == 'Ann Ark'
        assert c['unplaced_sample'][0]['job_title'] == 'Widget Wrangler'

    def test_an_empty_company_reports_no_percentage_rather_than_zero(self):
        c = self._coverage(0, 0, 0)
        assert c['level_pct'] is None and c['step_pct'] is None

    def test_the_screen_states_the_consequence_of_being_unplaced(self):
        with open('templates/admin/job_mapping.html') as f:
            src = ' '.join(f.read().split())     # the sentence wraps in the template
        assert 'pay-fairness check' in src and 'cannot see them' in src


class TestTheMappingProjectIsResumableAndReversible:
    """R-2: 41 titles at Acme, 75 at Telia, 146 people. Whether the screen is
    usable decides whether the rollout finishes."""

    def test_saving_the_map_places_nobody(self):
        """Deciding what a title means and changing 146 records are different acts."""
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service'):
            svc.save_title_map(CO, [{'job_title': 'Widget Wrangler',
                                     'job_level_id': LVL}], actor={'user_id': 'u-hr'})
        writes = ' '.join(str(c.args[0]) for c in exe.call_args_list)
        assert 'job_title_level_map' in writes
        assert 'employee_job_assignments' not in writes, 'saving the map placed somebody'

    def test_clearing_a_mapping_deletes_it(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service'):
            svc.save_title_map(CO, [{'job_title': 'Widget Wrangler',
                                     'job_level_id': None}], actor={'user_id': 'u-hr'})
        assert any('DELETE FROM job_title_level_map' in str(c.args[0])
                   for c in exe.call_args_list)

    def test_one_audit_row_for_the_sitting_not_one_per_title(self):
        """ADR-009 §3.5. 75 rows saying "a title was mapped" buries the rows
        somebody actually needs to find."""
        from app.services import job_architecture_service as svc
        maps = [{'job_title': f'T{i}', 'job_level_id': LVL} for i in range(20)]
        with patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'audit_service') as aud:
            svc.save_title_map(CO, maps, actor={'user_id': 'u-hr'})
        aud.record.assert_called_once()
        assert aud.record.call_args.kwargs['metadata']['titles'] == 20

    def test_titles_are_ordered_by_headcount(self):
        """The titles that place the most people must be at the top — that
        ordering is the difference between a screen somebody finishes and one
        they abandon."""
        import inspect
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc.title_counts)
        assert 'ORDER BY 2 DESC' in src

    def test_the_screen_autosaves(self):
        with open('templates/admin/job_mapping.html') as f:
            src = f.read()
        assert 'jmSave()' in src and 'setTimeout' in src, 'no debounced autosave'
        assert 'not one sitting' in src


class TestBulkApplyIsPreviewedAndNeverOverwrites:
    def _apply(self, rows, dry_run=True):
        from app.services import job_architecture_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        with patch.object(svc, 'query', return_value=rows), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'audit_service') as aud:
            out = svc.apply_title_map(CO, actor={'user_id': 'u-hr'}, dry_run=dry_run)
        return out, exe, aud

    ROWS = [
        {'employee_id': 'e1', 'name': 'Ann Ark', 'job_title': 'Dev',
         'job_level_id': LVL, 'ordinal': 2, 'level_title': 'Junior',
         'existing_assignment': None},
        {'employee_id': 'e2', 'name': 'Bo Bell', 'job_title': 'Dev',
         'job_level_id': LVL, 'ordinal': 2, 'level_title': 'Junior',
         'existing_assignment': 'a-existing'},
    ]

    def test_a_dry_run_changes_nothing(self):
        out, exe, aud = self._apply(self.ROWS, dry_run=True)
        assert out['applied'] is False
        assert len(out['create']) == 1 and len(out['skip']) == 1
        exe.assert_not_called()
        aud.record.assert_not_called()

    def test_somebody_already_on_a_level_is_skipped_never_overwritten(self):
        """A re-run must not quietly undo a manager's or HR's correction."""
        out, exe, _ = self._apply(self.ROWS, dry_run=False)
        assert [c['employee_id'] for c in out['create']] == ['e1']
        assert out['skip'][0]['reason'] == 'already on a level'
        inserts = [c for c in exe.call_args_list
                   if 'INSERT INTO employee_job_assignments' in str(c.args[0])]
        assert len(inserts) == 1, 'the already-placed employee was written to'

    def test_the_bulk_apply_leaves_the_step_unassessed(self):
        """This story places people on LEVELS. A step is a manager's judgement and
        must never be a side effect of a bulk apply (A6)."""
        out, exe, _ = self._apply(self.ROWS, dry_run=False)
        ins = [c for c in exe.call_args_list
               if 'INSERT INTO employee_job_assignments' in str(c.args[0])][0]
        assert 'NULL' in ' '.join(str(ins.args[0]).split()), \
            'the bulk apply set a step'

    def test_the_whole_apply_is_one_unit_of_work(self):
        """A failure part-way must leave ZERO assignments and ZERO audit rows —
        a half-placed workforce is worse than an unplaced one, because nobody can
        tell which half is real."""
        out, exe, aud = self._apply(self.ROWS, dry_run=False)
        assert exe.inside and all(exe.inside)
        aud.record.assert_called_once()

    def test_one_audit_row_with_counts_not_one_per_employee(self):
        out, exe, aud = self._apply(self.ROWS, dry_run=False)
        md = aud.record.call_args.kwargs['metadata']
        assert md['placed'] == 1 and md['skipped'] == 1

    def test_the_api_dry_runs_unless_confirm_is_sent(self):
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod.api_apply_title_map)
        assert "dry_run=not bool(d.get('confirm'))" in src

    def test_the_screen_previews_before_applying(self):
        with open('templates/admin/job_mapping.html') as f:
            src = f.read()
        assert 'Preview placement' in src
        assert 'confirm: false' in src and 'DRY RUN' in src
        assert 'Nothing has changed yet' in src


class TestNoAlgorithmicTitleSuggestion:
    """"No algorithmic title→level suggestion in this cycle." A wrong guess
    accepted in bulk is worse than an empty field."""

    def test_not_mapped_yet_is_the_default_option(self):
        with open('templates/admin/job_mapping.html') as f:
            src = f.read()
        block = src[src.index('function jmOptions('):]
        block = block[:block.index('\n}')]
        assert 'Not mapped yet' in block
        assert 'selected' in block.split('Not mapped yet')[0][-80:], \
            'the empty option is not the default'

    def test_the_service_never_guesses(self):
        import inspect
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc.title_counts).lower()
        for word in ('similar', 'fuzzy', 'suggest', 'levenshtein', 'ilike'):
            assert word not in src, f'{word} — no algorithmic suggestion this cycle'


class TestStepAssessmentIsAManagersJudgement:
    """A6's core rule: nothing pre-selected, nothing suggested, nothing derived
    from pay."""

    def _assess(self, step_no, described=True, current_step=None, **kw):
        from app.services import job_architecture_service as svc
        row = {'id': 'a-1', 'step_no': current_step, 'job_level_id': LVL,
               'ordinal': 2, 'title': 'Junior', 'step_count': 5}
        qs = [row, ({'x': 1} if described else None)]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service') as aud:
            out = svc.assess_step(CO, 'e1', step_no, actor={'user_id': 'u-mgr'}, **kw)
        return out, exe, aud

    def test_an_absent_step_is_refused_with_the_reason(self):
        from app.services import job_architecture_service as svc
        for empty in (None, ''):
            with pytest.raises(svc.LadderError) as exc:
                self._assess(empty)
            assert 'pre-selected' in str(exc.value), (
                'the refusal does not explain that nothing is pre-selected')

    def test_a_step_beyond_the_level_is_refused(self):
        from app.services import job_architecture_service as svc
        with pytest.raises(svc.LadderError) as exc:
            self._assess(6)
        assert '2.0 to 2.5' in str(exc.value)

    def test_an_undescribed_step_cannot_be_assessed_against(self):
        """A6 makes the authored expectations the ONLY legitimate input, so
        assessing against an undescribed step is assessing against nothing.
        That is why ladder completeness is a hard dependency, not a nicety."""
        from app.services import job_architecture_service as svc
        with pytest.raises(svc.LadderError) as exc:
            self._assess(3, described=False)
        assert 'no description yet' in str(exc.value)
        assert 'nothing to assess against' in str(exc.value)

    def test_a_valid_assessment_is_recorded_and_audited(self):
        out, exe, aud = self._assess(3)
        assert out == {'step_no': 3, 'label': '2.3', 'was_first_assessment': True}
        aud.record.assert_called_once()
        assert aud.record.call_args.args[0] == 'EMPLOYEE_STEP_ASSESSED'

    def test_the_audit_row_carries_no_pay_figure(self):
        """Amounts stay out of the trail entirely (ADR-009); the pay consequence
        is derived on read by a compensation:r holder."""
        _out, _exe, aud = self._assess(3)
        md = aud.record.call_args.kwargs['metadata']
        for k in md:
            assert 'pay' not in k and 'salary' not in k and 'amount' not in k
        assert md['step_before'] is None and md['step_after'] == 3

    def test_it_is_retained_as_employment_data(self):
        _out, _exe, aud = self._assess(3)
        assert aud.record.call_args.kwargs['retention_class'] == 'EMPLOYMENT'

    def test_an_hr_override_needs_a_reason(self):
        """HR is not the person who can judge the work, so an override has to say
        why it was made anyway."""
        from app.services import job_architecture_service as svc
        with pytest.raises(svc.LadderError) as exc:
            self._assess(3, is_hr_override=True, reason='   ')
        assert 'needs a reason' in str(exc.value)

    def test_an_hr_override_with_a_reason_is_recorded_as_an_override(self):
        _out, _exe, aud = self._assess(3, is_hr_override=True,
                                       reason='Manager on long-term leave.')
        assert aud.record.call_args.kwargs['metadata']['hr_override'] is True

    def test_somebody_not_on_a_level_cannot_be_assessed(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', side_effect=[None]):
            with pytest.raises(svc.LadderError) as exc:
                svc.assess_step(CO, 'e1', 2, actor={'user_id': 'u-mgr'})
        assert 'not on a level yet' in str(exc.value)

    def test_nothing_is_derived_from_pay_anywhere_in_the_service(self):
        """A6 forbids it, and this is the module where somebody would try."""
        import ast
        import inspect
        from app.services import job_architecture_service as svc
        # Parse rather than grep: the module NAMES the ban in its docstrings in
        # order to state it, and a grep cannot tell prose from a column read.
        # This walks the actual SQL strings and identifiers instead.
        tree = ast.parse(inspect.getsource(svc))
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue                          # a bare docstring
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                if 'select' in low or 'insert' in low or 'update' in low:
                    for word in ('salary', 'base_pay', 'pay_amount', 'currency'):
                        assert word not in low, (
                            f'{word!r} is read in SQL by the ladder service — a '
                            f'step may never be derived from pay (A6)')


class TestTheAssessmentScreenShowsTheExpectations:
    """R-20: no criterion can test whether an assessment was done thoughtfully.
    What holds it is the expectations being visible at the point of choice,
    nothing pre-selected, and HR's override."""

    def setup_method(self):
        with open('templates/employees/step_assessment.html') as f:
            self.src = f.read()

    def test_nothing_is_pre_selected_not_even_the_current_step(self):
        assert "'<option value=\"\">Choose…</option>'" in self.src
        assert 'pre-filling the current value invites confirming it unread' in self.src

    def test_the_expectations_appear_when_a_step_is_chosen(self):
        assert 'function saShowStep()' in self.src
        assert 'step.description' in self.src

    def test_the_step_below_is_shown_for_comparison(self):
        """"Have they reached this?" is a comparison, not an abstract judgement."""
        assert 'The step below' in self.src

    def test_an_undescribed_step_cannot_be_picked(self):
        assert 'disabled' in self.src
        assert 'not described yet' in self.src

    def test_it_never_shows_pay(self):
        """Nothing pay-shaped may be RENDERED. The comment block explains the ban,
        so this checks the markup and script, not the prose."""
        import re
        body = re.sub(r'\{#(?:.|\n)*?#\}', '', self.src)     # strip Jinja comments
        body = re.sub(r'//[^\n]*', '', body)                  # strip JS line comments
        for word in ('salary', 'pay_point', 'compensation', '€', '£'):
            assert word not in body.lower(), f'{word} is rendered on the assessment screen'
        # A bare `$` is JavaScript template-literal syntax, so look for a currency
        # amount specifically: a dollar sign immediately followed by a digit.
        import re as _re
        assert not _re.search(r'\$\s?\d', body), 'a currency amount is rendered'

    def test_it_uses_the_shared_shell_primitives(self):
        assert 'aria-live' not in self.src, 'use announce() from base.html'
        assert 'announce(' in self.src and 'escH(' in self.src
        assert 'role="dialog"' in self.src and 'saOpener.focus()' in self.src

    def test_the_unassessed_state_is_visible_as_itself(self):
        """The screen renders `step_display` from the service, which returns
        "Step not yet assessed" for an unassessed step rather than `2.0`."""
        import re
        assert 'step_display' in self.src
        # Any `.0` on the page must be built from the level's own ordinal, never
        # written as a literal — a literal would show a step nobody assessed.
        # The Jinja comment block quotes "never 2.0" while stating the rule, so
        # strip comments before looking for one.
        body = re.sub(r'\{#(?:.|\n)*?#\}', '', self.src)
        literals = re.findall(r'(?<![\w.${}])\d+\.0(?![\w])', body)
        assert not literals, f'hardcoded step label(s): {literals}'


class TestAssignKeepsHistoryTrustworthy:
    """ADR-020 half-open, plus the two database constraints behind it."""

    def _assign(self, current=None, **kw):
        """`assign` uses `insert_returning` for the new row — it needs the id to
        audit against, so a single placement points at its own record rather
        than at something coarser. Both writes are captured."""
        from app.services import job_architecture_service as svc
        lvl = {'ordinal': 2, 'title': 'Junior', 'step_count': 5}
        txn = FakeTransaction()
        exe = recording_execute(txn)
        ins = MagicMock(return_value={'id': 'a-new'})
        with patch.object(svc, 'query', side_effect=[lvl, current]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'insert_returning', ins), \
             patch.object(svc, 'audit_service') as aud:
            svc.assign(CO, 'e1', LVL, actor={'user_id': 'u-hr'}, **kw)
        return exe, ins, aud

    def test_the_same_date_closes_the_old_row_and_opens_the_new_one(self):
        import datetime as _d
        eff = _d.date(2026, 6, 1)
        current = {'id': 'a-old', 'job_level_id': 'lvl-1', 'step_no': 2,
                   'effective_from': '2026-01-01'}
        exe, ins, _ = self._assign(current=current, effective_date=eff)
        close = [c for c in exe.call_args_list
                 if 'UPDATE employee_job_assignments' in str(c.args[0])][0]
        # The SAME date closes the outgoing row and opens the incoming one, so
        # under half-open `[from, to)` they abut with no overlap and no gap.
        assert eff in close.args[1], 'the outgoing period was not closed on the date'
        assert eff in ins.call_args.args[1], 'the incoming period did not start on it'

    def test_a_first_placement_audits_as_assigned_not_changed(self):
        _exe, _ins, aud = self._assign(current=None)
        assert aud.record.call_args.args[0] == 'JOB_LEVEL_ASSIGNED'

    def test_a_move_audits_as_changed_and_records_the_previous_step(self):
        current = {'id': 'a-old', 'job_level_id': 'lvl-1', 'step_no': 4,
                   'effective_from': '2026-01-01'}
        _exe, _ins, aud = self._assign(current=current)
        assert aud.record.call_args.args[0] == 'JOB_LEVEL_CHANGED'
        assert aud.record.call_args.kwargs['metadata']['previous_step_no'] == 4

    def test_backdating_behind_the_current_period_is_refused(self):
        """It would create an overlap the database would reject anyway — refused
        here so the user gets a sentence rather than a constraint violation."""
        import datetime as _d
        from app.services import job_architecture_service as svc
        current = {'id': 'a-old', 'job_level_id': 'lvl-1', 'step_no': 1,
                   'effective_from': '2026-06-01'}
        with pytest.raises(svc.LadderError) as exc:
            self._assign(current=current, effective_date=_d.date(2026, 1, 1))
        assert 'before this employee' in str(exc.value)

    def test_the_database_forbids_overlaps_and_two_current_rows(self):
        with open('database/migrations/13_employee_level_mapping.sql') as f:
            sql = f.read()
        assert 'EXCLUDE USING gist' in sql
        assert "daterange(effective_from, effective_to, '[)')" in sql, \
            'the exclusion is not on the half-open convention'
        assert 'uq_eja_one_current' in sql and 'WHERE is_current' in sql


class TestWorkingTitleIsUntouched:
    """ADR-017d / CFL-42-4 — `employees.job_title` is KEPT, relabelled, and never
    a grouping key. Its index and the search trigger stay exactly as they are."""

    def test_no_migration_alters_the_column_or_the_search_trigger(self):
        import glob
        for path in glob.glob('database/migrations/1[23]_*.sql'):
            with open(path) as f:
                sql = f.read().lower()
            assert 'alter table employees' not in sql, f'{path} alters employees'
            assert 'trg_employee_search' not in sql, f'{path} touches the search trigger'

    def test_the_mapping_reads_the_title_and_never_writes_it(self):
        import inspect
        from app.services import job_architecture_service as svc
        for fn in (svc.title_counts, svc.apply_title_map):
            src = inspect.getsource(fn).lower()
            assert 'update employees' not in src
            assert 'set job_title' not in src

    def test_the_screen_calls_it_the_working_title(self):
        with open('templates/admin/job_mapping.html') as f:
            src = f.read()
        assert 'Working title' in src


class TestTheAuditRowsAreActuallyWritable:
    """The gap the mocked tests could not see.

    Every other test here patches `audit_service` wholesale, so the row it would
    have written is never validated — and `record()` is strict: it refuses a
    non-UUID `entity_id` rather than writing a row that points at nothing. Three
    calls passed `None` and 500'd the first time a real request reached them.
    Found by driving the screens in a browser, not by reasoning about it.

    These build the row through the REAL validator with the audit WRITE mocked,
    so the shape is checked without needing a database.
    """

    def _record_calls(self, fn, *args, **kw):
        """Run `fn`, capturing what it asks audit_service to write."""
        from app.services import job_architecture_service as svc
        captured = []

        def fake_record(action, entity_type, entity_id, **kwargs):
            captured.append((action, entity_type, entity_id, kwargs))

        with patch.object(svc.audit_service, 'record', side_effect=fake_record):
            fn(*args, **kw)
        return captured

    def test_every_ladder_audit_row_would_pass_the_real_validator(self):
        """Builds each row with `_build_row`, which is what `record()` calls."""
        from app.services import audit_service
        CO_UUID = '00000000-0000-0000-0000-0000000000c1'
        ENT_UUID = '00000000-0000-0000-0000-0000000000e1'
        actor = {'user_id': '00000000-0000-0000-0000-000000000001',
                 'employee_id': None, 'roles': ['HR_ADMIN']}
        for action, entity_type in (
                ('JOB_TITLE_MAP_SAVED', 'company_job_title_map'),
                ('JOB_LEVEL_BULK_ASSIGNED', 'company_job_level_assignments'),
                ('JOB_LEVEL_ASSIGNED', 'employee_job_assignment'),
                ('JOB_LEVEL_CHANGED', 'employee_job_assignment'),
                ('EMPLOYEE_STEP_ASSESSED', 'employee_job_assignment'),
                ('JOB_FAMILY_CREATED', 'job_family'),
                ('JOB_LEVEL_CREATED', 'job_level'),
                ('JOB_STEP_EXPECTATION_AUTHORED', 'job_step_expectation')):
            # Must not raise. A non-UUID entity_id, an unregistered action or a
            # secret-ish metadata key all raise here rather than at runtime.
            audit_service._build_row(
                action, entity_type, ENT_UUID,
                company_id=CO_UUID, actor=actor, reason='Probe.',
                metadata={'probe': True})

    def test_no_ladder_audit_call_passes_a_none_entity_id(self):
        """The specific defect: `record(..., None)` is refused by the validator,
        so a bulk operation has to name the COMPANY as its entity."""
        import inspect
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc)
        for i, line in enumerate(src.splitlines()):
            if 'audit_service.record(' in line:
                # The entity_id is the third positional argument, on this line or
                # the next.
                window = ' '.join(src.splitlines()[i:i + 3])
                assert ', None,' not in window, (
                    f'audit_service.record called with a None entity_id near: '
                    f'{line.strip()}')

    def test_a_single_assignment_audits_against_its_own_row(self):
        """Not the company — a single placement genuinely has an entity, so it
        must point at it rather than at something coarser."""
        from app.services import job_architecture_service as svc
        lvl = {'ordinal': 2, 'title': 'Junior', 'step_count': 5}
        with patch.object(svc, 'query', side_effect=[lvl, None]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'insert_returning', return_value={'id': 'a-new'}), \
             patch.object(svc, 'audit_service') as aud:
            svc.assign(CO, 'e1', LVL, actor={'user_id': 'u-hr'})
        assert aud.record.call_args.args[2] == 'a-new'


# ══════════════════════════════════════════════════════════════════════════════
# KAN-207 — step roadmaps
#
# **The object the owner actually asked for**, and it is NOT KAN-190's step
# expectation:
#   EXPECTATION  what step 1.2 means *here*, for anybody
#   ROADMAP      what *you specifically* need to do to get there
#
# The tests that matter are the ones about what it must NEVER become: a rating, a
# score, or a record that somebody "agreed".
# ══════════════════════════════════════════════════════════════════════════════

ROADMAP_ROW = {
    'id': 'rm-1', 'version': 2, 'content': 'Own the payments area end to end.',
    'review_context': 'PERFORMANCE_REVIEW', 'review_date': '2026-03-14',
    'authored_by_label': 'Ana Costa', 'authored_at': '2026-03-14T10:00:00+00:00',
    'acknowledged_at': None, 'superseded_at': None,
    'from_step_no': 2, 'target_step_no': 3,
    'from_ordinal': 1, 'from_title': 'Trainee', 'target_ordinal': 1,
    'target_title': 'Trainee Software Engineer', 'family_name': 'Engineering',
}


class TestARoadmapIsNotAnAssessment:
    """The boundary that keeps this out of GDPR Art. 22 / EU AI Act territory.

    A roadmap is a statement of **expectations**. A scored or automated judgement
    about a person is a different legal object with different obligations, so the
    absence of any score is a compliance property, not a style choice.
    """

    FORBIDDEN = ('score', 'rating', 'readiness', 'likelihood', 'percent',
                 'achieved', 'met_expectations', 'potential', 'ranking')

    def _ddl(self, path):
        with open(path) as f:
            src = f.read()
        for marker in ('CREATE TABLE IF NOT EXISTS employee_step_roadmaps',
                       'CREATE TABLE public.employee_step_roadmaps'):
            if marker in src:
                block = src[src.index(marker):]
                return block[:block.index(');')]
        raise AssertionError(f'{path}: roadmap table not found')

    def test_the_migration_has_no_assessment_column(self):
        ddl = self._ddl('database/migrations/14_step_roadmaps.sql')
        code = '\n'.join(l for l in ddl.splitlines() if not l.strip().startswith('--'))
        for w in self.FORBIDDEN:
            assert w not in code.lower(), f'{w!r} on the roadmap table — that is an assessment'

    def test_the_schema_has_no_assessment_column(self):
        ddl = self._ddl('database/schema.sql')
        code = '\n'.join(l for l in ddl.splitlines() if not l.strip().startswith('--'))
        for w in self.FORBIDDEN:
            assert w not in code.lower(), f'{w!r} in schema.sql'

    def test_the_reason_is_written_where_somebody_would_add_one(self):
        with open('database/migrations/14_step_roadmaps.sql') as f:
            sql = f.read()
        assert 'Art. 22' in sql, 'the legal reason for the ban is not recorded'

    def test_nothing_computes_a_readiness_judgement(self):
        """`next_step_target` returns WHERE the next rung is. It must not decide
        whether somebody is ready for it — that would be the assessment."""
        import ast
        import inspect
        import textwrap
        from app.services import job_architecture_service as svc
        # Parse rather than grep: the docstring NAMES the ban in order to state
        # it ("nothing here decides whether they are *ready*"), and a grep cannot
        # tell that from a column read.
        tree = ast.parse(textwrap.dedent(inspect.getsource(svc.next_step_target)))
        fn = tree.body[0]
        body = fn.body[1:] if (isinstance(fn.body[0], ast.Expr)
                               and isinstance(fn.body[0].value, ast.Constant)) else fn.body
        code = '\n'.join(ast.unparse(n) for n in body).lower()
        for w in ('ready', 'eligible', 'qualif', 'score'):
            assert w not in code, f'{w!r} in the body of next_step_target — a judgement'


class TestAcknowledgementRecordsADiscussionNotAgreement:
    """CFL-42-50. Recording "agreed" when somebody merely read it is a false
    record about a person, and the label is a claim (standing rule 6)."""

    def test_the_audit_action_says_discussion_not_accepted(self):
        from app.services import audit_service
        assert 'STEP_ROADMAP_DISCUSSION_CONFIRMED' in audit_service.ACTIONS
        for a in audit_service.ACTIONS:
            assert 'ROADMAP_ACCEPTED' not in a and 'ROADMAP_AGREED' not in a

    def test_the_audit_reason_says_so_explicitly(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', side_effect=[
                {'id': 'rm-1', 'version': 2, 'acknowledged_at': None}]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'audit_service') as aud:
            svc.acknowledge_roadmap(CO, 'e1', actor={'user_id': 'u-e'})
        reason = aud.record.call_args.kwargs['reason']
        assert 'not' in reason.lower() and 'agreement' in reason.lower(), (
            'the trail could be read as the employee agreeing with the content')

    def test_the_button_says_confirm_we_discussed_this(self):
        """The ban is on the BUTTON and the STATUS LABEL, not on prose.

        The screen legitimately says "not that you agreed with it" — explaining
        what confirming does NOT mean is the opposite of claiming agreement, and
        a cruder check would have forced that sentence out.
        """
        with open('templates/employees/my_ladder.html') as f:
            src = f.read()
        assert 'Confirm we discussed this' in src
        body = re.sub(r'\{#(?:.|\n)*?#\}', '', src)          # strip Jinja comments
        # Every button's visible text, and the acknowledged status line.
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', body, re.S)
        for label in buttons:
            low = re.sub(r'<[^>]*>', '', label).strip().lower()
            assert 'accept' not in low and 'agree' not in low, (
                f'a button claims agreement: {low!r}')
        status = re.findall(r'✓[^<]*', body)
        for st in status:
            assert 'agree' not in st.lower(), f'the status claims agreement: {st!r}'

    def test_the_state_reads_discussed_on_a_date(self):
        with open('templates/employees/my_ladder.html') as f:
            src = f.read()
        assert 'Discussed on' in src
        assert 'not that you agreed with it' in src, (
            'it does not tell the employee what confirming actually means')

    def test_confirming_twice_is_not_an_error_and_does_not_move_the_date(self):
        """The first confirmation is when the conversation happened."""
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', side_effect=[
                {'id': 'rm-1', 'version': 2, 'acknowledged_at': '2026-03-14T10:00:00+00:00'}]), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service') as aud:
            out = svc.acknowledge_roadmap(CO, 'e1', actor={'user_id': 'u-e'})
        assert out['already'] is True
        exe.assert_not_called()
        aud.record.assert_not_called()

    def test_only_the_subject_can_confirm(self):
        """A manager confirming on their report's behalf would be exactly the
        false record the wording avoids."""
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod.api_confirm_roadmap_discussed)
        assert "session.get('employee_id')" in src
        assert 'Only the person a roadmap is about' in src

    def test_an_unconfirmed_roadmap_blocks_nothing(self):
        """A non-responsive employee must not be able to freeze their own
        development plan — so the follow-up goes to the manager instead."""
        import inspect
        from app.services import job_architecture_service as svc
        assert hasattr(svc, 'unacknowledged_roadmaps')
        doc = inspect.getdoc(svc.unacknowledged_roadmaps)
        assert 'blocking workflow' in doc
        with open('templates/employees/my_ladder.html') as f:
            assert 'nothing is waiting on you' in f.read()


class TestRoadmapsAreVersionedNotOverwritten:
    """"What did we agree in March" is the question this object exists to answer."""

    def _author(self, prev=None):
        from app.services import job_architecture_service as svc
        where = {'current': {'job_level_id': LVL, 'step_no': 2, 'ordinal': 1,
                             'title': 'Trainee', 'step_count': 3,
                             'job_family_id': FAM, 'family_name': 'Eng'},
                 'target': {'job_level_id': LVL, 'step_no': 3, 'ordinal': 1,
                            'level_title': 'Trainee', 'same_level': True},
                 'reason': None}
        txn = FakeTransaction()
        exe = recording_execute(txn)
        with patch.object(svc, 'next_step_target', return_value=where), \
             patch.object(svc, 'query', side_effect=[prev, []]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'insert_returning', return_value={'id': 'rm-new'}) as ins, \
             patch.object(svc, 'audit_service') as aud, \
             patch.object(svc, 'notif'):
            out = svc.author_roadmap(CO, 'e1', 'Own payments.', 'PERFORMANCE_REVIEW',
                                     actor={'user_id': 'u-mgr'}, author_label='Ana')
        return out, exe, ins, aud

    def test_the_first_roadmap_is_version_1(self):
        out, exe, _ins, _aud = self._author(prev=None)
        assert out['version'] == 1
        assert not [c for c in exe.call_args_list if 'superseded_at' in str(c.args[0])]

    def test_a_second_roadmap_supersedes_the_first_in_the_same_transaction(self):
        """`uq_esr_one_live` must never see two live rows."""
        out, exe, _ins, _aud = self._author(prev={'id': 'rm-old', 'version': 1})
        assert out['version'] == 2
        sup = [c for c in exe.call_args_list if 'superseded_at=NOW()' in ' '.join(str(c.args[0]).split())]
        assert len(sup) == 1
        assert exe.inside and all(exe.inside), 'the supersede escaped the transaction'

    def test_the_old_version_is_superseded_not_deleted(self):
        _out, exe, _ins, _aud = self._author(prev={'id': 'rm-old', 'version': 1})
        writes = ' '.join(str(c.args[0]) for c in exe.call_args_list)
        assert 'DELETE' not in writes.upper()

    def test_the_target_is_denormalised_so_history_survives_a_move(self):
        """Resolving the target through the live assignment would silently
        re-target every historical roadmap the moment somebody is promoted."""
        _out, _exe, ins, _aud = self._author()
        sql = ' '.join(str(ins.call_args.args[0]).split())
        assert 'from_job_level_id' in sql and 'target_job_level_id' in sql
        assert 'from_step_no' in sql and 'target_step_no' in sql

    def test_the_database_permits_only_one_live_roadmap(self):
        with open('database/migrations/14_step_roadmaps.sql') as f:
            sql = f.read()
        assert 'uq_esr_one_live' in sql and 'WHERE superseded_at IS NULL' in sql

    def test_the_audit_row_records_the_version_and_no_content(self):
        """The content is free text about a named person; it stays out of the
        trail, along with anything pay-shaped (ADR-009)."""
        _out, _exe, _ins, aud = self._author(prev={'id': 'rm-old', 'version': 1})
        md = aud.record.call_args.kwargs['metadata']
        assert md['version'] == 2 and md['superseded_version'] == 1
        assert not any('content' in k or 'pay' in k for k in md)
        assert 'Own payments' not in str(md), 'the roadmap text leaked into the trail'

    def test_the_screen_says_the_old_one_is_kept(self):
        with open('templates/employees/step_assessment.html') as f:
            src = f.read()
        assert 'kept, not overwritten' in src


class TestTheEmployeeIsToldAndCanSeeIt:
    """"Visible to the employee — not optional." If they cannot see it, we have
    not built it. And the owner overruled the BA's and UX's "no" on notifying:
    a roadmap the employee does not know about delivers zero transparency."""

    def test_the_employee_is_notified_once_in_app(self):
        from app.services import job_architecture_service as svc
        where = {'current': {'job_level_id': LVL, 'step_no': 2, 'ordinal': 1,
                             'title': 'T', 'step_count': 3, 'job_family_id': FAM,
                             'family_name': 'Eng'},
                 'target': {'job_level_id': LVL, 'step_no': 3, 'ordinal': 1,
                            'level_title': 'T', 'same_level': True}, 'reason': None}
        with patch.object(svc, 'next_step_target', return_value=where), \
             patch.object(svc, 'query', side_effect=[None, [{'id': 'u-emp'}]]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'insert_returning', return_value={'id': 'rm-1'}), \
             patch.object(svc, 'audit_service'), \
             patch.object(svc, 'notif') as n:
            svc.author_roadmap(CO, 'e1', 'Do X.', 'OFF_CYCLE', actor={'user_id': 'u-mgr'})
        n.create_user_notification.assert_called_once()
        args, kwargs = n.create_user_notification.call_args
        assert args[0] == 'u-emp'
        assert kwargs['link'] == '/my-ladder'
        # No step number in the message — it must read the same whether or not the
        # company displays steps.
        assert not re.search(r'\d\.\d', args[2]), f'the message leaks a step: {args[2]!r}'

    def test_the_notification_is_sent_after_the_commit(self):
        """A notification cannot be rolled back, so announcing before the commit
        risks telling somebody about a roadmap that does not exist."""
        import inspect
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc.author_roadmap)
        commit_end = src.index("retention_class='EMPLOYMENT')")
        assert src.index('create_user_notification') > commit_end

    def test_a_failed_notification_does_not_undo_the_roadmap(self):
        import inspect
        from app.services import job_architecture_service as svc
        src = inspect.getsource(svc.author_roadmap)
        assert 'except Exception' in src
        assert 'must not undo a written roadmap' in src

    def test_it_retires_on_view_because_it_is_an_fyi(self):
        """An FYI must not sit in the bell like an approval waiting to be decided."""
        import inspect
        from app.services import job_architecture_service as svc
        assert 'resolve_related' in inspect.getsource(svc.mark_roadmap_seen)
        from app.routes import compensation as mod
        assert 'mark_roadmap_seen' in inspect.getsource(mod.my_ladder)

    def test_the_employees_own_view_is_gated_on_READ_not_write(self):
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod)
        head = src[:src.index('def my_ladder(')]
        assert "@require_feature_access('job_architecture')" in head[head.rindex('@app.route'):]

    def test_a_roadmap_is_not_readable_by_a_colleague(self):
        """Asserted at the PAYLOAD — a URL is a guess anybody can make."""
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod.api_roadmap)
        assert 'is_own' in src and 'manages' in src and 'is_admin' in src
        assert '403' in src


class TestTheDisclosureOffRendering:
    """A2 option (b). With the switch off the employee STILL sees their role,
    their family and every level's expectations — the roadmap just carries no
    step number and no "you are here". Hiding the roadmap too would discard the
    transparency the owner asked for twice in order to hide a label."""

    def test_the_switch_defaults_to_showing_the_step(self):
        with open('database/migrations/14_step_roadmaps.sql') as f:
            sql = f.read()
        assert 'display_step_to_employee BOOLEAN NOT NULL DEFAULT TRUE' in sql

    def test_it_is_in_the_schema_too_so_a_fresh_ci_database_agrees(self):
        with open('database/schema.sql') as f:
            assert 'display_step_to_employee boolean DEFAULT true NOT NULL' in f.read()

    def test_an_absent_company_assumes_the_transparent_default(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'query', return_value=None):
            assert svc.displays_step(CO) is True

    def test_with_the_switch_on_the_target_carries_its_step_number(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'displays_step', return_value=True):
            d = svc._decorate_roadmap(dict(ROADMAP_ROW), CO)
        assert d['target_label'] == '1.3'
        assert '1.3' in d['target_heading']

    def test_with_the_switch_off_there_is_no_step_number_anywhere(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'displays_step', return_value=False):
            d = svc._decorate_roadmap(dict(ROADMAP_ROW), CO)
        assert d['target_label'] is None and d['from_label'] is None
        assert not re.search(r'\d\.\d', d['target_heading']), d['target_heading']
        assert d['target_heading'] == 'What the next set of expectations looks like'

    def test_the_roadmap_content_itself_is_never_hidden(self):
        """Hiding it would discard the transparency in order to hide a label."""
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'displays_step', return_value=False):
            d = svc._decorate_roadmap(dict(ROADMAP_ROW), CO)
        assert d['content'] == ROADMAP_ROW['content']

    def test_the_switch_governs_the_step_not_the_level(self):
        """In the owner's own example the TITLE is the level, and the title is
        always visible — so a switch claiming to hide the level would hide
        nothing while claiming to."""
        import inspect
        from app.services import job_architecture_service as svc
        doc = inspect.getdoc(svc.displays_step)
        assert 'STEP, not the level' in doc
        with open('templates/employees/my_ladder.html') as f:
            src = f.read()
        # The role title renders unconditionally; only the step is behind the flag.
        block = src[src.index('My role'):src.index('My roadmap')]
        assert '{{ where.current.title }}' in block
        assert 'shows_step' in block, 'the step is not behind the switch'


class TestARoadmapNeedsSomewhereToPoint:
    def test_an_unassessed_step_has_no_next_step(self):
        """Proposing one would assert where they are, which is exactly the claim
        STEP_NOT_ASSESSED refuses to make (A6)."""
        from app.services import job_architecture_service as svc
        cur = {'job_level_id': LVL, 'step_no': None, 'ordinal': 1, 'title': 'T',
               'step_count': 3, 'job_family_id': FAM, 'family_name': 'Eng'}
        with patch.object(svc, 'query', side_effect=[cur]):
            out = svc.next_step_target(CO, 'e1')
        assert out['target'] is None
        assert 'not been assessed' in out['reason']

    def test_the_next_step_within_a_level_is_the_next_increment(self):
        from app.services import job_architecture_service as svc
        cur = {'job_level_id': LVL, 'step_no': 2, 'ordinal': 1, 'title': 'T',
               'step_count': 3, 'job_family_id': FAM, 'family_name': 'Eng'}
        with patch.object(svc, 'query', side_effect=[cur]):
            out = svc.next_step_target(CO, 'e1')
        assert out['target']['step_no'] == 3 and out['target']['same_level'] is True

    def test_the_top_step_points_at_the_entry_step_of_the_next_level(self):
        from app.services import job_architecture_service as svc
        cur = {'job_level_id': LVL, 'step_no': 3, 'ordinal': 1, 'title': 'T',
               'step_count': 3, 'job_family_id': FAM, 'family_name': 'Eng'}
        nxt = {'id': 'lvl-2', 'ordinal': 2, 'title': 'Junior', 'step_count': 5}
        with patch.object(svc, 'query', side_effect=[cur, nxt]):
            out = svc.next_step_target(CO, 'e1')
        assert out['target']['step_no'] == 0 and out['target']['ordinal'] == 2
        assert out['target']['same_level'] is False

    def test_the_top_of_the_highest_level_says_so_rather_than_inventing_one(self):
        from app.services import job_architecture_service as svc
        cur = {'job_level_id': LVL, 'step_no': 3, 'ordinal': 9, 'title': 'T',
               'step_count': 3, 'job_family_id': FAM, 'family_name': 'Eng'}
        with patch.object(svc, 'query', side_effect=[cur, None]):
            out = svc.next_step_target(CO, 'e1')
        assert out['target'] is None and 'top step' in out['reason']

    def test_authoring_is_refused_when_there_is_nowhere_to_point(self):
        from app.services import job_architecture_service as svc
        with patch.object(svc, 'next_step_target',
                          return_value={'current': {}, 'target': None,
                                        'reason': 'Their step has not been assessed yet.'}):
            with pytest.raises(svc.LadderError) as exc:
                svc.author_roadmap(CO, 'e1', 'Do X.', 'OFF_CYCLE', actor={'user_id': 'u'})
        assert 'not been assessed' in str(exc.value)

    def test_empty_content_is_refused(self):
        from app.services import job_architecture_service as svc
        for empty in ('', '   ', None):
            with pytest.raises(svc.LadderError) as exc:
                svc.author_roadmap(CO, 'e1', empty, 'OFF_CYCLE', actor={'user_id': 'u'})
            assert 'whole object' in str(exc.value)

    def test_an_unknown_review_context_is_refused(self):
        from app.services import job_architecture_service as svc
        with pytest.raises(svc.LadderError):
            svc.author_roadmap(CO, 'e1', 'Do X.', 'MADE_UP', actor={'user_id': 'u'})

    def test_the_contexts_match_the_org_change_vocabulary(self):
        """§14.5 — EP42 RECORDS that a step change happened at a review; it does
        not build the review. The same four contexts, so the vocabulary is one."""
        from app.services import job_architecture_service as svc
        assert set(svc.REVIEW_CONTEXTS) == {
            'PROBATION_REVIEW', 'MID_TERM_GOAL_REVIEW', 'PERFORMANCE_REVIEW', 'OFF_CYCLE'}


class TestTheAuthoringSurfaceShowsWhatTheStepExpects:
    """A roadmap that contradicts the step it points at is worse than none."""

    def setup_method(self):
        with open('templates/employees/step_assessment.html') as f:
            self.src = f.read()

    def test_the_target_steps_expectations_are_shown_while_writing(self):
        assert 'rwShowTargetExpectations' in self.src
        assert 'What that step expects' in self.src

    def test_the_author_is_told_the_employee_will_read_it(self):
        assert 'They will read this' in self.src

    def test_the_author_is_told_not_to_write_an_assessment(self):
        assert 'not how' in self.src and 'performing' in self.src
        assert "don't put pay in it" in self.src.lower()

    def test_a_blocked_case_explains_itself_rather_than_disabling_silently(self):
        assert 'rw-blocked' in self.src and 'rw-blocked-msg' in self.src

    def test_it_uses_the_shared_shell_primitives(self):
        assert 'announce(' in self.src and 'escH(' in self.src
        assert self.src.count('aria-live') == 0

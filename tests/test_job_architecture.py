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

    def test_no_write_route_is_gated_on_job_architecture_write(self):
        """`job_architecture:w` is ROADMAP authoring (KAN-207), not ladder editing.
        Gating the ladder on it would hand every SOLID_LINE_MANAGER the company's
        job architecture, which is the half of CFL-42-35 people forget."""
        import inspect
        from app.routes import compensation as mod
        src = inspect.getsource(mod)
        assert "'job_architecture', 'w'" not in src.replace('"', "'")

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

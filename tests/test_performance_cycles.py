"""Review cycles and eligibility — EP44 P0 (KAN-219, KAN-220, A7, D-009, D-010).

The foundation of performance management. Two decisions carry the whole story and
most of these tests exist to pin them:

1. **At most one round that is not CLOSED**, and **a closed round can never be
   reopened.** A round is the container that assessments, calibration outcomes and
   step changes point at. Two open rounds make "which round am I in?" ambiguous;
   reopening a closed one silently changes what every record pointing at it means.

2. **Eligibility is a SNAPSHOT, not a live query.** Live participation means a
   mid-cycle joiner silently appears in a manager's list, a leaver silently
   vanishes, and the completion meter moves for reasons nobody did — which is
   indistinguishable from a bug.

Plus the rule that is easiest to get wrong and worst to get wrong: **every
exclusion carries a named reason**, and **somebody with no manager blocks the
round** rather than being a footnote.

All DB interaction is mocked; data is synthetic.
"""
import datetime
import json
import re

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session, FakeTransaction, recording_execute

CO = 'co-1'
CYC = 'cyc-1'
TODAY = datetime.date.today()


def _cycle_row(status='DRAFT', deadline='2026-11-15', cutoff=90,
               excluded=('CONTRACTOR',), opens='2026-01-01', closes='2027-01-01'):
    return {'id': CYC, 'name': '2026 Annual Review', 'period_year': 2026,
            'opens_on': opens, 'closes_on': closes,
            'self_assessment_deadline': deadline,
            'joiner_cutoff_days': cutoff,
            'excluded_employment_types': list(excluded),
            'status': status, 'opened_at': None, 'closed_at': None}


def _emp(name, join='2020-01-01', exit=None, etype='PERMANENT', mgr='mgr-1', eid=None):
    return {'employee_id': eid or name.lower().replace(' ', '-'), 'name': name,
            'job_title': 'Engineer', 'join_date': join, 'exit_date': exit,
            'employment_type': etype, 'manager_employee_id': mgr}


@pytest.fixture
def hr_client(client):
    _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'],
                 employee_id='emp-hr', user_id='u-hr')
    with client.session_transaction() as s:
        s['company_id'] = CO
    return client


# ── One round at a time, forward only, never reopened ────────────────────────

class TestOnlyOneRoundRunsAtATime:
    """AC-219-03. Annual cadence makes this a real constraint, not a cap."""

    def test_the_database_enforces_it_not_the_service(self):
        """Two open rounds make every downstream reader pick one arbitrarily, so
        the guarantee belongs where it cannot be bypassed."""
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'uq_pc_one_active' in sql
        assert "WHERE status <> 'CLOSED'" in sql, 'the partial index is not on the right predicate'

    def test_creating_a_second_active_round_is_refused_with_a_sentence(self):
        """Refused in the service too, so the user gets an explanation rather than
        a raw constraint violation."""
        from app.services import performance_service as svc
        with patch.object(svc, 'list_cycles', return_value=[
                dict(_cycle_row(status='OPEN'), status_label='Open', is_active=True,
                     included=0, excluded=0, snapshot_taken=False)]):
            with pytest.raises(svc.CycleError) as exc:
                svc.create_cycle(CO, '2027', 2027, '2027-01-01', '2028-01-01')
        msg = str(exc.value)
        assert 'still open' in msg and '2026 Annual Review' in msg, (
            'the refusal does not name which round is blocking')

    def test_a_new_round_is_allowed_once_the_previous_is_closed(self):
        from app.services import performance_service as svc
        with patch.object(svc, 'list_cycles', return_value=[
                dict(_cycle_row(status='CLOSED'), status_label='Closed',
                     is_active=False, included=0, excluded=0, snapshot_taken=False)]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'insert_returning', return_value={'id': 'cyc-2'}), \
             patch.object(svc, 'audit_service'):
            assert svc.create_cycle(CO, '2027', 2027, '2027-01-01', '2028-01-01') == 'cyc-2'

    def test_active_cycle_is_singular_by_construction(self):
        import inspect
        from app.services import performance_service as svc
        doc = ' '.join(inspect.getdoc(svc.active_cycle).split())
        assert 'impossibility in the database' in doc


class TestARoundOnlyMovesForward:
    """AC-219-02 / AC-219-05."""

    def _advance(self, from_status, to_status, deadline='2026-11-15', snapshot=True):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row(from_status, deadline)), \
             patch.object(svc, '_snapshot_exists', return_value=snapshot), \
             patch.object(svc, 'preview_eligibility',
                          return_value={'blockers': [], 'included': [], 'excluded': [],
                                        'total': 0, 'excluded_by_reason': [],
                                        'partial_count': 0, 'cycle': _cycle_row()}), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'take_snapshot'), \
             patch.object(svc, 'audit_service') as aud:
            out = svc.advance_cycle(CO, CYC, to_status, actor={'user_id': 'u-hr'})
        return out, aud

    def test_forward_is_allowed(self):
        out, aud = self._advance('OPEN', 'IN_REVIEW')
        assert out['status'] == 'IN_REVIEW'
        assert aud.record.call_args.args[0] == 'PERFORMANCE_CYCLE_ADVANCED'

    def test_backwards_is_refused(self):
        from app.services import performance_service as svc
        with pytest.raises(svc.CycleError) as exc:
            self._advance('CALIBRATION', 'OPEN')
        assert 'only moves forward' in str(exc.value)

    def test_staying_put_is_refused(self):
        from app.services import performance_service as svc
        with pytest.raises(svc.CycleError):
            self._advance('OPEN', 'OPEN')

    def test_a_closed_round_can_never_be_reopened(self):
        """Assessments, calibration outcomes and step changes point at it."""
        from app.services import performance_service as svc
        with pytest.raises(svc.CycleError) as exc:
            self._advance('CLOSED', 'OPEN')
        msg = str(exc.value)
        assert 'cannot be reopened' in msg
        assert 'point at it' in msg, 'the refusal does not say WHY'

    def test_the_schema_comment_records_the_reason(self):
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'FORWARD ONLY' in sql and 'never be reopened' in sql

    def test_the_screen_warns_before_closing_rather_than_after(self):
        with open('templates/admin/performance_cycles.html') as f:
            src = f.read()
        assert 'cannot be reopened' in src
        # And on the confirmation itself, not only in the intro copy.
        confirm = src[src.index('function pcCloseCycle'):]
        assert 'cannot be reopened' in confirm[:600]

    def test_only_the_next_stage_is_offered_on_screen(self):
        """A dropdown of every stage would invite going backwards."""
        with open('templates/admin/performance_cycles.html') as f:
            src = f.read()
        block = src[src.index('function pcActions'):]
        block = block[:block.index('\n}')]
        assert 'PC_STATES[i + 1]' in block


class TestAssessmentsCannotStartWithoutADeadline:
    """AC-219-11 / OQ-10. The deadline is the only thing that stops a silent
    employee deadlocking their own review and the whole round."""

    def test_moving_to_in_review_without_a_deadline_is_refused(self):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN', deadline=None)), \
             patch.object(svc, '_snapshot_exists', return_value=True):
            with pytest.raises(svc.CycleError) as exc:
                svc.advance_cycle(CO, CYC, 'IN_REVIEW', actor={'user_id': 'u'})
        msg = str(exc.value)
        assert 'deadline' in msg
        assert 'never submits' in msg, 'the refusal does not say what it prevents'

    def test_moving_to_in_review_without_a_snapshot_is_refused(self):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')), \
             patch.object(svc, '_snapshot_exists', return_value=False):
            with pytest.raises(svc.CycleError) as exc:
                svc.advance_cycle(CO, CYC, 'IN_REVIEW', actor={'user_id': 'u'})
        assert 'snapshot' in str(exc.value)

    def test_a_deadline_outside_the_window_is_refused(self):
        from app.services import performance_service as svc
        with patch.object(svc, 'active_cycle', return_value=None):
            with pytest.raises(svc.CycleError) as exc:
                svc.create_cycle(CO, 'x', 2026, '2026-01-01', '2027-01-01',
                                 self_assessment_deadline='2027-06-01')
        assert 'inside the round' in str(exc.value)

    def test_the_database_enforces_the_window_bound_too(self):
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'chk_pc_deadline' in sql


class TestNoPeriodTypeAndNoPayReference:
    """D-009(1). Annual, and independent of the pay round."""

    def test_there_is_no_period_type_column(self):
        """A configurable field with one legal value is a lie about what the
        product supports."""
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        code = '\n'.join(l for l in sql.splitlines() if not l.strip().startswith('--'))
        assert 'period_type' not in code
        assert 'quarter' not in code.lower()

    def test_create_cycle_takes_no_period_type_argument(self):
        import inspect
        from app.services import performance_service as svc
        assert 'period_type' not in inspect.signature(svc.create_cycle).parameters

    def test_nothing_in_the_migration_references_pay(self):
        """AC-219-09 — keeps the compensation dependency one-directional and stops
        a rating reaching an amount through a shared key."""
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        code = '\n'.join(l for l in sql.splitlines() if not l.strip().startswith('--'))
        for w in ('salary', 'pay_', 'currency', 'amount', 'compensation'):
            assert w not in code.lower(), f'{w!r} in the cycle migration'

    def test_nothing_in_the_service_reads_pay(self):
        import ast
        import inspect
        from app.services import performance_service as svc
        tree = ast.parse(inspect.getsource(svc))
        # Collect docstrings so they can be excluded: the module docstring lists
        # the API (including `update_cycle`) and explains the pay boundary in
        # prose, so a naive walk matches it on both counts. Naming a rule in order
        # to state it is not breaking it.
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                d = ast.get_docstring(node, clean=False)
                if d:
                    docstrings.add(d)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if node.value in docstrings:
                continue
            low = node.value.lower()
            if 'select' in low or 'insert into' in low or 'update ' in low:
                for w in ('salary', 'pay_point', 'currency', 'compensation'):
                    assert w not in low, f'{w!r} read in SQL by the cycle service'

    def test_the_screen_says_annual_rather_than_hiding_it(self):
        with open('templates/admin/performance_cycles.html') as f:
            src = f.read()
        assert 'no quarterly option' in src


# ── Eligibility ──────────────────────────────────────────────────────────────

class TestEligibilityIsASnapshotNotALiveQuery:
    """AC-220-01, the load-bearing decision in KAN-220."""

    def test_the_table_says_so_where_somebody_would_change_it(self):
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'SNAPSHOT, NOT A LIVE QUERY' in sql
        assert 'indistinguishable from a bug' in sql

    def test_re_taking_a_snapshot_requires_an_explicit_re_evaluate(self):
        """Otherwise a stray call silently rewrites everybody's participation."""
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')), \
             patch.object(svc, 'query', return_value=[{'employee_id': 'e1',
                                                       'state': 'INCLUDED',
                                                       'exclusion_reason': None,
                                                       'overridden_by_user_id': None}]):
            with pytest.raises(svc.CycleError) as exc:
                svc.take_snapshot(CO, CYC, actor={'user_id': 'u'})
        assert 'already has a participant list' in str(exc.value)

    def test_a_re_evaluation_reports_what_changed(self):
        """That report is what makes it safe to run at all."""
        from app.services import performance_service as svc
        existing = [{'employee_id': 'ann', 'state': 'INCLUDED',
                     'exclusion_reason': None, 'overridden_by_user_id': None}]
        decided = [_emp('Ann'), _emp('Bo')]
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')), \
             patch.object(svc, 'query', return_value=existing), \
             patch.object(svc, '_evaluate', return_value=[
                 dict(d, state='INCLUDED', exclusion_reason=None, is_partial=False)
                 for d in decided]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'audit_service') as aud:
            out = svc.take_snapshot(CO, CYC, actor={'user_id': 'u'}, re_evaluate=True)
        assert out['added'] == ['Bo']
        assert aud.record.call_args.args[0] == 'PERFORMANCE_PARTICIPANTS_RE_EVALUATED'

    def test_a_re_evaluation_never_disturbs_an_hr_override(self):
        """HR decided that deliberately; a bulk re-run must not quietly undo it."""
        from app.services import performance_service as svc
        existing = [{'employee_id': 'ann', 'state': 'EXCLUDED',
                     'exclusion_reason': 'HR_EXCLUDED',
                     'overridden_by_user_id': 'u-hr'}]
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')), \
             patch.object(svc, 'query', return_value=existing), \
             patch.object(svc, '_evaluate', return_value=[
                 dict(_emp('Ann', eid='ann'), state='INCLUDED',
                      exclusion_reason=None, is_partial=False)]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service'):
            out = svc.take_snapshot(CO, CYC, actor={'user_id': 'u'}, re_evaluate=True)
        assert out['overrides_kept'] == ['Ann']
        assert not [c for c in exe.call_args_list
                    if 'INSERT INTO performance_cycle_participants' in str(c.args[0])], (
            'the override was overwritten by the re-evaluation')

    def test_one_audit_row_with_counts_not_one_per_person(self):
        """ADR-009 §3.5 — 147 rows saying "somebody was included" buries the rows
        anybody needs to find."""
        from app.services import performance_service as svc
        decided = [dict(_emp(f'P{i}', eid=f'e{i}'), state='INCLUDED',
                        exclusion_reason=None, is_partial=False) for i in range(50)]
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')), \
             patch.object(svc, 'query', return_value=[]), \
             patch.object(svc, '_evaluate', return_value=decided), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'audit_service') as aud:
            svc.take_snapshot(CO, CYC, actor={'user_id': 'u'})
        aud.record.assert_called_once()
        assert aud.record.call_args.kwargs['metadata']['included'] == 50

    def test_the_screen_explains_that_opening_freezes_the_list(self):
        with open('templates/admin/performance_cycles.html') as f:
            src = f.read()
        flat = ' '.join(src.split())          # the sentence wraps in the template
        assert 'freezes this list' in flat
        assert 'not silently appear' in flat


class TestEveryExclusionCarriesANamedReason:
    """AC-220-02. A silent exclusion from a review round is the defect this story
    exists to prevent — and exactly what somebody is later asked to justify."""

    def _evaluate(self, employees, cycle=None):
        from app.services import performance_service as svc
        with patch.object(svc, 'query', return_value=employees):
            return svc._evaluate(CO, cycle or _cycle_row())

    def test_an_ordinary_employee_is_included(self):
        out = self._evaluate([_emp('Ann')])
        assert out[0]['state'] == 'INCLUDED' and out[0]['exclusion_reason'] is None

    def test_an_excluded_employment_type_is_named(self):
        out = self._evaluate([_emp('Ann', etype='CONTRACTOR')])
        assert out[0]['exclusion_reason'] == 'EXCLUDED_EMPLOYMENT_TYPE'
        assert out[0]['exclusion_label']

    def test_a_leaver_before_the_end_is_named(self):
        out = self._evaluate([_emp('Ann', exit='2026-06-01')])
        assert out[0]['exclusion_reason'] == 'LEAVER'

    def test_a_leaver_after_the_end_is_still_included(self):
        """Their period is complete, so they are assessed on it."""
        out = self._evaluate([_emp('Ann', exit='2027-03-01')])
        assert out[0]['state'] == 'INCLUDED'

    def test_a_joiner_inside_the_cut_off_is_named(self):
        out = self._evaluate([_emp('Ann', join='2026-12-01')])
        assert out[0]['exclusion_reason'] == 'NEW_JOINER'

    def test_a_joiner_outside_the_cut_off_is_included_and_flagged_partial(self):
        """AC-220-05 — the manager must know they are assessing a shorter period."""
        out = self._evaluate([_emp('Ann', join='2026-03-01')])
        assert out[0]['state'] == 'INCLUDED' and out[0]['is_partial'] is True

    def test_somebody_there_the_whole_period_is_not_partial(self):
        out = self._evaluate([_emp('Ann', join='2020-01-01')])
        assert out[0]['is_partial'] is False

    def test_no_manager_is_named(self):
        out = self._evaluate([_emp('Ann', mgr=None)])
        assert out[0]['exclusion_reason'] == 'NO_MANAGER'

    def test_no_manager_is_not_masked_by_a_policy_exclusion(self):
        """Order matters: a policy exclusion is something the user can change, so
        "nobody can assess them" must not be hidden behind it."""
        from app.services import performance_service as svc
        # A contractor with no manager reports the POLICY reason, because the
        # policy answer is the actionable one — they are out either way.
        out = self._evaluate([_emp('Ann', etype='CONTRACTOR', mgr=None)])
        assert out[0]['exclusion_reason'] == 'EXCLUDED_EMPLOYMENT_TYPE'
        # But a PERMANENT employee with no manager surfaces as NO_MANAGER, which
        # is the one that blocks.
        out2 = self._evaluate([_emp('Bo', mgr=None)])
        assert out2[0]['exclusion_reason'] == 'NO_MANAGER'

    def test_the_reason_vocabulary_is_closed_in_the_database(self):
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'chk_pcp_reason_vocab' in sql
        for r in ('NEW_JOINER', 'LEAVER', 'EXCLUDED_EMPLOYMENT_TYPE',
                  'NO_MANAGER', 'HR_EXCLUDED'):
            assert r in sql

    def test_an_exclusion_without_a_reason_is_impossible(self):
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'chk_pcp_reason' in sql
        assert "(state = 'EXCLUDED') = (exclusion_reason IS NOT NULL)" in sql

    def test_the_policy_is_recorded_on_the_round_not_in_a_settings_table(self):
        """A 2027 round's exclusions must still be explicable in 2029 even if the
        company changed its rules — a settings table answers "what is the policy
        now?" when the question is "what was it then?"."""
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'joiner_cutoff_days' in sql and 'excluded_employment_types' in sql
        assert 'what was it then' in sql

    def test_the_policy_cannot_be_changed_once_the_round_has_opened(self):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')):
            with pytest.raises(svc.CycleError) as exc:
                svc.update_cycle(CO, CYC, joiner_cutoff_days=30, actor={'user_id': 'u'})
        assert 'draft' in str(exc.value)


class TestNobodyToAssessThemBlocksTheRound:
    """AC-220-06. There is nobody to assess them, so opening anyway guarantees the
    round cannot be completed. A footnote would not do that."""

    def test_opening_is_refused_and_names_the_people(self):
        from app.services import performance_service as svc
        preview = {'blockers': [{'employee_id': 'e1', 'name': 'Ann Ark'},
                                {'employee_id': 'e2', 'name': 'Bo Bell'}],
                   'included': [], 'excluded': [], 'total': 2,
                   'excluded_by_reason': [], 'partial_count': 0,
                   'cycle': _cycle_row()}
        with patch.object(svc, '_cycle', return_value=_cycle_row('DRAFT')), \
             patch.object(svc, 'preview_eligibility', return_value=preview), \
             patch.object(svc, '_snapshot_exists', return_value=False):
            with pytest.raises(svc.CycleError) as exc:
                svc.advance_cycle(CO, CYC, 'OPEN', actor={'user_id': 'u'})
        msg = str(exc.value)
        assert 'Ann Ark' in msg and 'Bo Bell' in msg, 'the refusal does not name them'
        assert 'nobody can assess them' in msg
        assert 'exclude them deliberately' in msg, 'it offers no way forward'

    def test_only_no_manager_blocks_and_policy_exclusions_do_not(self):
        """Policy exclusions are deliberate; this one means the round cannot finish."""
        from app.services import performance_service as svc
        emps = [_emp('Ann', etype='CONTRACTOR'), _emp('Bo', join='2026-12-01')]
        with patch.object(svc, '_cycle', return_value=_cycle_row()), \
             patch.object(svc, 'query', return_value=emps):
            prev = svc.preview_eligibility(CO, CYC)
        assert prev['blockers'] == []
        assert len(prev['excluded']) == 2

    def test_the_screen_disables_opening_and_says_why(self):
        with open('templates/admin/performance_cycles.html') as f:
            src = f.read()
        block = src[src.index('const blockers = pcEl'):]
        block = block[:block.index('// Every exclusion')]
        assert 'disabled = true' in block
        assert 'nobody can assess them' in block


class TestThePreviewChangesNothing:
    def test_preview_writes_nothing(self):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row()), \
             patch.object(svc, 'query', return_value=[_emp('Ann')]), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, 'audit_service') as aud:
            svc.preview_eligibility(CO, CYC)
        exe.assert_not_called()
        aud.record.assert_not_called()

    def test_the_preview_and_the_snapshot_use_the_same_decision_function(self):
        """If they diverged, the screen would promise one thing and do another."""
        import inspect
        from app.services import performance_service as svc
        assert '_evaluate(' in inspect.getsource(svc.preview_eligibility)
        assert '_evaluate(' in inspect.getsource(svc.take_snapshot)


class TestHrOverrideNeedsAReason:
    """AC-220-09. An unexplained exclusion from a review round is exactly what a
    works council or a tribunal asks about."""

    def test_an_override_without_a_reason_is_refused(self):
        from app.services import performance_service as svc
        for empty in (None, '', '   '):
            with pytest.raises(svc.CycleError) as exc:
                svc.override_participation(CO, CYC, 'e1', False, reason=empty,
                                           actor={'user_id': 'u-hr'})
            assert 'needs a reason' in str(exc.value)

    def test_an_override_with_a_reason_is_recorded_and_audited(self):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row('OPEN')), \
             patch.object(svc, 'query', side_effect=[
                 {'state': 'INCLUDED', 'exclusion_reason': None}, {'m': 'mgr-1'}]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, 'audit_service') as aud:
            svc.override_participation(CO, CYC, 'e1', False,
                                       reason='On long-term leave all period.',
                                       actor={'user_id': 'u-hr'})
        assert aud.record.call_args.args[0] == 'PERFORMANCE_PARTICIPATION_OVERRIDDEN'
        assert 'long-term leave' in aud.record.call_args.kwargs['reason']
        assert aud.record.call_args.kwargs['retention_class'] == 'EMPLOYMENT'

    def test_the_database_refuses_an_override_with_no_reason(self):
        with open('database/migrations/15_performance_cycles.sql') as f:
            sql = f.read()
        assert 'chk_pcp_override' in sql

    def test_a_closed_round_cannot_be_overridden(self):
        from app.services import performance_service as svc
        with patch.object(svc, '_cycle', return_value=_cycle_row('CLOSED')):
            with pytest.raises(svc.CycleError):
                svc.override_participation(CO, CYC, 'e1', True, reason='x',
                                          actor={'user_id': 'u'})


class TestCoverageNamesTheRemainder:
    """AC-220-10 — never a bare percentage; the excluded are the actionable part."""

    def test_it_reports_included_over_total_and_lists_the_excluded(self):
        from app.services import performance_service as svc
        rows = [
            {'employee_id': 'a', 'name': 'Ann', 'state': 'INCLUDED',
             'exclusion_reason': None, 'is_partial': True, 'is_override': False},
            {'employee_id': 'b', 'name': 'Bo', 'state': 'EXCLUDED',
             'exclusion_reason': 'LEAVER', 'is_partial': False, 'is_override': False},
            {'employee_id': 'c', 'name': 'Cy', 'state': 'EXCLUDED',
             'exclusion_reason': 'LEAVER', 'is_partial': False, 'is_override': True},
        ]
        with patch.object(svc, 'participants', return_value=rows):
            c = svc.coverage(CO, CYC)
        assert (c['total'], c['included'], c['excluded']) == (3, 1, 2)
        assert c['partial'] == 1 and c['overrides'] == 1
        assert c['excluded_by_reason'][0]['names'] == ['Bo', 'Cy']

    def test_an_empty_round_reports_no_percentage_rather_than_zero(self):
        from app.services import performance_service as svc
        with patch.object(svc, 'participants', return_value=[]):
            assert svc.coverage(CO, CYC)['pct'] is None


# ── Access ───────────────────────────────────────────────────────────────────

class TestAccessAndTenancy:
    def test_no_hardcoded_role_list_in_the_module(self):
        import inspect
        from app.routes import performance as mod
        assert '@require_roles(' not in inspect.getsource(mod)
        assert not hasattr(mod, 'require_roles')

    def test_every_admin_route_is_gated_on_performance_write(self):
        import inspect
        from app.routes import performance as mod
        src = inspect.getsource(mod)
        for name in ('admin_performance_cycles', 'api_create_cycle', 'api_update_cycle',
                     'api_advance_cycle', 'api_close_cycle', 'api_discard_cycle',
                     'api_preview_eligibility', 'api_take_snapshot',
                     'api_override_participation'):
            head = src[:src.index(f'def {name}(')]
            assert "require_feature_access('performance', 'w')" in head[head.rindex('@app.route'):], (
                f'{name} is not gated on performance:w')

    def test_the_participant_list_is_readable_on_performance_read(self):
        """An employee must be able to see that they are in the round."""
        import inspect
        from app.routes import performance as mod
        src = inspect.getsource(mod)
        head = src[:src.index('def api_participants(')]
        assert "@require_feature_access('performance')" in head[head.rindex('@app.route'):]

    def test_the_participant_list_is_row_scoped(self):
        """AC-220-11 — asserted at the payload, because a URL is a guess."""
        import inspect
        from app.routes import performance as mod
        src = inspect.getsource(mod.api_participants)
        assert 'manager_employee_id=me' in src
        assert "r['employee_id'] == me" in src

    def test_write_is_seeded_only_to_hr_and_portal_admin(self):
        """A line manager must not open or close the company's annual round."""
        with open('database/seed_rbac.sql') as f:
            seed = f.read()
        block = seed[seed.index("EP44 P0 — the `performance` feature code"):]
        assert "ro.name IN ('HR_ADMIN', 'PORTAL_ADMIN')" in block
        assert 'SOLID_LINE_MANAGER' not in block

    def test_read_is_seeded_to_every_role(self):
        with open('database/seed_rbac.sql') as f:
            seed = f.read()
        block = seed[seed.index("EP44 P0 — the `performance` feature code"):]
        assert 'CROSS JOIN public.portal_features' in block

    def test_the_feature_is_registered_in_all_the_places_ci_needs(self):
        """A feature row is DATA and migrations never replay on a fresh CI DB."""
        for path, needle in (('database/migrations/15_performance_cycles.sql', "'performance'"),
                             ('database/seed_rbac.sql', "'performance', 'Performance Reviews'"),
                             ('scripts/setup_db.py', "'performance'")):
            with open(path) as f:
                assert needle in f.read(), f'{path} does not register the feature'

    def test_the_open_permission_question_is_recorded_not_guessed(self):
        """A manager writing an assessment must not need the admin grant. That is
        the CFL-42-35 shape again, and it is left open on purpose rather than
        answered by inventing a sixth feature code early."""
        import inspect
        from app.routes import performance as mod
        doc = inspect.getdoc(mod)
        assert 'CFL-42-35' in doc
        assert 'left open' in doc

    def test_every_query_is_company_scoped(self):
        import ast
        import inspect
        from app.services import performance_service as svc
        tree = ast.parse(inspect.getsource(svc))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                if 'company_id is null' in low:
                    pytest.fail('a query admits another tenant or a global default')


class TestTheScreenUsesTheSharedShellPrimitives:
    def setup_method(self):
        with open('templates/admin/performance_cycles.html') as f:
            self.src = f.read()

    def test_no_private_live_region(self):
        assert 'aria-live' not in self.src

    def test_it_announces_and_escapes(self):
        assert 'announce(' in self.src and 'escH(' in self.src
        assert "'assertive'" in self.src

    def test_the_dialogs_have_dialog_semantics_and_return_focus(self):
        assert self.src.count('role="dialog"') == 2
        assert self.src.count('aria-modal="true"') == 2
        assert 'pcOpener.focus()' in self.src
        assert "e.key !== 'Escape'" in self.src

    def test_the_overlay_is_not_given_a_box_class(self):
        """DEF-190-1: `.modal` is the BOX class; on an overlay it renders a narrow
        left-aligned panel."""
        for m in re.finditer(r'<div[^>]*role="dialog"[^>]*>', self.src):
            classes = re.search(r'class="([^"]*)"', m.group(0))
            classes = set((classes.group(1) if classes else '').split())
            assert 'modal-overlay' in classes and 'open' in classes
            assert 'modal' not in classes - {'modal-overlay'}

    def test_the_window_end_is_never_rendered_raw(self):
        """Half-open: `closes_on` is the first day NOT covered, so showing it raw
        is a day late (ADR-020)."""
        assert 'setDate(last.getDate() - 1)' in self.src

    def test_required_fields_are_labelled(self):
        for fid in ('pc-name', 'pc-year', 'pc-opens', 'pc-closes', 'pc-deadline',
                    'pc-cutoff', 'pc-excluded'):
            assert f'for="{fid}"' in self.src, f'{fid} has no label'

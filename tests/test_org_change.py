"""
Tests for the position-change (org-change) workflow.
All DB interactions are mocked.
"""
import json

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import (
    _set_session, FakeTransaction, recording_execute, assert_single_atomic_unit)
from tests.test_transfer_entry_point import CURRENT_PLACEMENT, route_query


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def employee_client(client):
    _set_session(client, roles=['EMPLOYEE'], employee_id='emp-sub', user_id='u-emp')
    return client


@pytest.fixture
def lead_client(client):
    _set_session(client, roles=['SOLID_LINE_MANAGER', 'EMPLOYEE'], employee_id='emp-lead', user_id='u-lead')
    return client


@pytest.fixture
def hr_client(client):
    _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'], employee_id='emp-hr', user_id='u-hr')
    return client


def _post(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type='application/json')


# ── Route: create request — permissions ───────────────────────────────────────

class TestCreateRequestPermissions:
    def test_requires_login(self, client):
        r = _post(client, '/api/org-change/request', {'employee_id': 'emp-sub'})
        assert r.status_code == 302  # redirect to login

    def test_feature_blocks_plain_employee(self, employee_client):
        # Employee lacks org_change write access → require_feature_access redirects
        with patch('app.auth.can_access_feature', return_value=False):
            r = _post(employee_client, '/api/org-change/request', {'employee_id': 'x'})
        assert r.status_code in (302, 403)

    def test_manager_cannot_move_non_report(self, lead_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', return_value={'company_id': 'co-1'}), \
             patch('app.routes.org_change.employee_solid_manager', return_value='someone-else'):
            r = _post(lead_client, '/api/org-change/request',
                      {'employee_id': 'emp-sub', 'manager_id': 'm-2', 'reason': 'x'})
        assert r.status_code == 403

    def test_manager_can_move_own_report(self, lead_client):
        # KAN-185 added subject/manager/unit/no-op/duplicate guards ahead of
        # create_request, so the stub has to answer each of them (see
        # tests/test_transfer_entry_point.py for the shared dispatcher).
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query()), \
             patch('app.routes.org_change.employee_solid_manager', return_value='emp-lead'), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.create_request', return_value='req-1') as mk:
            r = _post(lead_client, '/api/org-change/request',
                      {'employee_id': 'emp-sub', 'manager_id': 'm-2', 'reason': 'growth'})
        assert r.status_code == 200
        assert json.loads(r.data)['id'] == 'req-1'
        mk.assert_called_once()

    def test_hr_can_move_anyone(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query()), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.create_request', return_value='req-2'):
            r = _post(hr_client, '/api/org-change/request',
                      {'employee_id': 'anybody', 'business_unit_id': 'bu-9', 'reason': 'realign'})
        assert r.status_code == 200

    def test_rejects_empty_change(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', return_value={'company_id': 'co-1'}):
            r = _post(hr_client, '/api/org-change/request', {'employee_id': 'anybody'})
        assert r.status_code == 400

    def test_rejects_self_manager(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', return_value={'company_id': 'co-1'}):
            r = _post(hr_client, '/api/org-change/request',
                      {'employee_id': 'emp-x', 'manager_id': 'emp-x', 'reason': 'x'})
        assert r.status_code == 400


# ── Service: sequential decide logic ──────────────────────────────────────────

def _req_row(step=1, status='PENDING'):
    return {'id': 'req-1', 'company_id': 'co-1', 'employee_id': 'emp-sub',
            'requested_by_user_id': 'u-lead', 'current_step': step, 'status': status,
            'proposed_manager_id': 'm-2'}


def _role_step():
    return {'step_order': 1, 'approver_type': 'ROLE', 'approver_role': 'HR_ADMIN',
            'approver_employee_id': None}


HR_USER = {'user_id': 'u-hr', 'employee_id': 'emp-hr', 'company_id': 'co-1', 'roles': ['HR_ADMIN']}
OUTSIDER = {'user_id': 'u-x', 'employee_id': 'emp-x', 'company_id': 'co-1', 'roles': ['EMPLOYEE']}


class TestDecideEngine:
    def test_ineligible_user_rejected(self):
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', side_effect=[_req_row(), _role_step()]), \
             patch.object(svc, 'execute'):
            ok, msg = svc.decide('req-1', OUTSIDER, 'approve', None)
        assert ok is False
        assert 'approver' in msg

    def test_reject_sets_status_rejected(self):
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        # query order: req, step, emp_name, subject_users
        qs = [_req_row(), _role_step(), {'n': 'Sub Ject'}, [{'id': 'u-sub'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'notif'):
            ok, status = svc.decide('req-1', HR_USER, 'reject', 'no')
        assert ok and status == 'REJECTED'
        assert any("REJECTED" in str(c.args[0]) for c in exe.call_args_list)
        # KAN-155: the step decision and the request status close-out are one unit
        assert_single_atomic_unit(txn, exe)

    def test_approve_non_final_advances_step(self):
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        # req, step, emp_name, total(count=2), next_step, approver_users
        qs = [_req_row(step=1), _role_step(), {'n': 'Sub'}, {'c': 2},
              {'step_order': 2, 'approver_type': 'ROLE', 'approver_role': 'PORTAL_ADMIN',
               'approver_employee_id': None}, [{'id': 'u-pa'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'notif'):
            ok, status = svc.decide('req-1', HR_USER, 'approve', None)
        assert ok and status == 'PENDING'
        assert any("current_step" in str(c.args[0]) for c in exe.call_args_list)
        assert_single_atomic_unit(txn, exe)

    def test_approve_final_applies_and_approves(self):
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        applied_inside = []
        # req(step2), step, emp_name, total(count=2), subject_users
        qs = [_req_row(step=2), _role_step(), {'n': 'Sub'}, {'c': 2}, [{'id': 'u-sub'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, '_apply_change',
                          side_effect=lambda rid: applied_inside.append((rid, txn.open))) as apply_mock, \
             patch.object(svc, 'notif'):
            ok, status = svc.decide('req-1', HR_USER, 'approve', None)
        assert ok and status == 'APPROVED'
        apply_mock.assert_called_once_with('req-1')
        assert any("APPROVED" in str(c.args[0]) for c in exe.call_args_list)
        # KAN-155 / TD-7: decision + move + status close-out commit together
        assert applied_inside == [('req-1', True)]
        assert_single_atomic_unit(txn, exe)

    def test_final_approval_failure_rolls_back_the_whole_unit(self):
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        qs = [_req_row(step=2), _role_step(), {'n': 'Sub'}, {'c': 2}]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, '_apply_change', side_effect=RuntimeError('apply blew up')), \
             patch.object(svc, 'notif') as notif_mock:
            with pytest.raises(RuntimeError):
                svc.decide('req-1', HR_USER, 'approve', None)
        # the unit was opened but never committed, and nobody was told it worked
        assert txn.opened == 1 and txn.committed == 0
        notif_mock.assert_not_called()

    def test_rejection_retires_the_call_to_action(self):
        """DEF-003 — a rejection ends the request, so nobody is 'awaiting' it.

        Several people can hold the approving role; only one of them decided.
        Without this the others keep a dead call to action in their bell for
        ever, and it is still labelled "awaiting your approval".
        """
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        qs = [_req_row(), _role_step(), {'n': 'Sub Ject'}, [{'id': 'u-sub'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'notif') as notif_mock:
            svc.decide('req-1', HR_USER, 'reject', 'no')
        notif_mock.resolve_related.assert_called_once_with(
            'ORG_CHANGE_REQUEST', 'req-1', ['ORG_CHANGE_REQUESTED'])

    def test_advancing_a_level_retires_the_previous_call_to_action(self):
        """DEF-003 — level N's call to action dies when level N is decided.

        Ordering matters: retire first, then raise level N+1. Retiring after
        would sweep away the notification just written for the next level.
        """
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        qs = [_req_row(step=1), _role_step(), {'n': 'Sub'}, {'c': 2},
              {'step_order': 2, 'approver_type': 'ROLE', 'approver_role': 'PORTAL_ADMIN',
               'approver_employee_id': None}, [{'id': 'u-pa'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'notif') as notif_mock:
            svc.decide('req-1', HR_USER, 'approve', None)
        calls = [c[0] for c in notif_mock.mock_calls]
        assert 'resolve_related' in calls
        assert calls.index('resolve_related') < calls.index('create_user_notification'), \
            "the next level's call to action was written before the retire, so it was swept away"

    def test_requester_receipt_is_not_a_call_to_action(self):
        """DEF-002/DEF-003 — the requester's receipt is a different event type.

        It must not be retired when a level is decided (it is the requester's
        only record that they raised it), and it must not render with an
        approver's pending-decision icon.
        """
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        qs = [{'bu': None, 'fu': None, 'loc': None, 'cc': None},   # current_placement: oa
              None,                                                # current_placement: mgr
              None,                                                # workflow lookup
              {'n': 'Sub'},                                        # _emp_name
              []]                                                  # step approver users
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'insert_returning', return_value={'id': 'req-9'}), \
             patch.object(svc, 'workflow_steps', return_value=list(svc._DEFAULT_STEPS)), \
             patch.object(svc, 'notif') as notif_mock:
            svc.create_request('co-1', 'emp-1', 'u-req', {'business_unit_id': 'bu-2'}, 'why')
        events = [c.args[1] for c in notif_mock.create_user_notification.call_args_list]
        assert 'ORG_CHANGE_SUBMITTED' in events, \
            "the requester's receipt reuses the approvers' call-to-action event type"

    def test_decide_blocks_non_pending(self):
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', side_effect=[_req_row(status='APPROVED')]):
            ok, msg = svc.decide('req-1', HR_USER, 'approve', None)
        assert ok is False


class TestApplyChange:
    def test_apply_creates_assignment_and_manager(self):
        from app.services import org_change_service as svc
        req = {'employee_id': 'emp-sub', 'from_manager_id': 'm-old',
               'bu': 'bu-1', 'fu': 'fu-1', 'loc': 'loc-1', 'mgr': 'm-2'}
        txn = FakeTransaction()
        exe = recording_execute(txn)
        # apply_change queries: request row (one), old cost centre (one)
        with patch.object(svc, 'query', side_effect=[req, {'cc': 'cc-1'}]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        sqls = " ".join(str(c.args[0]) for c in exe.call_args_list)
        assert "employee_org_assignments" in sqls
        assert "manager_relationships" in sqls        # manager changed (m-2 != m-old)
        # KAN-155: closing the old assignment, opening the new one and re-pointing
        # the manager are a single unit — never four independent commits
        assert_single_atomic_unit(txn, exe)

    def test_apply_skips_manager_when_unchanged(self):
        from app.services import org_change_service as svc
        req = {'employee_id': 'emp-sub', 'from_manager_id': 'm-2',
               'bu': 'bu-1', 'fu': 'fu-1', 'loc': 'loc-1', 'mgr': 'm-2'}
        txn = FakeTransaction()
        exe = recording_execute(txn)
        with patch.object(svc, 'query', side_effect=[req, {'cc': None}]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        sqls = " ".join(str(c.args[0]) for c in exe.call_args_list)
        assert "manager_relationships" not in sqls    # manager unchanged → no re-point
        assert_single_atomic_unit(txn, exe)


class TestApplyCarriesUnchangedFieldsForward:
    """A proposal stores ONLY what changed; NULL means "no change", not "clear".

    Regression: applying a business-unit-only move inserted the raw proposal and
    so wiped the employee's location and functional unit. Every prior test here
    passed a fully-populated proposal, which is why nothing caught it. These
    drive the partial proposals the Transfer… entry point makes routine — its
    selects all start at "— No change —".
    """

    CURRENT = {'loc': 'loc-old', 'bu': 'bu-old', 'fu': 'fu-old', 'cc': 'cc-old'}

    def _insert_params(self, proposed):
        from app.services import org_change_service as svc
        req = dict({'employee_id': 'emp-sub', 'from_manager_id': 'm-1', 'mgr': None},
                   **proposed)
        txn = FakeTransaction()
        exe = recording_execute(txn)
        with patch.object(svc, 'query', side_effect=[req, dict(self.CURRENT)]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        ins = next(c for c in exe.call_args_list
                   if 'INSERT INTO employee_org_assignments' in ' '.join(str(c.args[0]).split()))
        # (employee_id, location_id, business_unit_id, functional_unit_id,
        #  cost_center_id, effective_from) — `effective_from` became explicit in
        # KAN-189; it used to rely on the column default. Named rather than
        # unpacked-and-ignored so this reads as a deliberate widening.
        _emp, loc, bu, fu, cc, eff_from = ins.args[1]
        return {'loc': loc, 'bu': bu, 'fu': fu, 'cc': cc, 'effective_from': eff_from}

    def _placement(self, proposed):
        """The four placement columns only — the effective date has its own tests."""
        got = self._insert_params(proposed)
        got.pop('effective_from')
        return got

    def test_business_unit_only_move_keeps_location_and_functional_unit(self):
        got = self._placement({'bu': 'bu-new', 'fu': None, 'loc': None})
        assert got == {'bu': 'bu-new', 'fu': 'fu-old', 'loc': 'loc-old', 'cc': 'cc-old'}, (
            'a BU-only move must not clear the location or functional unit')

    def test_location_only_move_keeps_the_units(self):
        got = self._placement({'bu': None, 'fu': None, 'loc': 'loc-new'})
        assert got == {'bu': 'bu-old', 'fu': 'fu-old', 'loc': 'loc-new', 'cc': 'cc-old'}

    def test_manager_only_move_keeps_the_whole_placement(self):
        got = self._placement({'bu': None, 'fu': None, 'loc': None})
        assert got == dict(self.CURRENT)

    def test_a_full_proposal_still_overrides_everything(self):
        got = self._placement({'bu': 'bu-new', 'fu': 'fu-new', 'loc': 'loc-new'})
        assert got == {'bu': 'bu-new', 'fu': 'fu-new', 'loc': 'loc-new', 'cc': 'cc-old'}

    def test_an_employee_with_no_prior_assignment_does_not_crash(self):
        from app.services import org_change_service as svc
        req = {'employee_id': 'emp-sub', 'from_manager_id': None, 'mgr': None,
               'bu': 'bu-new', 'fu': None, 'loc': None}
        txn = FakeTransaction()
        exe = recording_execute(txn)
        with patch.object(svc, 'query', side_effect=[req, None]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        ins = next(c for c in exe.call_args_list
                   if 'INSERT INTO employee_org_assignments' in ' '.join(str(c.args[0]).split()))
        assert ins.args[1][2] == 'bu-new'
        assert ins.args[1][1] is None and ins.args[1][3] is None


class TestCreateRequest:
    def test_create_inserts_and_notifies(self):
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        inserted_inside = []
        ins = MagicMock(side_effect=lambda *a, **k: (inserted_inside.append(txn.open),
                                                     {'id': 'req-9'})[1])
        notified_inside = []
        with patch.object(svc, 'current_placement', return_value={'bu': None, 'fu': None, 'loc': None, 'cc': None, 'mgr': 'm-old'}), \
             patch.object(svc, 'workflow_steps', return_value=[_role_step()]), \
             patch.object(svc, 'query', return_value=None), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'insert_returning', ins), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, '_step_approver_user_ids', return_value=['u-hr']), \
             patch.object(svc, '_emp_name', return_value='Sub Ject'), \
             patch.object(svc.notif, 'create_user_notification',
                          side_effect=lambda *a, **k: notified_inside.append(txn.open)) as notif_mock:
            rid = svc.create_request('co-1', 'emp-sub', 'u-lead',
                                     {'manager_id': 'm-2', 'business_unit_id': None,
                                      'functional_unit_id': None, 'location_id': None}, 'growth')
        assert rid == 'req-9'
        # notified step-1 approver AND requester
        assert notif_mock.call_count >= 2
        # KAN-155: request + full approval chain are one unit...
        assert inserted_inside == [True]
        assert_single_atomic_unit(txn, exe)
        # ...and notifications are sent only after it commits — they cannot be
        # rolled back (EP38 technical design §5.4)
        assert notified_inside and not any(notified_inside)


# ── Workflow config route ─────────────────────────────────────────────────────

class TestWorkflowConfig:
    def test_save_requires_steps(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True):
            r = _post(hr_client, '/api/admin/org-change-workflow', {'name': 'W', 'steps': []})
        # hr session has no company_id set → company guard triggers 400 as well
        assert r.status_code == 400

    def test_save_ok(self, client):
        _set_session(client, roles=['PORTAL_ADMIN'], employee_id='emp-pa', user_id='u-pa')
        with client.session_transaction() as s:
            s['company_id'] = '11111111-1111-1111-1111-111111111111'
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.svc.save_workflow', return_value='wf-1') as mk:
            r = _post(client, '/api/admin/org-change-workflow',
                      {'name': 'W', 'steps': [{'approver_type': 'ROLE', 'approver_role': 'HR_ADMIN'}]})
        assert r.status_code == 200
        mk.assert_called_once()


# ── KAN-203 — nobody acts on a request about themselves ───────────────────────
# P0/Critical, pre-existing. Before this guard `_can_initiate_for` returned True
# for any HR/Portal/System admin regardless of the subject, and `decide()` never
# compared the decider to `req['employee_id']` — so an HR_ADMIN who is also an
# employee could raise their own position change and then approve it.
#
# The rule is UNIVERSAL: every request type, every role, SYSTEM_ADMIN included.
# It is an integrity control, so it is refused outright and is deliberately NOT
# subject to the advise-and-override rule that governs judgements about amounts.

SELF_SUBJECT_USER = {'user_id': 'u-sub', 'employee_id': 'emp-sub',
                     'company_id': 'co-1', 'roles': ['HR_ADMIN', 'EMPLOYEE']}
SELF_SYSADMIN_USER = {'user_id': 'u-sa', 'employee_id': 'emp-sub',
                      'company_id': 'co-1', 'roles': ['SYSTEM_ADMIN']}


class TestKan203SelfInitiationRefused:
    """`_can_initiate_for` must refuse the subject BEFORE the admin exemption."""

    def test_hr_admin_cannot_raise_a_request_about_themselves(self, hr_client):
        # hr_client is emp-hr; the subject is also emp-hr.
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query',
                   return_value={'company_id': 'co-1', 'employment_status': 'ACTIVE',
                                 'name': 'H R'}), \
             patch('app.routes.org_change.transaction', FakeTransaction()), \
             patch('app.routes.org_change.audit_service'):
            r = _post(hr_client, '/api/org-change/request',
                      {'employee_id': 'emp-hr', 'manager_id': 'm-2', 'reason': 'x'})
        assert r.status_code == 403
        assert 'yourself' in r.get_json()['error']

    def test_the_refusal_is_audited_as_a_security_event(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query',
                   return_value={'company_id': 'co-1', 'employment_status': 'ACTIVE',
                                 'name': 'H R'}), \
             patch('app.routes.org_change.transaction', FakeTransaction()), \
             patch('app.routes.org_change.audit_service') as aud:
            _post(hr_client, '/api/org-change/request',
                  {'employee_id': 'emp-hr', 'manager_id': 'm-2', 'reason': 'x'})
        aud.record.assert_called_once()
        args, kwargs = aud.record.call_args
        assert args[0] == 'ORG_CHANGE_SELF_ACTION_REFUSED'
        assert kwargs['outcome'] == 'FAILED'
        assert kwargs['retention_class'] == 'SECURITY'

    def test_hr_admin_can_still_raise_for_somebody_else(self, hr_client):
        """The admin exemption survives — it just no longer covers oneself."""
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query()), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.create_request', return_value='req-9') as mk:
            r = _post(hr_client, '/api/org-change/request',
                      {'employee_id': 'emp-sub', 'manager_id': 'm-2', 'reason': 'x'})
        assert r.status_code == 200, r.get_json()
        mk.assert_called_once()

    def test_display_helper_hides_the_affordance_for_oneself(self, hr_client):
        """Hiding a button is never the control, but it must agree with it."""
        from app.routes import org_change as oc
        with hr_client.application.test_request_context():
            _set_session(hr_client, roles=['HR_ADMIN'], employee_id='emp-hr', user_id='u-hr')
            with hr_client.session_transaction():
                pass
        with patch.object(oc, '_user', return_value={
                'user_id': 'u-hr', 'employee_id': 'emp-hr',
                'company_id': 'co-1', 'roles': ['HR_ADMIN']}):
            assert oc.can_initiate_org_change_for('emp-hr') is False
            with patch.object(oc, 'employee_solid_manager', return_value='emp-hr'):
                assert oc.can_initiate_org_change_for('emp-other') is True


class TestKan203SelfDecisionRefused:
    """`decide()` must refuse the subject at ANY level, in ANY role."""

    def test_subject_cannot_decide_their_own_request(self):
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', side_effect=[_req_row()]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'audit_service'), \
             patch.object(svc, 'execute') as exe:
            ok, msg = svc.decide('req-1', SELF_SUBJECT_USER, 'approve', None)
        assert ok is False
        assert 'yourself' in msg
        exe.assert_not_called()   # nothing was written

    def test_subject_cannot_decide_at_a_later_level_either(self):
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', side_effect=[_req_row(step=2)]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'audit_service'), \
             patch.object(svc, 'execute') as exe:
            ok, msg = svc.decide('req-1', SELF_SUBJECT_USER, 'approve', None)
        assert ok is False and 'yourself' in msg
        exe.assert_not_called()

    def test_system_admin_is_not_exempt(self):
        """SYSTEM_ADMIN bypasses feature gates, never integrity controls."""
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', side_effect=[_req_row()]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'audit_service'), \
             patch.object(svc, 'execute') as exe:
            ok, msg = svc.decide('req-1', SELF_SYSADMIN_USER, 'reject', 'mine')
        assert ok is False and 'yourself' in msg
        exe.assert_not_called()

    def test_the_refusal_is_audited_as_a_security_event(self):
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', side_effect=[_req_row()]), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'audit_service') as aud, \
             patch.object(svc, 'execute'):
            svc.decide('req-1', SELF_SUBJECT_USER, 'approve', None)
        aud.record.assert_called_once()
        args, kwargs = aud.record.call_args
        assert args[0] == 'ORG_CHANGE_SELF_ACTION_REFUSED'
        assert kwargs['retention_class'] == 'SECURITY'

    def test_a_normal_approver_is_unaffected(self):
        """The guard must not break the ordinary path (HR_USER is not the subject)."""
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        exe = recording_execute(txn)
        qs = [_req_row(), _role_step(), {'n': 'Sub Ject'}, [{'id': 'u-sub'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'notif'):
            ok, status = svc.decide('req-1', HR_USER, 'reject', 'no')
        assert ok and status == 'REJECTED'


# ── KAN-189 — effective dating (ADR-020, closes CFL-4) ────────────────────────
#
# HALF-OPEN `[effective_from, effective_to)` PROJECT-WIDE. `effective_to` is the
# first day NOT covered — the day the next row starts.
#
# What CFL-4 actually was: the old code closed an assignment with
# `effective_to = CURRENT_DATE` and let the new row default `effective_from` to
# CURRENT_DATE too. Read as INCLUSIVE that is a one-day overlap — both rows claim
# today — and fixing it would have meant rewriting history. Read as HALF-OPEN the
# same data is already correct and gapless. **The defect was the absence of a
# stated convention, not the data**, which is why this closes with no rewrite.
#
# DEF-42-2 rides along: the manager re-point set `is_current=FALSE` and nothing
# else, leaving every superseded reporting line with a NULL end date. Two such
# rows exist in the dev database, and EP42 was about to copy the pattern.

import datetime as _dt

_TODAY = _dt.date.today()


class TestFmtPeriodRendersHalfOpenCorrectly:
    """The off-by-one is the whole risk of half-open intervals."""

    def test_a_period_ending_31_march_stores_1_april_and_reads_31_march(self):
        from app.helpers import fmt_period
        # The design's own worked example (T-189-5).
        assert fmt_period(_dt.date(2026, 1, 1), _dt.date(2026, 4, 1)) \
            == '01 Jan 2026 – 31 Mar 2026'

    def test_an_open_period_reads_as_since_not_as_truncated(self):
        from app.helpers import fmt_period
        assert fmt_period(_dt.date(2026, 1, 1), None) == 'since 01 Jan 2026'

    def test_a_single_day_period_is_not_rendered_as_a_range(self):
        from app.helpers import fmt_period
        assert fmt_period(_dt.date(2026, 3, 5), _dt.date(2026, 3, 6)) == '05 Mar 2026'

    def test_a_zero_length_period_says_so_rather_than_reading_backwards(self):
        """`from == to` covers nothing under `[from, to)`. Rendering it as
        '05 Mar – 04 Mar' reads as corrupt data when it is merely empty."""
        from app.helpers import fmt_period
        assert fmt_period(_dt.date(2026, 3, 5), _dt.date(2026, 3, 5)) \
            == '05 Mar 2026 (no full day)'

    def test_it_accepts_strings_and_datetimes_not_just_dates(self):
        from app.helpers import fmt_period
        assert fmt_period('2026-01-01', '2026-04-01') == '01 Jan 2026 – 31 Mar 2026'
        assert fmt_period(_dt.datetime(2026, 1, 1, 9, 30),
                          _dt.datetime(2026, 4, 1, 9, 30)) == '01 Jan 2026 – 31 Mar 2026'

    def test_nothing_at_all_renders_as_a_dash_not_an_exception(self):
        from app.helpers import fmt_period
        assert fmt_period(None, None) == '—'
        assert fmt_period('not a date', None) == '—'

    def test_fmt_last_day_subtracts_the_day_too(self):
        from app.helpers import fmt_last_day
        assert fmt_last_day(_dt.date(2026, 4, 1)) == '31 Mar 2026'
        assert fmt_last_day(None) == '—'

    def test_both_helpers_are_available_to_every_template(self):
        """A convention nobody can reach is a convention nobody follows."""
        from app import app as flask_app
        with flask_app.test_request_context('/'):
            ctx = {}
            for proc in flask_app.template_context_processors[None]:
                ctx.update(proc())
        assert 'fmt_period' in ctx and 'fmt_last_day' in ctx

    def test_no_template_prints_the_exclusive_end_date_raw(self):
        """T-189-5's grep-assert. Printing `effective_to` is ALWAYS off by one.

        Nothing violates this today — the convention starts clean — so this
        guards the next surface, which is exactly when the mistake gets made.
        """
        import os
        offenders = []
        for root, _, files in os.walk('templates'):
            for f in files:
                if not f.endswith('.html'):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding='utf-8') as fh:
                    src = fh.read()
                if 'effective_to' in src and 'fmt_period' not in src and 'fmt_last_day' not in src:
                    offenders.append(path)
        assert not offenders, (
            f'{offenders} print effective_to raw — it is EXCLUSIVE, so that is a '
            f'day too late. Use fmt_period() / fmt_last_day().')


class TestEffectiveDateWindow:
    """`_validate_effective_date` — the company window and D4d's asymmetry."""

    def _v(self, d, request_type='TRANSFER'):
        from app.services import org_change_service as svc
        return svc._validate_effective_date('co-1', d, request_type)

    def test_today_is_allowed(self):
        assert self._v(_TODAY) is None

    def test_none_means_apply_on_approval_and_is_allowed(self):
        """Pre-KAN-189 rows carry NULL and must keep their original meaning."""
        assert self._v(None) is None

    def test_the_backdate_boundary_holds_at_exactly_the_limit(self):
        from app.services import org_change_service as svc
        back, _ = svc._dating_window('co-1')
        assert self._v(_TODAY - _dt.timedelta(days=back)) is None, 'the limit itself is allowed'
        msg = self._v(_TODAY - _dt.timedelta(days=back + 1))
        assert msg and str(back) in msg, 'one day past the limit must be refused, with the number'

    def test_a_future_dated_placement_is_refused_because_nothing_would_apply_it(self):
        """D4d. There is no scheduler, so a future date would silently mean
        'applied the moment the last approver clicked' — the lie the effective
        date exists to prevent. The message must say why."""
        msg = self._v(_TODAY + _dt.timedelta(days=1))
        assert msg and 'future' in msg.lower()

    def test_a_future_dated_pay_record_is_permitted(self):
        """The asymmetry is deliberate: pay is inert data until its date and
        every read filters on the date, so there is nothing to schedule."""
        assert self._v(_TODAY + _dt.timedelta(days=30), 'PAY') is None

    def test_a_future_pay_date_still_obeys_the_forward_window(self):
        from app.services import org_change_service as svc
        _, fwd = svc._dating_window('co-1')
        assert self._v(_TODAY + _dt.timedelta(days=fwd), 'PAY') is None
        msg = self._v(_TODAY + _dt.timedelta(days=fwd + 1), 'PAY')
        assert msg and str(fwd) in msg

    def test_a_non_date_is_refused_rather_than_crashing_the_engine(self):
        assert self._v('2026-01-01') is not None

    def test_level_change_counts_as_a_placement(self):
        """It moves somebody on the ladder, so it applies immediately too."""
        assert self._v(_TODAY + _dt.timedelta(days=1), 'LEVEL_CHANGE') is not None

    def test_the_window_is_company_scoped_by_signature(self):
        """So the switch to company_compensation_settings is one function.

        Per-company values are NOT yet delivered — that table is W1 — but no
        caller will need changing when they are.
        """
        import inspect
        from app.services import org_change_service as svc
        assert list(inspect.signature(svc._dating_window).parameters) == ['company_id']


class TestCreateRequestPersistsTheEffectiveDate:
    def _create(self, **kw):
        from app.services import org_change_service as svc
        txn = FakeTransaction()
        with patch.object(svc, 'current_placement', return_value=CURRENT_PLACEMENT), \
             patch.object(svc, 'workflow_steps', return_value=[_role_step()]), \
             patch.object(svc, 'query', return_value=None), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'insert_returning', return_value={'id': 'req-1'}) as ins, \
             patch.object(svc, 'execute'), \
             patch.object(svc, '_step_approver_user_ids', return_value=['u-hr']), \
             patch.object(svc, '_emp_name', return_value='Sub Ject'), \
             patch.object(svc, 'notif'):
            svc.create_request('co-1', 'emp-sub', 'u-hr',
                               {'business_unit_id': 'bu-new'}, 'why', **kw)
        return ins.call_args.args[0], ins.call_args.args[1]

    def test_the_date_is_written_to_the_request(self):
        chosen = _TODAY - _dt.timedelta(days=7)
        sql, params = self._create(effective_date=chosen)
        assert 'effective_date' in ' '.join(str(sql).split())
        assert chosen in params

    def test_it_defaults_to_today_when_not_given(self):
        """Which is what every request meant before the column existed."""
        _sql, params = self._create()
        assert _TODAY in params

    def test_the_engine_re_validates_rather_than_trusting_the_caller(self):
        """The route's check is the message; the engine's is the control."""
        from app.services import org_change_service as svc
        with pytest.raises(ValueError):
            svc.create_request('co-1', 'emp-sub', 'u-hr', {'business_unit_id': 'b'}, 'x',
                               effective_date=_TODAY + _dt.timedelta(days=5))

    def test_effective_date_is_keyword_only(self):
        """So the four positional arguments keep their meaning as ADR-021 adds
        request_type and compensation beside it."""
        import inspect
        from app.services import org_change_service as svc
        p = inspect.signature(svc.create_request).parameters['effective_date']
        assert p.kind is inspect.Parameter.KEYWORD_ONLY


class TestApplyUsesOneBoundaryDate:
    """T-189-4 — the CFL-4 overlap must be unreproducible.

    The DB is mocked here, so the overlap is asserted on the parameters the
    engine emits, using the same `[from, to)` arithmetic Postgres would apply.
    A real-DB assertion needs the integration tier (KAN-168), which is not built.
    """

    def _apply(self, effective_date, mgr='m-2', from_mgr='m-1'):
        from app.services import org_change_service as svc
        req = {'employee_id': 'emp-sub', 'from_manager_id': from_mgr, 'mgr': mgr,
               'bu': 'bu-new', 'fu': None, 'loc': None,
               'effective_date': effective_date}
        txn = FakeTransaction()
        exe = recording_execute(txn)
        with patch.object(svc, 'query', side_effect=[req, {'loc': 'l', 'bu': 'b',
                                                          'fu': 'f', 'cc': 'c'}]), \
             patch.object(svc, 'transaction', txn), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        return exe

    @staticmethod
    def _find(exe, needle):
        return [c for c in exe.call_args_list
                if needle in ' '.join(str(c.args[0]).split())]

    def test_the_same_date_closes_the_old_row_and_opens_the_new_one(self):
        """One date on both ends is what makes an overlap impossible."""
        eff = _TODAY - _dt.timedelta(days=3)
        exe = self._apply(eff)
        close = self._find(exe, 'UPDATE employee_org_assignments')[0]
        insert = self._find(exe, 'INSERT INTO employee_org_assignments')[0]
        assert eff in close.args[1], 'the outgoing assignment was not closed on the date'
        assert eff in insert.args[1], 'the incoming assignment did not start on the date'
        assert close.args[1][0] == insert.args[1][-1] == eff

    def test_the_close_no_longer_hardcodes_current_date(self):
        exe = self._apply(_TODAY - _dt.timedelta(days=3))
        sql = ' '.join(str(self._find(exe, 'UPDATE employee_org_assignments')[0].args[0]).split())
        assert 'CURRENT_DATE' not in sql, (
            'the boundary is back to "whenever this ran", which is CFL-4')

    def test_the_periods_do_not_overlap_under_half_open_arithmetic(self):
        """The actual CFL-4 property, expressed as Postgres would evaluate it."""
        eff = _TODAY - _dt.timedelta(days=3)
        exe = self._apply(eff)
        old_to = exe.call_args_list[0].args[1][0]
        new_from = self._find(exe, 'INSERT INTO employee_org_assignments')[0].args[1][-1]
        # [a, b) and [b, c) share no day, for any c > b.
        assert old_to == new_from
        assert not (new_from < old_to), 'the two periods overlap'

    def test_there_is_no_gap_either(self):
        """Abutting, not merely non-overlapping — an employee is never unplaced."""
        eff = _TODAY
        exe = self._apply(eff)
        old_to = exe.call_args_list[0].args[1][0]
        new_from = self._find(exe, 'INSERT INTO employee_org_assignments')[0].args[1][-1]
        assert (new_from - old_to).days == 0

    def test_def_42_2_the_manager_relationship_is_closed_WITH_an_end_date(self):
        """It set `is_current=FALSE` and nothing else, leaving a NULL end date —
        a closed relationship that reads as open to anything trusting the dates.
        Two such rows exist in the dev database."""
        eff = _TODAY - _dt.timedelta(days=2)
        exe = self._apply(eff)
        close = self._find(exe, 'UPDATE manager_relationships')[0]
        sql = ' '.join(str(close.args[0]).split())
        assert 'effective_to' in sql, 'DEF-42-2 has regressed — no end date is set'
        assert eff in close.args[1]

    def test_the_new_manager_relationship_starts_on_the_same_date(self):
        eff = _TODAY - _dt.timedelta(days=2)
        exe = self._apply(eff)
        ins = self._find(exe, 'INSERT INTO manager_relationships')[0]
        assert 'effective_from' in ' '.join(str(ins.args[0]).split())
        assert eff in ins.args[1]

    def test_a_pre_kan_189_request_with_no_date_still_applies_today(self):
        """NULL means 'apply on approval'. It must not crash or apply at epoch."""
        exe = self._apply(None)
        close = self._find(exe, 'UPDATE employee_org_assignments')[0]
        assert _TODAY in close.args[1]

    def test_a_manager_only_move_does_not_touch_the_relationship_twice(self):
        exe = self._apply(_TODAY, mgr='m-1', from_mgr='m-1')   # unchanged manager
        assert not self._find(exe, 'UPDATE manager_relationships')

    def test_everything_still_commits_as_one_unit(self):
        exe = self._apply(_TODAY)
        assert all(exe.inside), 'a dated write escaped the transaction (ADR-006)'


class TestEffectiveDateOverTheApi:
    """The route owes the user a specific 400, not an engine traceback."""

    def _post_eff(self, client, value):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query()), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.create_request', return_value='req-9') as mk:
            r = _post(client, '/api/org-change/request',
                      {'employee_id': 'emp-sub', 'manager_id': 'm-2', 'reason': 'x',
                       'effective_date': value})
        return r, mk

    def test_a_valid_date_reaches_the_engine_as_a_date_object(self, hr_client):
        chosen = _TODAY - _dt.timedelta(days=5)
        r, mk = self._post_eff(hr_client, chosen.isoformat())
        assert r.status_code == 200, r.get_json()
        assert mk.call_args.kwargs['effective_date'] == chosen

    def test_a_malformed_date_is_a_400_about_the_input(self, hr_client):
        r, mk = self._post_eff(hr_client, 'the third of never')
        assert r.status_code == 400
        assert 'valid date' in r.get_json()['error']
        mk.assert_not_called()

    def test_a_future_date_is_refused_with_the_reason(self, hr_client):
        r, mk = self._post_eff(hr_client, (_TODAY + _dt.timedelta(days=3)).isoformat())
        assert r.status_code == 400
        assert 'future' in r.get_json()['error'].lower()
        mk.assert_not_called()

    def test_too_far_back_is_refused_with_the_limit_named(self, hr_client):
        from app.services import org_change_service as svc
        back, _ = svc._dating_window('co-1')
        r, mk = self._post_eff(hr_client,
                               (_TODAY - _dt.timedelta(days=back + 5)).isoformat())
        assert r.status_code == 400
        assert str(back) in r.get_json()['error']
        mk.assert_not_called()

    def test_an_omitted_date_still_works_so_an_older_client_does_not_break(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query()), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.create_request', return_value='req-9') as mk:
            r = _post(hr_client, '/api/org-change/request',
                      {'employee_id': 'emp-sub', 'manager_id': 'm-2', 'reason': 'x'})
        assert r.status_code == 200
        assert mk.call_args.kwargs['effective_date'] is None   # engine defaults to today

    def test_prefill_hands_the_dialog_bounds_it_can_trust(self, hr_client):
        """The picker and the validator must agree — one authority, the server."""
        with hr_client.session_transaction() as s:
            s['company_id'] = 'co-1'
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query()), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.workflow_steps', return_value=[_role_step()]):
            r = hr_client.get('/api/org-change/prefill?subject=emp-sub')
        cfg = r.get_json()['effective_date']
        assert cfg['default'] == _TODAY.isoformat()
        # max is TODAY, not today+forward: a picker offering six months of dates
        # the server refuses one by one is a control that lies.
        assert cfg['max'] == _TODAY.isoformat()
        assert cfg['min'] < cfg['default']

    def test_the_dialog_renders_the_field_kan_185_left_out(self):
        with open('templates/org_change/_move_modal.html') as f:
            src = f.read()
        assert 'id="mv-effective"' in src and 'type="date"' in src
        assert 'for="mv-effective"' in src, 'the field has no label'
        assert 'aria-describedby' in src
        assert 'effective_date:' in src, 'the field is not sent to the server'

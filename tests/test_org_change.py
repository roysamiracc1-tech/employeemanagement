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
        # INSERT (employee_id, location_id, business_unit_id, functional_unit_id, cost_center_id)
        _emp, loc, bu, fu, cc = ins.args[1]
        return {'loc': loc, 'bu': bu, 'fu': fu, 'cc': cc}

    def test_business_unit_only_move_keeps_location_and_functional_unit(self):
        got = self._insert_params({'bu': 'bu-new', 'fu': None, 'loc': None})
        assert got == {'bu': 'bu-new', 'fu': 'fu-old', 'loc': 'loc-old', 'cc': 'cc-old'}, (
            'a BU-only move must not clear the location or functional unit')

    def test_location_only_move_keeps_the_units(self):
        got = self._insert_params({'bu': None, 'fu': None, 'loc': 'loc-new'})
        assert got == {'bu': 'bu-old', 'fu': 'fu-old', 'loc': 'loc-new', 'cc': 'cc-old'}

    def test_manager_only_move_keeps_the_whole_placement(self):
        got = self._insert_params({'bu': None, 'fu': None, 'loc': None})
        assert got == dict(self.CURRENT)

    def test_a_full_proposal_still_overrides_everything(self):
        got = self._insert_params({'bu': 'bu-new', 'fu': 'fu-new', 'loc': 'loc-new'})
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

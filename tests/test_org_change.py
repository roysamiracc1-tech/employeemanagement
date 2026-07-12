"""
Tests for the position-change (org-change) workflow.
All DB interactions are mocked.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session


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
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', return_value={'company_id': 'co-1'}), \
             patch('app.routes.org_change.employee_solid_manager', return_value='emp-lead'), \
             patch('app.routes.org_change.svc.create_request', return_value='req-1') as mk:
            r = _post(lead_client, '/api/org-change/request',
                      {'employee_id': 'emp-sub', 'manager_id': 'm-2', 'reason': 'growth'})
        assert r.status_code == 200
        assert json.loads(r.data)['id'] == 'req-1'
        mk.assert_called_once()

    def test_hr_can_move_anyone(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', return_value={'company_id': 'co-1'}), \
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
        exe = MagicMock()
        # query order: req, step, emp_name, subject_users
        qs = [_req_row(), _role_step(), {'n': 'Sub Ject'}, [{'id': 'u-sub'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc.notif, 'create_user_notification'):
            ok, status = svc.decide('req-1', HR_USER, 'reject', 'no')
        assert ok and status == 'REJECTED'
        assert any("REJECTED" in str(c.args[0]) for c in exe.call_args_list)

    def test_approve_non_final_advances_step(self):
        from app.services import org_change_service as svc
        exe = MagicMock()
        # req, step, emp_name, total(count=2), next_step, approver_users
        qs = [_req_row(step=1), _role_step(), {'n': 'Sub'}, {'c': 2},
              {'step_order': 2, 'approver_type': 'ROLE', 'approver_role': 'PORTAL_ADMIN',
               'approver_employee_id': None}, [{'id': 'u-pa'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc.notif, 'create_user_notification'):
            ok, status = svc.decide('req-1', HR_USER, 'approve', None)
        assert ok and status == 'PENDING'
        assert any("current_step" in str(c.args[0]) for c in exe.call_args_list)

    def test_approve_final_applies_and_approves(self):
        from app.services import org_change_service as svc
        exe = MagicMock()
        # req(step2), step, emp_name, total(count=2), subject_users
        qs = [_req_row(step=2), _role_step(), {'n': 'Sub'}, {'c': 2}, [{'id': 'u-sub'}]]
        with patch.object(svc, 'query', side_effect=qs), \
             patch.object(svc, 'execute', exe), \
             patch.object(svc, 'apply_change') as apply_mock, \
             patch.object(svc.notif, 'create_user_notification'):
            ok, status = svc.decide('req-1', HR_USER, 'approve', None)
        assert ok and status == 'APPROVED'
        apply_mock.assert_called_once_with('req-1')
        assert any("APPROVED" in str(c.args[0]) for c in exe.call_args_list)

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
        exe = MagicMock()
        # apply_change queries: request row (one), old cost centre (one)
        with patch.object(svc, 'query', side_effect=[req, {'cc': 'cc-1'}]), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        sqls = " ".join(str(c.args[0]) for c in exe.call_args_list)
        assert "employee_org_assignments" in sqls
        assert "manager_relationships" in sqls        # manager changed (m-2 != m-old)

    def test_apply_skips_manager_when_unchanged(self):
        from app.services import org_change_service as svc
        req = {'employee_id': 'emp-sub', 'from_manager_id': 'm-2',
               'bu': 'bu-1', 'fu': 'fu-1', 'loc': 'loc-1', 'mgr': 'm-2'}
        exe = MagicMock()
        with patch.object(svc, 'query', side_effect=[req, {'cc': None}]), \
             patch.object(svc, 'execute', exe):
            svc.apply_change('req-1')
        sqls = " ".join(str(c.args[0]) for c in exe.call_args_list)
        assert "manager_relationships" not in sqls    # manager unchanged → no re-point


class TestCreateRequest:
    def test_create_inserts_and_notifies(self):
        from app.services import org_change_service as svc
        ins = MagicMock(return_value={'id': 'req-9'})
        with patch.object(svc, 'current_placement', return_value={'bu': None, 'fu': None, 'loc': None, 'cc': None, 'mgr': 'm-old'}), \
             patch.object(svc, 'workflow_steps', return_value=[_role_step()]), \
             patch.object(svc, 'query', return_value=None), \
             patch.object(svc, 'insert_returning', ins), \
             patch.object(svc, 'execute'), \
             patch.object(svc, '_step_approver_user_ids', return_value=['u-hr']), \
             patch.object(svc, '_emp_name', return_value='Sub Ject'), \
             patch.object(svc.notif, 'create_user_notification') as notif_mock:
            rid = svc.create_request('co-1', 'emp-sub', 'u-lead',
                                     {'manager_id': 'm-2', 'business_unit_id': None,
                                      'functional_unit_id': None, 'location_id': None}, 'growth')
        assert rid == 'req-9'
        # notified step-1 approver AND requester
        assert notif_mock.call_count >= 2


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

"""
Integration tests for Organisation CRUD endpoints.
Verifies company-scoping: Tech Admin vs Portal Admin vs plain Employee.
All DB calls are mocked.
"""
import json
import pytest
from unittest.mock import patch, MagicMock, call

from tests.conftest import _set_session

# ── Shared fixtures ───────────────────────────────────────────────────────────

ACME_ID   = '709a1ece-0000-0000-0000-000000000001'
TELIA_ID  = '05a3fddb-0000-0000-0000-000000000001'
BU_ID     = 'bu000001-0000-0000-0000-000000000001'
LOC_ID    = 'loc00001-0000-0000-0000-000000000001'
FU_ID     = 'fu000001-0000-0000-0000-000000000001'

SAMPLE_BU  = {'id': BU_ID,  'name': 'Engineering', 'code': 'ENG',
               'description': 'Eng BU', 'emp_count': 5, 'company_id': ACME_ID}
SAMPLE_LOC = {'id': LOC_ID, 'name': 'London HQ', 'office_code': 'LDN',
               'city': 'London', 'country': 'UK', 'emp_count': 10, 'company_id': ACME_ID}
SAMPLE_FU  = {'id': FU_ID,  'name': 'Platform', 'code': 'PLT',
               'description': None, 'business_unit_id': BU_ID,
               'bu_name': 'Engineering', 'emp_count': 3, 'company_id': ACME_ID}


def portal_client(client, company_id=ACME_ID):
    _set_session(client, roles=['PORTAL_ADMIN', 'EMPLOYEE'])
    with client.session_transaction() as sess:
        sess['company_id']  = company_id
        sess['admin_company_id'] = None
    return client


def tech_admin_scoped(client, company_id=ACME_ID):
    """Tech Admin with a company context selected."""
    _set_session(client, roles=['SYSTEM_ADMIN', 'EMPLOYEE'])
    with client.session_transaction() as sess:
        sess['company_id']       = None
        sess['admin_company_id'] = company_id
    return client


# ─────────────────────────────────────────────────────────────────────────────
# GET list endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestOrgListEndpoints:
    def test_bu_list_requires_auth(self, client):
        r = client.get('/api/admin/org/business-units')
        assert r.status_code in (301, 302)

    def test_bu_list_blocked_for_employee(self, auth_client):
        r = auth_client.get('/api/admin/org/business-units')
        assert r.status_code == 302

    def test_bu_list_200_for_system_admin(self, admin_client):
        with patch('app.routes.admin.query', return_value=[SAMPLE_BU]):
            r = admin_client.get('/api/admin/org/business-units')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_loc_list_200_for_portal_admin(self, client):
        portal_client(client)
        with patch('app.routes.admin.query', return_value=[SAMPLE_LOC]):
            r = client.get('/api/admin/org/locations')
        assert r.status_code == 200

    def test_fu_list_200_for_portal_admin(self, client):
        portal_client(client)
        with patch('app.routes.admin.query', return_value=[SAMPLE_FU]):
            r = client.get('/api/admin/org/functional-units')
        assert r.status_code == 200

    def test_bu_list_passes_company_filter_for_portal_admin(self, client):
        """Query must include company_id filter when Portal Admin is logged in."""
        portal_client(client, ACME_ID)
        captured_sql = []

        def mock_query(sql, params=(), one=False):
            captured_sql.append(sql)
            return [SAMPLE_BU]

        with patch('app.routes.admin.query', side_effect=mock_query):
            r = client.get('/api/admin/org/business-units')
        assert r.status_code == 200
        assert any('company_id' in s for s in captured_sql), \
            "Portal Admin BU query must filter by company_id"

    def test_bu_list_no_company_filter_for_tech_admin_all_companies(self, admin_client):
        """Tech Admin with no company selected should see ALL BUs (no WHERE company_id)."""
        captured_sql = []

        def mock_query(sql, params=(), one=False):
            captured_sql.append((sql, params))
            return [SAMPLE_BU]

        with patch('app.routes.admin.query', side_effect=mock_query):
            r = admin_client.get('/api/admin/org/business-units')
        assert r.status_code == 200
        for sql, params in captured_sql:
            assert not params or ACME_ID not in str(params), \
                "Tech Admin with no company context should not filter by company_id"

    def test_bu_list_filters_when_tech_admin_selects_company(self, client):
        tech_admin_scoped(client, TELIA_ID)
        captured_params = []

        def mock_query(sql, params=(), one=False):
            captured_params.append(params)
            return [SAMPLE_BU]

        with patch('app.routes.admin.query', side_effect=mock_query):
            r = client.get('/api/admin/org/business-units')
        assert r.status_code == 200
        all_params_str = str(captured_params)
        assert TELIA_ID in all_params_str, \
            "Tech Admin with Telia context must pass Telia ID to query"


# ─────────────────────────────────────────────────────────────────────────────
# Company-scoped admin employees endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminEmployeesEndpoint:
    def test_requires_auth(self, client):
        r = client.get('/api/admin/employees')
        assert r.status_code in (301, 302)

    def test_blocked_for_plain_employee(self, auth_client):
        r = auth_client.get('/api/admin/employees')
        assert r.status_code == 302

    def test_returns_list_for_system_admin(self, admin_client):
        with patch('app.routes.admin.query', return_value=[]):
            r = admin_client.get('/api/admin/employees')
        assert r.status_code == 200
        assert json.loads(r.data) == []

    def test_returns_list_for_portal_admin(self, client):
        portal_client(client)
        with patch('app.routes.admin.query', return_value=[]):
            r = client.get('/api/admin/employees')
        assert r.status_code == 200

    def test_portal_admin_query_includes_company_filter(self, client):
        portal_client(client, ACME_ID)
        captured = []

        def mock_q(sql, params=(), one=False):
            captured.append((sql, params))
            return []

        with patch('app.routes.admin.query', side_effect=mock_q):
            client.get('/api/admin/employees')

        all_text = str(captured)
        assert 'company_id' in all_text, \
            "Portal Admin /api/admin/employees must filter by company_id"
        assert ACME_ID in all_text, \
            "Portal Admin query must use their own company_id"


# ─────────────────────────────────────────────────────────────────────────────
# BU CREATE (POST)
# ─────────────────────────────────────────────────────────────────────────────

class TestBUCreate:
    def _post(self, client, data):
        return client.post('/api/admin/org/business-units',
                           data=json.dumps(data),
                           content_type='application/json')

    def test_blocked_for_employee(self, auth_client):
        r = self._post(auth_client, {'name': 'Test BU'})
        assert r.status_code == 302

    def test_missing_name_returns_400(self, admin_client):
        with patch('app.routes.admin.query', return_value=None), \
             patch('app.routes.admin.insert_returning', return_value={'id': BU_ID}):
            r = self._post(admin_client, {'name': ''})
        assert r.status_code == 400

    def test_valid_create_returns_ok(self, admin_client):
        def mock_q(sql, params=(), one=False):
            return None  # no conflict on code check
        with patch('app.routes.admin.query', side_effect=mock_q), \
             patch('app.routes.admin.insert_returning', return_value={'id': BU_ID}):
            r = self._post(admin_client, {'name': 'New BU', 'code': 'NBU'})
        assert r.status_code == 200
        assert json.loads(r.data)['ok'] is True

    def test_portal_admin_create_includes_company_id(self, client):
        portal_client(client, ACME_ID)
        captured_inserts = []

        def mock_insert(sql, params):
            captured_inserts.append(params)
            return {'id': BU_ID}

        with patch('app.routes.admin.query', return_value=None), \
             patch('app.routes.admin.insert_returning', side_effect=mock_insert):
            r = self._post(client, {'name': 'Portal BU'})

        assert r.status_code == 200
        assert any(ACME_ID in str(p) for p in captured_inserts), \
            "Portal Admin BU insert must include their company_id"

    def test_duplicate_code_returns_409(self, admin_client):
        with patch('app.routes.admin.query', return_value={'id': 'existing'}):
            r = self._post(admin_client, {'name': 'BU', 'code': 'TAKEN'})
        assert r.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# BU UPDATE (PUT)
# ─────────────────────────────────────────────────────────────────────────────

class TestBUUpdate:
    def _put(self, client, bu_id, data):
        return client.put(f'/api/admin/org/business-units/{bu_id}',
                          data=json.dumps(data),
                          content_type='application/json')

    def test_blocked_for_employee(self, auth_client):
        r = self._put(auth_client, BU_ID, {'name': 'X'})
        assert r.status_code == 302

    def test_system_admin_can_update_any_bu(self, admin_client):
        with patch('app.routes.admin.query', return_value=None), \
             patch('app.routes.admin.execute'):
            r = self._put(admin_client, BU_ID, {'name': 'Updated'})
        assert r.status_code == 200

    def test_portal_admin_blocked_from_other_company_bu(self, client):
        portal_client(client, TELIA_ID)  # Telia admin

        def mock_q(sql, params=(), one=False):
            # Ownership check: return None (not owned by Telia)
            if 'company_id' in sql:
                return None
            return None

        with patch('app.routes.admin.query', side_effect=mock_q):
            r = self._put(client, BU_ID, {'name': 'Steal BU'})
        assert r.status_code == 403, \
            "Portal Admin must not update BUs from a different company"


# ─────────────────────────────────────────────────────────────────────────────
# BU DELETE
# ─────────────────────────────────────────────────────────────────────────────

class TestBUDelete:
    def _delete(self, client, bu_id):
        return client.delete(f'/api/admin/org/business-units/{bu_id}')

    def test_blocked_for_employee(self, auth_client):
        r = self._delete(auth_client, BU_ID)
        assert r.status_code == 302

    def test_delete_with_assigned_employees_returns_409(self, admin_client):
        def mock_q(sql, params=(), one=False):
            if 'company_id' in sql:
                return {'c': 0} if one else []  # ownership OK for tech admin (no filter)
            if 'COUNT' in sql:
                return {'c': 5} if one else [{'c': 5}]  # 5 employees assigned
            return None if one else []

        with patch('app.routes.admin.query', side_effect=mock_q):
            r = self._delete(admin_client, BU_ID)
        assert r.status_code == 409, "Delete must return 409 when employees are assigned"

    def test_delete_empty_bu_succeeds(self, admin_client):
        def mock_q(sql, params=(), one=False):
            if 'COUNT' in sql:
                return {'c': 0} if one else [{'c': 0}]
            return None if one else []

        with patch('app.routes.admin.query', side_effect=mock_q), \
             patch('app.routes.admin.execute'):
            r = self._delete(admin_client, BU_ID)
        assert r.status_code == 200
        assert json.loads(r.data)['ok'] is True


# ─────────────────────────────────────────────────────────────────────────────
# Location CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestLocationCRUD:
    def test_create_location_valid(self, admin_client):
        with patch('app.routes.admin.query', return_value=None), \
             patch('app.routes.admin.insert_returning', return_value={'id': LOC_ID}):
            r = admin_client.post('/api/admin/org/locations',
                                  data=json.dumps({'name': 'Paris', 'office_code': 'PAR'}),
                                  content_type='application/json')
        assert r.status_code == 200

    def test_create_location_missing_name_400(self, admin_client):
        with patch('app.routes.admin.query', return_value=None), \
             patch('app.routes.admin.insert_returning', return_value={'id': LOC_ID}):
            r = admin_client.post('/api/admin/org/locations',
                                  data=json.dumps({'office_code': 'XYZ'}),
                                  content_type='application/json')
        assert r.status_code == 400

    def test_delete_location_with_employees_409(self, admin_client):
        def mock_q(sql, params=(), one=False):
            if 'COUNT' in sql:
                return {'c': 3} if one else []
            return None if one else []

        with patch('app.routes.admin.query', side_effect=mock_q):
            r = admin_client.delete(f'/api/admin/org/locations/{LOC_ID}')
        assert r.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# Functional Unit CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestFunctionalUnitCRUD:
    def test_create_fu_valid(self, admin_client):
        with patch('app.routes.admin.query', return_value=None), \
             patch('app.routes.admin.insert_returning', return_value={'id': FU_ID}):
            r = admin_client.post('/api/admin/org/functional-units',
                                  data=json.dumps({'name': 'DevOps', 'code': 'DVS'}),
                                  content_type='application/json')
        assert r.status_code == 200

    def test_create_fu_duplicate_code_409(self, admin_client):
        with patch('app.routes.admin.query', return_value={'id': 'existing'}):
            r = admin_client.post('/api/admin/org/functional-units',
                                  data=json.dumps({'name': 'X', 'code': 'TAKEN'}),
                                  content_type='application/json')
        assert r.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# Company context switch
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanyContextSwitch:
    def test_switch_requires_system_admin(self, auth_client):
        r = auth_client.post('/api/admin/switch-company',
                             data=json.dumps({'company_id': TELIA_ID}),
                             content_type='application/json')
        assert r.status_code == 302

    def test_switch_portal_admin_blocked(self, client):
        portal_client(client)
        r = client.post('/api/admin/switch-company',
                        data=json.dumps({'company_id': TELIA_ID}),
                        content_type='application/json')
        assert r.status_code == 302

    def test_switch_sets_admin_company_id_in_session(self, admin_client):
        r = admin_client.post('/api/admin/switch-company',
                              data=json.dumps({'company_id': TELIA_ID}),
                              content_type='application/json')
        assert r.status_code == 200
        with admin_client.session_transaction() as sess:
            assert sess.get('admin_company_id') == TELIA_ID

    def test_switch_to_none_clears_filter(self, admin_client):
        # First set a company
        admin_client.post('/api/admin/switch-company',
                          data=json.dumps({'company_id': TELIA_ID}),
                          content_type='application/json')
        # Then clear it
        r = admin_client.post('/api/admin/switch-company',
                              data=json.dumps({'company_id': None}),
                              content_type='application/json')
        assert r.status_code == 200
        with admin_client.session_transaction() as sess:
            assert not sess.get('admin_company_id')


# ─────────────────────────────────────────────────────────────────────────────
# Role & Feature permissions matrix
# ─────────────────────────────────────────────────────────────────────────────

class TestRoleFeaturePermissions:
    def test_blocked_for_portal_admin(self, client):
        portal_client(client)
        r = client.get('/api/admin/roles/features')
        assert r.status_code == 302

    def test_blocked_for_employee(self, auth_client):
        r = auth_client.get('/api/admin/roles/features')
        assert r.status_code == 302

    def test_returns_matrix_for_system_admin(self, admin_client):
        mock_roles    = [{'id': 'r1', 'name': 'EMPLOYEE', 'description': ''}]
        mock_features = [{'id': 'f1', 'code': 'employee_profiles', 'label': 'Employees', 'description': ''}]
        mock_access   = [{'role_id': 'r1', 'feature_id': 'f1',
                          'can_read': True, 'can_write': False, 'can_delete': False}]

        def mock_q(sql, params=(), one=False):
            if 'portal_features' in sql:
                return mock_features
            if 'role_feature_access' in sql:
                return mock_access
            if 'roles' in sql:
                return mock_roles
            return []

        with patch('app.routes.admin.query', side_effect=mock_q):
            r = admin_client.get('/api/admin/roles/features')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'roles' in data
        assert 'features' in data
        assert 'matrix' in data

    def test_update_feature_access_requires_system_admin(self, auth_client):
        r = auth_client.post('/api/admin/roles/feature-access',
                             data=json.dumps({'role_id': 'r1', 'feature_id': 'f1',
                                              'can_read': True}),
                             content_type='application/json')
        assert r.status_code == 302

    def test_update_feature_access_succeeds(self, admin_client):
        with patch('app.routes.admin.execute'):
            r = admin_client.post('/api/admin/roles/feature-access',
                                  data=json.dumps({'role_id': 'r1', 'feature_id': 'f1',
                                                   'can_read': True, 'can_write': False,
                                                   'can_delete': False}),
                                  content_type='application/json')
        assert r.status_code == 200
        assert json.loads(r.data)['ok'] is True

    def test_update_missing_ids_returns_400(self, admin_client):
        with patch('app.routes.admin.execute'):
            r = admin_client.post('/api/admin/roles/feature-access',
                                  data=json.dumps({'can_read': True}),
                                  content_type='application/json')
        assert r.status_code == 400

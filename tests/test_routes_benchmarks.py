"""Unit tests for the tech benchmarks route."""
import json
import pytest
from unittest.mock import patch


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sa_client(app):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id']     = 'user-sa-001'
            s['employee_id'] = 'emp-sa-001'
            s['company_id']  = None
            s['roles']       = ['SYSTEM_ADMIN']
            s['user_name']   = 'Super Admin'
        yield c


_FAKE_ROWS = [
    {'technology': 'Python',     'usage_pct': 57.9, 'context': 'all_respondents', 'rank_in_category': 1},
    {'technology': 'JavaScript', 'usage_pct': 66.0, 'context': 'all_respondents', 'rank_in_category': 2},
]

_FAKE_OVERLAY = [
    {'technology': 'Python', 'emp_count': 8, 'company_pct': 53.3},
]

_FAKE_CATEGORIES = [
    {'category': 'Programming Languages', 'item_count': 42, 'survey_year': 2025},
    {'category': 'Databases', 'item_count': 30, 'survey_year': 2025},
]


# ── page access ───────────────────────────────────────────────────────────────

class TestBenchmarksAccess:
    def test_requires_login(self, client):
        r = client.get('/admin/benchmarks')
        assert r.status_code == 302

    def test_plain_employee_blocked(self, auth_client):
        r = auth_client.get('/admin/benchmarks')
        assert r.status_code == 302

    def test_portal_admin_blocked(self, app):
        with app.test_client() as c:
            with c.session_transaction() as s:
                s['user_id'] = 'u'; s['employee_id'] = 'e'
                s['company_id'] = 'co-001'; s['roles'] = ['PORTAL_ADMIN']
                s['user_name'] = 'PA'
            r = c.get('/admin/benchmarks')
            assert r.status_code == 302

    def test_system_admin_can_access(self, sa_client):
        with patch('app.routes.benchmarks.query', return_value=[]):
            r = sa_client.get('/admin/benchmarks')
            assert r.status_code == 200


# ── API data ──────────────────────────────────────────────────────────────────

class TestBenchmarksAPI:
    def test_requires_system_admin(self, auth_client):
        r = auth_client.get('/api/admin/benchmarks?category=Programming Languages')
        assert r.status_code == 302

    def test_returns_benchmark_rows(self, sa_client):
        def _query(sql, params=(), one=False):
            if 'survey_benchmarks' in sql:
                return _FAKE_ROWS
            return {'n': 0} if one else []

        with patch('app.routes.benchmarks.query', side_effect=_query):
            r = sa_client.get('/api/admin/benchmarks?category=Programming Languages&year=2025')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['category'] == 'Programming Languages'
            assert d['year'] == 2025
            assert len(d['rows']) == 2
            assert d['rows'][0]['technology'] == 'Python'
            assert d['source'] == 'Stack Overflow Developer Survey'

    def test_overlay_returned_when_company_selected(self, sa_client):
        def _query(sql, params=(), one=False):
            if 'survey_benchmarks' in sql:
                return _FAKE_ROWS
            if 'employee_skills' in sql:
                # Skill coverage query — must come before generic COUNT check
                return _FAKE_OVERLAY
            if 'COUNT' in sql:
                # total_emp count query (both instances)
                return {'n': 15} if one else [{'n': 15}]
            return [] if not one else {}

        with patch('app.routes.benchmarks.query', side_effect=_query):
            r = sa_client.get(
                '/api/admin/benchmarks?category=Programming Languages'
                '&year=2025&company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert len(d['overlay']) > 0
            assert d['overlay'][0]['technology'] == 'Python'

    def test_no_overlay_for_non_skill_category(self, sa_client):
        def _query(sql, params=(), one=False):
            if 'survey_benchmarks' in sql:
                return [{'technology': 'Stack Overflow', 'usage_pct': 84.2,
                          'context': 'all_respondents', 'rank_in_category': 1}]
            return [] if not one else {}

        with patch('app.routes.benchmarks.query', side_effect=_query):
            r = sa_client.get(
                '/api/admin/benchmarks?category=Community Platforms'
                '&year=2025&company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['overlay'] == []   # Community Platforms is not a skill category

    def test_categories_endpoint(self, sa_client):
        with patch('app.routes.benchmarks.query', return_value=_FAKE_CATEGORIES):
            r = sa_client.get('/api/admin/benchmarks/categories')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert any(c['category'] == 'Programming Languages' for c in d)

    def test_os_personal_context_filter(self, sa_client):
        def _query(sql, params=(), one=False):
            if 'survey_benchmarks' in sql:
                # Verify 'personal' context was passed
                assert 'personal' in str(params)
                return []
            return [] if not one else {}

        with patch('app.routes.benchmarks.query', side_effect=_query):
            sa_client.get(
                '/api/admin/benchmarks?category=Operating Systems'
                '&year=2025&context=personal')

    def test_data_has_correct_shape(self, sa_client):
        def _query(sql, params=(), one=False):
            if 'survey_benchmarks' in sql:
                return _FAKE_ROWS
            return {'n': 0} if one else []

        with patch('app.routes.benchmarks.query', side_effect=_query):
            r = sa_client.get('/api/admin/benchmarks?category=Databases&year=2025')
            d = json.loads(r.data)
            row = d['rows'][0]
            assert 'technology' in row
            assert 'usage_pct'  in row
            assert 'context'    in row

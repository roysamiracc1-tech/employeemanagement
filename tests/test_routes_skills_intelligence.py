"""Unit tests for the Skills Intelligence routes."""
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


@pytest.fixture
def pa_client(app):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id']     = 'user-pa-001'
            s['employee_id'] = 'emp-pa-001'
            s['company_id']  = 'co-001'
            s['roles']       = ['PORTAL_ADMIN']
            s['user_name']   = 'Portal Admin'
        yield c


@pytest.fixture
def hr_client(app):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id']     = 'user-hr-001'
            s['employee_id'] = 'emp-hr-001'
            s['company_id']  = 'co-001'
            s['roles']       = ['HR_ADMIN']
            s['user_name']   = 'HR Admin'
        yield c


_FAKE_KPI = {
    'total_employees': 100, 'emps_with_skills': 80, 'total_skill_entries': 900,
    'unique_skills': 30, 'coverage_pct': 80.0, 'validation_rate': 60.0, 'avg_yoe': 3.4,
}
_FAKE_GAPS = [
    {'technology': 'Python',     'category': 'Programming Languages',
     'bench_pct': 57.9, 'company_pct': 68.0, 'gap': -10.1, 'signal': 'strength',
     'desired_pct': 50.0, 'admired_pct': 72.0, 'sankey_role': 'both', 'rank': 1},
    {'technology': 'JavaScript', 'category': 'Programming Languages',
     'bench_pct': 66.0, 'company_pct': 30.0, 'gap': 36.0, 'signal': 'gap',
     'desired_pct': 40.0, 'admired_pct': 55.0, 'sankey_role': 'worked_with', 'rank': 2},
]
_FAKE_HEATMAP = {
    'skills': ['Python', 'JavaScript'],
    'levels': ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
    'data': {'Beginner': [5, 8], 'Intermediate': [20, 25], 'Advanced': [30, 20], 'Expert': [10, 5]},
}
_FAKE_TRENDS = [
    {'technology': 'Rust', 'category': 'Programming Languages',
     'desired_pct': 28.0, 'company_pct': 5.0, 'opportunity_score': 23.0,
     'sankey_role': 'want_to_work_with', 'quadrant': 'invest'},
]
_FAKE_COVERAGE = [
    {'category': 'Backend',  'emps_with_skill': 80, 'skills_covered': 10, 'coverage_pct': 80.0},
    {'category': 'Frontend', 'emps_with_skill': 60, 'skills_covered': 6,  'coverage_pct': 60.0},
]
_FAKE_JOB_COVERAGE = [
    {'job_title': 'Software Engineer', 'headcount': 40, 'with_skills': 35,
     'unique_skills': 8, 'coverage_pct': 87.5},
]
_FAKE_VALIDATION = [
    {'validation_status': 'VALIDATED',                  'cnt': 540},
    {'validation_status': 'PENDING_MANAGER_VALIDATION', 'cnt': 225},
    {'validation_status': 'SELF_ASSESSED',              'cnt': 180},
    {'validation_status': 'REJECTED',                   'cnt': 45},
]
_FAKE_GROWTH = [
    {'month': '2025-10', 'new_entries': 120},
    {'month': '2025-11', 'new_entries': 95},
    {'month': '2025-12', 'new_entries': 140},
]


# ── page access ───────────────────────────────────────────────────────────────

class TestPageAccess:
    def test_requires_login(self, client):
        r = client.get('/admin/skills-intelligence')
        assert r.status_code == 302

    def test_plain_employee_blocked(self, auth_client):
        r = auth_client.get('/admin/skills-intelligence')
        assert r.status_code == 302

    def test_sa_always_allowed(self, sa_client):
        with patch('app.routes.skills_intelligence.query', return_value=[]):
            r = sa_client.get('/admin/skills-intelligence')
            assert r.status_code == 200

    def test_portal_admin_sees_locked_when_disabled(self, pa_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=False):
            r = pa_client.get('/admin/skills-intelligence')
            assert r.status_code == 200
            assert b'Not Enabled' in r.data or b'not enabled' in r.data.lower()

    def test_portal_admin_allowed_when_enabled(self, pa_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=True):
            r = pa_client.get('/admin/skills-intelligence')
            assert r.status_code == 200

    def test_hr_admin_allowed_when_si_enabled(self, hr_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=True):
            r = hr_client.get('/admin/skills-intelligence')
            assert r.status_code == 200

    def test_hr_admin_sees_locked_when_si_disabled(self, hr_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=False):
            r = hr_client.get('/admin/skills-intelligence')
            assert r.status_code == 200
            assert b'not enabled' in r.data.lower() or b'Not Enabled' in r.data


# ── KPI endpoint ──────────────────────────────────────────────────────────────

class TestKpiEndpoint:
    def test_sa_gets_kpi(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_kpi_summary', return_value=_FAKE_KPI):
            r = sa_client.get('/api/admin/skills-intelligence/kpi?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['total_employees'] == 100
            assert d['coverage_pct'] == 80.0

    def test_blocked_when_feature_disabled(self, pa_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=False):
            r = pa_client.get('/api/admin/skills-intelligence/kpi?company_id=co-001')
            assert r.status_code == 403

    def test_hr_gets_kpi_when_si_enabled(self, hr_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_kpi_summary', return_value=_FAKE_KPI):
            r = hr_client.get('/api/admin/skills-intelligence/kpi?company_id=co-001')
            assert r.status_code == 200


# ── Gap analysis endpoint ─────────────────────────────────────────────────────

class TestGapsEndpoint:
    def test_returns_gaps(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_benchmark_gaps', return_value=_FAKE_GAPS):
            r = sa_client.get('/api/admin/skills-intelligence/gaps?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert len(d) == 2
            assert d[0]['technology'] == 'Python'
            assert d[0]['signal'] == 'strength'
            assert d[1]['signal'] == 'gap'

    def test_gap_shape(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_benchmark_gaps', return_value=_FAKE_GAPS):
            r = sa_client.get('/api/admin/skills-intelligence/gaps?company_id=co-001')
            row = json.loads(r.data)[0]
            assert 'technology' in row
            assert 'bench_pct'  in row
            assert 'company_pct' in row
            assert 'gap'        in row
            assert 'signal'     in row


# ── Heatmap endpoint ──────────────────────────────────────────────────────────

class TestHeatmapEndpoint:
    def test_returns_heatmap(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_proficiency_heatmap', return_value=_FAKE_HEATMAP):
            r = sa_client.get('/api/admin/skills-intelligence/heatmap?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert 'skills' in d and 'levels' in d and 'data' in d
            assert len(d['skills']) == 2


# ── Trends endpoint ───────────────────────────────────────────────────────────

class TestTrendsEndpoint:
    def test_returns_trends(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_trend_alignment', return_value=_FAKE_TRENDS):
            r = sa_client.get('/api/admin/skills-intelligence/trends?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d[0]['technology'] == 'Rust'
            assert d[0]['quadrant'] == 'invest'


# ── Coverage endpoint ─────────────────────────────────────────────────────────

class TestCoverageEndpoint:
    def test_returns_coverage(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_category_coverage', return_value=_FAKE_COVERAGE):
            r = sa_client.get('/api/admin/skills-intelligence/coverage?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert len(d) == 2
            assert d[0]['category'] == 'Backend'


# ── Job-coverage endpoint ─────────────────────────────────────────────────────

class TestJobCoverageEndpoint:
    def test_returns_job_coverage(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_job_title_coverage', return_value=_FAKE_JOB_COVERAGE):
            r = sa_client.get('/api/admin/skills-intelligence/job-coverage?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d[0]['job_title'] == 'Software Engineer'


# ── Validation endpoint ───────────────────────────────────────────────────────

class TestValidationEndpoint:
    def test_returns_funnel(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_validation_funnel', return_value=_FAKE_VALIDATION):
            r = sa_client.get('/api/admin/skills-intelligence/validation?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            statuses = {row['validation_status'] for row in d}
            assert 'VALIDATED' in statuses


# ── Growth endpoint ───────────────────────────────────────────────────────────

class TestGrowthEndpoint:
    def test_returns_growth(self, sa_client):
        with patch('app.routes.skills_intelligence._check_si_company_access', return_value=(True, None)), \
             patch('app.routes.skills_intelligence.svc.get_skill_growth', return_value=_FAKE_GROWTH):
            r = sa_client.get('/api/admin/skills-intelligence/growth?company_id=co-001')
            assert r.status_code == 200
            d = json.loads(r.data)
            assert len(d) == 3
            assert d[0]['month'] == '2025-10'


# ── HR toggle endpoint ────────────────────────────────────────────────────────

class TestHrToggleEndpoint:
    def test_requires_feature_write_access(self, auth_client):
        # Plain EMPLOYEE has no SI access at all — should be redirected
        r = auth_client.post('/api/admin/skills-intelligence/toggle-hr',
                             json={'enabled': True})
        assert r.status_code == 302

    def test_portal_admin_can_enable(self, pa_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=True), \
             patch('app.routes.skills_intelligence.query') as mock_q, \
             patch('app.routes.skills_intelligence.execute') as mock_e:
            mock_q.return_value = {'id': 'feat-id-001'}
            r = pa_client.post('/api/admin/skills-intelligence/toggle-hr',
                               json={'enabled': True})
            assert r.status_code == 200
            d = json.loads(r.data)
            assert d['enabled_for_hr'] is True

    def test_blocked_when_feature_not_enabled(self, pa_client):
        with patch('app.routes.skills_intelligence._si_enabled', return_value=False):
            r = pa_client.post('/api/admin/skills-intelligence/toggle-hr',
                               json={'enabled': True})
            assert r.status_code == 403


# ── Feature gate helpers ──────────────────────────────────────────────────────

class TestFeatureGateHelpers:
    def test_si_enabled_returns_false_for_no_company(self, app):
        with app.app_context():
            from app.routes.skills_intelligence import _si_enabled
            assert _si_enabled('') is False
            assert _si_enabled(None) is False

    def test_si_enabled_returns_false_for_none(self, app):
        with app.app_context():
            from app.routes.skills_intelligence import _si_enabled
            assert _si_enabled(None) is False

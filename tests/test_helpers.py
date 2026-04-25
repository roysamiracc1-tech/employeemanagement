"""
Unit tests for app/helpers.py.
Pure logic functions are tested directly; DB-dependent functions mock app.db.query.
"""
import datetime
import os
import pytest
from unittest.mock import patch, MagicMock, call


# ── rule_label ────────────────────────────────────────────────────────────────

from app.helpers import rule_label


class TestRuleLabel:
    def test_gender_eq_female(self):
        assert rule_label({'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'}) == 'Gender: Female'

    def test_gender_eq_male(self):
        assert rule_label({'rule_type': 'GENDER_EQ', 'rule_value': 'MALE'}) == 'Gender: Male'

    def test_min_tenure_months_plural(self):
        assert rule_label({'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '6'}) == 'Min tenure: 6 months'

    def test_min_tenure_years_singular(self):
        assert rule_label({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '1'}) == 'Min tenure: 1 year'

    def test_min_tenure_years_plural(self):
        assert rule_label({'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '3'}) == 'Min tenure: 3 years'

    def test_unknown_rule_returns_type(self):
        assert rule_label({'rule_type': 'UNKNOWN_RULE', 'rule_value': 'x'}) == 'UNKNOWN_RULE'


# ── build_nested ──────────────────────────────────────────────────────────────

from app.helpers import build_nested


class TestBuildNested:
    def test_single_root_no_children(self):
        flat = [{'id': 'a', 'manager_id': None, 'name': 'Root'}]
        result = build_nested(flat)
        assert len(result) == 1
        assert result[0]['id'] == 'a'
        assert result[0]['children'] == []

    def test_root_with_one_child(self):
        flat = [
            {'id': 'a', 'manager_id': None,  'name': 'Root'},
            {'id': 'b', 'manager_id': 'a',   'name': 'Child'},
        ]
        result = build_nested(flat)
        assert len(result) == 1
        assert len(result[0]['children']) == 1
        assert result[0]['children'][0]['id'] == 'b'

    def test_two_roots(self):
        flat = [
            {'id': 'a', 'manager_id': None, 'name': 'Root A'},
            {'id': 'b', 'manager_id': None, 'name': 'Root B'},
        ]
        result = build_nested(flat)
        assert len(result) == 2

    def test_three_levels_deep(self):
        flat = [
            {'id': 'a', 'manager_id': None, 'name': 'L1'},
            {'id': 'b', 'manager_id': 'a',  'name': 'L2'},
            {'id': 'c', 'manager_id': 'b',  'name': 'L3'},
        ]
        result = build_nested(flat)
        assert result[0]['children'][0]['children'][0]['id'] == 'c'

    def test_orphan_node_becomes_root(self):
        flat = [{'id': 'x', 'manager_id': 'nonexistent', 'name': 'Orphan'}]
        result = build_nested(flat)
        assert len(result) == 1
        assert result[0]['id'] == 'x'

    def test_empty_input(self):
        assert build_nested([]) == []


# ── next_employee_number ──────────────────────────────────────────────────────

from app.helpers import next_employee_number


class TestNextEmployeeNumber:
    @patch('app.helpers.query')
    def test_first_employee(self, mock_query):
        mock_query.return_value = {'n': 0}
        assert next_employee_number() == 'EMP-001'

    @patch('app.helpers.query')
    def test_increments_correctly(self, mock_query):
        mock_query.return_value = {'n': 12}
        assert next_employee_number() == 'EMP-013'

    @patch('app.helpers.query')
    def test_zero_pads_to_three_digits(self, mock_query):
        mock_query.return_value = {'n': 99}
        assert next_employee_number() == 'EMP-100'


# ── employee_solid_manager ────────────────────────────────────────────────────

from app.helpers import employee_solid_manager


class TestEmployeeSolidManager:
    @patch('app.helpers.query')
    def test_returns_manager_id_when_found(self, mock_query):
        mock_query.return_value = {'manager_id': 'mgr-001'}
        result = employee_solid_manager('emp-001')
        assert result == 'mgr-001'

    @patch('app.helpers.query')
    def test_returns_none_when_not_found(self, mock_query):
        mock_query.return_value = None
        result = employee_solid_manager('emp-001')
        assert result is None


# ── used_days ─────────────────────────────────────────────────────────────────

from app.helpers import used_days


class TestUsedDays:
    @patch('app.helpers.query')
    def test_returns_sum(self, mock_query):
        mock_query.return_value = {'used': 7}
        assert used_days('emp-001', 'vt-001', 2026) == 7

    @patch('app.helpers.query')
    def test_returns_zero_when_none(self, mock_query):
        mock_query.return_value = None
        assert used_days('emp-001', 'vt-001', 2026) == 0

    @patch('app.helpers.query')
    def test_returns_zero_when_used_is_zero(self, mock_query):
        mock_query.return_value = {'used': 0}
        assert used_days('emp-001', 'vt-001', 2026) == 0


# ── is_direct_report ─────────────────────────────────────────────────────────

from app.helpers import is_direct_report


class TestIsDirectReport:
    @patch('app.helpers.query')
    def test_true_when_row_returned(self, mock_query):
        mock_query.return_value = {'1': 1}
        assert is_direct_report('mgr-001', 'emp-001') is True

    @patch('app.helpers.query')
    def test_false_when_no_row(self, mock_query):
        mock_query.return_value = None
        assert is_direct_report('mgr-001', 'emp-999') is False


# ── vacation_types_for_employee — rule evaluation ─────────────────────────────

from app.helpers import vacation_types_for_employee


class TestVacationEligibilityRules:
    def _emp_info(self, gender='FEMALE', join_date=None):
        if join_date is None:
            join_date = datetime.date.today() - datetime.timedelta(days=365 * 5)
        return {'gender': gender, 'join_date': join_date, 'company_id': 'co-001'}

    def _vt(self, vt_id='vt-001'):
        return {
            'id': vt_id, 'name': 'Test Leave', 'description': '',
            'max_days_per_year': 10, 'is_paid': True,
            'color': '#000', 'scope': 'Company-wide',
        }

    @patch('app.helpers.query')
    def test_gender_eq_passes_for_matching_gender(self, mock_query):
        mock_query.side_effect = [
            self._emp_info(gender='FEMALE'),           # emp_info
            [self._vt()],                              # vacation types SQL
            [{'vacation_type_id': 'vt-001', 'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'}],  # rules
        ]
        result = vacation_types_for_employee('emp-001')
        assert len(result) == 1
        assert result[0]['id'] == 'vt-001'

    @patch('app.helpers.query')
    def test_gender_eq_filters_out_wrong_gender(self, mock_query):
        mock_query.side_effect = [
            self._emp_info(gender='MALE'),
            [self._vt()],
            [{'vacation_type_id': 'vt-001', 'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'}],
        ]
        result = vacation_types_for_employee('emp-001')
        assert result == []

    @patch('app.helpers.query')
    def test_min_tenure_months_passes_when_met(self, mock_query):
        join = datetime.date.today() - datetime.timedelta(days=200)  # ~6.5 months
        mock_query.side_effect = [
            self._emp_info(join_date=join),
            [self._vt()],
            [{'vacation_type_id': 'vt-001', 'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '6'}],
        ]
        result = vacation_types_for_employee('emp-001')
        assert len(result) == 1

    @patch('app.helpers.query')
    def test_min_tenure_months_filtered_when_not_met(self, mock_query):
        join = datetime.date.today() - datetime.timedelta(days=30)  # ~1 month
        mock_query.side_effect = [
            self._emp_info(join_date=join),
            [self._vt()],
            [{'vacation_type_id': 'vt-001', 'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '6'}],
        ]
        result = vacation_types_for_employee('emp-001')
        assert result == []

    @patch('app.helpers.query')
    def test_min_tenure_years_passes_when_met(self, mock_query):
        join = datetime.date.today() - datetime.timedelta(days=365 * 4)
        mock_query.side_effect = [
            self._emp_info(join_date=join),
            [self._vt()],
            [{'vacation_type_id': 'vt-001', 'rule_type': 'MIN_TENURE_YEARS', 'rule_value': '3'}],
        ]
        result = vacation_types_for_employee('emp-001')
        assert len(result) == 1

    @patch('app.helpers.query')
    def test_multiple_rules_all_must_pass(self, mock_query):
        join = datetime.date.today() - datetime.timedelta(days=30)
        mock_query.side_effect = [
            self._emp_info(gender='FEMALE', join_date=join),
            [self._vt()],
            [
                {'vacation_type_id': 'vt-001', 'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'},
                {'vacation_type_id': 'vt-001', 'rule_type': 'MIN_TENURE_MONTHS', 'rule_value': '6'},
            ],
        ]
        result = vacation_types_for_employee('emp-001')
        assert result == []  # Gender passes but tenure fails → excluded

    @patch('app.helpers.query')
    def test_no_rules_means_all_eligible(self, mock_query):
        mock_query.side_effect = [
            self._emp_info(),
            [self._vt()],
            [],  # no rules
        ]
        result = vacation_types_for_employee('emp-001')
        assert len(result) == 1

    @patch('app.helpers.query')
    def test_returns_empty_when_employee_not_found(self, mock_query):
        mock_query.return_value = None
        result = vacation_types_for_employee('nonexistent')
        assert result == []

    @patch('app.helpers.query')
    def test_rule_labels_attached_to_eligible_types(self, mock_query):
        mock_query.side_effect = [
            self._emp_info(gender='FEMALE'),
            [self._vt()],
            [{'vacation_type_id': 'vt-001', 'rule_type': 'GENDER_EQ', 'rule_value': 'FEMALE'}],
        ]
        result = vacation_types_for_employee('emp-001')
        assert 'rule_labels' in result[0]
        assert result[0]['rule_labels'] == ['Gender: Female']


# ── save_logo ─────────────────────────────────────────────────────────────────

from app.helpers import save_logo


class TestSaveLogo:
    def test_returns_none_for_empty_file(self):
        mock_file = MagicMock()
        mock_file.filename = ''
        assert save_logo(mock_file) is None

    def test_returns_none_for_none_input(self):
        assert save_logo(None) is None

    def test_rejects_disallowed_extension(self):
        mock_file = MagicMock()
        mock_file.filename = 'logo.exe'
        assert save_logo(mock_file) is None

    @patch('app.helpers.os.makedirs')
    @patch('app.helpers.uuid')
    def test_saves_file_and_returns_url(self, mock_uuid, mock_makedirs):
        mock_uuid.uuid4.return_value.hex = 'abc123'
        mock_file = MagicMock()
        mock_file.filename = 'logo.png'
        result = save_logo(mock_file)
        assert result == '/static/uploads/logos/abc123.png'
        mock_file.save.assert_called_once()

    @patch('app.helpers.os.path.isfile', return_value=True)
    @patch('app.helpers.os.remove')
    @patch('app.helpers.os.makedirs')
    @patch('app.helpers.uuid')
    def test_deletes_old_local_file_on_replacement(self, mock_uuid, mock_makedirs, mock_remove, mock_isfile):
        mock_uuid.uuid4.return_value.hex = 'newfile'
        mock_file = MagicMock()
        mock_file.filename = 'logo.png'
        save_logo(mock_file, old_url='/static/uploads/logos/oldfile.png')
        mock_remove.assert_called_once()

    @patch('app.helpers.os.makedirs')
    @patch('app.helpers.uuid')
    def test_does_not_delete_external_url(self, mock_uuid, mock_makedirs):
        mock_uuid.uuid4.return_value.hex = 'newfile'
        mock_file = MagicMock()
        mock_file.filename = 'logo.png'
        with patch('app.helpers.os.remove') as mock_remove:
            save_logo(mock_file, old_url='https://cdn.example.com/logo.png')
            mock_remove.assert_not_called()

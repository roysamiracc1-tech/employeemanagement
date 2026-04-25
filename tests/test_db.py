"""
Unit tests for app/db.py — serialize and to_dict helpers.
These are pure functions with no DB or Flask dependency.
"""
import datetime
import decimal
import pytest

from app.db import serialize, to_dict


class TestSerialize:
    def test_date_to_iso_string(self):
        d = datetime.date(2026, 4, 26)
        assert serialize(d) == '2026-04-26'

    def test_datetime_to_iso_string(self):
        dt = datetime.datetime(2026, 4, 26, 12, 30, 0)
        assert serialize(dt) == '2026-04-26T12:30:00'

    def test_decimal_to_float(self):
        assert serialize(decimal.Decimal('3.14')) == pytest.approx(3.14)

    def test_string_passthrough(self):
        assert serialize('hello') == 'hello'

    def test_integer_passthrough(self):
        assert serialize(42) == 42

    def test_none_passthrough(self):
        assert serialize(None) is None

    def test_boolean_passthrough(self):
        assert serialize(True) is True

    def test_list_passthrough(self):
        lst = [1, 2, 3]
        assert serialize(lst) == lst


class TestToDict:
    def test_converts_row_to_dict(self):
        row = {'name': 'Alice', 'age': 30}
        result = to_dict(row)
        assert result == {'name': 'Alice', 'age': 30}

    def test_serializes_date_values(self):
        row = {'join_date': datetime.date(2022, 1, 15)}
        result = to_dict(row)
        assert result['join_date'] == '2022-01-15'

    def test_serializes_decimal_values(self):
        row = {'salary': decimal.Decimal('75000.50')}
        result = to_dict(row)
        assert result['salary'] == pytest.approx(75000.50)

    def test_none_values_preserved(self):
        row = {'manager_id': None, 'name': 'Bob'}
        result = to_dict(row)
        assert result['manager_id'] is None

    def test_mixed_types(self):
        row = {
            'id': 'uuid-001',
            'joined': datetime.date(2023, 6, 1),
            'score': decimal.Decimal('9.5'),
            'active': True,
            'count': 0,
        }
        result = to_dict(row)
        assert result['id'] == 'uuid-001'
        assert result['joined'] == '2023-06-01'
        assert result['score'] == pytest.approx(9.5)
        assert result['active'] is True
        assert result['count'] == 0

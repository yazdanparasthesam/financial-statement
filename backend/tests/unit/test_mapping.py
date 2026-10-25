import pytest

from app.domain.mapping import ALL_CATEGORIES, auto_map, is_valid_category


@pytest.mark.unit
@pytest.mark.parametrize("code,expected", [
    ("1101", "current_assets"), ("1105", "current_assets"),
    ("1201", "non_current_assets"), ("1202", "non_current_assets"),
    ("2101", "current_liabilities"), ("2201", "non_current_liabilities"),
    ("3101", "equity"), ("4101", "revenue"), ("5101", "cogs"),
    ("6102", "operating_expenses"), ("7101", "other_income"),
    ("8101", "other_expenses"), ("8201", "tax_expense"),
])
def test_prefix_mapping(code, expected):
    assert auto_map(code, "Anything") == expected


@pytest.mark.unit
def test_keyword_fallback():
    assert auto_map("XX-9", "Long-term bank loan") == "non_current_liabilities"
    assert auto_map("", "Sales Revenue") == "revenue"


@pytest.mark.unit
def test_unmappable_returns_none():
    assert auto_map("9999", "Mystery Consulting Fee") is None


@pytest.mark.unit
def test_category_registry():
    assert is_valid_category("equity")
    assert not is_valid_category("crypto_gains")
    assert len(ALL_CATEGORIES) == 11

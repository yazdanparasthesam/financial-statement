import pytest

from app.domain.generator import account_amount, build_statements

ACCOUNTS = [
    {"code": "1101", "name": "Cash", "debit": 180000, "credit": 0, "category": "current_assets"},
    {"code": "1102", "name": "Receivables", "debit": 85000, "credit": 0, "category": "current_assets"},
    {"code": "1105", "name": "Inventory", "debit": 60000, "credit": 0, "category": "current_assets"},
    {"code": "1201", "name": "Equipment", "debit": 200000, "credit": 0, "category": "non_current_assets"},
    {"code": "1202", "name": "Acc. Depreciation", "debit": 0, "credit": 45000, "category": "non_current_assets"},
    {"code": "2101", "name": "Payables", "debit": 0, "credit": 55000, "category": "current_liabilities"},
    {"code": "2102", "name": "Taxes Payable", "debit": 0, "credit": 15000, "category": "current_liabilities"},
    {"code": "2201", "name": "Loan", "debit": 0, "credit": 90000, "category": "non_current_liabilities"},
    {"code": "3101", "name": "Share Capital", "debit": 0, "credit": 200000, "category": "equity"},
    {"code": "3201", "name": "Retained Earnings", "debit": 0, "credit": 60000, "category": "equity"},
    {"code": "4101", "name": "Sales", "debit": 0, "credit": 380000, "category": "revenue"},
    {"code": "4102", "name": "Services", "debit": 0, "credit": 60000, "category": "revenue"},
    {"code": "5101", "name": "COGS", "debit": 210000, "credit": 0, "category": "cogs"},
    {"code": "6101", "name": "Salaries", "debit": 90000, "credit": 0, "category": "operating_expenses"},
    {"code": "6102", "name": "Rent", "debit": 36000, "credit": 0, "category": "operating_expenses"},
    {"code": "6103", "name": "Utilities", "debit": 12000, "credit": 0, "category": "operating_expenses"},
    {"code": "6104", "name": "Depreciation Expense", "debit": 10000, "credit": 0, "category": "operating_expenses"},
    {"code": "7101", "name": "Interest Income", "debit": 0, "credit": 4000, "category": "other_income"},
    {"code": "8101", "name": "Interest Expense", "debit": 6000, "credit": 0, "category": "other_expenses"},
    {"code": "8201", "name": "Tax Expense", "debit": 20000, "credit": 0, "category": "tax_expense"},
]


@pytest.mark.unit
def test_credit_normal_amounts():
    assert account_amount("revenue", 0, 380000) == 380000
    assert account_amount("non_current_assets", 0, 45000) == -45000  # contra-asset
    assert account_amount("current_assets", 180000, 0) == 180000


@pytest.mark.unit
def test_profit_and_loss_math():
    pl = build_statements(ACCOUNTS)["pl"]
    assert pl["revenue"]["total"] == 440000
    assert pl["gross_profit"] == 230000            # 440k - 210k
    assert pl["operating_profit"] == 82000         # 230k - 148k opex (incl. 10k depreciation)
    assert pl["profit_before_tax"] == 80000        # +4k other income -6k other exp
    assert pl["net_profit"] == 60000               # -20k tax


@pytest.mark.unit
def test_balance_sheet_identity_holds():
    s = build_statements(ACCOUNTS)
    bs = s["bs"]
    assert bs["total_assets"] == 480000            # 325k current + 155k non-current
    assert bs["total_liabilities"] == 160000
    assert bs["total_equity"] == 320000            # 260k + 60k current-year profit
    assert bs["total_assets"] == bs["total_liabilities_and_equity"]

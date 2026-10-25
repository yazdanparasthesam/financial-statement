from datetime import date

import pytest

from app.domain.deadlines import add_months, days_remaining, filing_deadline, period_end


@pytest.mark.unit
def test_iranian_fy_pattern():
    # FY starting 2025, ending month 3 (≈ Esfand) → period ends 2026-03-31, +4 months
    assert period_end(2025, 3) == date(2026, 3, 31)
    assert filing_deadline(2025, 3, 4) == date(2026, 7, 31)


@pytest.mark.unit
def test_month_end_clamping():
    # the HW4-Q6 class of bug: day 31 + 1 month must clamp, never crash
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # leap year
    assert add_months(date(2026, 10, 31), 4) == date(2027, 2, 28)


@pytest.mark.unit
def test_days_remaining():
    assert days_remaining(date(2026, 1, 11), today=date(2026, 1, 1)) == 10
    assert days_remaining(date(2025, 12, 31), today=date(2026, 1, 1)) == -1

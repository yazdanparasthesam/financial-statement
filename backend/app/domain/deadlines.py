"""Statutory deadline math: fiscal-year end + N months (default 4, Art. 95 pattern)."""
import calendar
from datetime import date


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])  # clamp (no Feb-30 bugs — HW4 Q6!)
    return date(year, month, day)


def period_end(fiscal_year: int, fy_end_month: int) -> date:
    """End of the fiscal period. fiscal_year = Gregorian start year; a period ending in
    month M <= 12 closes in fiscal_year+1 when M < the start (Iranian FY: Mar 20 → Mar 20)."""
    end_year = fiscal_year + 1
    last_day = calendar.monthrange(end_year, fy_end_month)[1]
    return date(end_year, fy_end_month, last_day)


def filing_deadline(fiscal_year: int, fy_end_month: int, months_after: int = 4) -> date:
    return add_months(period_end(fiscal_year, fy_end_month), months_after)


def days_remaining(deadline: date, today: date | None = None) -> int:
    return (deadline - (today or date.today())).days

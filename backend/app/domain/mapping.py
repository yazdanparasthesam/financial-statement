"""Deterministic trial-balance → statutory-category mapping.

Category taxonomy mirrors the INTA statutory statement layout (English labels):
  Balance sheet: current_assets, non_current_assets, current_liabilities,
                 non_current_liabilities, equity
  Profit & loss: revenue, cogs, operating_expenses, other_income,
                 other_expenses, tax_expense
Default chart-of-accounts convention (configurable): 11xx current assets,
12xx non-current assets, 21xx current liabilities, 22xx non-current liabilities,
3xxx equity, 4xxx revenue, 5xxx COGS, 6xxx operating expenses, 7xxx other income,
8xxx other expenses (82xx tax).
"""

BS_CATEGORIES = [
    "current_assets", "non_current_assets",
    "current_liabilities", "non_current_liabilities", "equity",
]
PL_CATEGORIES = [
    "revenue", "cogs", "operating_expenses",
    "other_income", "other_expenses", "tax_expense",
]
ALL_CATEGORIES = BS_CATEGORIES + PL_CATEGORIES

# longest-prefix-first
PREFIX_MAP: dict[str, str] = {
    "11": "current_assets",
    "12": "non_current_assets",
    "21": "current_liabilities",
    "22": "non_current_liabilities",
    "3": "equity",
    "4": "revenue",
    "5": "cogs",
    "6": "operating_expenses",
    "7": "other_income",
    "82": "tax_expense",
    "8": "other_expenses",
}

# keyword fallback when the code is unknown (e.g. imported from foreign software)
KEYWORD_MAP: list[tuple[tuple[str, ...], str]] = [
    # order matters: specific liability/equity/P&L keywords before generic asset words
    (("payable", "accrued", "unearned", "deferred revenue"), "current_liabilities"),
    (("loan", "mortgage", "bond", "long-term", "long term"), "non_current_liabilities"),
    (("capital", "equity", "retained", "reserve", "dividend"), "equity"),
    (("revenue", "sales", "service income"), "revenue"),
    (("cost of goods", "cogs", "direct cost"), "cogs"),
    (("salaries", "salary", "wage", "rent", "utilities", "insurance", "marketing", "office"),
     "operating_expenses"),
    (("tax expense", "corporate tax", "income tax"), "tax_expense"),
    (("interest income", "other income", "gain"), "other_income"),
    (("interest expense", "loss", "other expense"), "other_expenses"),
    (("depreciation", "equipment", "building", "land", "vehicle", "intangible", "fixed"),
     "non_current_assets"),
    (("cash", "bank", "receivable", "inventory", "prepaid"), "current_assets"),
]


def auto_map(code: str, name: str) -> str | None:
    """Return the statutory category for an account, or None if unmapped."""
    digits = "".join(ch for ch in code if ch.isdigit())
    for size in (3, 2, 1):
        prefix = digits[:size]
        if prefix in PREFIX_MAP:
            return PREFIX_MAP[prefix]
    low = name.lower()
    for keywords, category in KEYWORD_MAP:
        if any(k in low for k in keywords):
            return category
    return None


def is_valid_category(category: str) -> bool:
    return category in ALL_CATEGORIES

"""Financial ratios — deterministic, each shipped with its formula string.

Liquidity:   current_ratio, quick_ratio
Leverage:    debt_to_equity
Profitability: gross_margin, operating_margin, net_margin, roe, roa, ebitda
Efficiency:  asset_turnover
Division by zero yields None (reported as "n/a" by the API) — never a crash,
never infinity in a financial report.
"""


def _dep_expense(accounts: list[dict]) -> float:
    return round(sum(
        a["debit"] - a["credit"] for a in accounts
        if a.get("category") == "operating_expenses" and "depreciation" in a["name"].lower()
    ), 2)


def _inventory(bs: dict) -> float:
    return round(sum(i["amount"] for i in bs["current_assets"]["items"]
                     if "inventory" in i["name"].lower()), 2)


def _div(a: float, b: float) -> float | None:
    return round(a / b, 4) if b else None


def compute_ratios(pl: dict, bs: dict, accounts: list[dict]) -> list[dict]:
    revenue = pl["revenue"]["total"]
    ca, cl = bs["current_assets"]["total"], bs["current_liabilities"]["total"]
    tl, te = bs["total_liabilities"], bs["total_equity"]
    ta = bs["total_assets"]
    inv = _inventory(bs)
    dep = _dep_expense(accounts)

    def row(key, label, value, unit, formula, interpretation):
        return {"key": key, "label": label, "value": value, "unit": unit,
                "formula": formula, "interpretation": interpretation}

    cr = _div(ca, cl)
    qr = _div(ca - inv, cl)
    dte = _div(tl, te)
    return [
        row("current_ratio", "Current ratio", cr, "x",
            "current_assets ÷ current_liabilities",
            ("n/a — no current liabilities" if cr is None else
             "healthy short-term liquidity (≥1)" if cr >= 1 else "WARNING: current liabilities exceed current assets")),
        row("quick_ratio", "Quick ratio (acid test)", qr, "x",
            "(current_assets − inventory) ÷ current_liabilities",
            ("n/a" if qr is None else
             ("liquid assets cover short-term debt" if qr >= 1
              else "below 1 — relies on inventory sales to pay short-term debt"))),
        row("debt_to_equity", "Debt-to-equity", dte, "x",
            "total_liabilities ÷ total_equity",
            ("n/a — zero/negative equity" if dte is None else
             "conservative leverage (≤2)" if dte <= 2 else "high leverage (>2) — review debt covenants")),
        row("gross_margin", "Gross margin", _div(pl["gross_profit"], revenue), "%",
            "gross_profit ÷ revenue × 100", "pricing vs direct-cost efficiency"),
        row("operating_margin", "Operating margin", _div(pl["operating_profit"], revenue), "%",
            "operating_profit ÷ revenue × 100", "core-operations profitability"),
        row("net_margin", "Net margin", _div(pl["net_profit"], revenue), "%",
            "net_profit ÷ revenue × 100", "bottom-line profitability"),
        row("roe", "Return on equity", _div(pl["net_profit"], te), "%",
            "net_profit ÷ total_equity × 100", "shareholder return"),
        row("roa", "Return on assets", _div(pl["net_profit"], ta), "%",
            "net_profit ÷ total_assets × 100", "asset productivity"),
        row("asset_turnover", "Asset turnover", _div(revenue, ta), "x",
            "revenue ÷ total_assets", "efficiency of assets generating sales"),
        row("ebitda", "EBITDA", round(pl["operating_profit"] + dep, 2), "amount",
            "operating_profit + depreciation expense",
            "earnings before interest, taxes, depreciation & amortization"),
    ]


def scale_percentages(ratios: list[dict]) -> list[dict]:
    """API convenience: express '%'-unit ratios as percentages (×100), rounded to 2dp."""
    out = []
    for r in ratios:
        r = dict(r)
        if r["unit"] == "%" and r["value"] is not None:
            r["value"] = round(r["value"] * 100, 2)
        out.append(r)
    return out

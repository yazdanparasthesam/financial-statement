"""Statement generator: mapped trial balance → statutory P&L and Balance Sheet.

Pure arithmetic — the AI layer never touches these numbers (see AGENTS.md rule 1).
"""

CREDIT_NORMAL = {"revenue", "other_income", "current_liabilities",
                 "non_current_liabilities", "equity"}

PL_SECTIONS = ["revenue", "cogs", "operating_expenses", "other_income",
               "other_expenses", "tax_expense"]
ASSET_SECTIONS = ["current_assets", "non_current_assets"]
LIABILITY_SECTIONS = ["current_liabilities", "non_current_liabilities"]


def account_amount(category: str, debit: float, credit: float) -> float:
    return credit - debit if category in CREDIT_NORMAL else debit - credit


def _section(accounts: list[dict], category: str) -> dict:
    items = [
        {"code": a["code"], "name": a["name"],
         "amount": round(account_amount(category, a["debit"], a["credit"]), 2)}
        for a in accounts
        if a["category"] == category
    ]
    return {"items": items, "total": round(sum(i["amount"] for i in items), 2)}


def build_profit_and_loss(accounts: list[dict]) -> dict:
    sections = {c: _section(accounts, c) for c in PL_SECTIONS}
    gross_profit = round(sections["revenue"]["total"] - sections["cogs"]["total"], 2)
    operating_profit = round(gross_profit - sections["operating_expenses"]["total"], 2)
    profit_before_tax = round(
        operating_profit + sections["other_income"]["total"] - sections["other_expenses"]["total"], 2
    )
    net_profit = round(profit_before_tax - sections["tax_expense"]["total"], 2)
    return {
        **sections,
        "gross_profit": gross_profit,
        "operating_profit": operating_profit,
        "profit_before_tax": profit_before_tax,
        "net_profit": net_profit,
    }


def build_balance_sheet(accounts: list[dict], net_profit: float) -> dict:
    sections = {c: _section(accounts, c) for c in ASSET_SECTIONS + LIABILITY_SECTIONS + ["equity"]}
    total_assets = round(sections["current_assets"]["total"] + sections["non_current_assets"]["total"], 2)
    total_liabilities = round(
        sections["current_liabilities"]["total"] + sections["non_current_liabilities"]["total"], 2
    )
    equity = sections["equity"]
    equity_total = round(equity["total"] + net_profit, 2)
    return {
        **sections,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "current_year_profit": net_profit,
        "total_equity": equity_total,
        "total_liabilities_and_equity": round(total_liabilities + equity_total, 2),
    }


def build_statements(accounts: list[dict]) -> dict[str, dict]:
    """accounts: dicts with code,name,debit,credit,category (mapped only)."""
    mapped = [a for a in accounts if a.get("category")]
    pl = build_profit_and_loss(mapped)
    bs = build_balance_sheet(mapped, pl["net_profit"])
    return {"pl": pl, "bs": bs}

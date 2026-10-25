"""Deterministic validation engine. Rules are pure functions; results are data.

R001 trial balance balanced (error)      R005 equity positive (warning)
R002 balance-sheet identity (error)      R006 year-over-year anomalies (warning)
R003 all accounts mapped (warning)       R007 cash-flow reconciliation (warning)
R004 revenue present (error)             R008 short-term liquidity (warning)
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleResult:
    rule_id: str
    severity: str
    passed: bool
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationOutcome:
    results: list[RuleResult]
    anomalies: list[dict]


def _section_total(node) -> float | None:
    """Section nodes carry {'items': [...], 'total': X}; top-line nodes are plain numbers."""
    if isinstance(node, dict):
        total = node.get("total")
        return float(total) if isinstance(total, (int, float)) else None
    return float(node) if isinstance(node, (int, float)) else None


def _pct_change(prior: float, current: float) -> float | None:
    if abs(prior) < 1e-9:
        return None
    return round((current - prior) / abs(prior) * 100.0, 1)


def run_rules(
    *,
    tb_total_debit: float,
    tb_total_credit: float,
    accounts: list[dict],
    statements: dict[str, dict] | None,
    prior_statements: dict[str, dict] | None = None,
    threshold_pct: float = 50.0,
    cash_flow: dict | None = None,
) -> ValidationOutcome:
    results: list[RuleResult] = []
    anomalies: list[dict] = []

    # R001 — trial balance must balance
    diff = round(tb_total_debit - tb_total_credit, 2)
    results.append(RuleResult(
        "R001", "error", diff == 0,
        f"Trial balance totals {'match' if diff == 0 else f'DIFFER by {diff:,.2f}'} "
        f"(debits {tb_total_debit:,.2f} vs credits {tb_total_credit:,.2f}).",
        {"total_debit": tb_total_debit, "total_credit": tb_total_credit, "difference": diff},
    ))

    if statements is None:
        results.append(RuleResult(
            "R002", "error", False,
            "Statements have not been generated yet — cannot check the balance-sheet identity.",
        ))
        return ValidationOutcome(results=results, anomalies=anomalies)



    bs = statements["bs"]
    pl = statements["pl"]

    # R002 — assets == liabilities + equity
    identity_diff = round(bs["total_assets"] - bs["total_liabilities_and_equity"], 2)
    results.append(RuleResult(
        "R002", "error", identity_diff == 0,
        f"Balance-sheet identity {'holds' if identity_diff == 0 else f'VIOLATED (off by {identity_diff:,.2f})'}: "
        f"assets {bs['total_assets']:,.2f} vs liabilities+equity {bs['total_liabilities_and_equity']:,.2f}.",
        {"total_assets": bs["total_assets"],
         "total_liabilities_and_equity": bs["total_liabilities_and_equity"]},
    ))

    # R003 — every account mapped to a statutory category
    unmapped = [a for a in accounts if not a.get("category")]
    results.append(RuleResult(
        "R003", "warning", not unmapped,
        "All accounts mapped to statutory categories." if not unmapped
        else f"{len(unmapped)} account(s) unmapped: " + ", ".join(a["code"] for a in unmapped[:10]),
        {"unmapped_codes": [a["code"] for a in unmapped]},
    ))

    # R004 — revenue present
    has_revenue = pl["revenue"]["total"] != 0
    results.append(RuleResult(
        "R004", "error", has_revenue,
        "Revenue section populated." if has_revenue
        else "No revenue mapped — a going-concern P&L must report revenue.",
        {"revenue_total": pl["revenue"]["total"]},
    ))

    # R005 — equity positive
    equity_ok = bs["total_equity"] > 0
    results.append(RuleResult(
        "R005", "warning", equity_ok,
        f"Total equity is {bs['total_equity']:,.2f}."
        + ("" if equity_ok else " NEGATIVE equity - review going-concern assumptions."),
        {"total_equity": bs["total_equity"]},
    ))

    # R006 — year-over-year anomalies on statement totals
    if prior_statements is None:
        results.append(RuleResult(
            "R006", "info", True,
            "No prior-year statements on file — year-over-year anomaly check skipped.",
        ))
    else:
        tracked = [
            ("pl", "revenue"), ("pl", "cogs"), ("pl", "operating_expenses"), ("pl", "net_profit"),
            ("bs", "current_assets"), ("bs", "total_assets"), ("bs", "total_liabilities"),
            ("bs", "total_equity"),
        ]
        flagged = 0
        for stmt, key in tracked:
            cur, pri = _section_total(statements[stmt].get(key)), \
                _section_total(prior_statements.get(stmt, {}).get(key))
            if cur is None or pri is None:
                continue
            pct = _pct_change(pri, cur)
            if pct is not None and abs(pct) > threshold_pct:
                flagged += 1
                anomalies.append({
                    "account_code": f"{stmt}:{key}",
                    "account_name": key.replace("_", " ").title(),
                    "metric": "section_total",
                    "prior_value": pri,
                    "current_value": cur,
                    "pct_change": pct,
                })
        results.append(RuleResult(
            "R006", "warning", flagged == 0,
            "Year-over-year movement within threshold." if flagged == 0
            else f"{flagged} section(s) moved more than {threshold_pct:.0f}% year-over-year — explanations required.",
            {"threshold_pct": threshold_pct, "flagged": flagged},
        ))

    # R007 — cash-flow reconciliation (indirect method must explain the cash movement)
    if cash_flow is None:
        results.append(RuleResult(
            "R007", "info", True,
            "Cash-flow statement not available (needs prior-year balance sheet) — reconciliation skipped.",
        ))
    else:
        gap = cash_flow["reconciliation_gap"]
        ok = abs(gap) <= 1.0
        results.append(RuleResult(
            "R007", "warning", ok,
            "Cash movement fully reconciled by operating/investing/financing activities." if ok
            else f"Unexplained cash movement of {gap:,.2f} — indirect cash flow does not tie to the cash account.",
            {"reconciliation_gap": gap},
        ))

    # R008 — short-term liquidity
    ca = bs["current_assets"]["total"]
    cl = bs["current_liabilities"]["total"]
    if cl <= 0:
        results.append(RuleResult("R008", "info", True, "No current liabilities — liquidity check not applicable."))
    else:
        ratio = round(ca / cl, 4)
        ok = ratio >= 1.0
        results.append(RuleResult(
            "R008", "warning", ok,
            f"Current ratio {ratio:.2f} — short-term obligations covered." if ok
            else f"Current ratio {ratio:.2f} — current liabilities exceed current assets.",
            {"current_ratio": ratio},
        ))

    return ValidationOutcome(results=results, anomalies=anomalies)

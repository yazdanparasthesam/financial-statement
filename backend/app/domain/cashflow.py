"""Cash-flow statement, indirect method — pure arithmetic over generated statements.

Formulas (every one also documented in docs/architecture.md §Formula reference):
  operating  = net_profit + depreciation_addback − Δreceivables − Δinventory + Δpayables
  investing  = −(gross equipment purchases)  ≈ −Δ(gross non-current assets excl. contra)
  financing  = Δ(non-current liabilities) + Δ(share capital)
  net_change = operating + investing + financing
  reconciliation_gap = net_change − (cash_end − cash_begin)   → rule R007
Depreciation addback = |accumulated depreciation| movement (current − prior).
Requires prior-year balance sheet; returns None without it.
"""


def _items(bs: dict, section: str) -> list[dict]:
    node = bs.get(section) or {}
    return node.get("items", []) if isinstance(node, dict) else []


def _find(items: list[dict], *keywords: str) -> float:
    total = 0.0
    for it in items:
        low = it["name"].lower()
        if any(k in low for k in keywords):
            total += it["amount"]
    return round(total, 2)


def build_cash_flow(pl: dict, bs: dict, prior_bs: dict) -> dict | None:
    if not prior_bs:
        return None

    net_profit = pl["net_profit"]

    cash_begin = _find(_items(prior_bs, "current_assets"), "cash", "bank")
    cash_end = _find(_items(bs, "current_assets"), "cash", "bank")
    ar_begin = _find(_items(prior_bs, "current_assets"), "receivable")
    ar_end = _find(_items(bs, "current_assets"), "receivable")
    inv_begin = _find(_items(prior_bs, "current_assets"), "inventory")
    inv_end = _find(_items(bs, "current_assets"), "inventory")
    ap_begin = _find(_items(prior_bs, "current_liabilities"), "payable")
    ap_end = _find(_items(bs, "current_liabilities"), "payable")

    accdep_begin = abs(_find(_items(prior_bs, "non_current_assets"), "depreciation"))
    accdep_end = abs(_find(_items(bs, "non_current_assets"), "depreciation"))
    depreciation = round(accdep_end - accdep_begin, 2)

    gross_nca_begin = sum(i["amount"] for i in _items(prior_bs, "non_current_assets") if i["amount"] > 0)
    gross_nca_end = sum(i["amount"] for i in _items(bs, "non_current_assets") if i["amount"] > 0)
    equipment_purchases = round(gross_nca_end - gross_nca_begin, 2)

    delta_loans = round(bs["non_current_liabilities"]["total"] - prior_bs["non_current_liabilities"]["total"], 2)
    cap_begin = _find(_items(prior_bs, "equity"), "capital")
    cap_end = _find(_items(bs, "equity"), "capital")
    delta_capital = round(cap_end - cap_begin, 2)

    d_ar = round(-(ar_end - ar_begin), 2)       # rise in receivables uses cash
    d_inv = round(-(inv_end - inv_begin), 2)    # rise in inventory uses cash
    d_ap = round(ap_end - ap_begin, 2)          # rise in payables frees cash

    operating = round(net_profit + depreciation + d_ar + d_inv + d_ap, 2)
    investing = round(-equipment_purchases, 2)
    financing = round(delta_loans + delta_capital, 2)
    net_change = round(operating + investing + financing, 2)
    gap = round(net_change - (cash_end - cash_begin), 2)

    return {
        "operating": {
            "net_profit": net_profit, "depreciation_addback": depreciation,
            "delta_receivables": d_ar, "delta_inventory": d_inv, "delta_payables": d_ap,
            "total": operating,
        },
        "investing": {"equipment_purchases": round(-equipment_purchases, 2), "total": investing},
        "financing": {"delta_loans": delta_loans, "delta_capital": delta_capital, "total": financing},
        "net_change_in_cash": net_change,
        "cash_begin": cash_begin,
        "cash_end": cash_end,
        "reconciliation_gap": gap,
    }

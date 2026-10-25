"""THE workflow test: upload → map → generate → validate → AI assist → submit →
review loop → accept → export. Covers criteria 6 + 9 (backend + integration)."""
from datetime import date

import pytest

from app.domain.deadlines import filing_deadline
from tests.conftest import upload_tb

# date-independent story: current FY's deadline always lands next year (future)
CUR_FY = date.today().year
PRIOR_FY = CUR_FY - 1


def _mk_filing(client, headers, company_id, fy):
    r = client.post("/api/filings", headers=headers,
                    json={"company_id": company_id, "fiscal_year": fy})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.integration
def test_full_filing_lifecycle(client, preparer, reviewer, company):
    cid = company["id"]

    # ---- deadlines + duplicate guard --------------------------------------
    fy24 = _mk_filing(client, preparer, cid, PRIOR_FY)
    fy25 = _mk_filing(client, preparer, cid, CUR_FY)
    expected_deadline = filing_deadline(CUR_FY, 3, 4).isoformat()
    assert fy25["deadline"] == expected_deadline     # FY end + 4 months (Art. 95 pattern)
    assert fy25["status"] == "draft"
    r = client.post("/api/filings", headers=preparer, json={"company_id": cid, "fiscal_year": CUR_FY})
    assert r.status_code == 409
    dl = client.get(f"/api/filings/{fy25['id']}/deadline", headers=preparer).json()
    assert dl["deadline"] == expected_deadline and dl["days_remaining"] > 0

    # ---- prior year (needed for YoY anomalies) ----------------------------
    upload_tb(client, preparer, fy24["id"], "trial_balance_prior_year.csv")
    assert client.post(f"/api/filings/{fy24['id']}/statements/generate",
                       headers=preparer).status_code == 201
    assert client.post(f"/api/filings/{fy24['id']}/validate", headers=preparer).status_code == 200

    # ---- current year: upload + auto-mapping ------------------------------
    tb = upload_tb(client, preparer, fy25["id"], "trial_balance_clean.csv")
    assert tb["total_debit"] == 909000 and tb["total_credit"] == 909000
    assert len(tb["accounts"]) == 20
    assert all(a["mapping_status"] == "mapped" for a in tb["accounts"])

    # ---- statements -------------------------------------------------------
    r = client.post(f"/api/filings/{fy25['id']}/statements/generate", headers=preparer)
    assert r.status_code == 201
    pl = client.get(f"/api/filings/{fy25['id']}/statements/pl", headers=preparer).json()
    bs = client.get(f"/api/filings/{fy25['id']}/statements/bs", headers=preparer).json()
    assert pl["data"]["net_profit"] == 60000
    assert bs["data"]["total_assets"] == bs["data"]["total_liabilities_and_equity"] == 480000

    # cash-flow statement (indirect method) — prior year exists, so cf is generated too
    cf = client.get(f"/api/filings/{fy25['id']}/statements/cf", headers=preparer).json()
    assert cf["data"]["operating"]["total"] == 70000       # 60k profit + 10k depreciation
    assert cf["data"]["reconciliation_gap"] == 0.0         # ties to the cash movement exactly

    # ---- validation with YoY anomalies (mock AI downstream) ---------------
    run = client.post(f"/api/filings/{fy25['id']}/validate", headers=preparer).json()
    by_id = {res["rule_id"]: res for res in run["results"]}
    assert by_id["R001"]["passed"] and by_id["R002"]["passed"] and by_id["R003"]["passed"]
    assert by_id["R007"]["passed"] and by_id["R008"]["passed"]
    assert not by_id["R006"]["passed"] and by_id["R006"]["severity"] == "warning"
    anomalies = client.get(f"/api/filings/{fy25['id']}/anomalies", headers=preparer).json()
    codes = {a["account_code"] for a in anomalies}
    assert "pl:revenue" in codes and "pl:net_profit" in codes
    rev = next(a for a in anomalies if a["account_code"] == "pl:revenue")
    assert rev["pct_change"] == 69.2  # (440k-260k)/260k

    # ---- deterministic ratios with formulas --------------------------------
    rats = {r["key"]: r for r in client.get(f"/api/filings/{fy25['id']}/ratios", headers=preparer).json()}
    assert rats["current_ratio"]["value"] == 4.6429        # 325,000 / 70,000
    assert rats["ebitda"]["value"] == 92000                # 82k operating + 10k depreciation
    assert "÷" in rats["current_ratio"]["formula"]

    # ---- AI assist (mock provider, deterministic) -------------------------
    ex = client.post(f"/api/anomalies/{rev['id']}/explain", headers=preparer).json()
    assert ex["provider"] == "mock" and "MOCK EXPLANATION" in ex["explanation"]
    note = client.post(f"/api/filings/{fy25['id']}/notes/draft", headers=preparer,
                       json={"section": "revenue"}).json()
    assert note["ai_generated"] and note["draft_text"]
    fin = client.patch(f"/api/notes/{note['id']}", headers=preparer,
                       json={"final_text": "Reviewed and finalized by preparer."}).json()
    assert fin["final_text"] == "Reviewed and finalized by preparer."
    chat = client.post(f"/api/filings/{fy25['id']}/assistant/chat", headers=preparer,
                       json={"message": "What is the net profit?"}).json()
    assert chat["reply"] and chat["provider"] == "mock"

    # ReWOO audit memo: plan -> execute read-only tools -> solve
    memo = client.post(f"/api/filings/{fy25['id']}/audit-memo", headers=preparer).json()
    assert memo["provider"] == "mock" and "MOCK AUDIT MEMO" in memo["memo"]
    assert len(memo["plan"]) >= 3 and memo["observations_count"] == len(memo["plan"])
    assert "get_validation_report" in memo["plan"]
    # R006 fails as a warning only -> gate wording must not say BLOCKED
    assert "PASS WITH WARNINGS" in memo["memo"]

    # ---- checklist ---------------------------------------------------------
    items = {i["item"]: i["done"] for i in
             client.get(f"/api/filings/{fy25['id']}/checklist", headers=preparer).json()}
    assert items["Trial balance uploaded"] and items["P&L and Balance Sheet generated"]
    assert not items["Submitted for review"]

    # ---- access control ----------------------------------------------------
    assert client.get(f"/api/filings/{fy25['id']}", headers=reviewer).status_code == 200  # read OK
    r = client.post(f"/api/filings/{fy25['id']}/trial-balance", headers=reviewer,
                    files={"file": ("x.csv", b"code,name,debit,credit\n1101,C,1,0\n", "text/csv")})
    assert r.status_code == 403

    # ---- submit → review loop → accept -------------------------------------
    r = client.post(f"/api/filings/{fy25['id']}/submit", headers=preparer)
    assert r.status_code == 200 and r.json()["status"] == "submitted"  # warning-only R006 doesn't block
    r = client.post(f"/api/filings/{fy25['id']}/trial-balance", headers=preparer,
                    files={"file": ("tb.csv", b"code,name,debit,credit\n1101,C,1,1\n", "text/csv")})
    assert r.status_code == 422  # locked after submit

    assert client.post(f"/api/filings/{fy25['id']}/review/transition", headers=reviewer,
                       json={"action": "start_review"}).json()["status"] == "in_review"
    cm = client.post(f"/api/filings/{fy25['id']}/comments", headers=reviewer,
                     json={"body": "Explain the revenue jump.", "anchor": "pl:revenue"}).json()
    assert client.post(f"/api/filings/{fy25['id']}/review/transition", headers=reviewer,
                       json={"action": "request_changes", "comment": "See comment"}
                       ).json()["status"] == "changes_requested"
    assert client.post(f"/api/filings/{fy25['id']}/review/transition", headers=preparer,
                       json={"action": "reopen"}).json()["status"] == "draft"
    assert client.post(f"/api/filings/{fy25['id']}/submit", headers=preparer).json()["status"] == "submitted"
    assert client.post(f"/api/filings/{fy25['id']}/review/transition", headers=reviewer,
                       json={"action": "start_review"}).json()["status"] == "in_review"
    # preparer cannot accept (role gate)
    assert client.post(f"/api/filings/{fy25['id']}/review/transition", headers=preparer,
                       json={"action": "accept"}).status_code == 403
    assert client.post(f"/api/filings/{fy25['id']}/review/transition", headers=reviewer,
                       json={"action": "accept", "comment": "LGTM"}).json()["status"] == "accepted"

    events = client.get(f"/api/filings/{fy25['id']}/review/events", headers=reviewer).json()
    assert [e["to_status"] for e in events] == [
        "submitted", "in_review", "changes_requested", "draft", "submitted", "in_review", "accepted"]
    comments = client.get(f"/api/filings/{fy25['id']}/comments", headers=preparer).json()
    assert len(comments) == 1
    res = client.patch(f"/api/filings/{fy25['id']}/comments/{cm['id']}/resolve", headers=reviewer).json()
    assert res["resolved"]

    # ---- exports -----------------------------------------------------------
    r = client.get(f"/api/filings/{fy25['id']}/exports/pl.xlsx", headers=preparer)
    assert r.status_code == 200 and r.headers["content-type"].startswith(
        "application/vnd.openxmlformats") and len(r.content) > 2000
    r = client.get(f"/api/filings/{fy25['id']}/exports/bs.pdf", headers=preparer)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    r = client.get(f"/api/filings/{fy25['id']}/exports/checklist.pdf", headers=preparer)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert client.get(f"/api/filings/{fy25['id']}/exports/pl.docx",
                      headers=preparer).status_code == 400

    # ---- reviewer scoping: sees everything ---------------------------------
    all_filings = client.get("/api/filings", headers=reviewer).json()
    assert {f["id"] for f in all_filings} >= {fy24["id"], fy25["id"]}


@pytest.mark.integration
def test_unbalanced_tb_blocks_submission(client, preparer, company):
    f = _mk_filing(client, preparer, company["id"], CUR_FY + 2)
    tb = upload_tb(client, preparer, f["id"], "trial_balance_unbalanced.csv")
    assert tb["total_debit"] != tb["total_credit"]
    assert client.post(f"/api/filings/{f['id']}/statements/generate", headers=preparer).status_code == 201
    run = client.post(f"/api/filings/{f['id']}/validate", headers=preparer).json()
    by_id = {res["rule_id"]: res for res in run["results"]}
    assert not by_id["R001"]["passed"] and by_id["R001"]["severity"] == "error"
    # submit gate: failing ERROR rule blocks, message names the rule
    r = client.post(f"/api/filings/{f['id']}/submit", headers=preparer)
    assert r.status_code == 422 and "R001" in r.json()["detail"]
    # submit without any validation run is also blocked
    f2 = _mk_filing(client, preparer, company["id"], CUR_FY + 3)
    r = client.post(f"/api/filings/{f2['id']}/submit", headers=preparer)
    assert r.status_code == 422


@pytest.mark.integration
def test_unmapped_accounts_and_ai_suggestions(client, preparer, company):
    f = _mk_filing(client, preparer, company["id"], CUR_FY + 4)
    tb = upload_tb(client, preparer, f["id"], "trial_balance_unmapped.csv")
    unmapped = [a for a in tb["accounts"] if a["mapping_status"] == "unmapped"]
    assert {a["code"] for a in unmapped} == {"9999", "9998"}

    sug = client.post(f"/api/filings/{f['id']}/trial-balance/suggest-mappings",
                      headers=preparer).json()
    assert {s["code"]: s["suggested_category"] for s in sug} == {
        "9999": "operating_expenses", "9998": "current_liabilities"}

    by_code = {a["code"]: a for a in tb["accounts"]}
    s99 = next(s for s in sug if s["code"] == "9999")
    r = client.patch(f"/api/filings/{f['id']}/trial-balance/accounts/{s99['account_id']}",
                     headers=preparer, json={"category": s99["suggested_category"]})
    assert r.status_code == 200 and r.json()["mapping_status"] == "mapped"
    # invalid category rejected
    assert client.patch(
        f"/api/filings/{f['id']}/trial-balance/accounts/{by_code['9998']['id']}",
        headers=preparer, json={"category": "moon_assets"}).status_code == 400

    # --- half-mapped pair: validation CAUGHT it, submit gate BLOCKS -----------
    # (9999 mapped to expenses without its 9998 suspense credit breaks the identity)
    client.post(f"/api/filings/{f['id']}/statements/generate", headers=preparer)
    run = client.post(f"/api/filings/{f['id']}/validate", headers=preparer).json()
    by_id = {res["rule_id"]: res for res in run["results"]}
    assert not by_id["R003"]["passed"] and "9998" in by_id["R003"]["message"]
    assert not by_id["R002"]["passed"] and by_id["R002"]["severity"] == "error"
    r = client.post(f"/api/filings/{f['id']}/submit", headers=preparer)
    assert r.status_code == 422 and "R002" in r.json()["detail"]

    # --- human applies the second suggestion → regenerate → clean → submit ----
    s98 = next(s for s in sug if s["code"] == "9998")
    r = client.patch(f"/api/filings/{f['id']}/trial-balance/accounts/{s98['account_id']}",
                     headers=preparer, json={"category": s98["suggested_category"]})
    assert r.status_code == 200
    client.post(f"/api/filings/{f['id']}/statements/generate", headers=preparer)
    run = client.post(f"/api/filings/{f['id']}/validate", headers=preparer).json()
    by_id = {res["rule_id"]: res for res in run["results"]}
    assert by_id["R002"]["passed"] and by_id["R003"]["passed"] and run["failed"] == 0
    assert client.post(f"/api/filings/{f['id']}/submit", headers=preparer).status_code == 200

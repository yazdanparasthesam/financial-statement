#!/usr/bin/env python3
"""Seed a running Financial Statement instance with the full demo story (needs BASE_URL reachable).

Creates: preparer + reviewer users, one company, prior-year filing (loss year) and
current-year filing (turnaround), uploads seed trial balances, generates statements,
runs validation (YoY anomalies appear), drafts a note. Prints a summary + credentials.

Usage:  python backend/scripts/seed_demo.py [BASE_URL]   (default http://localhost:8000)
"""
import pathlib
import sys
from datetime import date

import httpx

CUR_FY = date.today().year
PRIOR_FY = CUR_FY - 1

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
SEED = pathlib.Path(__file__).resolve().parents[2] / "seed"
DEMO_PASSWORD = "financial-statement-demo-123"
PREP = {"email": "preparer@fsapp.dev", "password": DEMO_PASSWORD,
        "full_name": "Pari Preparer", "role": "preparer"}
REV = {"email": "reviewer@fsapp.dev", "password": DEMO_PASSWORD,
       "full_name": "Reza Reviewer", "role": "reviewer"}


def register_and_login(c: httpx.Client, user: dict) -> dict:
    r = c.post(f"{BASE}/api/auth/register", json=user)
    assert r.status_code in (201, 409), r.text
    r = c.post(f"{BASE}/api/auth/login", json={"email": user["email"], "password": user["password"]})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def upload(c, h, filing_id, path):
    with open(path, "rb") as f:
        r = c.post(f"{BASE}/api/filings/{filing_id}/trial-balance", headers=h,
                   files={"file": (path.name, f, "text/csv")})
    r.raise_for_status()
    return r.json()


def main():
    with httpx.Client(timeout=30) as c:
        hp = register_and_login(c, PREP)
        hr = register_and_login(c, REV)

        r = c.post(f"{BASE}/api/companies", headers=hp, json={
            "name": "Pars Pivot Industries", "national_id": "DEMO-1400-0001",
            "economic_code": "DEMO-EC-001", "fiscal_year_end_month": 3})
        assert r.status_code == 201, r.text
        company_id = r.json()["id"]

        filings = {}
        for fy in (PRIOR_FY, CUR_FY):
            r = c.post(f"{BASE}/api/filings", headers=hp,
                       json={"company_id": company_id, "fiscal_year": fy})
            assert r.status_code in (201, 409), r.text
            if r.status_code == 201:
                filings[fy] = r.json()["id"]
            else:
                lst = c.get(f"{BASE}/api/filings", headers=hp, params={"company_id": company_id}).json()
                filings[fy] = next(f["id"] for f in lst if f["fiscal_year"] == fy)

        upload(c, hp, filings[PRIOR_FY], SEED / "trial_balance_prior_year.csv")
        c.post(f"{BASE}/api/filings/{filings[PRIOR_FY]}/statements/generate", headers=hp).raise_for_status()
        c.post(f"{BASE}/api/filings/{filings[PRIOR_FY]}/validate", headers=hp).raise_for_status()

        tb25 = upload(c, hp, filings[CUR_FY], SEED / "trial_balance_clean.csv")
        c.post(f"{BASE}/api/filings/{filings[CUR_FY]}/statements/generate", headers=hp).raise_for_status()
        val = c.post(f"{BASE}/api/filings/{filings[CUR_FY]}/validate", headers=hp).json()
        c.post(f"{BASE}/api/filings/{filings[CUR_FY]}/notes/draft", headers=hp,
               json={"section": "revenue"}).raise_for_status()

        print("Demo seeded.")
        print(f"  company   : Pars Pivot Industries (id {company_id})")
        print(f"  FY{PRIOR_FY}    : filing {filings[PRIOR_FY]} (loss year, net -120,000)")
        print(f"  FY{CUR_FY}    : filing {filings[CUR_FY]} — TB {tb25['total_debit']:,.0f}/{tb25['total_credit']:,.0f}")
        print(f"  validation: passed {val['passed']} / failed {val['failed']} (YoY anomalies expected)")
        print("  logins    : preparer@fsapp.dev | reviewer@fsapp.dev | financial-statement-demo-123")
        print(f"  reviewer headers ready: {bool(hr)}")


if __name__ == "__main__":
    main()

import pytest

from app.domain.generator import build_statements
from app.domain.validators import run_rules
from tests.unit.test_generator import ACCOUNTS

STATEMENTS = build_statements(ACCOUNTS)


def _by_id(outcome):
    return {r.rule_id: r for r in outcome.results}


@pytest.mark.unit
def test_clean_run_passes_all_but_yoy_info():
    out = run_rules(tb_total_debit=909000, tb_total_credit=909000,
                    accounts=ACCOUNTS, statements=STATEMENTS)
    res = _by_id(out)
    assert res["R001"].passed and res["R002"].passed and res["R003"].passed
    assert res["R004"].passed and res["R005"].passed
    assert res["R006"].severity == "info"  # skipped without prior year
    assert out.anomalies == []


@pytest.mark.unit
def test_unbalanced_trial_balance_fails_r001():
    out = run_rules(tb_total_debit=904000, tb_total_credit=909000,
                    accounts=ACCOUNTS, statements=STATEMENTS)
    r001 = _by_id(out)["R001"]
    assert not r001.passed and r001.severity == "error"
    assert r001.context["difference"] == -5000


@pytest.mark.unit
def test_broken_identity_fails_r002():
    broken = {"pl": STATEMENTS["pl"], "bs": {**STATEMENTS["bs"], "total_liabilities_and_equity": 1.0}}
    r002 = _by_id(run_rules(tb_total_debit=1, tb_total_credit=1, accounts=ACCOUNTS,
                            statements=broken))["R002"]
    assert not r002.passed


@pytest.mark.unit
def test_unmapped_accounts_flagged_r003():
    accounts = [*ACCOUNTS, {"code": "9999", "name": "Mystery", "debit": 1, "credit": 0, "category": ""}]
    r003 = _by_id(run_rules(tb_total_debit=1, tb_total_credit=1, accounts=accounts,
                            statements=STATEMENTS))["R003"]
    assert not r003.passed and "9999" in r003.message


@pytest.mark.unit
def test_missing_statements_short_circuits():
    out = run_rules(tb_total_debit=10, tb_total_credit=10, accounts=ACCOUNTS, statements=None)
    res = _by_id(out)
    assert not res["R002"].passed and "not been generated" in res["R002"].message
    assert "R003" not in res


@pytest.mark.unit
def test_yoy_anomaly_detected():
    prior_pl = {**STATEMENTS["pl"], "revenue": {"items": [], "total": 250000}}
    prior = {"pl": prior_pl, "bs": STATEMENTS["bs"]}
    out = run_rules(tb_total_debit=909000, tb_total_credit=909000,
                    accounts=ACCOUNTS, statements=STATEMENTS,
                    prior_statements=prior, threshold_pct=50.0)
    r006 = _by_id(out)["R006"]
    assert not r006.passed and r006.severity == "warning"
    codes = [a["account_code"] for a in out.anomalies]
    assert "pl:revenue" in codes
    rev = next(a for a in out.anomalies if a["account_code"] == "pl:revenue")
    assert rev["pct_change"] == 76.0  # (440k-250k)/250k

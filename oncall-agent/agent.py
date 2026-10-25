#!/usr/bin/env python3
"""On-call responder agent — wakes on Alertmanager webhooks and fixes what it safely can.

Position in the agent team (docs/agent-team.md): the RESPONDER. It is deliberately
deterministic: alertname → runbook → allow-listed command → verify → incident report.
No LLM, no improvised shell: it may only run commands accepted by the exact
command grammar in `is_allowed_command`; every action leaves a markdown report in
ops/incidents/ as evidence.

Run (host, repo root):   python oncall-agent/agent.py            # serve :8090
One-shot (drills/tests): python oncall-agent/agent.py --payload sample-alert.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

# Exact command grammar (not shell prefixes). Alerts cannot submit commands, and a
# compromised runbook cannot broaden this list without a reviewed code change.
ALLOWED_COMMANDS = (
    ("docker", "compose", "ps"),
    ("docker", "compose", "ps", "backend"),
    ("docker", "compose", "logs"),
    ("docker", "compose", "logs", "--tail"),  # numeric tail value checked below
    ("docker", "compose", "logs", "--tail", "backend"),
    ("docker", "compose", "restart", "backend"),
    ("echo",),
    ("true",),
)
REFUSED_RC = 126


def utcnow() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- runbook plumbing

def load_runbooks(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text())
    defaults = data.get("defaults", {})
    return {"defaults": defaults, "runbooks": data.get("runbooks", {})}


def match_runbook(alertname: str, cfg: dict) -> tuple[str, dict]:
    rbs = cfg["runbooks"]
    if alertname in rbs:
        return alertname, rbs[alertname]
    return "default", rbs.get("default", {})


def is_allowed_command(cmd: str) -> bool:
    """Allow only the small runbook grammar; never shell-evaluate user text."""
    if not cmd.strip():
        return False
    try:
        parts = tuple(shlex.split(cmd))
    except ValueError:
        return False
    if parts in ALLOWED_COMMANDS:
        return True
    # logs --tail N [backend], with a bounded numeric N (no extra tokens)
    if (len(parts) in (5, 6) and parts[:3] == ("docker", "compose", "logs")
            and parts[3] == "--tail" and parts[4].isdigit()
            and 1 <= int(parts[4]) <= 500
            and (len(parts) == 5 or parts[5] == "backend")):
        return True
    # echo is harmless stdout-only evidence (no shell is involved).
    return len(parts) >= 2 and parts[0] == "echo"


def run_command(cmd: str, cwd: str, timeout: int) -> tuple[int, str]:
    """Run an allow-listed command. Anything else is refused, never executed."""
    if not is_allowed_command(cmd):
        return REFUSED_RC, f"REFUSED — command not allow-listed: {cmd!r}"
    try:
        proc = subprocess.run(shlex.split(cmd), cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
        out = (proc.stdout + proc.stderr).strip()
        return proc.returncode, out[-2000:]
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s: {cmd}"
    except OSError as e:
        return 1, f"OS error running {cmd!r}: {e}"


def verify_recovery(url: str, attempts: int, delay: float) -> tuple[bool, int]:
    for i in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return True, i
        except OSError:
            pass
        time.sleep(delay)
    return False, attempts


# ---------------------------------------------------------------- incident model

@dataclass
class Incident:
    alertname: str
    severity: str = "unknown"
    summary: str = ""
    description: str = ""
    impact: str = ""
    fingerprint: str = ""
    runbook_name: str = ""
    status: str = "open"      # remediated | escalated | diagnosed | suppressed | resolved
    report_path: str = ""
    timeline: list = field(default_factory=list)   # [(ts, event, detail)]

    def log(self, event: str, detail: str = "") -> None:
        self.timeline.append((utcnow(), event, detail))

    def to_markdown(self) -> str:
        lines = [
            f"# Incident — {self.alertname} ({self.severity})",
            "",
            f"- **Status:** {self.status}",
            f"- **Summary:** {self.summary}",
            f"- **Impact:** {self.impact or 'n/a'}",
            f"- **Description:** {self.description or 'n/a'}",
            f"- **Fingerprint:** {self.fingerprint or 'n/a'}",
            f"- **Runbook:** {self.runbook_name}",
            "",
            "## Timeline",
            "",
            "| time (UTC) | event | detail |",
            "|---|---|---|",
        ]
        for ts, event, detail in self.timeline:
            safe = detail.replace("|", "\\|").replace("\n", " ")[:400]
            lines.append(f"| {ts} | {event} | {safe} |")
        lines += ["", "_Generated by the Financial Statement on-call responder agent "
                      "(deterministic runbook engine — see oncall-agent/README.md)._", ""]
        return "\n".join(lines)


def write_report(inc: Incident, report_dir: str | Path) -> str:
    d = Path(report_dir)
    d.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    fp = (inc.fingerprint or "nofp")[:8]
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", inc.alertname).strip("-")[:64] or "alert"
    path = d / f"{stamp}-{safe_name}-{fp}.md"
    path.write_text(inc.to_markdown())
    inc.report_path = str(path)
    return str(path)


# ---------------------------------------------------------------- the engine

class OncallEngine:
    def __init__(self, cfg: dict, cwd: str = "."):
        self.cfg = cfg
        self.cwd = cwd
        self.defaults = cfg.get("defaults", {})
        self._lock = threading.Lock()
        self._last_action: dict[str, float] = {}   # fingerprint → epoch of last remediation
        self.incidents: list[Incident] = []

    # -- alertmanager webhook payload → normalized alerts -------------------
    @staticmethod
    def parse_alerts(payload: dict) -> list[dict]:
        out = []
        for a in payload.get("alerts", []):
            labels = a.get("labels", {})
            ann = a.get("annotations", {})
            out.append({
                "status": a.get("status", "firing"),
                "alertname": labels.get("alertname", "UnnamedAlert"),
                "severity": labels.get("severity", "unknown"),
                "summary": ann.get("summary", ""),
                "description": ann.get("description", ""),
                "impact": ann.get("impact", ""),
                "fingerprint": a.get("fingerprint", ""),
            })
        return out

    def _in_cooldown(self, fingerprint: str) -> bool:
        cooldown = float(self.defaults.get("cooldown_seconds", 300))
        with self._lock:
            last = self._last_action.get(fingerprint, 0.0)
            return bool(fingerprint and last and time.time() - last < cooldown)

    def _mark_action(self, fingerprint: str) -> None:
        if fingerprint:
            with self._lock:
                self._last_action[fingerprint] = time.time()

    def handle_alert(self, alert: dict) -> Incident:
        inc = Incident(alertname=alert["alertname"], severity=alert["severity"],
                       summary=alert["summary"], description=alert["description"],
                       impact=alert["impact"], fingerprint=alert["fingerprint"])
        timeout = int(self.defaults.get("command_timeout_seconds", 90))
        report_dir = Path(os.environ.get(
            "ONCALL_REPORT_DIR", self.defaults.get("report_dir", "ops/incidents")))
        if not report_dir.is_absolute():
            report_dir = Path(self.cwd) / report_dir

        if alert["status"] == "resolved":
            inc.status = "resolved"
            inc.log("resolved", "Alertmanager reports the alert resolved — no action taken.")
            write_report(inc, report_dir)
            self.incidents.append(inc)
            return inc

        inc.log("received", f"firing alert {alert['alertname']} ({alert['severity']})")
        name, rb = match_runbook(alert["alertname"], self.cfg)
        inc.runbook_name = name
        if not rb:
            inc.status = "escalated"
            inc.log("escalate", "no runbook configured at all — human triage required")
            write_report(inc, report_dir)
            self.incidents.append(inc)
            return inc

        if self._in_cooldown(alert["fingerprint"]):
            inc.status = "suppressed"
            inc.log(
                "cooldown",
                f"same alert remediated < {self.defaults.get('cooldown_seconds', 300)}s ago — suppressed",
            )
            write_report(inc, report_dir)
            self.incidents.append(inc)
            return inc

        for key, event in (("diagnose", "diagnose"), ("logs", "collect-logs")):
            cmd = rb.get(key)
            if cmd:
                rc, out = run_command(cmd, self.cwd, timeout)
                inc.log(event, f"rc={rc} :: {out}")

        action = rb.get("action", "")
        escalate = rb.get("escalate", "Human triage required.")
        if not action:
            inc.status = "escalated"
            inc.log("escalate", f"no automated action for {name}: {escalate}")
            write_report(inc, report_dir)
            self.incidents.append(inc)
            return inc

        rc, out = run_command(action, self.cwd, timeout)
        inc.log("action", f"rc={rc} :: {action} :: {out}")
        if rc != 0:
            inc.status = "escalated"
            inc.log("escalate", f"action failed (rc={rc}): {escalate}")
            write_report(inc, report_dir)
            self.incidents.append(inc)
            return inc

        self._mark_action(alert["fingerprint"])
        verify_url = rb.get("verify_url", "")
        if verify_url:
            ok, tries = verify_recovery(
                verify_url, int(rb.get("verify_attempts", 6)),
                float(rb.get("verify_delay_seconds", 5)))
            if ok:
                inc.status = "remediated"
                inc.log("verify", f"recovered after {tries} attempt(s): {verify_url}")
            else:
                inc.status = "escalated"
                inc.log("verify-failed", f"{verify_url} still failing after {tries} attempts")
                inc.log("escalate", escalate)
        else:
            inc.status = "remediated"
            inc.log("verify", "no verify_url configured — action reported success")

        write_report(inc, report_dir)
        self.incidents.append(inc)
        return inc

    def process_payload(self, payload: dict) -> list[Incident]:
        return [self.handle_alert(a) for a in self.parse_alerts(payload)]


# ---------------------------------------------------------------- webhook server

ENGINE: OncallEngine | None = None


class WebhookHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/healthz":
            n = len(ENGINE.incidents) if ENGINE else 0
            self._send(200, {"status": "ok", "incidents_handled": n})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/alerts":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError) as e:
            self._send(400, {"error": f"bad payload: {e}"})
            return
        alerts = payload.get("alerts", [])
        # respond fast; Alertmanager retries otherwise. Work happens in a thread.
        threading.Thread(target=ENGINE.process_payload, args=(payload,), daemon=True).start()
        self._send(200, {"received": len(alerts)})

    def log_message(self, fmt, *args):  # keep stdout clean; incidents are the record
        pass


def serve(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"[oncall-agent] listening on :{port} — POST /alerts (Alertmanager webhook), GET /healthz",
          flush=True)
    server.serve_forever()


def main() -> None:
    global ENGINE
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Financial Statement on-call responder agent")
    ap.add_argument("--runbooks", default=str(here / "runbooks.yaml"))
    ap.add_argument("--cwd", default=str(here.parent), help="repo root (docker compose context)")
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--payload", help="process one Alertmanager payload JSON file and exit")
    args = ap.parse_args()

    ENGINE = OncallEngine(load_runbooks(args.runbooks), cwd=args.cwd)
    if args.payload:
        payload = json.loads(Path(args.payload).read_text())
        for inc in ENGINE.process_payload(payload):
            print(f"[oncall-agent] {inc.alertname}: {inc.status} → {inc.report_path}")
        return
    serve(args.port)


if __name__ == "__main__":
    main()

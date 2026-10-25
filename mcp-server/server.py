"""Financial Statement MCP server — READ-ONLY filing tools for coding agents (stdio transport).

Design (see security/agent-security.md):
  * no mutating tools exist — the agent can look, never touch;
  * the backend's RBAC still applies: the server has no privilege beyond FS_TOKEN;
  * no token ⇒ tools refuse to run (fail closed).

Run:  pip install -r mcp-server/requirements.txt
      FS_API_URL=http://localhost:8000 FS_TOKEN=<jwt> python mcp-server/server.py
"""
import os

import httpx
from mcp.server.fastmcp import FastMCP

BASE = os.environ.get("FS_API_URL", "http://localhost:8000").rstrip("/")
TOKEN = os.environ.get("FS_TOKEN", "")

mcp = FastMCP("financial-statement")


def _get(path: str, **params):
    if not TOKEN:
        raise RuntimeError("FS_TOKEN is not set — refusing to call the API unauthenticated")
    resp = httpx.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {TOKEN}"},
                     params=params or None, timeout=30.0)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def health() -> dict:
    """Backend liveness + which AI provider is active."""
    return {"healthz": _get("/healthz"), "version": _get("/version")}


@mcp.tool()
def list_filings(status: str = "") -> list:
    """List filings visible to the token's user. Optional status filter
    (draft|submitted|in_review|changes_requested|accepted|rejected)."""
    return _get("/api/filings", **({"status": status} if status else {}))


@mcp.tool()
def get_filing(filing_id: int) -> dict:
    """One filing: status, fiscal year, deadline."""
    return _get(f"/api/filings/{filing_id}")


@mcp.tool()
def get_statement(filing_id: int, kind: str = "pl") -> dict:
    """Latest generated statement. kind: 'pl' (profit & loss), 'bs' (balance sheet) or
    'cf' (cash flow, indirect method — exists only when a prior-year balance sheet was
    generated). All figures are server-computed; never recalculate them yourself."""
    return _get(f"/api/filings/{filing_id}/statements/{kind}")


@mcp.tool()
def get_latest_validation(filing_id: int) -> dict:
    """Latest validation run: rule-by-rule results (R001..R008) with severities."""
    return _get(f"/api/filings/{filing_id}/validations/latest")


@mcp.tool()
def get_ratios(filing_id: int) -> list:
    """Financial ratios with formula strings and interpretations (current/quick, D/E,
    margins, ROE/ROA, asset turnover, EBITDA). Server-computed — quote, never recompute."""
    return _get(f"/api/filings/{filing_id}/ratios")


@mcp.tool()
def list_anomalies(filing_id: int) -> list:
    """Year-over-year anomalies flagged by rule R006, with any AI explanations."""
    return _get(f"/api/filings/{filing_id}/anomalies")


@mcp.tool()
def list_notes(filing_id: int) -> list:
    """Notes to the accounts: AI drafts and human-finalized texts."""
    return _get(f"/api/filings/{filing_id}/notes")


@mcp.tool()
def get_checklist(filing_id: int) -> list:
    """Filing checklist computed from real state (8 items)."""
    return _get(f"/api/filings/{filing_id}/checklist")


@mcp.tool()
def review_history(filing_id: int) -> dict:
    """Workflow transitions and comments — the review trail."""
    return {"events": _get(f"/api/filings/{filing_id}/review/events"),
            "comments": _get(f"/api/filings/{filing_id}/comments")}


if __name__ == "__main__":
    mcp.run()

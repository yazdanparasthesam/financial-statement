# Financial Statement MCP Server (read-only)

Exposes the running Financial Statement API to coding agents (Claude Code, Copilot CLI, any MCP client)
as **read-only tools**: `health`, `list_filings`, `get_filing`, `get_statement` (pl/bs/cf),
`get_latest_validation`, `get_ratios`, `list_anomalies`, `list_notes`, `get_checklist`,
`review_history`.

## Why read-only

The extension pack's permission model (docs/permissions.md) gives agents *sight*, never
*reach*: mutations happen only through the authenticated UI/API where RBAC, workflow gates
and the audit log apply. See security/agent-security.md for the threat model.

## Setup

```bash
pip install -r mcp-server/requirements.txt

# token: log in as any demo user and copy the access_token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"reviewer@fsapp.dev","password":"financial-statement-demo-123"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

FS_API_URL=http://localhost:8000 FS_TOKEN="$TOKEN" python mcp-server/server.py
```

Client config example (Claude Code `claude mcp add`):

```json
{
  "mcpServers": {
    "financial-statement": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "env": {"FS_API_URL": "http://localhost:8000", "FS_TOKEN": "<jwt>"}
    }
  }
}
```

## Demo session (to be recorded at M8)

Planned transcript: agent lists filings → picks the accepted one → reads validation +
anomalies → writes an audit memo using only server-provided figures. Recorded output goes
to `custom-agent/validation-auditor.md` §Example run.

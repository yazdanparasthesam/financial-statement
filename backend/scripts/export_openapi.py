#!/usr/bin/env python3
"""Regenerate the root openapi.yaml from the running app definition.

The committed openapi.yaml is the CONTRACT (criterion 5); this script keeps it
byte-accurate against the implementation, and tests/integration/test_contract.py
fails CI if anyone edits one side without the other (`make openapi` to resync).
"""
import pathlib
import sys

import yaml

BACKEND = pathlib.Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402

spec = app.openapi()
spec["info"]["title"] = "Financial Statement API"
spec["info"]["description"] = (
    "AI-assisted financial statements & tax filing platform.\n\n"
    "**Contract-first:** this file is the single source of truth for the frontend client "
    "and backend tests. Deterministic core (statements, validation, workflow) computes all "
    "figures; AI endpoints (`tags: ai`) only explain/draft/suggest and are logged to "
    "`ai_requests`. Roles: `preparer` (owns companies/filings) and `reviewer` (review "
    "workflow). All endpoints under `/api` require `Bearer` auth except `/api/auth/register`, "
    "`/api/auth/login`, `/healthz`, `/version`."
)
spec["info"]["x-project"] = "DataTalksClub AI Dev Tools Zoomcamp 2026 — Final Project"
spec["servers"] = [
    {"url": "http://localhost:8000", "description": "local (docker compose / uvicorn)"},
    {"url": "https://financial-statement-api.onrender.com", "description": "production (Render; placeholder until M7)"},
]
out = ROOT / "openapi.yaml"
out.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=110))
print(f"wrote {out} ({len(spec['paths'])} paths)")

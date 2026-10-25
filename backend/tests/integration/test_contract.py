"""Contract test: committed openapi.yaml ⇄ live app spec. Drift = CI red (criterion 5)."""
import pathlib

import pytest
import yaml

from app.main import app

ROOT = pathlib.Path(__file__).resolve().parents[3]
METHODS = ("get", "post", "put", "patch", "delete")


@pytest.mark.integration
def test_contract_has_no_drift():
    spec_file = yaml.safe_load((ROOT / "openapi.yaml").read_text())
    live = app.openapi()["paths"]

    missing = [f"{m.upper()} {p}" for p, ms in spec_file["paths"].items()
               for m in ms if m in METHODS and (p not in live or m not in live[p])]
    assert not missing, f"Contract lists endpoints the app lacks (run `make openapi`): {missing}"

    undocumented = [f"{m.upper()} {p}" for p, ms in live.items() if p.startswith("/api")
                    for m in ms if m in METHODS
                    and (p not in spec_file["paths"] or m not in spec_file["paths"][p])]
    assert not undocumented, f"App has endpoints missing from openapi.yaml (run `make openapi`): {undocumented}"


@pytest.mark.integration
def test_contract_metadata():
    spec = yaml.safe_load((ROOT / "openapi.yaml").read_text())
    assert spec["openapi"].startswith("3.1")
    assert spec["info"]["title"] == "Financial Statement API"
    assert any("localhost" in s["url"] for s in spec["servers"])

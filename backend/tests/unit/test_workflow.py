import pytest

from app.domain.workflow import STATUSES, allowed_actions, can_transition


@pytest.mark.unit
def test_happy_path():
    ok, to = can_transition("draft", "submit", "preparer")
    assert ok and to == "submitted"
    ok, to = can_transition("submitted", "start_review", "reviewer")
    assert ok and to == "in_review"
    ok, to = can_transition("in_review", "accept", "reviewer")
    assert ok and to == "accepted"


@pytest.mark.unit
def test_wrong_status_rejected():
    ok, reason = can_transition("draft", "accept", "reviewer")
    assert not ok and "requires status" in reason


@pytest.mark.unit
def test_wrong_role_rejected():
    ok, reason = can_transition("draft", "submit", "reviewer")
    assert not ok and "requires role" in reason


@pytest.mark.unit
def test_unknown_action():
    ok, reason = can_transition("draft", "teleport", "preparer")
    assert not ok and "Unknown action" in reason


@pytest.mark.unit
def test_changes_requested_loop():
    ok, _ = can_transition("in_review", "request_changes", "reviewer")
    assert ok
    ok, _ = can_transition("changes_requested", "reopen", "preparer")
    assert ok
    ok, _ = can_transition("draft", "submit", "preparer")
    assert ok


@pytest.mark.unit
def test_allowed_actions_view():
    assert allowed_actions("draft", "preparer") == ["submit"]
    assert sorted(allowed_actions("in_review", "reviewer")) == ["accept", "reject", "request_changes"]
    assert allowed_actions("accepted", "reviewer") == []
    assert set(STATUSES) == {"draft", "submitted", "in_review", "changes_requested", "accepted", "rejected"}

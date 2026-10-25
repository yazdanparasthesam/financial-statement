"""Submission/review state machine. Pure data + pure function — routers enforce, tests prove."""

STATUSES = ["draft", "submitted", "in_review", "changes_requested", "accepted", "rejected"]

# action -> (from_status, to_status, required_role)
TRANSITIONS: dict[str, tuple[str, str, str]] = {
    "submit": ("draft", "submitted", "preparer"),
    "reopen": ("changes_requested", "draft", "preparer"),
    "start_review": ("submitted", "in_review", "reviewer"),
    "request_changes": ("in_review", "changes_requested", "reviewer"),
    "accept": ("in_review", "accepted", "reviewer"),
    "reject": ("in_review", "rejected", "reviewer"),
}


def can_transition(status: str, action: str, role: str) -> tuple[bool, str]:
    if action not in TRANSITIONS:
        return False, f"Unknown action '{action}'. Valid: {', '.join(sorted(TRANSITIONS))}"
    frm, to, required_role = TRANSITIONS[action]
    if status != frm:
        return False, f"Action '{action}' requires status '{frm}', filing is '{status}'."
    if role != required_role:
        return False, f"Action '{action}' requires role '{required_role}', user is '{role}'."
    return True, to


def allowed_actions(status: str, role: str) -> list[str]:
    return [a for a, (frm, _, r) in TRANSITIONS.items() if frm == status and r == role]

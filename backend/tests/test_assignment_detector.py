from app.services.assignment_detector import assignment_fingerprint, classify_workflow, diff_assignment


def test_assignment_fingerprint_is_stable():
    a = {"title": "K-Means", "description": "Explain clustering", "deadline": "2026-11-30T12:00:00+00:00"}
    b = dict(a)
    assert assignment_fingerprint(a) == assignment_fingerprint(b)


def test_assignment_fingerprint_changes_when_deadline_changes():
    a = {"title": "K-Means", "deadline": "2026-11-30T12:00:00+00:00"}
    b = {"title": "K-Means", "deadline": "2026-12-01T12:00:00+00:00"}
    assert assignment_fingerprint(a) != assignment_fingerprint(b)


def test_classify_workflow_does_not_treat_closed_as_submitted():
    assert classify_workflow("Closed", None, False) == "pending"
    assert classify_workflow("Submitted", None, False) == "submitted"
    assert classify_workflow("Ongoing", None, False) == "new"


def test_diff_assignment_finds_deadline_update():
    old = {"title": "Report", "deadline": "2026-11-25T00:00:00+00:00"}
    new = {"title": "Report", "deadline": "2026-11-26T00:00:00+00:00"}
    status, events = diff_assignment(old, new)
    assert status == "updated"
    assert events[0]["event_type"] == "deadline_changed"

from app.services.analytics_service import assignment_analytics


def test_assignment_analytics_counts_subjects_and_submissions():
    data = [
        {"workflow_status": "new", "subject_name": "Data Mining", "portal_is_submitted": False},
        {"workflow_status": "in_progress", "subject_name": "Data Mining", "portal_is_submitted": False},
        {"workflow_status": "ai_generated", "subject_name": "Machine Learning", "portal_is_submitted": True},
    ]
    result = assignment_analytics(data)
    assert result["total"] == 3
    assert result["new"] == 1
    assert result["in_progress"] == 1
    assert result["submitted"] == 1
    assert result["by_subject"] == {"Data Mining": 2, "Machine Learning": 1}

from app.integrations.digiicampus.normalizers import normalize_assignments, normalize_courses


def test_normalize_courses_from_wrapped_payload():
    payload = {"data": [{"classId": 10044, "className": "Machine Learning", "courseCode": "MDS305", "facultyName": "Faculty"}]}
    rows = normalize_courses(payload)
    assert rows[0]["external_class_id"] == "10044"
    assert rows[0]["course_name"] == "Machine Learning"
    assert rows[0]["course_code"] == "MDS305"


def test_normalize_assignments_maps_due_date_and_submission_fields():
    payload = {"assignments": [{
        "assignmentId": 44,
        "classId": 10044,
        "assignmentName": "MapReduce Word Count",
        "dueDate": "Nov 30, 2026, 11:59 PM",
        "submissionType": "Online Submissions",
        "assignmentType": "Class Assignment",
        "grading": "Graded Assignment",
        "totalMarks": 25,
    }]}
    rows = normalize_assignments(payload, "10044")
    assert rows[0]["external_assignment_id"] == "44"
    assert rows[0]["title"] == "MapReduce Word Count"
    assert rows[0]["deadline"].startswith("2026-11-30T")
    assert rows[0]["submission_type"] == "Online Submissions"
    assert rows[0]["total_marks"] == 25


def test_normalize_assignment_does_not_use_ukid_as_assignment_id():
    payload = {"data": [{"ukid": 1234, "assignmentName": "No external ID"}]}
    assert normalize_assignments(payload) == []

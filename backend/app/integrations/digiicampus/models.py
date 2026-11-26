from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PortalCourse(BaseModel):
    model_config = ConfigDict(extra="allow")
    external_course_id: str | None = None
    external_class_id: str | None = None
    course_name: str
    course_code: str | None = None
    faculty_name: str | None = None
    course_type: str | None = None
    course_status: str | None = None


class PortalAssignment(BaseModel):
    model_config = ConfigDict(extra="allow")
    external_assignment_id: str
    external_class_id: str | None = None
    title: str
    description: str | None = None
    instructions: str | None = None
    start_at: datetime | None = None
    deadline: datetime | None = None
    submission_type: str | None = None
    assignment_type: str | None = None
    grading_type: str | None = None
    total_marks: float | None = None
    portal_status: str | None = None
    source_url: str | None = None

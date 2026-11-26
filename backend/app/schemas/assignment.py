from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    subject_id: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    total_marks: float | None = Field(default=None, ge=0)
    priority: Literal["low", "medium", "high"] = "medium"


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    deadline: datetime | None = None
    priority: Literal["low", "medium", "high"] | None = None
    workflow_status: Literal["new", "pending", "in_progress", "ai_generated", "awaiting_approval"] | None = None


class GenerateAnswerRequest(BaseModel):
    assignment_id: str | None = None
    question: str = Field(min_length=3, max_length=20000)
    subject: str | None = None
    marks: float | None = Field(default=None, ge=0)
    answer_length: Literal["short", "medium", "detailed"] = "medium"
    language: Literal["English", "Bengali", "Hindi"] = "English"
    style: Literal["simple_academic", "exam_oriented", "detailed_academic"] = "exam_oriented"


class SummaryRequest(BaseModel):
    assignment_id: str

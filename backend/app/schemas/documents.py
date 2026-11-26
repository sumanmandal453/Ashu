from typing import Literal
from pydantic import BaseModel, Field


class DocumentGenerateRequest(BaseModel):
    assignment_id: str
    format: Literal["pdf", "docx"] = "pdf"
    include_cover_page: bool = True
    font_size: int = Field(default=11, ge=8, le=18)

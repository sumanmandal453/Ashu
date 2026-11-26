from typing import Any
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "OK"


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class PaginatedResponse(BaseModel):
    success: bool = True
    data: list[Any] = Field(default_factory=list)
    pagination: Pagination

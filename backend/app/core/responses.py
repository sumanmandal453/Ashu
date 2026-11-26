from typing import Any


def success(data: Any, message: str = "OK") -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def paginated(data: list[Any], page: int, page_size: int, total: int) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        },
    }

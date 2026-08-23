from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.extra = extra or {}
        super().__init__(detail)


async def problem_handler(request: Request, exc: ProblemError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        media_type="application/problem+json",
        content={
            "type": f"https://api.runlete.com/problems/{exc.code}",
            "title": exc.title,
            "status": exc.status,
            "detail": exc.detail,
            "instance": str(request.url.path),
            "code": exc.code,
            **exc.extra,
        },
    )


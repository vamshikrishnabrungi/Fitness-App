from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .config import get_settings
from .http_client import http_client


class OpenAIResponseError(RuntimeError):
    """Safe provider failure that never exposes credentials or response bodies."""


@dataclass(frozen=True)
class StructuredResponse:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


def _output_text(payload: dict[str, Any]) -> str:
    refusal: str | None = None
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") == "output_text" and content.get("text"):
                return str(content["text"])
            if content.get("type") == "refusal":
                refusal = str(content.get("refusal") or "request refused")
    if refusal:
        raise OpenAIResponseError(refusal[:240])
    raise OpenAIResponseError("OpenAI returned no structured output")


async def create_structured_response(
    *,
    model: str,
    system: str,
    user_content: str | list[dict[str, Any]],
    schema_name: str,
    schema: dict[str, Any],
    strict: bool,
    max_output_tokens: int,
    timeout_seconds: float = 120.0,
) -> StructuredResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        raise OpenAIResponseError("OPENAI_API_KEY is not configured")

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": strict,
                "schema": schema,
            }
        },
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    if model.startswith(("gpt-5", "o1", "o3", "o4")):
        payload["reasoning"] = {"effort": "low"}
    try:
        response = await http_client().post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
        )
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as exc:
        raise OpenAIResponseError(f"OpenAI request failed with HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenAIResponseError("OpenAI request failed") from exc

    if body.get("status") != "completed":
        reason = (body.get("incomplete_details") or {}).get("reason") or body.get("status") or "unknown"
        raise OpenAIResponseError(f"OpenAI response was not completed: {reason}")
    usage = body.get("usage") or {}
    return StructuredResponse(
        text=_output_text(body),
        model=str(body.get("model") or model),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )

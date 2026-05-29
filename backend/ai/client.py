"""LLM client factory using emergentintegrations.

All AI services in the backend go through this thin wrapper. We use the
Emergent universal key with Anthropic Claude Sonnet 4.5 by default, but the
underlying model can be swapped via env vars (AI_*_MODEL).
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from backend.core.config import EMERGENT_LLM_KEY

logger = logging.getLogger(__name__)

try:
    from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage  # type: ignore
except Exception:  # pragma: no cover
    LlmChat = None  # type: ignore
    UserMessage = None  # type: ignore
    ImageContent = None  # type: ignore


def llm_available() -> bool:
    return bool(EMERGENT_LLM_KEY) and LlmChat is not None and UserMessage is not None


def _strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()


def parse_json_response(raw: str) -> Dict[str, Any]:
    """Best-effort JSON parsing from an LLM reply that may include prose."""
    cleaned = _strip_code_fence(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Look for the first '{' and try to match a balanced object
    start = cleaned.find('{')
    if start == -1:
        raise ValueError('LLM did not return valid JSON')

    depth = 0
    in_string = False
    escape = False
    end = -1
    for idx in range(start, len(cleaned)):
        ch = cleaned[idx]
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = idx
                break

    if end > start:
        candidate = cleaned[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # last resort: log a snippet for debugging
    snippet = cleaned[:300].replace('\n', ' ')
    logger.warning('Failed to parse LLM JSON. First 300 chars: %s', snippet)
    raise ValueError('LLM did not return valid JSON')


async def chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    provider: str = 'anthropic',
    session_id: Optional[str] = None,
    images_base64: Optional[List[str]] = None,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    """Send a single-shot user message and return parsed JSON.

    Raises ValueError if the model output cannot be parsed or RuntimeError if
    the LLM is not configured.
    """
    if not llm_available():
        raise RuntimeError('LLM not configured: missing EMERGENT_LLM_KEY or emergentintegrations')

    full_system = (
        system_prompt.rstrip()
        + '\n\nRespond with ONLY valid JSON. No prose, no markdown, no code fences. '
        'Do not invent fields that are not in the schema.'
    )

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id or f'sftc-{uuid.uuid4()}',
        system_message=full_system,
    ).with_model(provider, model).with_params(max_tokens=max_tokens)

    file_contents = None
    if images_base64 and ImageContent is not None:
        file_contents = [ImageContent(image_base64=img) for img in images_base64 if img]

    message = UserMessage(text=user_prompt, file_contents=file_contents)
    raw = await chat.send_message(message)
    return parse_json_response(str(raw))

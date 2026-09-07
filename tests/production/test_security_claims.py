from __future__ import annotations

import asyncio

import pytest

from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id


def test_malformed_subject_claim_is_a_controlled_401() -> None:
    with pytest.raises(ProblemError) as error:
        asyncio.run(current_user_id({"sub": "not-a-uuid"}))
    assert error.value.status == 401
    assert error.value.code == "invalid_token"

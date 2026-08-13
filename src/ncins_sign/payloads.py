from __future__ import annotations

from copy import deepcopy
from typing import Any

from ncins_sign.config import get_settings


def example_payload() -> dict[str, Any]:
    """Canonical example from create-operation curl."""
    settings = get_settings()
    return {
        "userId": settings.body_user_id,
        "clientId": settings.body_client_id,
        "documentId": settings.body_document_id,
    }


def payload_with(**overrides: Any) -> dict[str, Any]:
    data = example_payload()
    data.update(overrides)
    return data


def clone(payload: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(payload)

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateOperationRequest(BaseModel):
    """Request body for POST /v1/sign/create-operation."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    user_id: str = Field(..., alias="userId", min_length=1)
    client_id: str = Field(..., alias="clientId", min_length=1)
    document_id: str = Field(..., alias="documentId", min_length=1)

    @field_validator("document_id")
    @classmethod
    def validate_document_id_uuid(cls, value: str) -> str:
        try:
            UUID(str(value))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("documentId must be a valid UUID") from exc
        return str(value)

    def to_api_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, mode="json")


class CreateOperationResponse(BaseModel):
    """
    Flexible response model.

    Exact schema may vary; we look for a recognizable operation identifier.
    """

    model_config = ConfigDict(extra="allow")

    @staticmethod
    def extract_operation_id(payload: dict[str, Any]) -> str:
        candidates = (
            "operationId",
            "signOperationId",
            "id",
            "uuid",
            "operationUUID",
            "operation_id",
        )
        for key in candidates:
            if key in payload and payload[key] is not None and str(payload[key]).strip():
                return str(payload[key])

        for nested_key in ("data", "result", "operation", "payload"):
            nested = payload.get(nested_key)
            if isinstance(nested, dict):
                for key in candidates:
                    if key in nested and nested[key] is not None and str(nested[key]).strip():
                        return str(nested[key])

        raise AssertionError(
            "Response does not contain a recognizable operation id field. "
            f"Got keys: {sorted(payload.keys())}"
        )

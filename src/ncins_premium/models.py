from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class InsuranceObject(BaseModel):
    """Insured employee object from NCINS-200 example request."""

    model_config = ConfigDict(extra="forbid")

    employee_fio: str = Field(..., alias="employeeFIO", min_length=1)
    employee_birth_date: date = Field(..., alias="employeeBirthDate")
    employee_email: EmailStr = Field(..., alias="employeeEmail")
    employee_phone_number: str = Field(..., alias="employeePhoneNumber", min_length=1)

    @field_validator("employee_phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("employeePhoneNumber must contain at least 10 digits")
        return value


class CalculatePremiumRequest(BaseModel):
    """Request body for POST /v1/ins-premium/calculate."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    program_id: int = Field(..., alias="programId", gt=0)
    duration: int = Field(..., gt=0, description="Insurance duration in months")
    insurance_sum: Decimal = Field(..., alias="insuranceSum", gt=0)
    insurance_objects: list[InsuranceObject] = Field(
        ..., alias="insuranceObjects", min_length=1
    )

    def to_api_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, mode="json")


class CalculatePremiumResponse(BaseModel):
    """
    Flexible response model.

    Exact schema is in Confluence (unavailable from this environment).
    We accept common premium field names and require a numeric premium > 0.
    """

    model_config = ConfigDict(extra="allow")

    @staticmethod
    def extract_premium(payload: dict[str, Any]) -> Decimal:
        candidates = (
            "insurancePremium",
            "premium",
            "premiumAmount",
            "calculatedPremium",
            "insPremium",
            "amount",
        )
        for key in candidates:
            if key in payload and payload[key] is not None:
                return Decimal(str(payload[key]))

        # nested variants
        for nested_key in ("data", "result", "calculation"):
            nested = payload.get(nested_key)
            if isinstance(nested, dict):
                for key in candidates:
                    if key in nested and nested[key] is not None:
                        return Decimal(str(nested[key]))

        raise AssertionError(
            "Response does not contain a recognizable premium field. "
            f"Got keys: {sorted(payload.keys())}"
        )


def is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False

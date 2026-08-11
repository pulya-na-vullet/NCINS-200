from __future__ import annotations

from copy import deepcopy
from typing import Any


def example_payload() -> dict[str, Any]:
    """Canonical example from NCINS-200 comment (07.08.2026)."""
    return {
        "programId": 3,
        "duration": 12,
        "insuranceSum": 500000.00,
        "insuranceObjects": [
            {
                "employeeFIO": "Сидоров Иван Сергеевич",
                "employeeBirthDate": "1995-05-20",
                "employeeEmail": "sidorov@example.com",
                "employeePhoneNumber": "+79991112233",
            }
        ],
    }


def payload_with(**overrides: Any) -> dict[str, Any]:
    data = example_payload()
    data.update(overrides)
    return data


def clone(payload: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(payload)

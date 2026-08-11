from __future__ import annotations

from decimal import Decimal

import pytest

from ncins_premium.models import CalculatePremiumResponse


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"insurancePremium": 1234.56}, Decimal("1234.56")),
        ({"premium": "100.00"}, Decimal("100.00")),
        ({"premiumAmount": 10}, Decimal("10")),
        ({"data": {"calculatedPremium": 55.5}}, Decimal("55.5")),
        ({"result": {"insPremium": "9.99"}}, Decimal("9.99")),
        ({"calculation": {"amount": 1}}, Decimal("1")),
    ],
)
def test_extract_premium_supports_common_shapes(payload, expected):
    assert CalculatePremiumResponse.extract_premium(payload) == expected


@pytest.mark.unit
def test_extract_premium_raises_when_absent():
    with pytest.raises(AssertionError):
        CalculatePremiumResponse.extract_premium({"status": "ok"})

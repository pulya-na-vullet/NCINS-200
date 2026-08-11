"""1, 8, 24, 25, 26 — позитивные проверки метода calculate."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ncins_premium.models import CalculatePremiumResponse
from ncins_premium.payloads import clone, example_payload, payload_with

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]


@pytest.mark.smoke
def test_01_happy_path_from_ncins_200_example(client, valid_payload):
    """№1: пример запроса из PDF/комментария → 200 и премия > 0."""
    response = client.calculate(valid_payload)
    assert response.status_code == 200, response.text
    premium = CalculatePremiumResponse.extract_premium(response.json())
    assert premium > 0


def test_08_valid_headers_from_postman_accepted(client, valid_payload):
    """№8: A-* headers как в Postman Insurance API Tests → 200."""
    response = client.calculate(
        valid_payload,
        headers={
            "A-userId": "123456",
            "A-customerId": "123456",
            "A-clientType": "MOBILE",
            "A-channelId": "INTERNET",
        },
    )
    assert response.status_code == 200, response.text


def test_24_multiple_insurance_objects(client):
    """№24: два застрахованных в insuranceObjects → 200 и премия > 0."""
    payload = example_payload()
    payload["insuranceObjects"].append(
        {
            "employeeFIO": "Иванова Анна Петровна",
            "employeeBirthDate": "1988-11-03",
            "employeeEmail": "ivanova@example.com",
            "employeePhoneNumber": "+79992223344",
        }
    )
    response = client.calculate(payload)
    assert response.status_code == 200, response.text
    assert CalculatePremiumResponse.extract_premium(response.json()) > 0


@pytest.mark.parametrize("duration", [1, 6, 12, 24], ids=["d1", "d6", "d12", "d24"])
def test_25_various_durations(client, duration):
    """№25: разные сроки страхования → 200."""
    response = client.calculate(payload_with(duration=duration))
    assert response.status_code == 200, response.text


def test_26_idempotent_same_request_same_premium(client, valid_payload):
    """№26: два одинаковых запроса дают одну и ту же премию."""
    first = client.calculate(clone(valid_payload))
    second = client.calculate(clone(valid_payload))
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    p1 = CalculatePremiumResponse.extract_premium(first.json())
    p2 = CalculatePremiumResponse.extract_premium(second.json())
    assert p1 == p2
    assert isinstance(p1, Decimal)

from __future__ import annotations

from decimal import Decimal

import pytest

from ncins_premium.models import CalculatePremiumResponse
from ncins_premium.payloads import clone, example_payload, payload_with


pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]


@pytest.mark.smoke
def test_calculate_premium_happy_path_from_ncins_200(client, valid_payload):
    """Пример запроса из комментария NCINS-200 должен успешно рассчитать премию."""
    response = client.calculate(valid_payload)

    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict)
    premium = CalculatePremiumResponse.extract_premium(body)
    assert premium > 0


def test_calculate_premium_with_multiple_insured_objects(client):
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
    premium = CalculatePremiumResponse.extract_premium(response.json())
    assert premium > 0


@pytest.mark.parametrize("duration", [1, 3, 6, 12, 24, 36])
def test_calculate_premium_various_durations(client, duration):
    response = client.calculate(payload_with(duration=duration))
    assert response.status_code == 200, response.text
    premium = CalculatePremiumResponse.extract_premium(response.json())
    assert premium > 0


@pytest.mark.parametrize("insurance_sum", [1, 1000, 500000, 1_000_000, 10_000_000])
def test_calculate_premium_various_sums(client, insurance_sum):
    response = client.calculate(payload_with(insuranceSum=insurance_sum))
    assert response.status_code == 200, response.text
    premium = CalculatePremiumResponse.extract_premium(response.json())
    assert premium > 0


def test_premium_scales_with_insurance_sum(client):
    """При прочих равных большая страховая сумма должна давать не меньшую премию."""
    small = client.calculate(payload_with(insuranceSum=100_000))
    large = client.calculate(payload_with(insuranceSum=1_000_000))

    assert small.status_code == 200, small.text
    assert large.status_code == 200, large.text

    premium_small = CalculatePremiumResponse.extract_premium(small.json())
    premium_large = CalculatePremiumResponse.extract_premium(large.json())
    assert premium_large >= premium_small


def test_response_is_json_and_not_empty(client, valid_payload):
    response = client.calculate(valid_payload)
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("application/json")
    body = response.json()
    assert body


def test_idempotent_same_request_same_premium(client, valid_payload):
    first = client.calculate(clone(valid_payload))
    second = client.calculate(clone(valid_payload))

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    p1 = CalculatePremiumResponse.extract_premium(first.json())
    p2 = CalculatePremiumResponse.extract_premium(second.json())
    assert p1 == p2
    assert isinstance(p1, Decimal)

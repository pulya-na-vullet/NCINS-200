"""Позитивные проверки метода POST /v1/sign/create-operation."""

from __future__ import annotations

import pytest

from ncins_sign.models import CreateOperationResponse
from ncins_sign.payloads import clone, example_payload

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

SUCCESS = {200, 201}


@pytest.mark.smoke
def test_01_happy_path_from_curl_example(client, valid_payload):
    """№1: пример из curl → 200/201 и есть id операции."""
    response = client.create_operation(valid_payload)
    assert response.status_code in SUCCESS, response.text
    body = response.json()
    assert isinstance(body, dict), body
    operation_id = CreateOperationResponse.extract_operation_id(body)
    assert operation_id


def test_02_valid_headers_from_curl_accepted(client, valid_payload):
    """№2: A-* headers как в curl create-operation → 200/201."""
    response = client.create_operation(
        valid_payload,
        headers={
            "A-userId": "123456",
            "A-customerId": "123456",
            "A-clientType": "MOBILE",
            "A-channelId": "nib",
            "A-projectId": "corp-ncinsurance",
        },
    )
    assert response.status_code in SUCCESS, response.text


def test_03_response_is_json_object(client, valid_payload):
    """№3: успешный ответ — JSON-объект."""
    response = client.create_operation(clone(valid_payload))
    assert response.status_code in SUCCESS, response.text
    assert "application/json" in (response.headers.get("Content-Type") or "").lower()
    assert isinstance(response.json(), dict)


def test_04_same_payload_can_be_sent_twice(client):
    """№4: повторный вызов с тем же телом не даёт 5xx."""
    payload = example_payload()
    first = client.create_operation(clone(payload))
    second = client.create_operation(clone(payload))
    assert first.status_code < 500, first.text
    assert second.status_code < 500, second.text
    # оба либо успешны, либо одинаково отклонены бизнес-логикой (не сетевой сбой)
    assert first.status_code in SUCCESS or first.status_code in {400, 404, 409, 422}
    assert second.status_code in SUCCESS or second.status_code in {400, 404, 409, 422}

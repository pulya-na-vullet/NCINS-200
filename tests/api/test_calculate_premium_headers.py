from __future__ import annotations

import pytest

from ncins_premium.payloads import example_payload


pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

AUTH_OR_CLIENT_ERROR = {400, 401, 403, 422}


REQUIRED_HEADERS = [
    "A-userId",
    "A-customerId",
    "A-clientType",
    "A-channelId",
    "A-userIp",
    "A-projectId",
]


@pytest.mark.parametrize("header_name", REQUIRED_HEADERS)
def test_missing_required_header_rejected(client, header_name):
    """Заголовки из скриншота NCINS-200 обязательны для вызова метода."""
    response = client.calculate(example_payload(), omit_headers={header_name})
    assert response.status_code in AUTH_OR_CLIENT_ERROR, response.text


def test_wrong_content_type_rejected(client, settings):
    headers = settings.default_headers()
    headers["Content-Type"] = "text/plain"
    response = client.session.post(
        settings.calculate_url,
        data='{"programId":3}',
        headers=headers,
        timeout=settings.timeout,
    )
    assert response.status_code in AUTH_OR_CLIENT_ERROR | {415}, response.text


def test_get_method_not_allowed(client, settings):
    response = client.session.get(
        settings.calculate_url,
        headers=settings.default_headers(),
        timeout=settings.timeout,
    )
    assert response.status_code in {404, 405}, response.text


def test_put_method_not_allowed(client, settings):
    response = client.session.put(
        settings.calculate_url,
        json=example_payload(),
        headers=settings.default_headers(),
        timeout=settings.timeout,
    )
    assert response.status_code in {404, 405}, response.text


def test_headers_with_valid_values_accepted(client, valid_payload):
    response = client.calculate(
        valid_payload,
        headers={
            "A-userId": "123456",
            "A-customerId": "123456",
            "A-clientType": "XXXXX",
            "A-channelId": "XXXXX",
            "A-userIp": "XXXXX",
            "A-projectId": "XXXXX",
        },
    )
    assert response.status_code == 200, response.text

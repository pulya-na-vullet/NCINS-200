"""Проверки обязательных headers и HTTP-метода create-operation."""

from __future__ import annotations

import pytest

from ncins_sign.payloads import example_payload

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

AUTH_OR_CLIENT_ERROR = {400, 401, 403, 422}

REQUIRED_HEADERS = [
    ("A-userId", "05"),
    ("A-customerId", "06"),
    ("A-clientType", "07"),
    ("A-channelId", "08"),
    ("A-projectId", "09"),
]


@pytest.mark.parametrize("header_name,case_no", REQUIRED_HEADERS)
def test_required_a_header_missing_rejected(client, header_name, case_no):
    """№5–9: отсутствие обязательного A-* header → ошибка клиента/авторизации."""
    response = client.create_operation(example_payload(), omit_headers={header_name})
    assert response.status_code in AUTH_OR_CLIENT_ERROR, response.text


def test_10_without_authorization_rejected(client, settings, valid_payload):
    """№10: без Authorization → 401/403."""
    # обходим автополучение токена: шлём запрос напрямую без Authorization
    headers = settings.default_headers()
    headers.pop("Authorization", None)
    response = client.session.post(
        settings.create_operation_url,
        json=valid_payload,
        headers=headers,
        timeout=settings.timeout,
        verify=settings.api_verify_ssl,
    )
    assert response.status_code in {401, 403}, response.text


def test_11_get_method_not_allowed(client, settings):
    """№11: GET на URL create-operation недопустим → 404/405."""
    response = client.session.get(
        settings.create_operation_url,
        headers=client.headers(),
        timeout=settings.timeout,
        verify=settings.api_verify_ssl,
    )
    assert response.status_code in {404, 405}, response.text


def test_12_wrong_content_type_rejected(client, settings):
    """№12: неверный Content-Type → 400/415/422."""
    headers = client.headers(extra={"Content-Type": "text/plain"})
    response = client.session.post(
        settings.create_operation_url,
        data='{"userId":"XAGA56","clientId":"UAY4DP","documentId":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}',
        headers=headers,
        timeout=settings.timeout,
        verify=settings.api_verify_ssl,
    )
    assert response.status_code in AUTH_OR_CLIENT_ERROR | {415}, response.text

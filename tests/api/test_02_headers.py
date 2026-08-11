"""2–7, 27, 28 — headers и HTTP-метод."""

from __future__ import annotations

import pytest

from ncins_premium.payloads import example_payload

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

AUTH_OR_CLIENT_ERROR = {400, 401, 403, 422}


@pytest.mark.parametrize(
    "header_name,case_no",
    [
        ("A-userId", "02"),
        ("A-customerId", "03"),
        ("A-clientType", "04"),
        ("A-channelId", "05"),
        ("A-userIp", "06"),
        ("A-projectId", "07"),
    ],
)
def test_required_a_header_missing_rejected(client, header_name, case_no):
    """№2–7: отсутствие обязательного A-* header → ошибка клиента/авторизации."""
    response = client.calculate(example_payload(), omit_headers={header_name})
    assert response.status_code in AUTH_OR_CLIENT_ERROR, response.text


def test_27_get_method_not_allowed(client, settings):
    """№27: GET на URL calculate недопустим → 404/405."""
    response = client.session.get(
        settings.calculate_url,
        headers=settings.default_headers(),
        timeout=settings.timeout,
    )
    assert response.status_code in {404, 405}, response.text


def test_28_wrong_content_type_rejected(client, settings):
    """№28: неверный Content-Type → 400/415/422."""
    headers = settings.default_headers()
    headers["Content-Type"] = "text/plain"
    response = client.session.post(
        settings.calculate_url,
        data='{"programId":3}',
        headers=headers,
        timeout=settings.timeout,
    )
    assert response.status_code in AUTH_OR_CLIENT_ERROR | {415}, response.text

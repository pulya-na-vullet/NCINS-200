from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ncins_premium.client import InsPremiumClient
from ncins_premium.config import Settings
from ncins_premium.payloads import example_payload


def _settings(**kwargs) -> Settings:
    base = dict(
        base_url="http://example.test/api",
        timeout=5,
        user_id="123456",
        customer_id="123456",
        client_type="MOBILE",
        channel_id="INTERNET",
        user_ip="",
        project_id="",
        fetch_token=False,
    )
    base.update(kwargs)
    return Settings(**base)


@pytest.mark.unit
def test_default_headers_contain_required_gateway_keys():
    headers = _settings().default_headers()
    assert headers["A-userId"] == "123456"
    assert headers["A-customerId"] == "123456"
    assert headers["A-clientType"] == "MOBILE"
    assert headers["A-channelId"] == "INTERNET"
    assert "A-userIp" not in headers
    assert "A-projectId" not in headers
    assert headers["Content-Type"] == "application/json"


@pytest.mark.unit
def test_calculate_url_built_correctly():
    settings = _settings(base_url="http://example.test/api/")
    assert settings.calculate_url == "http://example.test/api/v1/ins-premium/calculate"


@pytest.mark.unit
def test_client_sends_post_with_json_and_headers():
    settings = _settings(timeout=7, authorization="Bearer test-token")
    session = MagicMock()
    response = MagicMock()
    session.post.return_value = response
    client = InsPremiumClient(settings=settings, session=session)

    payload = example_payload()
    result = client.calculate(payload)

    assert result is response
    session.post.assert_called_once()
    args, kwargs = session.post.call_args
    assert args[0] == settings.calculate_url
    assert kwargs["json"] == payload
    assert kwargs["timeout"] == 7
    assert kwargs["headers"]["A-userId"] == "123456"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.unit
def test_client_can_omit_header():
    settings = _settings()
    session = MagicMock()
    session.post.return_value = MagicMock()
    client = InsPremiumClient(settings=settings, session=session)

    client.calculate(example_payload(), omit_headers={"A-userId"})
    headers = session.post.call_args.kwargs["headers"]
    assert "A-userId" not in headers
    assert "A-customerId" in headers


@pytest.mark.unit
def test_client_fetches_keycloak_token_when_enabled():
    settings = _settings(
        fetch_token=True,
        keycloak_token_url="https://idp.example/token",
        keycloak_client_id="nib-corp-ncins",
        keycloak_client_secret="secret",
    )
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text="{}", headers={})
    with patch("ncins_premium.client.fetch_access_token", return_value="abc123") as mocked:
        client = InsPremiumClient(settings=settings, session=session)
        client.calculate(example_payload())
    mocked.assert_called()
    assert session.post.call_args.kwargs["headers"]["Authorization"] == "Bearer abc123"

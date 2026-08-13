from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ncins_sign.client import SignCreateOperationClient
from ncins_sign.config import Settings
from ncins_sign.payloads import example_payload


def _settings(**kwargs) -> Settings:
    base = dict(
        base_url="http://example.test/api",
        timeout=5,
        user_id="123456",
        customer_id="123456",
        client_type="MOBILE",
        channel_id="nib",
        project_id="corp-ncinsurance",
        user_ip="",
        fetch_token=False,
        api_verify_ssl=False,
    )
    base.update(kwargs)
    return Settings(**base)


@pytest.mark.unit
def test_default_headers_match_curl():
    headers = _settings().default_headers()
    assert headers["A-userId"] == "123456"
    assert headers["A-customerId"] == "123456"
    assert headers["A-clientType"] == "MOBILE"
    assert headers["A-channelId"] == "nib"
    assert headers["A-projectId"] == "corp-ncinsurance"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.unit
def test_create_operation_url_built_correctly():
    settings = _settings(base_url="http://example.test/api/")
    assert settings.create_operation_url == "http://example.test/api/v1/sign/create-operation"


@pytest.mark.unit
def test_client_sends_post_with_json_and_headers():
    settings = _settings(timeout=7, authorization="Bearer test-token")
    session = MagicMock()
    response = MagicMock()
    session.post.return_value = response
    client = SignCreateOperationClient(settings=settings, session=session)

    payload = {
        "userId": "XAGA56",
        "clientId": "UAY4DP",
        "documentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }
    result = client.create_operation(payload)

    assert result is response
    session.post.assert_called_once()
    args, kwargs = session.post.call_args
    assert args[0] == settings.create_operation_url
    assert kwargs["json"] == payload
    assert kwargs["timeout"] == 7
    assert kwargs["verify"] is False
    assert kwargs["headers"]["A-channelId"] == "nib"
    assert kwargs["headers"]["A-projectId"] == "corp-ncinsurance"
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.unit
def test_client_can_omit_header():
    settings = _settings()
    session = MagicMock()
    session.post.return_value = MagicMock()
    client = SignCreateOperationClient(settings=settings, session=session)

    client.create_operation(
        {
            "userId": "XAGA56",
            "clientId": "UAY4DP",
            "documentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
        omit_headers={"A-projectId"},
    )
    headers = session.post.call_args.kwargs["headers"]
    assert "A-projectId" not in headers
    assert "A-userId" in headers


@pytest.mark.unit
def test_client_fetches_keycloak_token_when_enabled():
    settings = _settings(
        fetch_token=True,
        keycloak_token_url="https://idp.example/token",
        keycloak_client_id="nib-corp-ncinsurance-accounting",
        keycloak_client_secret="secret",
    )
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text="{}", headers={})
    with patch("ncins_sign.client.fetch_access_token", return_value="abc123") as mocked:
        client = SignCreateOperationClient(settings=settings, session=session)
        client.create_operation(
            {
                "userId": "XAGA56",
                "clientId": "UAY4DP",
                "documentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            }
        )
    mocked.assert_called()
    assert session.post.call_args.kwargs["headers"]["Authorization"] == "Bearer abc123"


@pytest.mark.unit
def test_example_payload_shape():
    payload = example_payload()
    assert set(payload) == {"userId", "clientId", "documentId"}
    assert payload["userId"]
    assert payload["clientId"]
    assert payload["documentId"]

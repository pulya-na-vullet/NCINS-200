from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ncins_premium.client import InsPremiumClient
from ncins_premium.config import Settings
from ncins_premium.payloads import example_payload


@pytest.mark.unit
def test_default_headers_contain_required_gateway_keys():
    settings = Settings(
        base_url="http://example.test/api",
        timeout=5,
        user_id="123456",
        customer_id="123456",
        client_type="XXXXX",
        channel_id="XXXXX",
        user_ip="XXXXX",
        project_id="XXXXX",
    )
    headers = settings.default_headers()
    assert headers["A-userId"] == "123456"
    assert headers["A-customerId"] == "123456"
    assert headers["A-clientType"] == "XXXXX"
    assert headers["A-channelId"] == "XXXXX"
    assert headers["A-userIp"] == "XXXXX"
    assert headers["A-projectId"] == "XXXXX"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.unit
def test_calculate_url_built_correctly():
    settings = Settings(
        base_url="http://example.test/api/",
        timeout=5,
        user_id="1",
        customer_id="1",
        client_type="x",
        channel_id="x",
        user_ip="x",
        project_id="x",
    )
    assert settings.calculate_url == "http://example.test/api/v1/ins-premium/calculate"


@pytest.mark.unit
def test_client_sends_post_with_json_and_headers():
    settings = Settings(
        base_url="http://example.test/api",
        timeout=7,
        user_id="123456",
        customer_id="123456",
        client_type="XXXXX",
        channel_id="XXXXX",
        user_ip="XXXXX",
        project_id="XXXXX",
    )
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


@pytest.mark.unit
def test_client_can_omit_header():
    settings = Settings(
        base_url="http://example.test/api",
        timeout=5,
        user_id="123456",
        customer_id="123456",
        client_type="XXXXX",
        channel_id="XXXXX",
        user_ip="XXXXX",
        project_id="XXXXX",
    )
    session = MagicMock()
    session.post.return_value = MagicMock()
    client = InsPremiumClient(settings=settings, session=session)

    client.calculate(example_payload(), omit_headers={"A-userId"})
    headers = session.post.call_args.kwargs["headers"]
    assert "A-userId" not in headers
    assert "A-customerId" in headers

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ncins_sign.auth import fetch_access_token, reset_token_cache


@pytest.mark.unit
def test_fetch_access_token_client_credentials():
    reset_token_cache()
    fake = MagicMock()
    fake.status_code = 200
    fake.json.return_value = {"access_token": "tok-1", "expires_in": 300}
    with patch("ncins_sign.auth.requests.post", return_value=fake) as post:
        token = fetch_access_token(
            token_url="https://idp.example/token",
            client_id="nib-corp-ncinsurance-accounting",
            client_secret="secret",
            verify_ssl=False,
        )
    assert token == "tok-1"
    kwargs = post.call_args.kwargs
    assert kwargs["data"]["grant_type"] == "client_credentials"
    assert kwargs["data"]["client_id"] == "nib-corp-ncinsurance-accounting"
    assert kwargs["verify"] is False


@pytest.mark.unit
def test_fetch_access_token_uses_cache():
    reset_token_cache()
    fake = MagicMock()
    fake.status_code = 200
    fake.json.return_value = {"access_token": "tok-cache", "expires_in": 300}
    with patch("ncins_sign.auth.requests.post", return_value=fake) as post:
        t1 = fetch_access_token(
            token_url="https://idp.example/token",
            client_id="c",
            client_secret="s",
        )
        t2 = fetch_access_token(
            token_url="https://idp.example/token",
            client_id="c",
            client_secret="s",
        )
    assert t1 == t2 == "tok-cache"
    assert post.call_count == 1

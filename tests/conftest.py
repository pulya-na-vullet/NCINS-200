from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

import pytest
import requests

from ncins_premium.client import InsPremiumClient
from ncins_premium.config import get_settings
from ncins_premium.payloads import example_payload


def _host_reachable(url: str, timeout: float = 2.0) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def gateway_available(settings) -> bool:
    return _host_reachable(settings.base_url)


@pytest.fixture
def client(settings) -> InsPremiumClient:
    return InsPremiumClient(settings=settings)


@pytest.fixture
def valid_payload() -> dict:
    return example_payload()


@pytest.fixture
def skip_if_gateway_unavailable(gateway_available):
    if not gateway_available and os.getenv("FORCE_INTEGRATION") != "1":
        pytest.skip(
            "Test gateway is not reachable from this environment. "
            "Set FORCE_INTEGRATION=1 to force-run integration tests."
        )


@pytest.fixture
def http_session() -> requests.Session:
    return requests.Session()

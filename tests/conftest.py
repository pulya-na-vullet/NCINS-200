from __future__ import annotations

import logging
import os
import socket
from urllib.parse import urlparse

import pytest
import requests

from ncins_premium.client import InsPremiumClient
from ncins_premium.config import get_settings
from ncins_premium.payloads import example_payload

log = logging.getLogger("ncins200.tests")


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
    s = get_settings()
    log.info("API endpoint: %s", s.calculate_url)
    log.info(
        "Keycloak: env=%s fetch_token=%s token_url=%s",
        s.environment,
        s.fetch_token,
        s.keycloak_token_url,
    )
    return s


@pytest.fixture(scope="session")
def gateway_available(settings) -> bool:
    ok = _host_reachable(settings.base_url)
    log.info("Gateway reachable: %s (%s)", ok, settings.base_url)
    return ok


@pytest.fixture
def client(settings) -> InsPremiumClient:
    return InsPremiumClient(settings=settings)


@pytest.fixture
def valid_payload() -> dict:
    return example_payload()


@pytest.fixture
def skip_if_gateway_unavailable(gateway_available):
    """По умолчанию API-тесты НЕ skip (FORCE_INTEGRATION из app.py).
    Skip только если явно SKIP_IF_OFFLINE=1 и gateway недоступен.
    """
    if gateway_available:
        return
    if os.getenv("SKIP_IF_OFFLINE") == "1" and os.getenv("FORCE_INTEGRATION") != "1":
        pytest.skip("Gateway недоступен и включён SKIP_IF_OFFLINE=1")
    # иначе идём в тест — requests упадёт с понятной сетевой ошибкой


@pytest.fixture
def http_session() -> requests.Session:
    return requests.Session()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    log.info(">>> START %s", item.nodeid)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item):
    yield
    log.info("<<< END   %s", item.nodeid)

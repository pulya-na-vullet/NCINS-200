from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests

log = logging.getLogger("ncins.sign.auth")


@dataclass
class TokenCache:
    access_token: str = ""
    expires_at: float = 0.0

    def valid(self) -> bool:
        # обновляем за 30 сек до истечения
        return bool(self.access_token) and time.time() < (self.expires_at - 30)


_CACHE = TokenCache()


def fetch_access_token(
    *,
    token_url: str,
    client_id: str,
    client_secret: str,
    timeout: float = 30.0,
    verify_ssl: bool = False,
) -> str:
    """Получить access_token через client_credentials (Keycloak corporate / mks-gateway)."""
    if _CACHE.valid():
        log.info("Keycloak token: используем cached token")
        return _CACHE.access_token

    log.info("Keycloak token: POST %s (client_id=%s)", token_url, client_id)
    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=timeout,
        verify=verify_ssl,
    )
    if response.status_code >= 400:
        log.error(
            "Keycloak token error: status=%s body=%s",
            response.status_code,
            (response.text or "")[:500],
        )
        response.raise_for_status()

    payload = response.json()
    token = payload["access_token"]
    expires_in = float(payload.get("expires_in", 300))
    _CACHE.access_token = token
    _CACHE.expires_at = time.time() + expires_in
    log.info("Keycloak token: OK, expires_in=%ss", int(expires_in))
    return token


def reset_token_cache() -> None:
    _CACHE.access_token = ""
    _CACHE.expires_at = 0.0

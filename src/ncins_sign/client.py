from __future__ import annotations

import logging
from typing import Any

import requests

from ncins_sign.auth import fetch_access_token
from ncins_sign.config import Settings, get_settings

log = logging.getLogger("ncins.sign.client")


class SignCreateOperationClient:
    """HTTP client for POST /v1/sign/create-operation."""

    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None):
        self.settings = settings or get_settings()
        self.session = session or requests.Session()
        self._bearer: str | None = None
        self._ensure_authorization()

    def _ensure_authorization(self) -> None:
        if self.settings.authorization:
            return
        if not self.settings.fetch_token:
            log.warning("Keycloak token: FETCH_KEYCLOAK_TOKEN=0 и AUTHORIZATION не задан")
            return
        token = fetch_access_token(
            token_url=self.settings.keycloak_token_url,
            client_id=self.settings.keycloak_client_id,
            client_secret=self.settings.keycloak_client_secret,
            timeout=self.settings.timeout,
            verify_ssl=self.settings.keycloak_verify_ssl,
        )
        self._bearer = f"Bearer {token}"
        log.info("Authorization: Bearer <token> установлен (env=%s)", self.settings.environment)

    def _auth_header(self) -> str | None:
        if self.settings.authorization:
            return self.settings.authorization
        return self._bearer

    def headers(self, *, extra: dict[str, str] | None = None, omit: set[str] | None = None) -> dict[str, str]:
        if self.settings.fetch_token and not self.settings.authorization:
            self._ensure_authorization()
        request_headers = self.settings.default_headers()
        auth = self._auth_header()
        if auth:
            request_headers["Authorization"] = auth
        if extra:
            request_headers.update(extra)
        if omit:
            for key in omit:
                request_headers.pop(key, None)
        return request_headers

    def create_operation(
        self,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        omit_headers: set[str] | None = None,
    ) -> requests.Response:
        if self.settings.fetch_token and not self.settings.authorization:
            self._ensure_authorization()

        request_headers = self.settings.default_headers()
        auth = self._auth_header()
        if auth:
            request_headers["Authorization"] = auth
        if headers:
            request_headers.update(headers)
        if omit_headers:
            for key in omit_headers:
                request_headers.pop(key, None)

        url = self.settings.create_operation_url
        log.info("POST %s", url)
        log.info(
            "Headers: %s | Authorization=%s",
            sorted(k for k in request_headers if k != "Authorization"),
            "yes" if "Authorization" in request_headers else "no",
        )
        log.info("Body: %s", payload)

        response = self.session.post(
            url,
            json=payload,
            headers=request_headers,
            timeout=self.settings.timeout,
            verify=self.settings.api_verify_ssl,
        )

        log.info(
            "Response: status=%s content-type=%s",
            response.status_code,
            response.headers.get("Content-Type"),
        )
        body_preview = (response.text or "")[:500]
        if body_preview:
            log.info("Response body (preview): %s", body_preview)
        body = response.text or ""
        if response.status_code == 401 and "Jwt issuer" in body:
            log.error(
                "401 Jwt issuer: нужен token из mks-gateway / realms/corporate "
                "(client nib-corp-ncinsurance-accounting), не UMP Keycloak."
            )
        if response.status_code == 403 and "RBAC" in body:
            log.error("RBAC 403: у клиента нет права на этот метод.")
        return response

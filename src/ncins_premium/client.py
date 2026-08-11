from __future__ import annotations

import logging
from typing import Any

import requests

from ncins_premium.auth import fetch_access_token
from ncins_premium.config import Settings, get_settings

log = logging.getLogger("ncins200.client")


class InsPremiumClient:
    """HTTP client for NCINS insurance premium calculation method."""

    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None):
        self.settings = settings or get_settings()
        self.session = session or requests.Session()
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
        # settings frozen — храним на инстансе через object.__setattr__ нельзя на dataclass frozen в settings
        # поэтому кладём в session headers / локальный override
        self._bearer = f"Bearer {token}"
        log.info("Authorization: Bearer <token> установлен (env=%s)", self.settings.environment)

    def _auth_header(self) -> str | None:
        if self.settings.authorization:
            return self.settings.authorization
        return getattr(self, "_bearer", None)

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

    def calculate(
        self,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        omit_headers: set[str] | None = None,
    ) -> requests.Response:
        # токен мог протухнуть между тестами
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

        log.info("POST %s", self.settings.calculate_url)
        log.info(
            "Headers: %s | Authorization=%s",
            sorted(k for k in request_headers if k != "Authorization"),
            "yes" if "Authorization" in request_headers else "no",
        )
        log.info("Body: %s", payload)

        response = self.session.post(
            self.settings.calculate_url,
            json=payload,
            headers=request_headers,
            timeout=self.settings.timeout,
        )

        log.info(
            "Response: status=%s content-type=%s",
            response.status_code,
            response.headers.get("Content-Type"),
        )
        body_preview = (response.text or "")[:500]
        if body_preview:
            log.info("Response body (preview): %s", body_preview)
        if response.status_code == 403 and "RBAC" in (response.text or ""):
            log.error(
                "RBAC 403: проверьте ENV/Keycloak client и что у nib-corp-ncins есть доступ "
                "к методу calculate (сейчас в UMP часто выданы только /applications)."
            )
        return response

from __future__ import annotations

from typing import Any

import requests

from ncins_premium.config import Settings, get_settings


class InsPremiumClient:
    """HTTP client for NCINS insurance premium calculation method."""

    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None):
        self.settings = settings or get_settings()
        self.session = session or requests.Session()

    def calculate(
        self,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        omit_headers: set[str] | None = None,
    ) -> requests.Response:
        request_headers = self.settings.default_headers()
        if headers:
            request_headers.update(headers)
        if omit_headers:
            for key in omit_headers:
                request_headers.pop(key, None)

        return self.session.post(
            self.settings.calculate_url,
            json=payload,
            headers=request_headers,
            timeout=self.settings.timeout,
        )

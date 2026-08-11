from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Keycloak UMP (НИБ) — client_credentials для обхода RBAC на gateway
KEYCLOAK_PROFILES: dict[str, dict[str, str]] = {
    "dev": {
        "token_url": (
            "https://keycloak.umpdevwk8sm1.moscow.alfaintra.net/"
            "realms/ump/protocol/openid-connect/token"
        ),
        "client_id": "nib-corp-ncins",
        "client_secret": "OlcnSVnz3UiORtl4XfJZ3NRRZlqw7QPY",
    },
    "qa": {
        "token_url": (
            "https://keycloak.umpqak8sm1.moscow.alfaintra.net/"
            "realms/ump/protocol/openid-connect/token"
        ),
        "client_id": "nib-corp-ncins",
        "client_secret": "DRcjLK7ZeFSy4P0A7fPuZrD1ppXccxd0",
    },
    "test": {
        "token_url": (
            "https://idp-api-test.alfaintra.net/"
            "auth/realms/ump/protocol/openid-connect/token"
        ),
        "client_id": "nib-corp-ncins",
        "client_secret": "wcpWehuLXKRWwMYE17EXvg9ShCQ7Rovc",
    },
}


@dataclass(frozen=True)
class Settings:
    base_url: str
    timeout: float
    user_id: str
    customer_id: str
    client_type: str
    channel_id: str
    user_ip: str
    project_id: str
    environment: str = "test"
    keycloak_token_url: str = ""
    keycloak_client_id: str = ""
    keycloak_client_secret: str = ""
    keycloak_verify_ssl: bool = False
    authorization: str | None = None  # готовый Bearer, если задан вручную
    fetch_token: bool = True

    @property
    def calculate_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/v1/ins-premium/calculate"

    def default_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "A-userId": self.user_id,
            "A-customerId": self.customer_id,
            "A-clientType": self.client_type,
            "A-channelId": self.channel_id,
            "A-userIp": self.user_ip,
            "A-projectId": self.project_id,
        }
        if self.authorization:
            headers["Authorization"] = self.authorization
        return headers


def get_settings() -> Settings:
    env = (os.getenv("ENV") or os.getenv("KEYCLOAK_ENV") or "test").strip().lower()
    profile = KEYCLOAK_PROFILES.get(env, KEYCLOAK_PROFILES["test"])

    auth = os.getenv("AUTHORIZATION") or None
    fetch_token = (os.getenv("FETCH_KEYCLOAK_TOKEN", "1") or "1").strip() not in {
        "0",
        "false",
        "False",
        "no",
    }

    return Settings(
        base_url=os.getenv(
            "BASE_URL",
            "http://corp-gateway-test.moscow.alfaintra.net/"
            "corp-ncins-acc-gateway/secure/corp-ncins-acc-corp-ncins-acc-api",
        ),
        timeout=float(os.getenv("REQUEST_TIMEOUT", "30")),
        user_id=os.getenv("A_USER_ID", "123456"),
        customer_id=os.getenv("A_CUSTOMER_ID", "123456"),
        client_type=os.getenv("A_CLIENT_TYPE", "XXXXX"),
        channel_id=os.getenv("A_CHANNEL_ID", "XXXXX"),
        user_ip=os.getenv("A_USER_IP", "XXXXX"),
        project_id=os.getenv("A_PROJECT_ID", "XXXXX"),
        environment=env,
        keycloak_token_url=os.getenv("KEYCLOAK_TOKEN_URL", profile["token_url"]),
        keycloak_client_id=os.getenv("KEYCLOAK_CLIENT_ID", profile["client_id"]),
        keycloak_client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET", profile["client_secret"]),
        keycloak_verify_ssl=(os.getenv("KEYCLOAK_VERIFY_SSL", "0") in {"1", "true", "True"}),
        authorization=auth,
        fetch_token=fetch_token and not bool(auth),
    )

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Auth из Postman-коллекции "Insurance API Tests"
# (realm corporate через mks-gateway) — НЕ UMP Keycloak.
KEYCLOAK_PROFILES: dict[str, dict[str, str]] = {
    "test": {
        "token_url": (
            "http://corp-gateway-test.moscow.alfaintra.net/"
            "mks-gateway/public/auth/realms/corporate/protocol/openid-connect/token"
        ),
        "client_id": "nib-corp-ncinsurance-accounting",
        "client_secret": "nib_corp_ncinsurance_accounting",
        "base_url": (
            "http://corp-gateway-test.moscow.alfaintra.net/"
            "corp-ncins-acc-gateway/secure/corp-ncins-acc-corp-ncins-acc-api"
        ),
    },
    "dev": {
        "token_url": (
            "http://corp-gateway-dev.moscow.alfaintra.net/"
            "mks-gateway/public/auth/realms/corporate/protocol/openid-connect/token"
        ),
        "client_id": "nib-corp-ncinsurance-accounting",
        "client_secret": "nib_corp_ncinsurance_accounting",
        "base_url": (
            "http://corp-gateway-dev.moscow.alfaintra.net/"
            "corp-ncins-acc-gateway/secure/corp-ncins-acc-corp-ncins-acc-api"
        ),
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
    authorization: str | None = None
    fetch_token: bool = True

    @property
    def calculate_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/v1/ins-premium/calculate"

    def default_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            # как в collection pre-request
            "A-userId": self.user_id,
            "A-customerId": self.customer_id,
            "A-clientType": self.client_type,
            "A-channelId": self.channel_id,
        }
        # опциональные headers из NCINS-200 скрина (в Postman их нет)
        if self.user_ip:
            headers["A-userIp"] = self.user_ip
        if self.project_id:
            headers["A-projectId"] = self.project_id
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
        base_url=os.getenv("BASE_URL", profile["base_url"]),
        timeout=float(os.getenv("REQUEST_TIMEOUT", "30")),
        # значения из collection variables Postman
        user_id=os.getenv("A_USER_ID", "123456"),
        customer_id=os.getenv("A_CUSTOMER_ID", "123456"),
        client_type=os.getenv("A_CLIENT_TYPE", "MOBILE"),
        channel_id=os.getenv("A_CHANNEL_ID", "INTERNET"),
        # в Postman этих headers нет — по умолчанию пусто (не отправляем)
        user_ip=os.getenv("A_USER_IP", ""),
        project_id=os.getenv("A_PROJECT_ID", ""),
        environment=env,
        keycloak_token_url=os.getenv("KEYCLOAK_TOKEN_URL", profile["token_url"]),
        keycloak_client_id=os.getenv("KEYCLOAK_CLIENT_ID", profile["client_id"]),
        keycloak_client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET", profile["client_secret"]),
        keycloak_verify_ssl=(os.getenv("KEYCLOAK_VERIFY_SSL", "0") in {"1", "true", "True"}),
        authorization=auth,
        fetch_token=fetch_token and not bool(auth),
    )

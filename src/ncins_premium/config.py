from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


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
    authorization: str | None = None

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
        authorization=os.getenv("AUTHORIZATION") or None,
    )

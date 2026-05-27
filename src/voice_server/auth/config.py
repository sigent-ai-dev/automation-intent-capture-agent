"""Auth configuration for Cognito JWT validation."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthConfig:
    cognito_user_pool_id: str = field(
        default_factory=lambda: os.environ.get("COGNITO_USER_POOL_ID", "")
    )
    cognito_client_id: str = field(
        default_factory=lambda: os.environ.get("COGNITO_CLIENT_ID", "")
    )
    cognito_region: str = field(
        default_factory=lambda: os.environ.get("COGNITO_REGION", "eu-west-1")
    )
    local_mode: bool = field(
        default_factory=lambda: os.environ.get("LOCAL_MODE", "false").lower() == "true"
    )

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"


def get_auth_config() -> AuthConfig:
    return AuthConfig()

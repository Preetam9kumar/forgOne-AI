from __future__ import annotations

from functools import lru_cache
from typing import Any

import requests
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings


class _AzureOpenIDConfig(BaseModel):
    issuer: str
    jwks_uri: str


http_bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _fetch_openid_config() -> _AzureOpenIDConfig:
    if not settings.azure_ad_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Azure AD tenant ID is required for azure_ad auth mode.",
        )
    metadata_url = (
        f"https://login.microsoftonline.com/{settings.azure_ad_tenant_id}/v2.0/.well-known/openid-configuration"
    )
    response = requests.get(metadata_url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    return _AzureOpenIDConfig(issuer=payload["issuer"], jwks_uri=payload["jwks_uri"])


@lru_cache(maxsize=1)
def _fetch_jwks() -> dict[str, Any]:
    config = _fetch_openid_config()
    response = requests.get(config.jwks_uri, timeout=10)
    response.raise_for_status()
    return response.json()


def _validate_azure_token(token: str) -> dict[str, Any]:
    audience = settings.azure_ad_audience or settings.azure_ad_client_id
    if not audience:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Azure AD client ID or audience must be configured for azure_ad auth mode.",
        )

    config = _fetch_openid_config()
    try:
        return jwt.decode(
            token,
            _fetch_jwks(),
            algorithms=["RS256"],
            audience=audience,
            issuer=config.issuer,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Azure AD bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_admin_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(http_bearer),
    x_api_key: str | None = Header(None, alias="X-API-KEY"),
) -> dict[str, Any]:
    auth_mode = settings.auth_mode.lower()
    if auth_mode == "none":
        return {"mode": "none"}

    if auth_mode == "api_key":
        if not settings.ingest_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="INGEST_API_KEY must be set when auth_mode=api_key.",
            )
        if x_api_key != settings.ingest_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-KEY header.",
            )
        return {"mode": "api_key"}

    if auth_mode == "azure_ad":
        if credentials is None or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        claims = _validate_azure_token(credentials.credentials)
        return {"mode": "azure_ad", "claims": claims}

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported auth_mode: {settings.auth_mode}",
    )

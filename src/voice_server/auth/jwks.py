"""JWKS key fetcher with caching for Cognito JWT validation."""

import time

import httpx

from voice_server.auth.config import get_auth_config
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

_jwks_cache: dict = {}
_jwks_fetched_at: float = 0
JWKS_CACHE_TTL = 3600


async def get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache, _jwks_fetched_at

    if not force_refresh and _jwks_cache and (time.time() - _jwks_fetched_at) < JWKS_CACHE_TTL:
        return _jwks_cache

    config = get_auth_config()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(config.jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = time.time()
            logger.info("jwks_fetched", url=config.jwks_url)
    except Exception as e:
        if _jwks_cache:
            logger.warning("jwks_fetch_failed_using_cache", error=str(e))
        else:
            logger.error("jwks_fetch_failed_no_cache", error=str(e))
            raise
    return _jwks_cache

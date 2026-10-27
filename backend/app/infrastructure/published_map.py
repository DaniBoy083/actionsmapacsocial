"""Bounded server-only HTTP adapter. No database or operational fallback."""

import asyncio
import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx

from app.domain.published_map import PublishedMap
from app.infrastructure.platform_contract import approved_actions, instant, unavailable_actions

logger = logging.getLogger("actionsmap.published_map")
HOST = "plataforma-consolidada-de-analise-d.vercel.app"
MAX_BYTES = 2 * 1024 * 1024


def approved_url(value: str) -> bool:
    try:
        url = urlsplit(value)
        return (
            url.scheme == "https"
            and url.hostname == HOST
            and url.port in {None, 443}
            and url.path == "/api/v1/analytics"
            and not url.query
            and not url.fragment
            and not url.username
            and not url.password
        )
    except ValueError:
        return False


def retry_delay(value: str | None) -> int:
    try:
        seconds = (
            int(value)
            if value and value.isascii() and value.isdigit()
            else (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        )
        return max(30, min(86400, int(seconds)))
    except (TypeError, ValueError, OverflowError):
        return 60


def unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


class PlatformPublishedMap:
    def __init__(self, url: str, token: str, transport: httpx.AsyncBaseTransport | None = None):
        self.url, self.token, self.transport = url, token, transport
        self.cached: PublishedMap | None = None
        self.until = 0.0
        self.lock = asyncio.Lock()
        self.generation: int | None = None
        self.fingerprint: str | None = None

    def current_cache(self) -> PublishedMap | None:
        if self.cached is None or time.monotonic() >= self.until:
            return None
        if self.cached.expires_at and instant(self.cached.expires_at) <= datetime.now(UTC):
            return None
        return self.cached.model_copy(deep=True)

    async def read(self) -> PublishedMap:
        cached = self.current_cache()
        if cached is not None:
            return cached
        async with self.lock:
            cached = self.current_cache()
            if cached is not None:
                return cached
            checked = datetime.now(UTC).isoformat()
            result = unavailable_actions("not_configured", checked)
            ttl = 30
            if self.token and approved_url(self.url):
                try:
                    async with (
                        asyncio.timeout(20),
                        httpx.AsyncClient(
                            transport=self.transport,
                            timeout=20,
                            follow_redirects=False,
                            trust_env=False,
                        ) as client,
                        client.stream(
                            "GET",
                            self.url,
                            headers={
                                "Accept": "application/json",
                                "Authorization": "Bearer " + self.token,
                                "x-api-key": self.token,
                            },
                        ) as response,
                    ):
                        response.raise_for_status()
                        if (
                            response.headers.get("content-type", "").split(";")[0]
                            != "application/json"
                        ):
                            raise ValueError("Expected JSON")
                        body = bytearray()
                        async for part in response.aiter_bytes(chunk_size=65536):
                            body.extend(part)
                            if len(body) > MAX_BYTES:
                                raise ValueError("Payload limit")
                    payload = json.loads(body, object_pairs_hook=unique_object)
                    result = approved_actions(payload, checked)
                    if result["status"] in {"available", "empty"}:
                        generation = int(result["generation"])
                        fingerprint = hashlib.sha256(
                            json.dumps(
                                [
                                    result["summary"],
                                    result["municipalities"],
                                ],
                                sort_keys=True,
                            ).encode()
                        ).hexdigest()
                        if self.generation is not None and (
                            generation < self.generation
                            or (generation == self.generation and fingerprint != self.fingerprint)
                        ):
                            raise ValueError("Generation regression or conflict")
                        self.generation, self.fingerprint = generation, fingerprint
                        ttl = min(
                            60,
                            max(
                                0,
                                int(
                                    (
                                        instant(result["expires_at"]) - datetime.now(UTC)
                                    ).total_seconds()
                                ),
                            ),
                        )
                except httpx.HTTPStatusError as error:
                    status = error.response.status_code
                    result = unavailable_actions(
                        "unauthorized" if status in {401, 403} else "unavailable", checked
                    )
                    if status in {429, 503}:
                        ttl = retry_delay(error.response.headers.get("Retry-After"))
                    logger.warning("platform_map.http_failure status=%d", status)
                except (ValueError, TypeError, RecursionError, TimeoutError, httpx.HTTPError):
                    result = unavailable_actions("unavailable", checked)
                    logger.warning("platform_map.invalid_or_unavailable")
            result["refresh_after_seconds"] = max(1, ttl)
            self.cached = PublishedMap.model_validate(result)
            self.until = time.monotonic() + ttl
            return self.cached.model_copy(deep=True)

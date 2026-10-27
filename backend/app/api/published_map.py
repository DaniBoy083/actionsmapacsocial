from functools import lru_cache

from fastapi import APIRouter, Depends

from app.application.published_map import ReadPublishedMap
from app.config import get_settings
from app.domain.contracts import Professional
from app.domain.published_map import PublishedMap, PublishedMapSource
from app.infrastructure.published_map import PlatformPublishedMap
from app.security.session import current_professional

router = APIRouter(prefix="/api/v1")


@lru_cache
def platform_source() -> PublishedMapSource:
    settings = get_settings()
    return PlatformPublishedMap(
        settings.consolidated_analytics_api_base_url,
        settings.consolidated_analytics_api_token.get_secret_value(),
    )


@router.get("/mapa-acoes", response_model=PublishedMap)
async def published_map(
    _professional: Professional = Depends(current_professional),
    source: PublishedMapSource = Depends(platform_source),
) -> PublishedMap:
    return await ReadPublishedMap(source).execute()

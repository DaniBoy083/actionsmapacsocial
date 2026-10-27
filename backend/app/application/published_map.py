from app.domain.published_map import PublishedMap, PublishedMapSource


class ReadPublishedMap:
    def __init__(self, source: PublishedMapSource):
        self.source = source

    async def execute(self) -> PublishedMap:
        return await self.source.read()

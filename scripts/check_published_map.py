"""Read-only integration check; prints status and aggregate metadata only."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.api.published_map import platform_source


async def main() -> int:
    result = await platform_source().read()
    ready = result.status in {"available", "empty"}
    print(
        json.dumps(
            {
                "ready": ready,
                "status": result.status,
                "checked_at": result.checked_at,
                "generation": result.generation,
                "municipality_count": len(result.municipalities),
            }
        )
    )
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

import pytest

from app.cache.ttl import TTLCache


async def test_ttl_cache_expires_and_evicts_least_recently_used_entry() -> None:
    now = 0.0

    def clock() -> float:
        return now

    cache: TTLCache[str, int] = TTLCache(ttl_seconds=10, max_entries=2, clock=clock)
    await cache.set("first", 1)
    await cache.set("second", 2)
    assert await cache.get("first") == 1

    await cache.set("third", 3)

    assert await cache.get("second") is None
    assert await cache.get("first") == 1
    now = 11.0
    assert await cache.get("first") is None


@pytest.mark.parametrize("ttl,max_entries", [(0, 1), (1, 0)])
def test_ttl_cache_rejects_non_positive_bounds(ttl: int, max_entries: int) -> None:
    with pytest.raises(ValueError):
        TTLCache[str, int](ttl_seconds=ttl, max_entries=max_entries)

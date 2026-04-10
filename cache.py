import json
import redis

# если Redis в Docker на твоей машине — так и будет работать
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

DEFAULT_TTL = 60  # секунды


def cache_get(key: str):
    raw = r.get(key)
    return None if raw is None else json.loads(raw)


def cache_set(key: str, value, ttl: int = DEFAULT_TTL):
    r.setex(key, ttl, json.dumps(value, ensure_ascii=False))


def cache_get_or_set(key: str, ttl: int, producer):
    cached = cache_get(key)
    if cached is not None:
        return cached
    value = producer()
    cache_set(key, value, ttl)
    return value


def invalidate_prefix(prefix: str):
    # удаляем все ключи вида prefix:*
    for k in r.scan_iter(match=f"{prefix}:*"):
        r.delete(k)
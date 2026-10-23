import redis
import os
import redis.exceptions
from dotenv import load_dotenv
from app.exceptions import CacheError
load_dotenv()

def get_cache():
    cache = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        socket_connect_timeout = 5.0,
        socket_timeout=5.0,
        decode_responses=True
    )

    return cache

def cache_health_check(cache):
    try:
        return cache.ping()
    except redis.exceptions.RedisError as error:
        raise CacheError from error


def get_from_cache(cache, key):
    try:
        return cache.get(key)
    except redis.exceptions.RedisError as error:
        raise CacheError from error


def set_cache_response(cache, key, value):
    try:
        cache.set(key, value, nx=True, ex=86400)
    except redis.exceptions.RedisError as error:
        raise CacheError from error






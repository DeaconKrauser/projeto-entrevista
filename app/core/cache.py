# app/core/cache.py

import redis.asyncio as redis
from core.config import REDIS_URL

cache = redis.from_url(REDIS_URL, decode_responses=True)
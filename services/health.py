from database import database_health_check
from cache import cache_health_check
from schemas.health import HealthResponse
from exceptions import DatabaseError, CacheError
import logging

logger = logging.getLogger(__name__)

def get_health_check(db, cache):
    try:
        db_health = database_health_check(db)
    except DatabaseError as error:
        db_health = False
        logger.error('database health check failed', exc_info=error)

    try:
        cache_health = cache_health_check(cache)
    except CacheError as error:
        cache_health = False
        logger.error('redis health check failed', exc_info=error)

    return HealthResponse(
        status='health' if (db_health and cache_health) else 'unhealth',
        database_health=db_health,
        cache_health=cache_health
    )











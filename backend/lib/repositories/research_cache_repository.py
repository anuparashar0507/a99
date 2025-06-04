from typing import Any, Dict, Optional
import datetime
from .exceptions import RepositoryReadException, RepositoryUpdateException
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.research_cache_models import CACHE_EXPIRY_HOURS


class ResearchCacheRepository:
    """
    Repository class for managing research cache.

    Functions:
      - get_cached_response: Retrieve cached response if not expired.
      - set_cache: Insert/update a cached response with an expiration time.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("research_cache")

    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cached response by cache_key if it hasn't expired.
        """
        try:
            cached = await self.collection.find_one({"cache_key": cache_key})
            if cached:
                expires_at = cached.get("expires_at")
                if expires_at:
                    if expires_at.tzinfo is None:  # If naive, make it aware
                        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
                    if expires_at > datetime.datetime.now(datetime.timezone.utc):
                        return cached.get("data")
            return None
        except Exception as e:
            raise RepositoryReadException("ResearchCacheRepository", e)

    async def set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Set or update a cached response with an expiration time.
        """
        try:
            expiry_time = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(hours=CACHE_EXPIRY_HOURS)
            document = {
                "cache_key": cache_key,
                "data": data,
                "expires_at": expiry_time,
            }
            await self.collection.update_one(
                {"cache_key": cache_key}, {"$set": document}, upsert=True
            )
        except Exception as e:
            raise RepositoryUpdateException("ResearchCacheRepository", e)

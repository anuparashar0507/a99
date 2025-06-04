from typing import Any, Dict, List
from pymongo import ReturnDocument
from bson import ObjectId
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister


class ProspectRepository:
    """
    Repository for managing prospects.

    Functions:
      - create: Add a new prospect.
      - get: Fetch a prospect by id.
      - update: Update a prospect by id.
      - update_where: Update multiple prospects matching a query.
      - delete: Delete a prospect by id.
      - delete_where: Delete multiple prospects matching a query.
      - create_many: Bulk insert multiple prospects asynchronously.
      - get_many: Fetch multiple prospects by a list of ids.
      - get_where: Fetch multiple prospects based on a query.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("prospects")

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new prospect.
        """
        try:
            data["created_at"] = datetime.datetime.now(datetime.timezone.utc)
            data["updated_at"] = data["created_at"]
            insert_result = await self.collection.insert_one(data)
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if not inserted_data:
                raise RepositoryCreateException(
                    "ProspectRepository", Exception("Inserted document not found")
                )
            return inserted_data
        except Exception as e:
            raise RepositoryCreateException("ProspectRepository", e)

    async def get(self, prospect_id: str) -> Dict[str, Any]:
        """
        Fetch a prospect by `prospect_id`.
        """
        try:
            prospect = await self.collection.find_one({"_id": ObjectId(prospect_id)})
            if not prospect:
                raise RepositoryNotFoundException(
                    "ProspectRepository", f"Prospect with id '{prospect_id}' not found."
                )
            return prospect
        except Exception as e:
            raise RepositoryReadException("ProspectRepository", e)

    async def get_prospect_where(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch a prospect by `prospect_id`.
        """
        try:
            prospect = await self.collection.find_one(query)
            if not prospect:
                raise RepositoryNotFoundException(
                    "ProspectRepository", f"Prospect with filter '{query}' not found."
                )
            return prospect
        except Exception as e:
            raise RepositoryReadException("ProspectRepository", e)

    async def update(
        self, prospect_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing prospect by `prospect_id`.
        """
        try:
            update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
            updated_prospect = await self.collection.find_one_and_update(
                {"_id": ObjectId(prospect_id)},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_prospect:
                raise RepositoryNotFoundException(
                    "ProspectRepository", f"Prospect with id '{prospect_id}' not found."
                )
            return updated_prospect
        except Exception as e:
            raise RepositoryUpdateException("ProspectRepository", e)

    async def update_where(
        self, query: Dict[str, Any], update_data: Dict[str, Any]
    ) -> int:
        """
        Update multiple prospects matching a query.
        Returns the count of updated documents.
        """
        try:
            update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
            update_result = await self.collection.update_many(
                query, {"$set": update_data}
            )
            return update_result.modified_count
        except Exception as e:
            raise RepositoryUpdateException("ProspectRepository", e)

    async def delete(self, prospect_id: str) -> Dict[str, Any]:
        """
        Delete a prospect by `prospect_id`.
        """
        try:
            deleted_prospect = await self.collection.find_one_and_delete(
                {"_id": ObjectId(prospect_id)}
            )
            if not deleted_prospect:
                raise RepositoryNotFoundException(
                    "ProspectRepository", f"Prospect with id '{prospect_id}' not found."
                )
            return deleted_prospect
        except Exception as e:
            raise RepositoryDeleteException("ProspectRepository", e)

    async def delete_where(self, query: Dict[str, Any]) -> int:
        """
        Delete multiple prospects matching a query.
        Returns the count of deleted documents.
        """
        try:
            delete_result = await self.collection.delete_many(query)
            return delete_result.deleted_count
        except Exception as e:
            raise RepositoryDeleteException("ProspectRepository", e)

    async def create_many(
        self, prospects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bulk insert multiple prospects asynchronously and handle errors.
        Returns a list of successfully inserted prospects.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            for prospect in prospects:
                prospect["created_at"] = time_now
                prospect["updated_at"] = time_now

            insert_result = await self.collection.insert_many(prospects)
            inserted_ids = insert_result.inserted_ids
            inserted_prospects = await self.collection.find(
                {"_id": {"$in": inserted_ids}}
            ).to_list(length=None)
            return inserted_prospects
        except Exception as e:
            raise RepositoryCreateException("ProspectRepository", e)

    async def get_many(self, prospect_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple prospects by a list of prospect_ids.
        """
        try:
            object_ids = [ObjectId(pid) for pid in prospect_ids]
            prospects = await self.collection.find(
                {"_id": {"$in": object_ids}}
            ).to_list(length=None)
            return prospects if prospects else []
        except Exception as e:
            raise RepositoryReadException("ProspectRepository", e)

    async def get_where(
        self, query: Dict[str, Any], sort: Dict[str, int] = None, skip: int = 0, limit: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple prospects based on a query with optional sorting and pagination.
        
        Args:
            query: MongoDB query document
            sort: Optional sort specification (e.g., {"created_at": -1})
            skip: Number of documents to skip
            limit: Maximum number of documents to return (0 for no limit)
        """
        try:
            cursor = self.collection.find(query)
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
                
            if skip:
                cursor = cursor.skip(skip)
                
            if limit:
                cursor = cursor.limit(limit)
                
            prospects = await cursor.to_list(length=None)
            return prospects if prospects else []
        except Exception as e:
            raise RepositoryReadException("ProspectRepository", e)

    async def count_where(self, query: Dict[str, Any]) -> int:
        """
        Count the number of prospects matching a query.
        """
        try:
            count = await self.collection.count_documents(query)
            return count
        except Exception as e:
            raise RepositoryReadException("ProspectRepository", e)

    async def get_score(self, prospect_id: str) -> Dict[str, Any]:
        """
        Get a prospect's score information.
        """
        try:
            prospect = await self.collection.find_one({"_id": ObjectId(prospect_id)})
            if not prospect:
                return None
                
            # Extract scoring-related fields
            score_data = {
                "prospect_id": str(prospect["_id"]),
                "score": prospect.get("engagement_score", 0),
                "engagement_status": prospect.get("engagement_status", "cold"),
                "warm_timestamp": prospect.get("warm_timestamp"),
                "hot_timestamp": prospect.get("hot_timestamp"),
                "events": prospect.get("score_events", []),
                "updated_at": prospect.get("updated_at")
            }
            
            return score_data
        except Exception as e:
            raise RepositoryReadException("ProspectRepository", e)

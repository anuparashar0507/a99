from typing import Any, Dict, List, Optional
from pymongo import ReturnDocument
from bson import ObjectId
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.action_result_models import ActionResultModel, ActionResultUpdateModel


class ActionResultRepository:
    """
    Repository class for action result-related database operations.

    Functions:
      - get: Find one action result based on an ID.
      - update: Update an action result by ID.
      - delete: Delete an action result by ID.
      - create: Insert a new action result.
      - get_where: Find action results matching a given filter.
      - delete_where: Delete action results matching a given filter.
      - update_where: Update multiple action results based on a query.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = self.db.get_collection("action_results")

    async def get(self, action_result_id: str) -> Optional[ActionResultModel]:
        """
        Find a single action result by ID.
        """
        try:
            action_result = await self.collection.find_one(
                {"_id": ObjectId(action_result_id)}
            )
            if not action_result:
                return None
            return ActionResultModel(**action_result)
        except Exception as e:
            raise RepositoryReadException("ActionResultRepository", e)

    async def create(
        self, action_id: str, status: str, result_data: Optional[Dict[str, Any]] = None
    ) -> ActionResultModel:
        """
        Create a new action result and return it.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            action_result = ActionResultModel(
                action_id=action_id,
                status=status,
                result_data=result_data or {},
                created_at=time_now,
                updated_at=time_now,
            )

            insert_result = await self.collection.insert_one(
                action_result.model_dump(exclude_unset=True, by_alias=True)
            )
            inserted_action_result = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            return ActionResultModel(**inserted_action_result)  # type: ignore
        except Exception as e:
            raise RepositoryCreateException("ActionResultRepository", e)

    async def update(
        self, action_result_id: str, update_data: ActionResultUpdateModel
    ) -> Optional[ActionResultModel]:
        """
        Update an action result by ID.
        """
        try:
            update_data.updated_at = datetime.datetime.now(datetime.timezone.utc)
            updated_action_result = await self.collection.find_one_and_update(
                {"_id": ObjectId(action_result_id)},
                {"$set": update_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_action_result:
                return None
            return ActionResultModel(**updated_action_result)
        except Exception as e:
            raise RepositoryUpdateException("ActionResultRepository", e)

    async def delete(self, action_result_id: str) -> bool:
        """
        Delete an action result by ID.
        Returns True if successful.
        """
        try:
            delete_result = await self.collection.delete_one(
                {"_id": ObjectId(action_result_id)}
            )
            return delete_result.deleted_count > 0
        except Exception as e:
            raise RepositoryDeleteException("ActionResultRepository", e)

    async def get_where(self, query: Dict[str, Any]) -> List[ActionResultModel]:
        """
        Find action results that match a query.
        """
        try:
            results = await self.collection.find(query).to_list(length=None)
            return (
                [ActionResultModel(**result) for result in results] if results else []
            )
        except Exception as e:
            raise RepositoryReadException("ActionResultRepository", e)

    async def delete_where(self, query: Dict[str, Any]) -> int:
        """
        Delete action results matching a given query.
        Returns the count of deleted documents.
        """
        try:
            delete_result = await self.collection.delete_many(query)
            return delete_result.deleted_count
        except Exception as e:
            raise RepositoryDeleteException("ActionResultRepository", e)

    async def update_where(
        self, query: Dict[str, Any], update_data: ActionResultUpdateModel
    ) -> int:
        """
        Update action results that match a given query.
        Returns the count of modified documents.
        """
        try:
            update_data.updated_at = datetime.datetime.now(datetime.timezone.utc)
            update_result = await self.collection.update_many(
                query,
                {"$set": update_data.model_dump(exclude_unset=True)},
            )
            return update_result.modified_count
        except Exception as e:
            raise RepositoryUpdateException("ActionResultRepository", e)

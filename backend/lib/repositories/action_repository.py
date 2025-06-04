from typing import Any, Dict, List

from pymongo import ReturnDocument

from .exceptions import (
    RepositoryCreateException,
    RepositoryDeleteException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
)
from ..db.db_protocol import AsyncIOMotorCollection, AsyncIOMotorDatabase, Persister
from ..models.action_models import ActionType, ActionModel, ActionUpdateDataModel
from bson import ObjectId
import datetime


class ActionRepository:
    """
    This repository class is for persisting actions in db and performing CRUD operations on them.
    Add new functions as neccessary.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("actions")

    async def create(
        self,
        workflow_id: str,
        action_type: ActionType,
        action_payload: Dict[str, Any],
        name: str,
        description: str,
        time_interval: int,
    ) -> ActionModel:
        try:
            action = ActionModel(
                workflow_id=workflow_id,
                action_type=action_type,
                action_payload=action_payload,
                name=name,
                description=description,
                time_interval=time_interval,
            )
            time_now = datetime.datetime.now(datetime.timezone.utc)
            action.created_at = time_now
            action.updated_at = time_now
            insert_result = await self.collection.insert_one(action.model_dump())
            inserted_action_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            action = ActionModel(**inserted_action_data)  # type: ignore
            return action
        except Exception as e:
            raise RepositoryCreateException("ActionRepository", e)

    async def get(self, action_id: str) -> ActionModel:
        try:
            action = await self.collection.find_one({"_id": ObjectId(action_id)})
            if not action:
                raise RepositoryNotFoundException(
                    "ActionRepository", f"Action with id: ${action_id} not found."
                )
            return ActionModel(**action)
        except Exception as e:
            raise RepositoryReadException("ActionRepository", e)

    async def get_workflow_actions(self, workflow_id: str) -> List[ActionModel]:
        try:
            actions = await self.collection.find({"workflow_id": workflow_id}).to_list(
                length=None
            )
            actions = [ActionModel(**action) for action in actions]
            return actions if actions else []
        except Exception as e:
            raise RepositoryReadException(
                "ActionRepository",
                Exception("Failed to read workflow actions: " + str(e)),
            )

    async def update(
        self, action_id: str, action_data: ActionUpdateDataModel
    ) -> ActionModel:
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            action_data.updated_at = time_now
            action = await self.collection.find_one_and_update(
                {"_id": ObjectId(action_id)},
                {"$set": action_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            return ActionModel(**action)
        except Exception as e:
            raise RepositoryUpdateException("ActionRepository", e)

    async def delete(self, action_id: str) -> ActionModel:
        try:
            action = await self.collection.find_one_and_delete(
                {"_id": ObjectId(action_id)}
            )
            return ActionModel(**action)
        except Exception as e:
            raise RepositoryDeleteException("ActionRepository", e)

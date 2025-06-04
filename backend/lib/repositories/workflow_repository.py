from typing import Any, Dict, List
from pymongo import ReturnDocument
from bson import ObjectId
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryDeleteException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
)
from ..db.db_protocol import AsyncIOMotorCollection, AsyncIOMotorDatabase, Persister
from ..models.workflow_models import WorkflowModel, WorkflowUpdateDataModel


class WorkflowRepository:
    """
    Repository class for persisting workflows in the database and performing CRUD operations.
    Also supports retrieving workflows by campaign IDs.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("workflows")

    async def create(self, data: Dict[str, Any]) -> WorkflowModel:
        """
        Create a workflow using the provided data dictionary.
        Data must contain fields required by WorkflowModel.
        """
        try:
            workflow = WorkflowModel(**data)
            time_now = datetime.datetime.now(datetime.timezone.utc)
            workflow.created_at = time_now
            workflow.updated_at = time_now
            # Insert the workflow and then retrieve the inserted document
            insert_result = await self.collection.insert_one(workflow.model_dump())
            inserted_workflow_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if inserted_workflow_data is None:
                raise RepositoryCreateException(
                    "WorkflowRepository", Exception("Inserted document not found")
                )
            return WorkflowModel(**inserted_workflow_data)
        except Exception as e:
            raise RepositoryCreateException("WorkflowRepository", e)

    async def get(self, workflow_id: str) -> WorkflowModel:
        """
        Retrieve a workflow by its unique identifier.
        """
        try:
            workflow_data = await self.collection.find_one(
                {"_id": ObjectId(workflow_id)}
            )
            if not workflow_data:
                raise RepositoryNotFoundException(
                    "WorkflowRepository", f"Workflow with id '{workflow_id}' not found."
                )
            return WorkflowModel(**workflow_data)
        except Exception as e:
            raise RepositoryReadException("WorkflowRepository", e)

    async def update(
        self, workflow_id: str, update_data: WorkflowUpdateDataModel
    ) -> WorkflowModel:
        """
        Update the workflow with the given id using the provided update data.
        Only fields provided in update_data (via exclude_unset) will be updated.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data.updated_at = time_now
            updated_workflow = await self.collection.find_one_and_update(
                {"_id": ObjectId(workflow_id)},
                {"$set": update_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_workflow:
                raise RepositoryNotFoundException(
                    "WorkflowRepository", f"Workflow with id '{workflow_id}' not found."
                )
            return WorkflowModel(**updated_workflow)
        except Exception as e:
            raise RepositoryUpdateException("WorkflowRepository", e)

    async def delete(self, workflow_id: str) -> WorkflowModel:
        """
        Delete the workflow by its id and return the deleted workflow.
        """
        try:
            deleted_workflow = await self.collection.find_one_and_delete(
                {"_id": ObjectId(workflow_id)}
            )
            if not deleted_workflow:
                raise RepositoryNotFoundException(
                    "WorkflowRepository", f"Workflow with id '{workflow_id}' not found."
                )
            return WorkflowModel(**deleted_workflow)
        except Exception as e:
            raise RepositoryDeleteException("WorkflowRepository", e)

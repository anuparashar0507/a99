from typing import Any, Dict
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
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.workflow_runtime_models import (
    WorkflowRuntimeModel,
    WorkflowRuntimeUpdateDataModel,
)


class WorkflowRuntimeRepository:
    """
    Repository class for persisting workflow runtimes in the database and performing CRUD operations.
    Provides functions to:
      - create: Insert a new workflow runtime document.
      - get: Retrieve a runtime by its runtime id.
      - get_workflow_runtime: Retrieve a runtime by the associated workflow id.
      - update: Update a runtime by its runtime id.
      - update_workflow_runtime: Update a runtime by the associated workflow id.
      - delete: Delete a runtime by its runtime id.
      - delete_workflow_runtime: Delete a runtime by the associated workflow id.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("workflow_runtimes")

    async def create(self, data: Dict[str, Any]) -> WorkflowRuntimeModel:
        """
        Create a new workflow runtime document.
        The provided data dictionary must contain fields required by WorkflowRuntimeModel.
        """
        try:
            runtime = WorkflowRuntimeModel(**data)
            time_now = datetime.datetime.now(datetime.timezone.utc)
            runtime.created_at = time_now
            runtime.updated_at = time_now
            insert_result = await self.collection.insert_one(runtime.model_dump())
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if inserted_data is None:
                raise RepositoryCreateException(
                    "WorkflowRuntimeRepository",
                    Exception("Inserted document not found"),
                )
            return WorkflowRuntimeModel(**inserted_data)
        except Exception as e:
            raise RepositoryCreateException("WorkflowRuntimeRepository", e)

    async def get(self, runtime_id: str) -> WorkflowRuntimeModel:
        """
        Retrieve a workflow runtime by its runtime id.
        """
        try:
            runtime_data = await self.collection.find_one({"_id": ObjectId(runtime_id)})
            if not runtime_data:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime with id '{runtime_id}' not found.",
                )
            return WorkflowRuntimeModel(**runtime_data)
        except Exception as e:
            raise RepositoryReadException("WorkflowRuntimeRepository", e)

    async def get_where(self, query: Dict[str, Any]) -> WorkflowRuntimeModel:
        """
        Retrieve a workflow runtime by filter.
        """
        try:
            runtime_data = await self.collection.find_one(query)
            if not runtime_data:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime with query {query} not found.",
                )
            return WorkflowRuntimeModel(**runtime_data)
        except Exception as e:
            raise RepositoryReadException("WorkflowRuntimeRepository", e)

    async def get_workflow_runtime(self, workflow_id: str) -> WorkflowRuntimeModel:
        """
        Retrieve a workflow runtime by its associated workflow id.
        """
        try:
            runtime_data = await self.collection.find_one({"workflow_id": workflow_id})
            if not runtime_data:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime for workflow id '{workflow_id}' not found.",
                )
            return WorkflowRuntimeModel(**runtime_data)
        except Exception as e:
            raise RepositoryReadException("WorkflowRuntimeRepository", e)

    async def update(
        self, runtime_id: str, update_data: WorkflowRuntimeUpdateDataModel
    ) -> WorkflowRuntimeModel:
        """
        Update a workflow runtime by its runtime id.
        Only the fields provided in update_data (using model_dump(exclude_unset=True)) are updated.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data.updated_at = time_now
            updated_runtime = await self.collection.find_one_and_update(
                {"_id": ObjectId(runtime_id)},
                {"$set": update_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_runtime:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime with id '{runtime_id}' not found.",
                )
            return WorkflowRuntimeModel(**updated_runtime)
        except Exception as e:
            raise RepositoryUpdateException("WorkflowRuntimeRepository", e)

    async def update_where(
        self, filter: Dict[str, Any], update_data: WorkflowRuntimeUpdateDataModel
    ) -> int:
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data.updated_at = time_now
            updated_runtime = await self.collection.update_many(
                filter,
                {"$set": update_data.model_dump(exclude_unset=True)},
            )
            return updated_runtime.modified_count
        except Exception as e:
            raise RepositoryUpdateException("WorkflowRuntimeRepository", e)

    async def update_workflow_runtime(
        self, workflow_id: str, update_data: WorkflowRuntimeUpdateDataModel
    ) -> WorkflowRuntimeModel:
        """
        Update a workflow runtime by its associated workflow id.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data.updated_at = time_now
            updated_runtime = await self.collection.find_one_and_update(
                {"workflow_id": workflow_id},
                {"$set": update_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_runtime:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime for workflow id '{workflow_id}' not found.",
                )
            return WorkflowRuntimeModel(**updated_runtime)
        except Exception as e:
            raise RepositoryUpdateException("WorkflowRuntimeRepository", e)

    async def delete(self, runtime_id: str) -> WorkflowRuntimeModel:
        """
        Delete a workflow runtime by its runtime id and return the deleted document.
        """
        try:
            deleted_runtime = await self.collection.find_one_and_delete(
                {"_id": ObjectId(runtime_id)}
            )
            if not deleted_runtime:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime with id '{runtime_id}' not found.",
                )
            return WorkflowRuntimeModel(**deleted_runtime)
        except Exception as e:
            raise RepositoryDeleteException("WorkflowRuntimeRepository", e)

    async def delete_where(self, query: Dict[str, Any]) -> int:
        try:
            delete_result = await self.collection.delete_many(query)
            return delete_result.deleted_count
        except Exception as e:
            raise RepositoryDeleteException("WorkflowRuntimeRepository", e)

    async def delete_workflow_runtime(self, workflow_id: str) -> WorkflowRuntimeModel:
        """
        Delete a workflow runtime by its associated workflow id and return the deleted document.
        """
        try:
            deleted_runtime = await self.collection.find_one_and_delete(
                {"workflow_id": workflow_id}
            )
            if not deleted_runtime:
                raise RepositoryNotFoundException(
                    "WorkflowRuntimeRepository",
                    f"Workflow runtime for workflow id '{workflow_id}' not found.",
                )
            return WorkflowRuntimeModel(**deleted_runtime)
        except Exception as e:
            raise RepositoryDeleteException("WorkflowRuntimeRepository", e)

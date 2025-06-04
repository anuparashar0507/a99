from typing import Any, Dict, List
from pymongo import ReturnDocument
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.kb_models import KnowledgeBaseModel


class KnowledgeBaseRepository:
    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("knowledge_base")

    async def create(self, data: Dict[str, Any]) -> KnowledgeBaseModel:
        """
        Create a new knowledge base entry.
        """
        try:
            knowledge_entry = KnowledgeBaseModel(**data)
            time_now = datetime.datetime.now(datetime.timezone.utc)
            knowledge_entry.created_at = time_now
            knowledge_entry.updated_at = time_now
            insert_result = await self.collection.insert_one(
                knowledge_entry.model_dump()
            )
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if not inserted_data:
                raise RepositoryCreateException(
                    "KnowledgeBaseRepository", Exception("Inserted document not found")
                )
            return KnowledgeBaseModel(**inserted_data)
        except Exception as e:
            raise RepositoryCreateException("KnowledgeBaseRepository", e)

    async def get_all(self, rag_id: str) -> List[KnowledgeBaseModel]:
        """
        Fetch a knowledge base entry by `rag_id`.
        """
        try:
            entry_data = (
                await self.collection.find({"kb_id": rag_id})
                .sort({"_id": -1})
                .to_list(length=None)
            )
            if not entry_data:
                raise RepositoryNotFoundException(
                    "KnowledgeBaseRepository",
                    f"Knowledge base entry with rag_id '{rag_id}' not found.",
                )
            docs = []
            for doc in entry_data:
                docs.append(KnowledgeBaseModel(**doc))
            return docs
        except Exception as e:
            raise RepositoryReadException("KnowledgeBaseRepository", e)

    async def update(self, rag_id: str, update_data: Dict) -> KnowledgeBaseModel:
        """
        Update an existing knowledge base entry by `rag_id`.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data["updated_at"] = time_now
            updated_entry = await self.collection.find_one_and_update(
                {"kb_id": rag_id},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_entry:
                raise RepositoryNotFoundException(
                    "KnowledgeBaseRepository",
                    f"Knowledge base entry with rag_id '{rag_id}' not found.",
                )
            return KnowledgeBaseModel(**updated_entry)
        except Exception as e:
            raise RepositoryUpdateException("KnowledgeBaseRepository", e)

    async def delete(self, rag_id: str) -> KnowledgeBaseModel:
        """
        Delete a knowledge base entry by `rag_id` and return the deleted document.
        """
        try:
            deleted_entry = await self.collection.find_one_and_delete({"kb_id": rag_id})
            if not deleted_entry:
                raise RepositoryNotFoundException(
                    "KnowledgeBaseRepository",
                    f"Knowledge base entry with rag_id '{rag_id}' not found.",
                )
            return KnowledgeBaseModel(**deleted_entry)
        except Exception as e:
            raise RepositoryDeleteException("KnowledgeBaseRepository", e)

    async def delete_docs(self, rag_id: str, names: List[str]) -> int:
        """
        Delete multiple knowledge base entries by `rag_id` and a list of `names`.

        Args:
            rag_id (str): The unique ID for the knowledge base.
            names (List[str]): A list of names to match for deletion.

        Returns:
            int: The number of documents deleted.
        """
        try:
            delete_result = await self.collection.delete_many(
                {"kb_id": rag_id, "name": {"$in": names}}
            )
            return delete_result.deleted_count
        except Exception as e:
            raise RepositoryDeleteException("KnowledgeBaseRepository", e)

import datetime
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.results import DeleteResult

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)

from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister

from ..models.topic_models import (
    TopicModel,
)


class TopicsRepository:
    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        """
        Initializes the TopicsRepository.

        Args:
            db (Persister): The database persistence layer instance.
        """
        self.db = db.get_db()
        self.collection = db.get_collection("topics")

    async def create(self, data: TopicModel) -> TopicModel:
        """
        Create a new topic entry.

        Args:
            data (Dict[str, Any]): The data for the new topic.

        Returns:
            TopicModel: The newly created topic object.

        Raises:
            RepositoryCreateException: If the creation fails.
        """
        try:
            topic_entry = data
            time_now = datetime.datetime.now(datetime.timezone.utc)
            if not hasattr(topic_entry, "created_at") or not topic_entry.created_at:
                topic_entry.created_at = time_now
            if not hasattr(topic_entry, "updated_at") or not topic_entry.updated_at:
                topic_entry.updated_at = time_now

            data_to_insert = topic_entry.model_dump(by_alias=True, exclude_none=True)

            insert_result = await self.collection.insert_one(data_to_insert)
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if not inserted_data:
                raise RepositoryCreateException(
                    "TopicsRepository",
                    Exception("Inserted topic document not found after creation"),
                )
            return TopicModel(**inserted_data)
        except Exception as e:
            raise RepositoryCreateException("TopicsRepository", e)

    async def get(self, topic_id: str) -> TopicModel:
        """
        Fetch a single topic entry by its `topic_id`.

        Args:
            topic_id (str): The unique identifier for the topic.

        Returns:
            Optional[TopicModel]: The found topic object, or None if not found.

        Raises:
            RepositoryReadException: If there's an issue during the read operation.
            RepositoryNotFoundException: If the topic with the specified id is not found.
        """
        try:
            entry_data = await self.collection.find_one({"_id": ObjectId(topic_id)})
            if not entry_data:
                raise RepositoryNotFoundException(
                    "TopicsRepository",
                    f"Topic with topic_id '{topic_id}' not found.",
                )
            return TopicModel(**entry_data)
        except RepositoryNotFoundException as e:
            raise e
        except Exception as e:
            raise RepositoryReadException("TopicsRepository", e)

    async def get_total_count(self, query: Dict[str, Any]):
        try:
            count = await self.collection.count_documents(query)
            return count
        except Exception as e:
            raise RepositoryReadException("TopicsRepository", e)

    async def get_where(
        self, query: Dict[str, Any], skip: int, limit: int
    ) -> List[TopicModel]:
        """
        Fetch topic entries matching a specific query.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary.

        Returns:
            List[TopicModel]: A list of topic objects matching the query. Can be empty.

        Raises:
            RepositoryReadException: If there's an issue during the read operation.
        """
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            entry_data_list = await cursor.to_list(length=limit)
            print(entry_data_list)
            topics = [TopicModel(**doc) for doc in entry_data_list]
            return topics
        except Exception as e:
            raise RepositoryReadException("TopicsRepository", e)

    async def update(self, topic_id: str, update_data: Dict[str, Any]) -> TopicModel:
        """
        Update an existing topic entry by `topic_id`.

        Args:
            topic_id (str): The unique identifier for the topic to update.
            update_data (Dict[str, Any]): A dictionary containing the fields to update.

        Returns:
            TopicModel: The updated topic object.

        Raises:
            RepositoryUpdateException: If the update fails.
            RepositoryNotFoundException: If the topic to update is not found.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_payload = {"$set": {**update_data, "updated_at": time_now}}

            updated_entry = await self.collection.find_one_and_update(
                {"_id": ObjectId(topic_id)},
                update_payload,
                return_document=ReturnDocument.AFTER,  # Return the document *after* update
            )
            if not updated_entry:
                raise RepositoryNotFoundException(
                    "TopicsRepository",
                    f"Topic with topic_id '{topic_id}' not found for update.",
                )
            return TopicModel(**updated_entry)
        except RepositoryNotFoundException as e:
            # Re-raise specific exception
            raise e
        except Exception as e:
            raise RepositoryUpdateException("TopicsRepository", e)

    async def delete(self, topic_id: str) -> TopicModel:
        """
        Delete a topic entry by `topic_id` and return the deleted document.

        Args:
            topic_id (str): The unique identifier for the topic to delete.

        Returns:
            TopicModel: The topic object that was deleted.

        Raises:
            RepositoryDeleteException: If the deletion fails.
            RepositoryNotFoundException: If the topic to delete is not found.
        """
        try:
            deleted_entry = await self.collection.find_one_and_delete(
                {"_id": ObjectId(topic_id)}
            )
            if not deleted_entry:
                raise RepositoryNotFoundException(
                    "TopicsRepository",
                    f"Topic with topic_id '{topic_id}' not found for deletion.",
                )
            # Return the data of the deleted document, wrapped in the model
            return TopicModel(**deleted_entry)
        except RepositoryNotFoundException as e:
            # Re-raise specific exception
            raise e
        except Exception as e:
            raise RepositoryDeleteException("TopicsRepository", e)

    async def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Delete multiple topic entries matching a specific query.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary to match documents for deletion.

        Returns:
            int: The number of documents deleted.

        Raises:
            RepositoryDeleteException: If the deletion process encounters an error.
        """
        try:
            delete_result: DeleteResult = await self.collection.delete_many(query)
            return delete_result.deleted_count
        except Exception as e:
            raise RepositoryDeleteException("TopicsRepository", e)

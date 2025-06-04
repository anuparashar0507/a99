import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)

from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from lib.models.content_desk_models import ContentDeskModel

# Configure logging
logger = logging.getLogger(__name__)


class ContentDeskRepository:
    """
    Repository class for handling CRUD operations for ContentDesk documents in MongoDB,
    following the confirmed pattern.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        """
        Initializes the ContentDeskRepository.

        Args:
            db (Persister): The database persistence layer instance.
        """
        self.db = db.get_db()
        # Get the MongoDB collection, named "content_desks"
        self.collection = db.get_collection("content_desks")
        logger.debug("ContentDeskRepository initialized.")

    async def create(self, desk_data: ContentDeskModel) -> ContentDeskModel:
        logger.info(
            f"Attempting to create content desk document with topic: '{desk_data.topic}'"
        )
        try:
            # Set timestamps just before insertion
            time_now = datetime.now(timezone.utc)
            desk_data.created_at = time_now
            desk_data.updated_at = time_now

            # Prepare data for MongoDB using Pydantic V2 model_dump
            # by_alias ensures _id mapping, exclude id if None, exclude_none avoids sending null optional fields
            insert_payload = desk_data.model_dump(
                by_alias=True, exclude_none=True, exclude={"id"}
            )

            insert_result = await self.collection.insert_one(insert_payload)
            inserted_id = insert_result.inserted_id  # This is an ObjectId
            logger.debug(f"Document inserted with MongoDB ObjectId: {inserted_id}")

            # Fetch the newly created document using the ObjectId
            created_doc = await self.collection.find_one({"_id": inserted_id})

            if not created_doc:
                logger.error(
                    f"Failed to fetch newly created content desk document with ID: {inserted_id}"
                )
                raise RepositoryCreateException(
                    "ContentDeskRepository",  # Updated context
                    Exception("Created document not found after insert."),
                )

            logger.info(
                f"Successfully created content desk document with ID: {inserted_id}"
            )
            # Parse dict from DB into Pydantic model (validator handles _id -> id str)
            return ContentDeskModel(**created_doc)
        except Exception as e:
            logger.exception(
                f"Database error during content desk creation: {e}", exc_info=True
            )
            raise RepositoryCreateException(
                "ContentDeskRepository", e
            )  # Updated context

    async def get(self, desk_id: str) -> ContentDeskModel:
        logger.info(f"Attempting to retrieve content desk document with ID: {desk_id}")
        try:
            # Convert string ID to ObjectId directly in the query filter.
            entry_data = await self.collection.find_one({"_id": ObjectId(desk_id)})

            if not entry_data:
                logger.warning(f"Content desk document not found with ID: {desk_id}")
                raise RepositoryNotFoundException(
                    "ContentDeskRepository",  # Updated context
                    f"Content desk document with ID '{desk_id}' not found.",
                )

            logger.info(
                f"Successfully retrieved content desk document with ID: {desk_id}"
            )
            # Parse dict from DB into Pydantic model
            return ContentDeskModel(**entry_data)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise specific exception
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for get operation: {desk_id}. Error: {e}"
                )
                raise RepositoryReadException(
                    "ContentDeskRepository", Exception(f"Invalid ID format: {desk_id}")
                )
            else:
                logger.exception(
                    f"Database error retrieving content desk document {desk_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryReadException("ContentDeskRepository", e)

    async def update(
        self, desk_id: str, update_data: Dict[str, Any]
    ) -> ContentDeskModel:
        logger.info(f"Attempting to update content desk document with ID: {desk_id}")
        try:
            # Prepare the $set payload with updated_at timestamp
            time_now = datetime.now(timezone.utc)
            update_payload = {"$set": {**update_data, "updated_at": time_now}}

            # Prevent updating immutable fields
            if "_id" in update_payload["$set"]:
                del update_payload["$set"]["_id"]
            if "id" in update_payload["$set"]:
                del update_payload["$set"]["id"]
            if "created_at" in update_payload["$set"]:
                del update_payload["$set"]["created_at"]
            if "user_id" in update_payload["$set"]:
                del update_payload["$set"]["user_id"]  # User shouldn't change

            logger.debug(
                f"Update payload for {desk_id}: {update_payload['$set'].keys()}"
            )

            # Perform find_one_and_update, converting ID string to ObjectId
            updated_entry = await self.collection.find_one_and_update(
                {"_id": ObjectId(desk_id)},  # Raises InvalidId if format is wrong
                update_payload,
                return_document=ReturnDocument.AFTER,
            )

            if not updated_entry:
                logger.warning(
                    f"Content desk document not found for update with ID: {desk_id}"
                )
                raise RepositoryNotFoundException(
                    "ContentDeskRepository",  # Updated context
                    f"Content desk document with ID '{desk_id}' not found for update.",
                )

            logger.info(
                f"Successfully updated content desk document with ID: {desk_id}"
            )
            # Parse and return the updated document
            return ContentDeskModel(**updated_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for update operation: {desk_id}. Error: {e}"
                )
                raise RepositoryUpdateException(
                    "ContentDeskRepository", Exception(f"Invalid ID format: {desk_id}")
                )  # Updated context
            else:
                logger.exception(
                    f"Database error updating content desk document {desk_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryUpdateException(
                    "ContentDeskRepository", e
                )  # Updated context

    async def delete(self, desk_id: str) -> ContentDeskModel:
        logger.info(f"Attempting to delete content desk document with ID: {desk_id}")
        try:
            # Perform find_one_and_delete, converting ID string to ObjectId
            deleted_entry = await self.collection.find_one_and_delete(
                {"_id": ObjectId(desk_id)}  # Raises InvalidId if format is wrong
            )

            if not deleted_entry:
                logger.warning(
                    f"Content desk document not found for deletion with ID: {desk_id}"
                )
                raise RepositoryNotFoundException(
                    "ContentDeskRepository",  # Updated context
                    f"Content desk document with ID '{desk_id}' not found for deletion.",
                )

            logger.info(
                f"Successfully deleted content desk document with ID: {desk_id}"
            )
            # Parse and return the deleted document
            return ContentDeskModel(**deleted_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for delete operation: {desk_id}. Error: {e}"
                )
                raise RepositoryDeleteException(
                    "ContentDeskRepository", Exception(f"Invalid ID format: {desk_id}")
                )  # Updated context
            else:
                logger.exception(
                    f"Database error deleting content desk document {desk_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryDeleteException(
                    "ContentDeskRepository", e
                )  # Updated context

    async def get_where(
        self,
        query: Dict[str, Any],
        skip: int = 0,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> List[ContentDeskModel]:
        logger.info(
            f"Attempting to retrieve content desk documents with query: {query}, skip: {skip}, limit: {limit}, sort: {sort}"
        )
        try:
            # Build cursor with query, sorting, and pagination
            cursor = self.collection.find(query)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.skip(skip)
            if limit is not None and limit > 0:
                cursor = cursor.limit(limit)

            # Execute query and fetch results
            results_list = await cursor.to_list(length=limit)
            logger.info(
                f"Retrieved {len(results_list)} content desk documents matching query."
            )

            # Parse results into list of ContentDeskModel instances
            return [ContentDeskModel(**doc) for doc in results_list]
        except Exception as e:
            logger.exception(
                f"Database error during get_where for content desks: {e}", exc_info=True
            )
            raise RepositoryReadException("ContentDeskRepository", e)  # Updated context

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import ReturnDocument
from bson.errors import (
    InvalidId,
)
from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from lib.models.content_models import ContentModel

# Configure logging
logger = logging.getLogger(__name__)


class ContentRepository:
    """
    Repository class for handling CRUD operations for final Content documents in MongoDB,
    following the confirmed pattern.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        """
        Initializes the ContentRepository.

        Args:
            db (Persister): The database persistence layer instance.
        """
        self.db = db.get_db()
        # Get the MongoDB collection, named "contents"
        self.collection = db.get_collection("contents")
        logger.debug("ContentRepository initialized.")

    async def create(self, content_data: ContentModel) -> ContentModel:
        """
        Creates a new content document in the database.

        Args:
            content_data (ContentModel): The Pydantic model instance containing content data.
                                         The 'id' field should typically be None.

        Returns:
            ContentModel: The created content object, including the generated database ID (as str)
                          and timestamps.

        Raises:
            RepositoryCreateException: If the database operation fails.
        """
        logger.info(f"Attempting to create content document: {content_data}")
        try:
            # Set timestamps just before insertion
            time_now = datetime.now(timezone.utc)
            content_data.created_at = time_now
            content_data.updated_at = time_now

            # Prepare data for MongoDB using Pydantic V2 model_dump
            insert_payload = content_data.model_dump(
                by_alias=True, exclude_none=True, exclude={"id"}
            )

            insert_result = await self.collection.insert_one(insert_payload)
            inserted_id = insert_result.inserted_id  # This is an ObjectId
            logger.debug(f"Document inserted with MongoDB ObjectId: {inserted_id}")

            # Fetch the newly created document using the ObjectId
            created_doc = await self.collection.find_one({"_id": inserted_id})

            if not created_doc:
                logger.error(
                    f"Failed to fetch newly created content document with ID: {inserted_id}"
                )
                raise RepositoryCreateException(
                    "ContentRepository",  # Updated context
                    Exception("Created document not found after insert."),
                )

            logger.info(f"Successfully created content document with ID: {inserted_id}")
            # Parse dict from DB into Pydantic model (validator handles _id -> id str)
            return ContentModel(**created_doc)
        except Exception as e:
            logger.exception(
                f"Database error during content creation: {e}", exc_info=True
            )
            raise RepositoryCreateException("ContentRepository", e)  # Updated context

    async def get(self, content_id: str) -> ContentModel:
        """
        Retrieves a single content document by its string ID.

        Args:
            content_id (str): The unique identifier (string representation of ObjectId)
                              of the content document.

        Returns:
            ContentModel: The found content object.

        Raises:
            RepositoryNotFoundException: If no document matches the provided ID.
            RepositoryReadException: If the provided ID string is invalid or a database error occurs.
        """
        logger.info(f"Attempting to retrieve content document with ID: {content_id}")
        try:
            # Convert string ID to ObjectId directly in the query filter.
            entry_data = await self.collection.find_one({"_id": ObjectId(content_id)})

            if not entry_data:
                logger.warning(f"Content document not found with ID: {content_id}")
                raise RepositoryNotFoundException(
                    "ContentRepository",  # Updated context
                    f"Content document with ID '{content_id}' not found.",
                )

            logger.info(
                f"Successfully retrieved content document with ID: {content_id}"
            )
            # Parse dict from DB into Pydantic model
            return ContentModel(**entry_data)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise specific exception
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for get operation: {content_id}. Error: {e}"
                )
                # Raise general Read exception as per pattern
                raise RepositoryReadException(
                    "ContentRepository", f"Invalid ID format: {content_id}"
                )
            else:
                logger.exception(
                    f"Database error retrieving content document {content_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryReadException("ContentRepository", e)  # Updated context

    async def update(
        self, content_id: str, update_data: Dict[str, Any]
    ) -> ContentModel:
        """
        Updates an existing content document by its string ID.

        Args:
            content_id (str): The unique identifier (string representation of ObjectId)
                              of the content document to update.
            update_data (Dict[str, Any]): A dictionary containing the fields to update
                                          (e.g., {"result": "new content"}).

        Returns:
            ContentModel: The updated content object.

        Raises:
            RepositoryNotFoundException: If the document to update is not found.
            RepositoryUpdateException: If the provided ID string is invalid or the update fails.
        """
        logger.info(f"Attempting to update content document with ID: {content_id}")
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

            logger.debug(
                f"Update payload for {content_id}: {update_payload['$set'].keys()}"
            )

            # Perform find_one_and_update, converting ID string to ObjectId
            updated_entry = await self.collection.find_one_and_update(
                {"_id": ObjectId(content_id)},  # Raises InvalidId if format is wrong
                update_payload,
                return_document=ReturnDocument.AFTER,
            )

            if not updated_entry:
                logger.warning(
                    f"Content document not found for update with ID: {content_id}"
                )
                raise RepositoryNotFoundException(
                    "ContentRepository",  # Updated context
                    f"Content document with ID '{content_id}' not found for update.",
                )

            logger.info(f"Successfully updated content document with ID: {content_id}")
            # Parse and return the updated document
            return ContentModel(**updated_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for update operation: {content_id}. Error: {e}"
                )
                raise RepositoryUpdateException(
                    "ContentRepository", f"Invalid ID format: {content_id}"
                )
            else:
                logger.exception(
                    f"Database error updating content document {content_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryUpdateException(
                    "ContentRepository", e
                )  # Updated context

    async def delete(self, content_id: str) -> ContentModel:
        """
        Deletes a content document by its string ID and returns the deleted document.

        Args:
            content_id (str): The unique identifier (string representation of ObjectId)
                              of the content document to delete.

        Returns:
            ContentModel: The content object that was deleted.

        Raises:
            RepositoryNotFoundException: If the document to delete is not found.
            RepositoryDeleteException: If the provided ID string is invalid or the delete fails.
        """
        logger.info(f"Attempting to delete content document with ID: {content_id}")
        try:
            # Perform find_one_and_delete, converting ID string to ObjectId
            deleted_entry = await self.collection.find_one_and_delete(
                {"_id": ObjectId(content_id)}  # Raises InvalidId if format is wrong
            )

            if not deleted_entry:
                logger.warning(
                    f"Content document not found for deletion with ID: {content_id}"
                )
                raise RepositoryNotFoundException(
                    "ContentRepository",  # Updated context
                    f"Content document with ID '{content_id}' not found for deletion.",
                )

            logger.info(f"Successfully deleted content document with ID: {content_id}")
            # Parse and return the deleted document
            return ContentModel(**deleted_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for delete operation: {content_id}. Error: {e}"
                )
                raise RepositoryDeleteException(
                    "ContentRepository", f"Invalid ID format: {content_id}"
                )
            else:
                logger.exception(
                    f"Database error deleting content document {content_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryDeleteException(
                    "ContentRepository", e
                )  # Updated context

    async def get_where(
        self, query: Dict[str, Any], skip: int = 0, limit: Optional[int] = None
    ) -> List[ContentModel]:
        """
        Retrieves multiple content documents matching a given query, with optional pagination.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary (e.g., {"user_id": "..."}).
            skip (int): Number of documents to skip (for pagination). Defaults to 0.
            limit (Optional[int]): Maximum number of documents to return. Defaults to None (no limit).

        Returns:
            List[ContentModel]: A list of matching content objects. Can be empty.

        Raises:
            RepositoryReadException: If a database error occurs.
        """
        logger.info(
            f"Attempting to retrieve content documents with query: {query}, skip: {skip}, limit: {limit}"
        )
        try:
            # Build cursor with query and pagination
            cursor = self.collection.find(query).skip(skip)
            if limit is not None and limit > 0:
                cursor = cursor.limit(limit)

            # Execute query and fetch results
            results_list = await cursor.to_list(length=limit)
            logger.info(
                f"Retrieved {len(results_list)} content documents matching query."
            )

            # Parse results into list of ContentModel instances
            return [ContentModel(**doc) for doc in results_list]
        except Exception as e:
            logger.exception(
                f"Database error during get_where for contents: {e}", exc_info=True
            )
            raise RepositoryReadException("ContentRepository", e)  # Updated context

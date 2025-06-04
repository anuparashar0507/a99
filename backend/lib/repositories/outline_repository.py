import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
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
from lib.models.outline_models import OutlineModel
from pymongo import ReturnDocument


# Configure logging
logger = logging.getLogger(__name__)


class OutlineRepository:
    """
    Repository class for handling CRUD operations for Outline documents in MongoDB,
    following the confirmed pattern.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        """
        Initializes the OutlineRepository.

        Args:
            db (Persister): The database persistence layer instance.
        """
        self.db = db.get_db()
        # Get the MongoDB collection, named "outlines"
        self.collection = db.get_collection("outlines")
        logger.debug("OutlineRepository initialized.")

    async def create(self, outline_data: OutlineModel) -> OutlineModel:
        """
        Creates a new outline document in the database.

        Args:
            outline_data (OutlineModel): The Pydantic model instance containing outline data.
                                         The 'id' field should typically be None.

        Returns:
            OutlineModel: The created outline object, including the generated database ID (as str)
                          and timestamps.

        Raises:
            RepositoryCreateException: If the database operation fails.
        """
        logger.info(f"Attempting to create outline document.")
        # Log sensitive data carefully, e.g., log only keys or summary
        # logger.debug(f"Outline data for creation: {outline_data.model_dump(exclude={'result', 'feedback'})}")
        try:
            # Set timestamps just before insertion
            time_now = datetime.now(timezone.utc)
            outline_data.created_at = time_now
            outline_data.updated_at = time_now

            # Prepare data for MongoDB using Pydantic V2 model_dump
            # by_alias=True ensures '_id' is used if 'id' is present (it shouldn't be on create)
            # exclude={'id'} ensures the 'id' field (even if None) isn't sent, letting MongoDB generate '_id'
            insert_payload = outline_data.model_dump(
                by_alias=True, exclude_none=True, exclude={"id"}
            )

            insert_result = await self.collection.insert_one(insert_payload)
            inserted_id = insert_result.inserted_id  # This is an ObjectId
            logger.debug(f"Document inserted with MongoDB ObjectId: {inserted_id}")

            # Fetch the newly created document using the ObjectId to return the complete object
            created_doc = await self.collection.find_one({"_id": inserted_id})

            if not created_doc:
                logger.error(
                    f"Failed to fetch newly created outline document with ID: {inserted_id}"
                )
                # Raise specific exception for creation failure after insert
                raise RepositoryCreateException(
                    "OutlineRepository",
                    Exception("Created document not found after insert."),
                )

            logger.info(f"Successfully created outline document with ID: {inserted_id}")
            # Parse the dict from DB into the Pydantic model.
            # The model's validator will convert the '_id' (ObjectId) to 'id' (str).
            return OutlineModel(**created_doc)
        except Exception as e:
            logger.exception(
                f"Database error during outline creation: {e}", exc_info=True
            )
            # Wrap generic exception into specific repository exception
            raise RepositoryCreateException("OutlineRepository", e)

    async def get(self, outline_id: str) -> OutlineModel:
        """
        Retrieves a single outline document by its string ID.

        Args:
            outline_id (str): The unique identifier (string representation of ObjectId)
                              of the outline document.

        Returns:
            OutlineModel: The found outline object.

        Raises:
            RepositoryNotFoundException: If no document matches the provided ID.
            RepositoryReadException: If the provided ID string is invalid or a database error occurs.
        """
        logger.info(f"Attempting to retrieve outline document with ID: {outline_id}")
        try:
            # Convert string ID to ObjectId directly in the query.
            # This will raise bson.errors.InvalidId if the string is not valid,
            # which will be caught by the generic Exception handler below.
            entry_data = await self.collection.find_one({"_id": ObjectId(outline_id)})

            if not entry_data:
                logger.warning(f"Outline document not found with ID: {outline_id}")
                raise RepositoryNotFoundException(
                    "OutlineRepository",
                    f"Outline document with ID '{outline_id}' not found.",
                )

            logger.info(
                f"Successfully retrieved outline document with ID: {outline_id}"
            )
            # Parse the retrieved dictionary. Validator handles _id -> id (str).
            return OutlineModel(**entry_data)
        except RepositoryNotFoundException as specific_ex:
            # Re-raise specific exceptions we want to propagate clearly
            raise specific_ex
        except Exception as e:
            # This catches InvalidId errors from ObjectId(outline_id) and other DB errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for get operation: {outline_id}. Error: {e}"
                )
                # Raising RepositoryReadException as per the user's confirmed pattern (no specific InvalidId exception)
                raise RepositoryReadException(
                    "OutlineRepository", f"Invalid ID format: {outline_id}"
                )
            else:
                logger.exception(
                    f"Database error retrieving outline document {outline_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryReadException("OutlineRepository", e)

    async def update(
        self, outline_id: str, update_data: Dict[str, Any]
    ) -> OutlineModel:
        """
        Updates an existing outline document by its string ID.

        Args:
            outline_id (str): The unique identifier (string representation of ObjectId)
                              of the outline document to update.
            update_data (Dict[str, Any]): A dictionary containing the fields to update.
                                          Keys should match OutlineModel field names (e.g., 'feedback', 'result').

        Returns:
            OutlineModel: The updated outline object.

        Raises:
            RepositoryNotFoundException: If the document to update is not found.
            RepositoryUpdateException: If the provided ID string is invalid or the database update fails.
        """
        logger.info(f"Attempting to update outline document with ID: {outline_id}")
        try:
            # Prepare the $set payload
            time_now = datetime.now(timezone.utc)
            update_payload = {"$set": {**update_data, "updated_at": time_now}}

            # Prevent updating immutable fields like _id, id, or created_at via $set
            if "_id" in update_payload["$set"]:
                del update_payload["$set"]["_id"]
            if "id" in update_payload["$set"]:
                del update_payload["$set"]["id"]
            if "created_at" in update_payload["$set"]:
                del update_payload["$set"]["created_at"]

            logger.debug(
                f"Update payload for {outline_id}: {update_payload['$set'].keys()}"
            )  # Log keys being updated

            # Perform the find and update operation, converting ID string to ObjectId.
            # Return the document *after* the update.
            updated_entry = await self.collection.find_one_and_update(
                {"_id": ObjectId(outline_id)},  # Raises InvalidId if format is wrong
                update_payload,
                return_document=ReturnDocument.AFTER,
            )

            if not updated_entry:
                logger.warning(
                    f"Outline document not found for update with ID: {outline_id}"
                )
                raise RepositoryNotFoundException(
                    "OutlineRepository",
                    f"Outline document with ID '{outline_id}' not found for update.",
                )

            logger.info(f"Successfully updated outline document with ID: {outline_id}")
            # Parse and return the updated document. Validator handles _id -> id (str).
            return OutlineModel(**updated_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # This catches InvalidId errors from ObjectId(outline_id) and other DB errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for update operation: {outline_id}. Error: {e}"
                )
                raise RepositoryUpdateException(
                    "OutlineRepository", f"Invalid ID format: {outline_id}"
                )
            else:
                logger.exception(
                    f"Database error updating outline document {outline_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryUpdateException("OutlineRepository", e)

    async def delete(self, outline_id: str) -> OutlineModel:
        """
        Deletes an outline document by its string ID and returns the deleted document.

        Args:
            outline_id (str): The unique identifier (string representation of ObjectId)
                              of the outline document to delete.

        Returns:
            OutlineModel: The outline object that was deleted.

        Raises:
            RepositoryNotFoundException: If the document to delete is not found.
            RepositoryDeleteException: If the provided ID string is invalid or the database delete fails.
        """
        logger.info(f"Attempting to delete outline document with ID: {outline_id}")
        try:
            # Perform the find and delete operation, converting ID string to ObjectId.
            deleted_entry = await self.collection.find_one_and_delete(
                {"_id": ObjectId(outline_id)}  # Raises InvalidId if format is wrong
            )

            if not deleted_entry:
                logger.warning(
                    f"Outline document not found for deletion with ID: {outline_id}"
                )
                raise RepositoryNotFoundException(
                    "OutlineRepository",
                    f"Outline document with ID '{outline_id}' not found for deletion.",
                )

            logger.info(f"Successfully deleted outline document with ID: {outline_id}")
            # Parse and return the data of the deleted document. Validator handles _id -> id (str).
            return OutlineModel(**deleted_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # This catches InvalidId errors from ObjectId(outline_id) and other DB errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for delete operation: {outline_id}. Error: {e}"
                )
                raise RepositoryDeleteException(
                    "OutlineRepository", f"Invalid ID format: {outline_id}"
                )
            else:
                logger.exception(
                    f"Database error deleting outline document {outline_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryDeleteException("OutlineRepository", e)

    async def get_where(
        self, query: Dict[str, Any], skip: int = 0, limit: Optional[int] = None
    ) -> List[OutlineModel]:
        """
        Retrieves multiple outline documents matching a given query, with optional pagination.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary.
            skip (int): Number of documents to skip (for pagination). Defaults to 0.
            limit (Optional[int]): Maximum number of documents to return. Defaults to None (no limit).

        Returns:
            List[OutlineModel]: A list of matching outline objects. Can be empty.

        Raises:
            RepositoryReadException: If a database error occurs.
        """
        logger.info(
            f"Attempting to retrieve outline documents with query: {query}, skip: {skip}, limit: {limit}"
        )
        try:
            # Build the cursor with query and pagination options
            cursor = self.collection.find(query).skip(skip)
            if limit is not None and limit > 0:
                cursor = cursor.limit(limit)

            # Execute the query and fetch results into a list
            results_list = await cursor.to_list(
                length=limit
            )  # Pass limit for potential optimization
            logger.info(
                f"Retrieved {len(results_list)} outline documents matching query."
            )

            # Parse each document dictionary into an OutlineModel instance
            return [OutlineModel(**doc) for doc in results_list]
        except Exception as e:
            logger.exception(
                f"Database error during get_where for outlines: {e}", exc_info=True
            )
            raise RepositoryReadException("OutlineRepository", e)

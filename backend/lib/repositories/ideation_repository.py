import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument

from bson import ObjectId

from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)

from ..models.ideation_models import IdeationModel


logger = logging.getLogger(__name__)


class IdeationRepository:
    """
    Repository class for handling CRUD operations for Ideation documents in MongoDB.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        """
        Initializes the IdeationRepository.

        Args:
            db (Persister): The database persistence layer instance.
        """
        self.db = db.get_db()
        # Get the MongoDB collection, named "ideations"
        self.collection = db.get_collection("ideations")
        logger.debug("IdeationRepository initialized.")

    async def create(self, ideation_data: IdeationModel) -> IdeationModel:
        """
        Creates a new ideation document in the database.

        Args:
            ideation_data (IdeationModel): The Pydantic model instance containing ideation data.
                                           The 'id' field should typically be None.

        Returns:
            IdeationModel: The created ideation object, including the generated database ID and timestamps.

        Raises:
            RepositoryCreateException: If the database operation fails.
        """
        logger.info(
            f"Attempting to create ideation document for data: '{ideation_data}'"
        )
        try:
            # Set timestamps just before insertion
            time_now = datetime.now(timezone.utc)
            ideation_data.created_at = time_now
            ideation_data.updated_at = time_now

            # Prepare data for MongoDB, using aliases (like '_id') and excluding 'id' if None
            insert_payload = ideation_data.model_dump(
                by_alias=True, exclude_none=True, exclude={"id"}
            )

            insert_result = await self.collection.insert_one(insert_payload)
            inserted_id = insert_result.inserted_id
            logger.debug(f"Document inserted with ID: {inserted_id}")

            # Fetch the newly created document to return the complete object
            created_doc = await self.collection.find_one({"_id": inserted_id})
            if not created_doc:
                logger.error(
                    f"Failed to fetch newly created ideation document with ID: {inserted_id}"
                )
                raise RepositoryCreateException(
                    "IdeationRepository",
                    Exception("Created document not found after insert."),
                )

            logger.info(
                f"Successfully created ideation document with ID: {inserted_id}"
            )
            return IdeationModel(**created_doc)
        except Exception as e:
            logger.exception(
                f"Database error during ideation creation: {e}", exc_info=True
            )
            raise RepositoryCreateException("IdeationRepository", e)

    async def get(self, ideation_id: str) -> IdeationModel:
        """
        Retrieves a single ideation document by its ID.

        Args:
            ideation_id (str): The unique identifier (string representation of ObjectId)
                               of the ideation document.

        Returns:
            IdeationModel: The found ideation object.

        Raises:
            RepositoryInvalidIdException: If the provided ideation_id is not a valid ObjectId string.
            RepositoryNotFoundException: If no document matches the provided ID.
            RepositoryReadException: If a database error occurs during retrieval.
        """
        logger.info(f"Attempting to retrieve ideation document with ID: {ideation_id}")
        try:

            entry_data = await self.collection.find_one({"_id": ObjectId(ideation_id)})

            if not entry_data:
                logger.warning(f"Ideation document not found with ID: {ideation_id}")
                raise RepositoryNotFoundException(
                    "IdeationRepository",
                    f"Ideation document with ID '{ideation_id}' not found.",
                )

            logger.info(
                f"Successfully retrieved ideation document with ID: {ideation_id}"
            )
            # Parse the retrieved dictionary into the Pydantic model
            return IdeationModel(**entry_data)
        except RepositoryNotFoundException as specific_ex:
            # Re-raise specific exceptions we want to propagate clearly
            raise specific_ex
        except Exception as e:
            logger.exception(
                f"Database error retrieving ideation document {ideation_id}: {e}",
                exc_info=True,
            )
            raise RepositoryReadException("IdeationRepository", e)

    async def update(
        self, ideation_id: str, update_data: Dict[str, Any]
    ) -> IdeationModel:
        """
        Updates an existing ideation document by its ID.

        Args:
            ideation_id (str): The unique identifier (string representation of ObjectId)
                               of the ideation document to update.
            update_data (Dict[str, Any]): A dictionary containing the fields to update.
                                          Keys should match IdeationModel field names.

        Returns:
            IdeationModel: The updated ideation object.

        Raises:
            RepositoryInvalidIdException: If the provided ideation_id is not valid.
            RepositoryNotFoundException: If the document to update is not found.
            RepositoryUpdateException: If the database update operation fails.
        """
        logger.info(f"Attempting to update ideation document with ID: {ideation_id}")
        try:

            # Ensure 'updated_at' is always set on update
            time_now = datetime.now(timezone.utc)
            update_payload = {"$set": {**update_data, "updated_at": time_now}}

            # Prevent updating immutable fields like _id or created_at via $set
            if "_id" in update_payload["$set"]:
                del update_payload["$set"]["_id"]
            if "id" in update_payload["$set"]:
                del update_payload["$set"]["id"]
            if "created_at" in update_payload["$set"]:
                del update_payload["$set"]["created_at"]

            logger.debug(f"Update payload for {ideation_id}: {update_payload}")

            # Perform the find and update operation, returning the updated document
            updated_entry = await self.collection.find_one_and_update(
                {"_id": ObjectId(ideation_id)},
                update_payload,
                return_document=ReturnDocument.AFTER,  # Return the document *after* the update
            )

            if not updated_entry:
                logger.warning(
                    f"Ideation document not found for update with ID: {ideation_id}"
                )
                raise RepositoryNotFoundException(
                    "IdeationRepository",
                    f"Ideation document with ID '{ideation_id}' not found for update.",
                )

            logger.info(
                f"Successfully updated ideation document with ID: {ideation_id}"
            )
            # Parse and return the updated document
            return IdeationModel(**updated_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex
        except Exception as e:
            logger.exception(
                f"Database error updating ideation document {ideation_id}: {e}",
                exc_info=True,
            )
            raise RepositoryUpdateException("IdeationRepository", e)

    async def delete(self, ideation_id: str) -> IdeationModel:
        """
        Deletes an ideation document by its ID and returns the deleted document.

        Args:
            ideation_id (str): The unique identifier (string representation of ObjectId)
                               of the ideation document to delete.

        Returns:
            IdeationModel: The ideation object that was deleted.

        Raises:
            RepositoryInvalidIdException: If the provided ideation_id is not valid.
            RepositoryNotFoundException: If the document to delete is not found.
            RepositoryDeleteException: If the database delete operation fails.
        """
        logger.info(f"Attempting to delete ideation document with ID: {ideation_id}")
        try:

            # Perform the find and delete operation
            deleted_entry = await self.collection.find_one_and_delete(
                {"_id": ObjectId(ideation_id)}
            )

            if not deleted_entry:
                logger.warning(
                    f"Ideation document not found for deletion with ID: {ideation_id}"
                )
                raise RepositoryNotFoundException(
                    "IdeationRepository",
                    f"Ideation document with ID '{ideation_id}' not found for deletion.",
                )

            logger.info(
                f"Successfully deleted ideation document with ID: {ideation_id}"
            )
            # Parse and return the data of the deleted document
            return IdeationModel(**deleted_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            logger.exception(
                f"Database error deleting ideation document {ideation_id}: {e}",
                exc_info=True,
            )
            raise RepositoryDeleteException("IdeationRepository", e)

    async def get_where(
        self, query: Dict[str, Any], skip: int = 0, limit: Optional[int] = None
    ) -> List[IdeationModel]:
        """
        Retrieves multiple ideation documents matching a given query, with optional pagination.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary.
            skip (int): Number of documents to skip (for pagination). Defaults to 0.
            limit (Optional[int]): Maximum number of documents to return. Defaults to None (no limit).

        Returns:
            List[IdeationModel]: A list of matching ideation objects. Can be empty.

        Raises:
            RepositoryReadException: If a database error occurs.
        """
        logger.info(
            f"Attempting to retrieve ideation documents with query: {query}, skip: {skip}, limit: {limit}"
        )
        try:
            cursor = self.collection.find(query).skip(skip)
            if limit is not None and limit > 0:
                cursor = cursor.limit(limit)

            results_list = await cursor.to_list(
                length=limit
            )  # Pass limit for efficiency
            logger.info(
                f"Retrieved {len(results_list)} ideation documents matching query."
            )
            return [IdeationModel(**doc) for doc in results_list]
        except Exception as e:
            logger.exception(
                f"Database error during get_where for ideations: {e}", exc_info=True
            )
            raise RepositoryReadException("IdeationRepository", e)

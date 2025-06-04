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
from lib.models.post_models import PostModel

# Configure logging
logger = logging.getLogger(__name__)


class PostRepository:
    """
    Repository class for handling CRUD operations for Post documents in MongoDB,
    following the confirmed pattern.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        """
        Initializes the PostRepository.

        Args:
            db (Persister): The database persistence layer instance.
        """
        self.db = db.get_db()
        # Get the MongoDB collection, named "posts"
        self.collection = db.get_collection("posts")
        logger.debug("PostRepository initialized.")

    async def create(self, post_data: PostModel) -> PostModel:
        """
        Creates a new post document in the database.

        Args:
            post_data (PostModel): The Pydantic model instance containing post data.
                                   The 'id' field should typically be None.

        Returns:
            PostModel: The created post object, including the generated database ID (as str)
                       and timestamps.

        Raises:
            RepositoryCreateException: If the database operation fails.
        """
        logger.info(f"Attempting to create post document topic: '{post_data.topic}'")
        try:
            # Set timestamps just before insertion
            time_now = datetime.now(timezone.utc)
            post_data.created_at = time_now
            post_data.updated_at = time_now

            # Prepare data for MongoDB using Pydantic V2 model_dump
            insert_payload = post_data.model_dump(
                by_alias=True, exclude_none=True, exclude={"id"}
            )

            insert_result = await self.collection.insert_one(insert_payload)
            inserted_id = insert_result.inserted_id  # This is an ObjectId
            logger.debug(f"Document inserted with MongoDB ObjectId: {inserted_id}")

            # Fetch the newly created document using the ObjectId
            created_doc = await self.collection.find_one({"_id": inserted_id})

            if not created_doc:
                logger.error(
                    f"Failed to fetch newly created post document with ID: {inserted_id}"
                )
                raise RepositoryCreateException(
                    "PostRepository",  # Updated context
                    Exception("Created document not found after insert."),
                )

            logger.info(f"Successfully created post document with ID: {inserted_id}")
            # Parse dict from DB into Pydantic model (validator handles _id -> id str)
            return PostModel(**created_doc)
        except Exception as e:
            logger.exception(f"Database error during post creation: {e}", exc_info=True)
            raise RepositoryCreateException("PostRepository", e)  # Updated context

    async def get(self, post_id: str) -> PostModel:
        """
        Retrieves a single post document by its string ID.

        Args:
            post_id (str): The unique identifier (string representation of ObjectId)
                           of the post document.

        Returns:
            PostModel: The found post object.

        Raises:
            RepositoryNotFoundException: If no document matches the provided ID.
            RepositoryReadException: If the provided ID string is invalid or a database error occurs.
        """
        logger.info(f"Attempting to retrieve post document with ID: {post_id}")
        try:
            # Convert string ID to ObjectId directly in the query filter.
            entry_data = await self.collection.find_one({"_id": ObjectId(post_id)})

            if not entry_data:
                logger.warning(f"Post document not found with ID: {post_id}")
                raise RepositoryNotFoundException(
                    "PostRepository",  # Updated context
                    f"Post document with ID '{post_id}' not found.",
                )

            logger.info(f"Successfully retrieved post document with ID: {post_id}")
            # Parse dict from DB into Pydantic model
            return PostModel(**entry_data)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise specific exception
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for get operation: {post_id}. Error: {e}"
                )
                raise RepositoryReadException(
                    "PostRepository", Exception(f"Invalid ID format: {post_id}")
                )  # Updated context
            else:
                logger.exception(
                    f"Database error retrieving post document {post_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryReadException("PostRepository", e)  # Updated context

    async def update(self, post_id: str, update_data: Dict[str, Any]) -> PostModel:
        """
        Updates an existing post document by its string ID.

        Args:
            post_id (str): The unique identifier (string representation of ObjectId)
                           of the post document to update.
            update_data (Dict[str, Any]): A dictionary containing the fields to update

        Returns:
            PostModel: The updated post object.

        Raises:
            RepositoryNotFoundException: If the document to update is not found.
            RepositoryUpdateException: If the provided ID string is invalid or the update fails.
        """
        logger.info(f"Attempting to update post document with ID: {post_id}")
        try:
            # Prepare the $set payload with updated_at timestamp
            time_now = datetime.now(timezone.utc)
            update_payload = {"$set": {**update_data, "updated_at": time_now}}

            # Prevent updating immutable fields like _id, id, user_id, content_desk_id, created_at
            immutable_fields = {"_id", "id", "user_id", "content_desk_id", "created_at"}
            for field in immutable_fields:
                if field in update_payload["$set"]:
                    del update_payload["$set"][field]
                    logger.warning(
                        f"Attempted to update immutable field '{field}' for post {post_id}. Update ignored for this field."
                    )

            logger.debug(
                f"Update payload for {post_id}: {update_payload['$set'].keys()}"
            )

            # Perform find_one_and_update, converting ID string to ObjectId
            updated_entry = await self.collection.find_one_and_update(
                {"_id": ObjectId(post_id)},  # Raises InvalidId if format is wrong
                update_payload,
                return_document=ReturnDocument.AFTER,
            )

            if not updated_entry:
                logger.warning(f"Post document not found for update with ID: {post_id}")
                raise RepositoryNotFoundException(
                    "PostRepository",  # Updated context
                    f"Post document with ID '{post_id}' not found for update.",
                )

            logger.info(f"Successfully updated post document with ID: {post_id}")
            # Parse and return the updated document
            return PostModel(**updated_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for update operation: {post_id}. Error: {e}"
                )
                raise RepositoryUpdateException(
                    "PostRepository", Exception(f"Invalid ID format: {post_id}")
                )  # Updated context
            else:
                logger.exception(
                    f"Database error updating post document {post_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryUpdateException("PostRepository", e)  # Updated context

    async def delete(self, post_id: str) -> PostModel:
        """
        Deletes a post document by its string ID and returns the deleted document.

        Args:
            post_id (str): The unique identifier (string representation of ObjectId)
                           of the post document to delete.

        Returns:
            PostModel: The post object that was deleted.

        Raises:
            RepositoryNotFoundException: If the document to delete is not found.
            RepositoryDeleteException: If the provided ID string is invalid or the delete fails.
        """
        logger.info(f"Attempting to delete post document with ID: {post_id}")
        try:
            # Perform find_one_and_delete, converting ID string to ObjectId
            deleted_entry = await self.collection.find_one_and_delete(
                {"_id": ObjectId(post_id)}  # Raises InvalidId if format is wrong
            )

            if not deleted_entry:
                logger.warning(
                    f"Post document not found for deletion with ID: {post_id}"
                )
                raise RepositoryNotFoundException(
                    "PostRepository",  # Updated context
                    f"Post document with ID '{post_id}' not found for deletion.",
                )

            logger.info(f"Successfully deleted post document with ID: {post_id}")
            # Parse and return the deleted document
            return PostModel(**deleted_entry)
        except RepositoryNotFoundException as specific_ex:
            raise specific_ex  # Re-raise
        except Exception as e:
            # Catch InvalidId and other potential errors
            if isinstance(e, InvalidId):
                logger.warning(
                    f"Invalid ID format provided for delete operation: {post_id}. Error: {e}"
                )
                raise RepositoryDeleteException(
                    "PostRepository", Exception(f"Invalid ID format: {post_id}")
                )  # Updated context
            else:
                logger.exception(
                    f"Database error deleting post document {post_id}: {e}",
                    exc_info=True,
                )
                raise RepositoryDeleteException("PostRepository", e)  # Updated context

    async def get_where(
        self,
        query: Dict[str, Any],
        skip: int = 0,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> List[PostModel]:
        """
        Retrieves multiple post documents matching a query, with optional pagination and sorting.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary (e.g., {"user_id": "..."}).
            skip (int): Number of documents to skip. Defaults to 0.
            limit (Optional[int]): Maximum number of documents to return. Defaults to None.
            sort (Optional[List[tuple]]): Sorting order. Example: [("created_at", -1)].

        Returns:
            List[PostModel]: A list of matching post objects. Can be empty.

        Raises:
            RepositoryReadException: If a database error occurs.
        """
        logger.info(
            f"Attempting to retrieve post documents with query: {query}, skip: {skip}, limit: {limit}, sort: {sort}"
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
            logger.info(f"Retrieved {len(results_list)} post documents matching query.")

            # Parse results into list of PostModel instances
            return [PostModel(**doc) for doc in results_list]
        except Exception as e:
            logger.exception(
                f"Database error during get_where for posts: {e}", exc_info=True
            )
            raise RepositoryReadException("PostRepository", e)  # Updated context

    async def get_total_count(self, query: Dict[str, Any]) -> int:
        """
        Counts the total number of documents matching a given query.

        Args:
            query (Dict[str, Any]): The MongoDB query dictionary.

        Returns:
            int: The total number of matching documents.

        Raises:
            RepositoryReadException: If the database count operation fails.
        """
        logger.debug(f"Counting documents in 'posts' collection with query: {query}")
        try:
            count = await self.collection.count_documents(query)
            logger.debug(f"Found {count} documents matching query.")
            return count
        except Exception as e:
            logger.exception(
                f"Database error counting post documents with query {query}: {e}",
                exc_info=True,
            )
            raise RepositoryReadException(
                "PostRepository", Exception(f"Failed to count documents: {e}")
            )

    async def delete_many(self, post_ids: List[str]) -> int:
        """
        Deletes multiple post documents based on a list of string IDs.

        Args:
            post_ids (List[str]): A list of unique identifiers (string representation of ObjectId).

        Returns:
            int: The number of documents actually deleted.

        Raises:
            RepositoryDeleteException: If the database delete operation fails or if any ID is invalid.
        """
        if not post_ids:
            logger.warning("delete_many called with empty post_ids list.")
            return 0

        logger.info(f"Attempting to delete {len(post_ids)} post documents.")
        object_ids = []
        try:
            # Convert all string IDs to ObjectIds first
            for post_id in post_ids:
                object_ids.append(ObjectId(post_id))
        except InvalidId as id_err:
            logger.error(
                f"Invalid ObjectId format found in list for delete_many: {id_err}"
            )
            raise RepositoryDeleteException(
                "PostRepository", Exception(f"Invalid ID format in list: {id_err}")
            )
        except Exception as e:  # Catch other potential errors during conversion
            logger.exception(
                f"Error converting IDs for delete_many: {e}", exc_info=True
            )
            raise RepositoryDeleteException(
                "PostRepository", Exception(f"Error processing IDs: {e}")
            )

        try:
            # Perform the delete_many operation
            query = {"_id": {"$in": object_ids}}
            delete_result = await self.collection.delete_many(query)
            deleted_count = delete_result.deleted_count
            logger.info(f"Successfully deleted {deleted_count} post documents.")
            return deleted_count
        except Exception as e:
            logger.exception(
                f"Database error during delete_many posts: {e}", exc_info=True
            )
            raise RepositoryDeleteException(
                "PostRepository", Exception(f"Failed delete_many: {e}")
            )

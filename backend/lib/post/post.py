import logging
from typing import Any, Dict, List, Optional

from lib.repositories.repository_manager_protocol import (
    RepositoryManagerProtocol,
)

from lib.models.post_models import (
    PostModel,
    PostStatus,
    PostsPaginatedResponse,
)
from lib.repositories.exceptions import (
    RepositoryCreateException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)


logger = logging.getLogger(__name__)


class Post:
    """
    Service class for managing Posts (e.g., blog posts, articles).
    Handles CRUD operations and retrieval using the PostRepository.
    """

    def __init__(self, db: RepositoryManagerProtocol):
        """
        Initializes the Post service.

        Args:
            db (RepositoryManagerProtocol): Provides access to data repositories,
                                             specifically post_repository.
        """
        self.db = db
        logger.info("Post service initialized.")

    async def create_post(self, post_data: PostModel) -> PostModel:
        """
        Creates a new post record.

        Args:
            post_data (PostModel): A PostModel instance containing the initial data.
                                   'id', 'created_at', 'updated_at' should be None.
                                   Status defaults to DRAFT if not provided.

        Returns:
            PostModel: The created Post object.

        Raises:
            Exception: Generic exception if creation fails.
        """
        logger.info(f"Attempting to create post: topic='{post_data.topic}'")
        try:
            # The repository's create method handles setting timestamps
            created_post = await self.db.post_repository.create(post_data)
            logger.info(f"Successfully created post with ID: {created_post.id}")
            return created_post
        except RepositoryCreateException as e:
            logger.error(f"Failed to create post: {e}", exc_info=True)
            # Raise generic exception as per pattern
            raise Exception(f"Cannot create post at the moment: {e}")
        except Exception as e:
            # Catch other potential errors (e.g., validation if model creation happens here)
            logger.exception(
                f"Unexpected error during post creation: {e}", exc_info=True
            )
            raise Exception(f"An unexpected error occurred during post creation: {e}")

    async def update_post(self, post_id: str, update_data: Dict[str, Any]) -> PostModel:
        """
        Updates an existing post record.

        Args:
            post_id (str): The ID of the post to update.
            update_data (Dict[str, Any]): Dictionary containing fields to update
                                          (e.g., {"title": "...", "status": PostStatus.PUBLISHED}).

        Returns:
            PostModel: The updated post object.

        Raises:
            Exception: Generic exception if not found or update fails.
        """
        logger.info(f"Attempting to update post with ID: {post_id}")
        if not update_data:
            logger.warning(f"Update post called for {post_id} with empty data.")
            # Maybe return current data or raise error? Let's raise for now.
            raise ValueError("No update data provided for post.")
        try:
            # Repository's update method handles setting updated_at
            updated_post = await self.db.post_repository.update(post_id, update_data)
            logger.info(f"Successfully updated post with ID: {post_id}")
            return updated_post
        except RepositoryNotFoundException:
            logger.warning(f"Post not found for update: ID={post_id}")
            raise Exception(f"Could not find post with id: {post_id} to update.")
        except (
            RepositoryUpdateException,
            RepositoryReadException,
        ) as e:  # Catch update or potential ID read errors
            logger.error(f"Failed to update post {post_id}: {e}", exc_info=True)
            raise Exception(f"Cannot update post ({post_id}) at the moment: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error during post update {post_id}: {e}", exc_info=True
            )
            raise Exception(f"An unexpected error occurred during post update: {e}")

    async def delete_post(self, post_id: str) -> PostModel:
        """
        Deletes a post record by its ID.

        Args:
            post_id (str): The ID of the post to delete.

        Returns:
            PostModel: The deleted post object.

        Raises:
            Exception: Generic exception if not found or deletion fails.
        """
        logger.info(f"Attempting to delete post with ID: {post_id}")
        try:
            deleted_post = await self.db.post_repository.delete(post_id)
            logger.info(f"Successfully deleted post with ID: {post_id}")
            return deleted_post
        except RepositoryNotFoundException:
            logger.warning(f"Post not found for deletion: ID={post_id}")
            raise Exception(f"Could not find post with id: {post_id} to delete.")
        except (
            RepositoryDeleteException,
            RepositoryReadException,
        ) as e:  # Catch delete or potential ID read errors
            logger.error(f"Failed to delete post {post_id}: {e}", exc_info=True)
            raise Exception(f"Cannot delete post ({post_id}) at the moment: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error during post deletion {post_id}: {e}", exc_info=True
            )
            raise Exception(f"An unexpected error occurred during post deletion: {e}")

    async def get_post(self, post_id: str) -> PostModel:
        """
        Retrieves a single post by its ID.

        Args:
            post_id (str): The ID of the post to retrieve.

        Returns:
            PostModel: The found post object.

        Raises:
            Exception: Generic exception if not found or retrieval fails.
        """
        logger.info(f"Attempting to retrieve post with ID: {post_id}")
        try:
            post = await self.db.post_repository.get(post_id)
            logger.info(f"Successfully retrieved post with ID: {post_id}")
            return post
        except RepositoryNotFoundException:
            logger.warning(f"Post not found: ID={post_id}")
            raise Exception(f"Could not find post with id: {post_id}")
        except RepositoryReadException as e:
            logger.error(f"Failed to read post {post_id}: {e}", exc_info=True)
            raise Exception(f"Cannot retrieve post ({post_id}) at the moment: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error during post retrieval {post_id}: {e}", exc_info=True
            )
            raise Exception(f"An unexpected error occurred during post retrieval: {e}")

    async def get_paginated_posts(
        self,
        page_size: int,
        page_no: int,
        status: Optional[PostStatus] = None,
        user_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: int = -1,
    ) -> PostsPaginatedResponse:
        """
        Retrieves a paginated list of posts, allowing filtering by status
        and potentially other criteria.

        Args:
            page_size (int): Number of items per page.
            page_no (int): The page number (1-based).
            status (Optional[PostStatus]): Filter by post status (e.g., PostStatus.APPROVED).
            user_id (Optional[str]): Filter by user ID.
            topic_id (Optional[str]): Filter by topic ID.
            sort_by (str): Field name to sort by. Defaults to 'created_at'.
            sort_order (int): Sort direction (-1 for desc, 1 for asc). Defaults to -1.


        Returns:
            PostsPaginatedResponse: An object containing the list of posts for the page
                                    and pagination metadata.

        Raises:
            Exception: Generic exception if retrieval fails.
        """
        logger.info(
            f"Fetching posts: Page={page_no}, Size={page_size}, Status={status}, User={user_id}, Topic={topic_id}"
        )
        if page_no < 1:
            page_no = 1
        if page_size < 1:
            page_size = 10  # Default/minimum size

        try:
            skip = (page_no - 1) * page_size
            query: Dict[str, Any] = {}  # Start with empty query

            if topic_id:
                query["topic_id"] = topic_id
            if status:
                # Ensure we use the enum's value (string) for the query
                query["status"] = status.value

            # Define sorting
            sort_order_tuple = [(sort_by, sort_order)]

            # Fetch total count matching the query (before pagination)
            total_items = await self.db.post_repository.get_total_count(query=query)

            # Fetch the paginated items
            posts = await self.db.post_repository.get_where(
                query=query, skip=skip, limit=page_size, sort=sort_order_tuple
            )

            total_pages = (
                total_items + page_size - 1
            ) // page_size  # Calculate total pages

            logger.info(f"Retrieved {len(posts)} posts (Total matching: {total_items})")

            # Construct and return the paginated response
            return PostsPaginatedResponse(
                items=posts,
                total_items=total_items,
                page_no=page_no,
                page_size=page_size,
                total_pages=total_pages,
            )
        except RepositoryReadException as e:
            logger.error(f"Failed to read paginated posts: {e}", exc_info=True)
            raise Exception(f"Cannot retrieve posts at the moment: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error retrieving paginated posts: {e}", exc_info=True
            )
            raise Exception(f"An unexpected error occurred while retrieving posts: {e}")

    async def delete_multiple_posts(self, post_ids: List[str]) -> int:
        """
        Deletes multiple posts based on a list of IDs.

        Args:
            post_ids (List[str]): List of post IDs (string representation of ObjectId) to delete.

        Returns:
            int: The number of posts successfully deleted.

        Raises:
            Exception: If the deletion process fails.
        """
        if not post_ids:
            logger.warning("delete_multiple_posts called with empty list.")
            return 0

        logger.info(f"Attempting to delete {len(post_ids)} posts.")
        try:
            # Note: Authorization check for ownership of all IDs is complex and omitted here.
            # Implement if necessary based on application requirements.
            deleted_count = await self.db.post_repository.delete_many(post_ids)
            logger.info(f"Service call resulted in {deleted_count} posts deleted.")
            return deleted_count
        except RepositoryDeleteException as e:
            logger.error(f"Failed to delete multiple posts: {e}", exc_info=True)
            raise Exception(f"Cannot delete posts at the moment: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error during multiple post deletion: {e}", exc_info=True
            )
            raise Exception(f"An unexpected error occurred during post deletion: {e}")

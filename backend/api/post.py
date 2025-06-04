import logging
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field


from lib.post import get_post_service, Post

from lib.models.post_models import (
    PostModel,
    PostStatus,
    PostsPaginatedResponse,
)
from lib.repositories.exceptions import (
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
    RepositoryDeleteException,
    RepositoryCreateException,
)
from lib.auth import get_auth


logger = logging.getLogger(__name__)

post_router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)


class PostCreateRequest(BaseModel):
    """Data needed to create a new post."""

    topic_id: str = Field(..., description="ID of the parent Topic")
    # Based on PostModel provided by user
    topic: str = Field(..., min_length=1, description="Post topic summary")
    context: str = Field(..., min_length=1, description="Post context")
    platform: str = Field(..., description="Target platform")
    content_type: str = Field(..., description="Type of content")
    content: str = Field(..., description="The main content generated")
    qna: List[str] = Field(
        default_factory=list, description="List of Q&A strings generated"
    )
    # Status could be optional, defaulting in service/model
    status: Optional[PostStatus] = PostStatus.PENDING_REVIEW


class PostUpdateRequest(BaseModel):
    """Fields that can be updated on a Post."""

    topic: Optional[str] = Field(None, min_length=1)
    context: Optional[str] = Field(None, min_length=1)
    platform: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    qna: Optional[List[str]] = None
    status: Optional[PostStatus] = None
    # Add other updatable fields from PostModel like title, body, tags, slug, publish_date if they existed


class DeleteMultiplePostsRequest(BaseModel):
    """List of Post IDs to delete."""

    post_ids: List[str] = Field(
        ..., description="A list of post IDs (strings) to be deleted."
    )


@post_router.get(
    "/",
    response_model=PostsPaginatedResponse,
    summary="Get Paginated Posts",
)
async def get_paginated_posts_endpoint(
    page: int = Query(1, ge=1, alias="pageNo", description="Page number (1-based)"),
    size: int = Query(
        10, ge=1, le=100, alias="pageSize", description="Items per page (max 100)"
    ),
    status: Optional[PostStatus] = Query(
        None, description="Filter by post status (e.g., 'approved', 'pending')"
    ),
    topic_id: Optional[str] = Query(None, description="Filter by the parent Topic ID"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: int = Query(-1, description="Sort order (-1 desc, 1 asc)"),
    user_id: str = Depends(get_auth),  # Get authenticated user ID
    post_service: Post = Depends(get_post_service),
):
    """
    Retrieves a paginated list of posts, with optional filtering by topic_id
    and status, and sorting. Requires authentication.
    """
    try:
        # Pass user_id to service if posts should be scoped by user
        # The current PostModel doesn't include user_id, but filtering might still be desired
        paginated_result = await post_service.get_paginated_posts(
            page_size=size,
            page_no=page,
            status=status,
            topic_id=topic_id,
            user_id=user_id,  # Pass user_id for potential filtering logic in service/repo
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return paginated_result
    except RepositoryReadException as e:
        logger.error(f"Read error fetching posts for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving posts: {e}",
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching posts for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        )


@post_router.post(
    "/",
    response_model=PostModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Post",
)
async def create_post_endpoint(
    post_create_data: PostCreateRequest,
    user_id: str = Depends(get_auth),  # Get authenticated user
    post_service: Post = Depends(get_post_service),
):
    """
    Creates a new Post associated with a specific Topic and the authenticated user.
    """
    try:
        # Create the Pydantic model instance from request data
        # Note: If PostModel requires user_id, it should be added here.
        # The provided PostModel doesn't have user_id. Assuming it's not stored on post.
        post_model = PostModel(
            **post_create_data.model_dump(),
            # user_id=user_id # Add if user_id needs to be stored on PostModel
        )
        # Set default status if not provided? Model handles this.
        created_post = await post_service.create_post(post_model)
        return created_post
    except RepositoryCreateException as e:
        logger.error(f"Create error for post by user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create post: {e}",
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error creating post for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@post_router.patch(
    "/{post_id}",
    response_model=PostModel,
    summary="Update a Post",
    responses={404: {"description": "Post not found"}},
)
async def update_post_endpoint(
    post_id: str,
    update_data: PostUpdateRequest,
    user_id: str = Depends(get_auth),  # Get authenticated user
    post_service: Post = Depends(get_post_service),
):
    """
    Updates specific fields of an existing post. Requires authentication.
    Authorization (checking if user owns post) is assumed handled if user_id was on model.
    """
    update_payload = update_data.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    try:
        # Optional: Authorization Check
        # post = await post_service.get_post(post_id) # Fetch first
        # if post.user_id != user_id: # If user_id were on PostModel
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

        updated_post = await post_service.update_post(post_id, update_payload)
        return updated_post
    except RepositoryNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id '{post_id}' not found.",
        )
    except (RepositoryUpdateException, RepositoryReadException) as e:
        logger.error(f"Update error for post {post_id} by user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update post: {e}",
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error updating post {post_id} by user {user_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@post_router.delete(
    "/",
    status_code=status.HTTP_200_OK,  # Or 204 No Content if not returning count
    summary="Delete Multiple Posts",
    response_model=Dict[str, int],  # Return the count of deleted items
    responses={400: {"description": "Invalid request (e.g., empty ID list)"}},
)
async def delete_multiple_posts_endpoint(
    delete_request: DeleteMultiplePostsRequest,
    user_id: str = Depends(get_auth),  # Get authenticated user
    post_service: Post = Depends(get_post_service),
):
    """
    Deletes one or more posts based on the provided list of IDs.
    Requires authentication. Authorization for each ID is complex and not checked here by default.
    """
    if not delete_request.post_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No post IDs provided for deletion.",
        )
    try:
        # Optional: Authorization check - verify user owns ALL post_ids before deleting.
        # This would typically involve fetching posts by IDs and checking ownership.
        # Skipping for simplicity, assuming user only provides IDs they should be able to delete.

        deleted_count = await post_service.delete_multiple_posts(
            delete_request.post_ids
        )
        logger.info(f"User {user_id} deleted {deleted_count} posts.")
        return {"deleted_count": deleted_count}
    except (
        RepositoryDeleteException,
        RepositoryReadException,
    ) as e:  # Catch delete or ID conversion errors
        logger.error(f"Delete error for multiple posts by user {user_id}: {e}")
        # Might be 400 Bad Request if ID format is wrong, 500 if DB fails
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete posts: {e}",
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error deleting multiple posts by user {user_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


# Optional: Add GET /posts/{post_id} endpoint if needed
@post_router.get(
    "/{post_id}",
    response_model=PostModel,
    summary="Get Single Post",
    responses={404: {"description": "Post not found"}},
)
async def get_post_endpoint(
    post_id: str,
    user_id: str = Depends(get_auth),  # Get authenticated user
    post_service: Post = Depends(get_post_service),
):
    """Retrieves a single post by its ID. Requires authentication."""
    try:
        post = await post_service.get_post(post_id)
        # Optional: Authorization Check if user_id was on model
        # if post.user_id != user_id:
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return post
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RepositoryReadException as e:
        logger.error(f"Read error for post {post_id} by user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve post: {e}",
        )  # Maybe 400 if ID invalid
    except Exception as e:
        logger.exception(
            f"Unexpected error getting post {post_id} by user {user_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

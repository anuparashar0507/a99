import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Body,
)
from lib.auth import get_auth
from lib.topic import Topic, get_topic_service
from lib.models.topic_models import (
    TopicCreateRequest,
    TopicModel,
    TopicUpdateRequest,
    TopicsPaginatedResponse,
)

# --- Logging Setup ---
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/topics",
    tags=["Topics"],
)


@router.post(
    "/",
    response_model=TopicModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new topic",
    description="Creates a new topic associated with the authenticated user. "
    "A corresponding Knowledge Base entry is also created.",
)
async def create_topic(
    topic_data: TopicCreateRequest = Body(...),
    user_id: str = Depends(get_auth),
    topic_service: Topic = Depends(get_topic_service),
):
    """
    Handles the creation of a new topic.

    - Verifies authentication using `get_auth`.
    - Retrieves the `user_id` associated with the authenticated email.
    - Constructs a `TopicModel` instance.
    - Calls the `topic_service` to create the topic (which includes KB creation).
    - Returns the created topic data.
    """
    logger.info(f"Received request to create topic from user: {user_id}")

    topic_model_instance = TopicModel(
        user_id=user_id,
        topic=topic_data.topic,
        context=topic_data.context if topic_data.context else "",
        kb_id="",
        desk_id="",
    )

    try:
        logger.debug(f"Calling topic_service.create for user_id: {user_id}")
        created_topic = await topic_service.create(topic_model_instance)
        logger.info(
            f"Successfully created topic with id: {created_topic.id} for user: {user_id}"
        )
        return created_topic
    except Exception as e:
        # Catch exceptions raised by the topic_service.create method
        logger.exception(
            f"Failed to create topic for user {user_id}: {e}", exc_info=True
        )
        # Provide a generic error message to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create topic: {str(e)}",  # Include original error message for context if safe
        )


@router.get(
    "/",
    response_model=TopicsPaginatedResponse,
    summary="Get topics for the authenticated user",
    description="Retrieves a paginated list of topics belonging to the authenticated user, "
    "ordered by creation date (descending).",
)
async def get_user_topics(
    user_id: str = Depends(get_auth),
    topic_service: Topic = Depends(get_topic_service),
    page: int = Query(
        1, ge=1, alias="page", description="Page number to retrieve (starts at 1)"
    ),
    size: int = Query(
        10,
        ge=1,
        le=100,
        alias="size",
        description="Number of topics per page (max 100)",
    ),
):
    """
    Handles retrieving a paginated list of topics for the logged-in user.

    - Verifies authentication.
    - Gets the user's ID.
    - Calls the `topic_service` to fetch the paginated topics.
    - Returns the list and pagination metadata.
    """
    logger.info(
        f"Received request to get topics for user: {user_id}, page: {page}, size: {size}"
    )

    try:
        logger.debug(f"Calling topic_service.get_user_topics for user_id: {user_id}")
        paginated_response = await topic_service.get_user_topics(
            user_id=user_id, page_no=page, page_size=size
        )
        logger.info(
            f"Found {paginated_response.total_items} total topics for user: {user_id}"
        )
        return paginated_response
    except Exception as e:
        logger.exception(f"Failed to get topics for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve topics: {str(e)}",
        )


@router.get(
    "/{topic_id}",
    response_model=TopicModel,
    summary="Get a specific topic by ID",
    description="Retrieves details of a specific topic by its ID. "
    "Ensures the topic belongs to the authenticated user.",
    responses={
        404: {"description": "Topic not found"},
        403: {"description": "User not authorized to access this topic"},
    },
)
async def get_topic_by_id(
    topic_id: str,
    user_id: str = Depends(get_auth),
    topic_service: Topic = Depends(get_topic_service),
):
    """
    Handles retrieving a single topic by its ID.

    - Verifies authentication.
    - Retrieves the topic using `topic_service`.
    - Verifies that the retrieved topic belongs to the authenticated user.
    - Returns the topic data.
    """
    logger.info(f"Received request to get topic_id: {topic_id} for user: {user_id}")

    try:
        logger.debug(f"Calling topic_service.get for topic_id: {topic_id}")
        topic = await topic_service.get(topic_id)  # Service should raise if not found

        # Authorization check: Does this topic belong to the authenticated user?
        if topic.user_id != user_id:
            logger.warning(
                f"Authorization failed: User ({user_id}) attempted to access topic {topic_id} owned by {topic.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this topic.",
            )

        logger.info(f"Successfully retrieved topic {topic_id} for user {user_id}")
        return topic
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message or "find a topic" in error_message:
            logger.warning(f"Topic not found with id {topic_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with id {topic_id} not found.",
            )
        else:
            logger.exception(
                f"Failed to get topic {topic_id} for user {user_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not retrieve topic: {str(e)}",
            )


@router.put(
    "/{topic_id}",
    response_model=TopicModel,
    summary="Update a topic",
    description="Updates specified fields of a topic (name, description). "
    "Ensures the topic belongs to the authenticated user.",
    responses={
        404: {"description": "Topic not found"},
        403: {"description": "User not authorized to update this topic"},
    },
)
async def update_topic(
    topic_id: str,
    update_data: TopicUpdateRequest = Body(...),
    user_id: str = Depends(get_auth),
    topic_service: Topic = Depends(get_topic_service),
):
    """
    Handles updating an existing topic.

    - Verifies authentication.
    - Fetches the topic to ensure it exists and belongs to the user.
    - Calls the `topic_service` to perform the update.
    - Returns the updated topic data.
    """
    logger.info(f"Received request to update topic_id: {topic_id} for user: {user_id}")

    # Convert Pydantic model to dict, excluding unset fields for partial updates
    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        logger.warning(
            f"Update request for topic {topic_id} received with no fields to update."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    try:
        # 1. Fetch the existing topic first for authorization check
        logger.debug(f"Fetching topic {topic_id} for update authorization check.")
        existing_topic = await topic_service.get(topic_id)  # Raises if not found

        # 2. Authorization check
        if existing_topic.user_id != user_id:
            logger.warning(
                f"Authorization failed: User ({user_id}) attempted to update topic {topic_id} owned by {existing_topic.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this topic.",
            )

        # 3. Perform the update
        logger.debug(
            f"Calling topic_service.update for topic_id: {topic_id} with data: {update_dict.keys()}"
        )
        updated_topic = await topic_service.update(topic_id, update_dict)
        logger.info(f"Successfully updated topic {topic_id} for user {user_id}")
        return updated_topic

    except HTTPException as http_exc:
        raise http_exc  # Re-raise 404, 403 etc.
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message or "find a topic" in error_message:
            logger.warning(f"Topic not found for update with id {topic_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with id {topic_id} not found.",
            )
        else:
            logger.exception(
                f"Failed to update topic {topic_id} for user {user_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not update topic: {str(e)}",
            )


@router.delete(
    "/{topic_id}",
    response_model=TopicModel,  # Return the deleted topic data as confirmation
    # Alternatively, use status_code=status.HTTP_204_NO_CONTENT and remove response_model
    summary="Delete a topic",
    description="Deletes a specific topic by its ID. "
    "Ensures the topic belongs to the authenticated user. Returns the deleted topic data.",
    responses={
        404: {"description": "Topic not found"},
        403: {"description": "User not authorized to delete this topic"},
        200: {"description": "Topic deleted successfully", "model": TopicModel},
    },
)
async def delete_topic(
    topic_id: str,
    user_id: str = Depends(get_auth),
    topic_service: Topic = Depends(get_topic_service),
):
    """
    Handles deleting a topic by its ID.

    - Verifies authentication.
    - Fetches the topic to ensure it exists and belongs to the user.
    - Calls the `topic_service` to perform the deletion.
    - Returns the data of the deleted topic.
    """
    logger.info(f"Received request to delete topic_id: {topic_id} for user: {user_id}")

    try:
        # 1. Fetch the existing topic first for authorization check
        logger.debug(f"Fetching topic {topic_id} for delete authorization check.")
        existing_topic = await topic_service.get(topic_id)  # Raises if not found

        # 2. Authorization check
        if existing_topic.user_id != user_id:
            logger.warning(
                f"Authorization failed: User {user_id} ({user_id}) attempted to delete topic {topic_id} owned by {existing_topic.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this topic.",
            )

        # 3. Perform the deletion
        logger.debug(f"Calling topic_service.delete for topic_id: {topic_id}")
        deleted_topic_data = await topic_service.delete(topic_id)
        logger.info(f"Successfully deleted topic {topic_id} for user {user_id}")
        return deleted_topic_data  # Return the deleted object's data

    except HTTPException as http_exc:
        raise http_exc  # Re-raise 404, 403 etc.
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message or "find a topic" in error_message:
            logger.warning(f"Topic not found for deletion with id {topic_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with id {topic_id} not found.",
            )
        else:
            logger.exception(
                f"Failed to delete topic {topic_id} for user {user_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not delete topic: {str(e)}",
            )

import logging
import asyncio
import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    BackgroundTasks,
)
from pydantic import BaseModel, Field

from lib.content_desk import ContentDesk, sse_client_queues
from lib.content import ContentGenerator

from lib.models.content_desk_models import (
    ContentDeskModel,
    GenerationStatus,
)
from lib.models.ideation_models import IdeationModel
from lib.models.outline_models import OutlineModel
from lib.models.content_models import ContentModel

from lib.repositories.exceptions import RepositoryNotFoundException

from lib.auth import get_auth
from lib.user import (
    UserService,
    get_user_service,
)

from lib.content_desk import (
    get_content_desk_service,
    get_content_service,
)
from lib.models.post_models import PostModel, PostStatus
from lib.post import Post, get_post_service
from lib.topic import Topic, get_topic_service
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

config_router = APIRouter(prefix="/config", tags=["Configuration"])


@config_router.get("/content-types", response_model=List[str])
async def get_available_content_types():
    return ["News Roundup", "Manufacturing Metrices", "Manufacturing Business Models"]


@config_router.get("/platforms", response_model=List[str])
async def get_available_platforms():
    return ["LinkedIn", "Twitter"]


# --- Router for /desk ---
desk_router = APIRouter(
    prefix="/desk",
    tags=["Content Desk"],
)


class CreateDeskRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="The main topic for the content.")
    context: str = Field(
        ..., min_length=10, description="Context, audience, goals for the content."
    )


class ContentDeskDetailResponse(ContentDeskModel):
    ideation: Optional[IdeationModel] = None
    outline: Optional[OutlineModel] = None
    content: Optional[ContentModel] = None


class FeedbackUpdateRequest(BaseModel):
    feedback: str = Field(..., description="User feedback for the specific phase.")


class ContentUpdateRequest(BaseModel):
    feedback: Optional[str] = None
    result: Optional[str] = None


class ContentDeskUpdateRequest(BaseModel):
    topic: Optional[str] = Field(None, min_length=3)
    context: Optional[str] = Field(None, min_length=10)
    platform: Optional[str] = Field(
        None, description="Update the target platform."
    )  # Optional update
    content_type: Optional[str] = Field(
        None, description="Update the content type."
    )  # Optional update


async def get_api_key_for_user(user_id: str, user_service: UserService) -> str:
    """Fetches user and returns API key, raising HTTPException if not found."""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        logger.error(f"User not found for ID {user_id} when retrieving API key.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user not found.",
        )
    # Ensure the user object actually has an api_key attribute
    if not hasattr(user, "api_key") or not user.api_key:
        logger.error(f"API key attribute not found or is empty for user ID {user_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key for authenticated user not found.",
        )
    return user.api_key


@desk_router.get(
    "/{desk_id}",
    response_model=ContentDeskDetailResponse,
    summary="Get Content Desk Details",
    responses={404: {"description": "Content Desk not found"}},
)
async def get_desk(
    desk_id: str,
    user_id: str = Depends(get_auth),
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
):
    """
    Retrieves the full details of a Content Desk, including sub-documents.
    Requires authentication, but access is not restricted by user ownership.
    """
    try:
        desk = await content_desk_service.get_desk_details(desk_id)

        content_res = await content_desk_service.get_content_for_desk(desk_id)

        response = ContentDeskDetailResponse(
            **desk.model_dump(),
            content=content_res if not isinstance(content_res, Exception) else None,
        )
        return response
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Error fetching desk details {desk_id} (requested by user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch desk details.",
        )


@desk_router.patch(
    "/{desk_id}/content",
    response_model=ContentModel,
    summary="Update Content Feedback or Result",
    responses={404: {"description": "Desk/Content not found"}},
)
async def update_content(
    desk_id: str,
    update_request: ContentUpdateRequest,
    user_id: str = Depends(get_auth),
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
    content_service: ContentGenerator = Depends(get_content_service),
):
    """Updates feedback or result for the Content record linked to the desk."""
    try:
        desk = await content_desk_service.get_desk_details(desk_id)
        if not desk.content_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content record not linked.",
            )

        update_payload = update_request.model_dump(exclude_unset=True)
        if not update_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided."
            )

        updated_content = await content_service.update_content(
            desk.content_id, update_payload
        )
        return updated_content
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Error updating content desk {desk_id} (user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content.",
        )


@desk_router.patch(
    "/{desk_id}",
    response_model=ContentDeskModel,
    summary="Update Content Desk Properties",
    responses={404: {"description": "Content Desk not found"}},
)
async def update_content_desk(
    desk_id: str,
    update_request: ContentDeskUpdateRequest,
    user_id: str = Depends(get_auth),  # Keep auth
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
):
    """Updates core properties of the Content Desk itself (name, topic, platform, etc.)."""
    try:
        # Fetch first to verify existence before update
        await content_desk_service.get_desk_details(desk_id)  # Raises 404 if not found
        # ** Authorization Check REMOVED **

        update_payload = update_request.model_dump(exclude_unset=True)
        if not update_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided."
            )

        # Update using the repository via the service's db handle
        updated_desk = await content_desk_service.db.content_desk_repository.update(
            desk_id, update_payload
        )
        return updated_desk
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Error updating content desk {desk_id} (user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content desk.",
        )


@desk_router.post(
    "/{desk_id}/run/content",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run Content Generation Phase (Background)",
    responses={404: {"description": "Desk not found"}},
)
async def trigger_run_content_generation(
    desk_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_auth),  # Auth
    user_service: UserService = Depends(get_user_service),  # Get user service
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
):
    """Triggers the final content generation process in the background."""
    try:
        await content_desk_service.get_desk_details(desk_id)  # Check desk exists
        api_key = await get_api_key_for_user(user_id, user_service)

        background_tasks.add_task(
            content_desk_service.run_content_generation,
            desk_id,
            user_id,
            api_key,
        )
        return {
            "message": "Content generation process accepted and started in background."
        }
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(
            f"Error triggering content generation desk {desk_id} (user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger content generation.",
        )


@desk_router.post(
    "/{desk_id}/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run All Phases (Background)",
    responses={404: {"description": "Desk not found"}},
)
async def trigger_run_generation(
    desk_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_auth),
    user_service: UserService = Depends(get_user_service),
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
):
    """Triggers the entire content generation process in the background."""
    try:
        await content_desk_service.get_desk_details(desk_id)  # Check desk exists
        api_key = await get_api_key_for_user(user_id, user_service)

        background_tasks.add_task(
            content_desk_service.run,
            desk_id,
            user_id,
            api_key,
        )
        return {
            "message": "Content generation process accepted and started in background."
        }
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(
            f"Error triggering content generation desk {desk_id} (user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger content generation.",
        )


@desk_router.get(
    "/{desk_id}/status",
    response_model=GenerationStatus,
    summary="Get Content Desk Status",
    responses={404: {"description": "Content Desk not found"}},
)
async def get_content_desk_status(
    desk_id: str,
    user_id: str = Depends(get_auth),  # Keep auth to identify caller
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
):
    """Retrieves the current generation status of a specific Content Desk."""
    try:
        # Fetch desk first to ensure it exists before getting status
        # Ownership check is removed. Any authenticated user can check status.
        await content_desk_service.get_desk_details(desk_id)  # Raises 404 if not found

        status_obj = await content_desk_service.get_status(desk_id)
        return status_obj
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Error retrieving status desk {desk_id} (user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve status.",
        )


sse_router = APIRouter(prefix="/sse", tags=["Status Update"])


@sse_router.get(
    "/{desk_id}/stream",
    summary="Stream Content Desk Status Updates (SSE)",
    responses={
        404: {"description": "Content Desk not found"},
        # 403: {"description": "Not authorized"}, # Add if needed
    },
    # Note: SSE response type isn't explicitly set here, it's handled by EventSourceResponse
)
async def stream_content_desk_status(
    desk_id: str,
    request: Request,  # Inject request to detect disconnection
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
):
    """
    Establishes a Server-Sent Events connection to stream status updates
    for a specific Content Desk.
    """
    logger.info(f"SSE connection requested for desk {desk_id} ")

    # Optional: Authorization check if needed - can user access this desk stream?
    try:
        # Verify desk exists before starting stream
        await content_desk_service.get_desk_details(desk_id)
        # Add any other authorization logic here if required
        # Example: check if user_id belongs to an org that owns desk_id
    except RepositoryNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Pre-stream check failed for desk {desk_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate status stream.",
        )

    async def event_generator():
        """Async generator function to yield SSE events."""
        queue = asyncio.Queue()
        # Check if another client is already listening (simple single-listener model)
        # WARNING: Prone to race conditions without locking in a real app.
        # For multiple listeners, use a list of queues or pub/sub.
        if desk_id in sse_client_queues:
            logger.warning(
                f"Another SSE client is already listening for desk {desk_id}. Closing new request."
            )
            # Send an error event and close? Or just close?
            # Yielding an error event:
            error_payload = {
                "error": "Resource Busy",
                "message": "Another listener is active.",
            }
            yield {"event": "error", "data": json.dumps(error_payload)}
            return  # Exit generator

        sse_client_queues[desk_id] = queue
        logger.info(
            f"SSE listener added for desk {desk_id}. Total listeners: {len(sse_client_queues)}"
        )
        try:
            # 1. Send the current status immediately on connection
            try:
                current_status = await content_desk_service.get_status(desk_id)
                status_payload = current_status.model_dump()
                yield {"event": "status_update", "data": json.dumps(status_payload)}
                logger.debug(f"SSE sent initial status for desk {desk_id}")
            except Exception as initial_err:
                logger.error(
                    f"SSE failed to send initial status for desk {desk_id}: {initial_err}"
                )
                # Send an error event?
                err_payload = {
                    "error": "InitialStatusError",
                    "message": str(initial_err),
                }
                yield {"event": "error", "data": json.dumps(err_payload)}
                # Continue listening or close? Let's continue listening for now.

            # 2. Loop, waiting for updates from the queue
            while True:
                # Check for client disconnect before waiting on queue
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected for desk {desk_id}.")
                    break

                try:
                    # Wait for a new status update (JSON string) from the queue
                    # Add a timeout to periodically check disconnect? Or rely on queue get?
                    # Let's add a small timeout to check disconnect more often.
                    new_status_json = await asyncio.wait_for(
                        queue.get(), timeout=30.0
                    )  # 30 sec timeout
                    yield {
                        "event": "status_update",
                        "data": new_status_json,  # Send the pre-formatted JSON string
                    }
                    queue.task_done()
                    logger.debug(f"SSE sent status update for desk {desk_id}")
                except asyncio.TimeoutError:
                    # No update received, just loop again to check disconnect
                    logger.debug(
                        f"SSE poll timeout for desk {desk_id}, checking connection..."
                    )
                    # Send a keep-alive comment (optional)
                    # yield ":" # SSE comment for keep-alive
                    continue
                except Exception as q_err:
                    logger.error(
                        f"SSE queue error for desk {desk_id}: {q_err}", exc_info=True
                    )
                    # Send an error event to the client?
                    err_payload = {"error": "QueueError", "message": str(q_err)}
                    try:
                        yield {"event": "error", "data": json.dumps(err_payload)}
                    except Exception:
                        pass  # Avoid crashing if yield fails
                    break  # Stop listening on queue error

        finally:
            # Cleanup: Remove queue when client disconnects or error occurs
            removed_queue = sse_client_queues.pop(desk_id, None)
            if removed_queue:
                logger.info(
                    f"SSE listener removed for desk {desk_id}. Total listeners: {len(sse_client_queues)}"
                )
            else:
                logger.warning(
                    f"SSE tried to remove listener for desk {desk_id}, but it was already gone."
                )

    # Return the streaming response
    return EventSourceResponse(event_generator())


@desk_router.post(
    "/topic/{topic_id}/content/add",
    response_model=PostModel,  # Return the newly created Post
    status_code=status.HTTP_201_CREATED,
    summary="Submit Generated Content for Review",
    responses={
        404: {"description": "Content Desk, Outline, or Content record not found"},
        409: {"description": "Content result is empty or missing"},
        403: {"description": "Not authorized (if auth checks were present)"},
    },
)
async def add_content_for_review_endpoint(
    topic_id: str,
    user_id: str = Depends(get_auth),
    content_desk_service: ContentDesk = Depends(get_content_desk_service),
    post_service: Post = Depends(get_post_service),
    topic_service: Topic = Depends(get_topic_service),
):
    """
    Takes the generated content associated with a Content Desk and creates
    a new Post record with 'pending_review' status.
    """
    logger.info(
        f"User {user_id} requested to add content for review from topic {topic_id}"
    )
    try:
        topic = await topic_service.get(topic_id)
        # 1. Fetch Desk and Sub-documents
        desk = await content_desk_service.get_desk_details(topic.desk_id)
        # Add authorization check here if necessary (e.g., based on org, etc.)

        # Fetch Content to get the final result
        content = await content_desk_service.get_content_for_desk(topic.desk_id)
        if not content or not content.result:
            logger.warning(
                f"Content result missing or empty for desk {topic.desk_id}. Cannot create post."
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Generated content is missing or empty for desk {topic.desk_id}. Run content generation first.",
            )

        # 2. Prepare data for the new PostModel
        # Using desk_id as topic_id for simplicity as discussed
        post_payload = PostModel(
            topic_id=topic_id,
            topic=desk.topic,
            context=desk.context,
            platform=desk.platform,
            content_type=desk.content_type,
            content=content.result,
            qna=(
                content.qna if hasattr(content, "qna") else []
            ),  # Get QnA from outline if available
            status=PostStatus.PENDING_REVIEW,
            feedback="",
        )

        # 3. Create the Post using the Post service
        created_post = await post_service.create_post(post_payload)
        logger.info(
            f"Created new post (ID: {created_post.id}) from content desk {topic.desk_id} for review."
        )

        return created_post

    except RepositoryNotFoundException as e:
        # Handle desk, outline, or content not found during fetches
        logger.warning(
            f"Not found error during content submission for desk {topic_id}: {e}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        raise e  # Re-raise specific HTTP exceptions (like 409, 403 if added)
    except Exception as e:
        logger.exception(
            f"Error creating post from content desk {topic_id} (user {user_id}): {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit content for review: {e}",
        )

import logging  # Import logging
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File,
    Form,  # Import Form for file upload endpoint
    status,  # Import status for consistency
)
from pydantic import BaseModel
from lib.auth import get_auth
from lib.knowledge_base import (
    KnowledgeBase,
    get_kb_service,
)  # Import KbFileType if needed by models
from lib.topic import Topic, get_topic_service
from lib.user import get_user_service
from lib.user.user import UserService  # Assuming direct import is okay

# --- End Assumed Imports ---

# Configure logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


# --- Pydantic Models (remain the same) ---
class UploadWebsitePayload(BaseModel):
    kb_id: str
    source: str
    urls: List[str]


class UploadTextPayload(BaseModel):
    kb_id: str
    text: str
    name: Optional[str] = None  # Added optional name field


class DeleteDocumentsRequest(BaseModel):
    kb_id: str
    sources: List[str]


# --- Endpoints with Logging ---


@router.post("/file", summary="Upload a File to Knowledge Base")
async def add_file(
    kb_id: str = Query(...),
    file: UploadFile = File(...),
    kb_service: KnowledgeBase = Depends(get_kb_service),
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_auth),
):
    """Handles file upload, parsing, and storage in KB, S3, and DB."""
    log_prefix = f"User {user_id} | KB {kb_id} | File '{file.filename}':"
    logger.info(f"{log_prefix} Received file upload request.")
    try:
        logger.debug(f"{log_prefix} Fetching user details...")
        authed_user = await user_service.get_user_by_id(user_id)
        if not authed_user or not authed_user.api_key:
            logger.error(f"{log_prefix} Failed to retrieve user details or API key.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details or API key not found.",
            )

        logger.debug(f"{log_prefix} Calling kb_service.upload_file...")
        uploaded_doc = await kb_service.upload_file(kb_id, file, authed_user.api_key)
        if uploaded_doc is None:
            logger.error(
                f"{log_prefix} kb_service.upload_file returned None, indicating failure."
            )
            # Raise a more specific error if upload_file indicates failure by returning None
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File processing or upload failed.",
            )

        logger.info(
            f"{log_prefix} File uploaded successfully. DB ID: {uploaded_doc.id}"
        )
        return uploaded_doc
    except (
        ValueError
    ) as ve:  # Catch specific errors like unsupported file type from service
        logger.warning(f"{log_prefix} Validation error: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException as http_exc:  # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception(
            f"{log_prefix} Unexpected error during file upload: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )
    finally:
        # Ensure the uploaded file resource is closed
        await file.close()
        logger.debug(f"{log_prefix} File stream closed.")


@router.post("/website", summary="Add Website Content to Knowledge Base")
async def add_website(
    payload: UploadWebsitePayload,
    kb_service: KnowledgeBase = Depends(get_kb_service),
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_auth),
):
    """Handles website parsing and storage in KB and DB."""
    kb_id = payload.kb_id
    source = payload.source
    urls = payload.urls
    log_prefix = f"User {user_id} | KB {kb_id} | Website '{source}':"
    logger.info(f"{log_prefix} Received website upload request for {len(urls)} URLs.")

    # Basic validation (Payload model handles type checks)
    if not kb_id or not source or not urls:
        logger.warning(f"{log_prefix} Request missing kb_id, source, or urls.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing kb_id, source, or urls",
        )

    try:
        logger.debug(f"{log_prefix} Fetching user details...")
        authed_user = await user_service.get_user_by_id(user_id)  # Corrected method
        if not authed_user or not authed_user.api_key:
            logger.error(f"{log_prefix} Failed to retrieve user details or API key.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details or API key not found.",
            )

        logger.debug(f"{log_prefix} Calling kb_service.upload_website_data...")
        uploaded_doc = await kb_service.upload_website_data(
            kb_id, source, urls, authed_user.api_key
        )
        if uploaded_doc is None:
            logger.error(f"{log_prefix} kb_service.upload_website_data returned None.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Website processing or upload failed.",
            )

        logger.info(
            f"{log_prefix} Website data uploaded successfully. DB ID: {uploaded_doc.id}"
        )
        return uploaded_doc
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(
            f"{log_prefix} Unexpected error during website upload: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.post("/text", summary="Add Raw Text to Knowledge Base")
async def add_text(
    payload: UploadTextPayload,
    kb_service: KnowledgeBase = Depends(get_kb_service),
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_auth),
):
    """Handles raw text parsing and storage in KB and DB."""
    kb_id = payload.kb_id
    text = payload.text
    # Use provided name or derive one from text if not given
    name = payload.name or f"Text Snippet: {text[:30]}..."
    log_prefix = f"User {user_id} | KB {kb_id} | Text '{name[:50]}...':"
    logger.info(f"{log_prefix} Received text upload request.")

    if not kb_id or not text:
        logger.warning(f"{log_prefix} Request missing kb_id or text.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing kb_id or text"
        )

    try:
        logger.debug(f"{log_prefix} Fetching user details...")
        authed_user = await user_service.get_user_by_id(user_id)  # Corrected method
        if not authed_user or not authed_user.api_key:
            logger.error(f"{log_prefix} Failed to retrieve user details or API key.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details or API key not found.",
            )

        logger.debug(f"{log_prefix} Calling kb_service.upload_text_data...")
        # Pass the derived/provided name to the service method
        uploaded_doc = await kb_service.upload_text_data(
            kb_id, name, text, authed_user.api_key
        )
        if uploaded_doc is None:
            logger.error(f"{log_prefix} kb_service.upload_text_data returned None.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Text processing or upload failed.",
            )

        logger.info(
            f"{log_prefix} Text data uploaded successfully. DB ID: {uploaded_doc.id}"
        )
        return uploaded_doc
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(
            f"{log_prefix} Unexpected error during text upload: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/documents/by-topic/{topic_id}", summary="Get KB Documents by Topic ID")
async def get_documents_by_topic(  # Renamed from get_documents_by_campaign for clarity
    topic_id: str,
    search_string: str = Query(
        "", description="Optional search string to filter documents by name"
    ),  # Use Query for better docs
    kb_service: KnowledgeBase = Depends(get_kb_service),
    topic_service: Topic = Depends(get_topic_service),
    # NOTE: No auth needed if KB docs aren't user-specific *after* getting kb_id? Add if needed.
):
    """Retrieves document metadata associated with a Topic's Knowledge Base."""
    log_prefix = f"Topic {topic_id}:"
    logger.info(
        f"{log_prefix} Received request to get KB documents, search: '{search_string}'."
    )
    try:
        logger.debug(f"{log_prefix} Fetching topic details...")
        topic = await topic_service.get(
            topic_id
        )  # Assumes topic_service.get raises if not found
        if not topic or not hasattr(topic, "kb_id") or not topic.kb_id:
            logger.warning(f"{log_prefix} Topic found but missing kb_id attribute.")
            # Raise 404 as the KB cannot be determined from this topic
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base ID not found for the given topic.",
            )

        kb_id = topic.kb_id
        logger.debug(f"{log_prefix} Found KB ID: {kb_id}. Fetching documents...")
        documents = await kb_service.get_kb_documents(kb_id, search_string)
        logger.info(
            f"{log_prefix} Retrieved {len(documents)} documents for KB {kb_id} matching search."
        )
        return documents
    except (
        HTTPException
    ) as http_exc:  # Catch specific 404 from topic_service.get if it raises that
        raise http_exc
    except Exception as e:  # Catch generic errors from topic_service.get or kb_service
        logger.exception(
            f"{log_prefix} Error retrieving KB documents: {e}", exc_info=True
        )
        # Check if it was likely a topic not found error vs internal error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with id '{topic_id}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.delete("/documents", summary="Delete Documents from Knowledge Base")
async def delete_documents(
    payload: DeleteDocumentsRequest,
    kb_service: KnowledgeBase = Depends(get_kb_service),
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_auth),
):
    """Deletes specified documents (by source name) from a Knowledge Base."""
    kb_id = payload.kb_id
    sources = payload.sources
    log_prefix = f"User {user_id} | KB {kb_id}:"
    logger.info(f"{log_prefix} Received request to delete sources: {sources}")

    if not kb_id or not sources or not isinstance(sources, list) or len(sources) == 0:
        logger.warning(f"{log_prefix} Request missing kb_id or valid sources list.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing kb_id or non-empty sources list",
        )

    try:
        logger.debug(f"{log_prefix} Fetching user details...")
        authed_user = await user_service.get_user_by_id(user_id)  # Corrected method
        if not authed_user or not authed_user.api_key:
            logger.error(f"{log_prefix} Failed to retrieve user details or API key.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details or API key not found.",
            )

        # Optional: Add authorization check here - does user_id own kb_id?

        logger.debug(
            f"{log_prefix} Calling kb_service.delete_kb_documents for {len(sources)} sources..."
        )
        # Service method returns the count of documents deleted from the DB
        deleted_count = await kb_service.delete_kb_documents(
            kb_id, sources, authed_user.api_key
        )
        logger.info(
            f"{log_prefix} Deletion process completed. DB records deleted: {deleted_count}"
        )
        # Return success message or count
        return {
            "message": f"Deletion request processed for {len(sources)} sources.",
            "db_records_deleted": deleted_count,
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(
            f"{log_prefix} Unexpected error during document deletion: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )

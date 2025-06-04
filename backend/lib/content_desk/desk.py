import logging
from typing import Optional, Dict
from nanoid import generate
from lib.repositories.repository_manager_protocol import RepositoryManagerProtocol
from lib.ideation import Ideation
from lib.outline import Outline
from lib.content import (
    ContentGenerator,
)
from lib.models.content_models import ContentModel
from lib.models.content_desk_models import (
    ContentDeskModel,
    GenerationStatus,
    GenerationPhase,
    StatusText,
)
from lib.models.ideation_models import IdeationModel
from lib.models.outline_models import OutlineModel
from lib.repositories.exceptions import (
    RepositoryNotFoundException,
)
import asyncio
import json


logger = logging.getLogger(__name__)
sse_client_queues: Dict[str, asyncio.Queue] = {}


class ContentDesk:
    """
    Orchestrates the content generation process through Ideation, Outline,
    and Content generation phases, managing the state via a ContentDeskModel.
    """

    def __init__(
        self,
        db: RepositoryManagerProtocol,
        content: ContentGenerator,
    ):
        """
        Initializes the ContentDesk orchestrator.

        Args:
            db: Provides access to repositories (content_desk_repository, etc.).
            ideation: Instance of the Ideation service.
            outline: Instance of the Outline service.
            content: Instance of the ContentGenerator service.
        """
        self.db = db
        self.content = content
        logger.info("ContentDesk service initialized.")

    async def _update_status(
        self,
        desk_id: str,
        phase: GenerationPhase,
        status_text: StatusText,
        message: str = "",
    ):
        """Internal helper to update desk status in DB and push to SSE queue."""
        log_prefix = f"Desk {desk_id} Status Update:"
        logger.debug(
            f"{log_prefix} Phase={phase.value}, Status={status_text.value}, Msg='{message[:100]}...'"
        )
        updated_status = None
        try:
            status = GenerationStatus(
                phase=phase, message=message, status_text=status_text
            )
            status_payload = status.model_dump()  # Use model_dump for pydantic v2

            # Update database first
            await self.db.content_desk_repository.update(
                desk_id, {"status": status_payload}
            )
            logger.debug(f"{log_prefix} Status updated successfully in DB.")
            updated_status = status  # Store the successful status object

        except Exception as e:
            # Log error but don't necessarily block the main flow if only status update fails
            logger.error(
                f"{log_prefix} Failed to update status in DB: {e}", exc_info=True
            )
            # Decide if we should still try to push an error status via SSE? Probably not if DB failed.
            return  # Exit if DB update failed

        # If DB update succeeded, try pushing to SSE queue
        if updated_status:
            queue = sse_client_queues.get(desk_id)
            if queue:
                try:
                    # Send the status object (or its JSON representation)
                    # Sending JSON string is safer for SSE data field
                    status_json = json.dumps(status_payload)
                    await queue.put(status_json)
                    logger.debug(f"{log_prefix} Pushed status update to SSE queue.")
                except Exception as q_err:
                    logger.error(
                        f"{log_prefix} Failed to push status update to SSE queue: {q_err}",
                        exc_info=True,
                    )
            # else:
            #     logger.debug(f"{log_prefix} No active SSE listener for this desk.")

    async def create_empty_desk(
        self,
        topic: str,
        context: str,
        platform: str,
        content_type: str,
    ) -> ContentDeskModel:
        """
        Creates the initial ContentDesk record and associated empty records
        for Ideation, Outline, and Content steps.

        Args:
            name (str): A user-defined name for this content desk/project.
            topic (str): The main topic.
            context (str): Context/Audience/Goal.
            platform (str): Target platform.
            content_type (str): Requested high-level content type.
            user_id (str): The user ID owning this desk.

        Returns:
            ContentDeskModel: The created content desk record.

        Raises:
            Exception: If any underlying creation step fails.
        """
        logger.info(f"Creating empty content desk: Topic='{topic}'")
        try:
            # Create placeholders in dependent services/repositories
            # NOTE: This pattern requires the sub-services' create methods
            # to handle potentially missing required fields (like topic, user_id)
            # if they are needed upon creation, which might be a design flaw to revisit.
            # Or, pass required IDs during creation here.
            # For now, following the user's existing pattern.

            # Assuming ContentGenerator now has create_content similar to others
            empty_content = await self.content.create_content()  # Needs user_id?
            # *** Modification End ***

            # Validate IDs were returned
            if not empty_content.id:
                raise Exception(
                    "Failed to create one or more required sub-records (ideation/outline/content)."
                )

            # Create the main ContentDesk record linking the sub-records
            initial_desk_data = ContentDeskModel(
                topic=topic,
                context=context,
                platform=platform,
                content_type=content_type,
                content_id=empty_content.id,
                status=GenerationStatus(  # Initial status
                    phase=GenerationPhase.NOT_RUNNING,
                    message="Desk created.",
                    status_text=StatusText.SUCCESS,
                ),
                # created_at/updated_at are set by the repository
            )

            desk = await self.db.content_desk_repository.create(initial_desk_data)
            logger.info(f"Content desk created successfully with ID: {desk.id}")
            return desk
        except Exception as e:
            logger.exception(f"Failed to create empty content desk: {e}", exc_info=True)
            # Propagate the error
            raise Exception(f"Failed to create content desk setup: {e}")

    async def get_desk_details(self, desk_id: str) -> ContentDeskModel:
        """Fetches the core ContentDeskModel data."""
        # Simple wrapper around repository get for clarity or future logic
        return await self.db.content_desk_repository.get(desk_id)  # Handles not found

    async def get_content_for_desk(self, desk_id: str) -> Optional[ContentModel]:
        """Fetches the ContentModel associated with a Content Desk."""
        try:
            desk = await self.get_desk_details(desk_id)
            if desk.content_id:
                return await self.content.get(desk.content_id)
            logger.warning(f"Desk {desk_id} does not have an associated content_id.")
            return None
        except RepositoryNotFoundException:
            logger.warning(f"Desk {desk_id} not found when trying to get content.")
            raise
        except Exception as e:
            logger.error(
                f"Error fetching content for desk {desk_id}: {e}", exc_info=True
            )
            return None

    async def run_content_generation(self, desk_id: str, user_id: str, api_key: str):
        """Runs the Content Generation phase for the specified Content Desk."""
        logger.info(f"Running Content Generation phase for desk ID: {desk_id}")
        desk: Optional[ContentDeskModel] = None
        try:
            desk = await self.db.content_desk_repository.get(desk_id)

            # Update status to PROCESSING
            await self._update_status(
                desk_id,
                GenerationPhase.CONTENT,
                StatusText.PROCESSING,
                "Starting content generation...",
            )

            # Run the content generation process using ContentGenerator.run
            # This assumes ContentGenerator.run updates its own record and returns None
            await self.content.run(
                content_id=desk.content_id,  # Pass the ID for the content record
                topic=desk.topic,
                context=desk.context,
                content_type=desk.content_type,
                platform=desk.platform,
                studio_api_key=api_key,  # Passed in
                user_id=user_id,  # Passed in
            )

            # Update status to SUCCESS for this phase
            await self._update_status(
                desk_id,
                GenerationPhase.CONTENT,
                StatusText.SUCCESS,
                "Content generation complete.",
            )
            logger.info(
                f"Content Generation phase completed successfully for desk ID: {desk_id}"
            )

        except Exception as e:
            logger.exception(
                f"Error during Content Generation phase for desk {desk_id}: {e}",
                exc_info=True,
            )
            # Update status to ERROR
            await self._update_status(
                desk_id,
                GenerationPhase.CONTENT,
                StatusText.ERROR,
                f"Content generation failed: {str(e)[:500]}",
            )
            raise Exception(
                f"Content Generation phase failed for desk {desk_id}: {e}"
            ) from e

    async def run(self, desk_id: str, user_id: str, api_key: str):
        """
        Runs the full content generation pipeline: Ideation -> Outline -> Content.
        Updates the Content Desk status throughout the process.
        """
        logger.info(f"Starting full generation run for desk ID: {desk_id}")
        try:
            # generate the apt content
            await self.run_content_generation(desk_id, user_id, api_key)
            await self._update_status(
                desk_id,
                GenerationPhase.CONTENT,
                StatusText.SUCCESS,
                "All generation steps completed successfully.",
            )
            logger.info(
                f"Full generation run completed successfully for desk ID: {desk_id}"
            )

        except Exception as e:
            logger.error(
                f"Full generation run failed for desk ID {desk_id} during one of the phases. See previous errors. Final exception: {e}",
                exc_info=False,
            )

    async def get_status(self, desk_id: str) -> GenerationStatus:
        """
        Retrieves the current status of a Content Desk.

        Args:
            desk_id (str): The ID of the Content Desk.

        Returns:
            GenerationStatus: The current status object.

        Raises:
            Exception: If the desk is not found or retrieval fails.
        """
        logger.debug(f"Fetching status for desk ID: {desk_id}")
        try:
            desk = await self.db.content_desk_repository.get(desk_id)
            logger.debug(f"Status for desk {desk_id}: {desk.status}")
            return desk.status
        except RepositoryNotFoundException as e:
            logger.warning(
                f"Attempted to get status for non-existent desk ID: {desk_id}"
            )
            raise Exception(f"Content Desk with ID '{desk_id}' not found.")
        except Exception as e:
            logger.exception(
                f"Error retrieving status for desk ID {desk_id}: {e}", exc_info=True
            )
            raise Exception(f"Failed to retrieve status for desk {desk_id}: {e}")

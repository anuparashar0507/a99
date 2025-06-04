import logging
from typing import Any, Dict
from nanoid import generate
from lib.agent_manager.manager import AgentManager
from lib.models.outline_models import OutlineModel
from lib.repositories.exceptions import (
    RepositoryCreateException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
)

from lib.repositories.repository_manager_protocol import (
    RepositoryManagerProtocol,
)


logger = logging.getLogger(__name__)


class Outline:
    """
    Service class for managing content Outlines.
    Handles CRUD operations via its repository and uses AgentManager
    to generate outline content based on prior ideation results.
    """

    def __init__(self, db: RepositoryManagerProtocol, agent_manager: AgentManager):
        """
        Initializes the Outline service.

        Args:
            db (RepositoryManagerProtocol): Provides access to data repositories (e.g., outline_repository).
            agent_manager (AgentManager): Service for interacting with AI agents.
        """
        self.db = db
        self.agent_manager = agent_manager
        logger.info("Outline service initialized.")

    async def create_outline(self) -> OutlineModel:
        """
        Creates a new, empty outline record in the database.
        Typically called at the start of the outline generation process.

        Returns:
            OutlineModel: The newly created outline object with empty feedback/result.

        Raises:
            Exception: A user-friendly error if outline creation fails.
        """
        logger.info("Attempting to create a new outline record.")
        try:
            # Create an initial OutlineModel instance with empty fields
            # Assumes the OutlineModel allows creation with only default/empty values initially.
            # If OutlineModel requires fields like user_id, topic_id, they need to be passed here.
            # Following the provided Ideation pattern:
            initial_outline = OutlineModel(
                feedback="", result=""
            )  # Ensure OutlineModel can be init'd like this
            outline = await self.db.outline_repository.create(initial_outline)
            logger.info(f"Successfully created outline record with ID: {outline.id}")
            return outline
        except RepositoryCreateException as e:
            logger.error(f"Failed to create outline record: {e}", exc_info=True)
            # Re-raise as a generic exception as per the pattern
            raise Exception(
                "Cannot create outline step at the moment, please try again!"
            )
        except Exception as e:
            # Catch potential validation errors if OutlineModel needs more fields
            logger.error(
                f"Unexpected error during outline creation: {e}", exc_info=True
            )
            raise Exception(
                f"An unexpected error occurred during outline creation: {e}"
            )

    async def update_outline(
        self, outline_id: str, update_data: Dict[str, Any]
    ) -> OutlineModel:
        """
        Updates an existing outline record.

        Args:
            outline_id (str): The ID of the outline record to update.
            update_data (Dict[str, Any]): Dictionary containing fields to update (e.g., {"feedback": "...", "result": "..."}).

        Returns:
            OutlineModel: The updated outline object.

        Raises:
            Exception: A user-friendly error if the update fails.
        """
        logger.info(f"Attempting to update outline record with ID: {outline_id}")
        try:
            # Prevent updating immutable fields if necessary (already handled in repo pattern)
            outline = await self.db.outline_repository.update(outline_id, update_data)
            logger.info(f"Successfully updated outline record with ID: {outline_id}")
            return outline
        except RepositoryNotFoundException as e:
            logger.warning(f"Outline record not found for update: ID={outline_id}")
            raise Exception(
                f"Could not find the outline module with id: {outline_id} to update."
            )
        except RepositoryUpdateException as e:
            logger.error(
                f"Failed to update outline record {outline_id}: {e}", exc_info=True
            )
            raise Exception(
                "Cannot update outline step at the moment, please try again!"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during outline update {outline_id}: {e}",
                exc_info=True,
            )
            raise Exception(f"An unexpected error occurred during outline update: {e}")

    async def get(self, outline_id: str) -> OutlineModel:
        """
        Retrieves a specific outline record by its ID.

        Args:
            outline_id (str): The ID of the outline to retrieve.

        Returns:
            OutlineModel: The found outline object.

        Raises:
            Exception: A user-friendly error if the outline is not found or retrieval fails.
        """
        logger.info(f"Attempting to retrieve outline record with ID: {outline_id}")
        try:
            outline = await self.db.outline_repository.get(outline_id)
            logger.info(f"Successfully retrieved outline record with ID: {outline_id}")
            return outline
        except RepositoryNotFoundException as e:
            logger.warning(f"Outline record not found: ID={outline_id}")
            raise Exception(f"Could not find the outline module with id: {outline_id}")
        except RepositoryReadException as e:
            logger.error(
                f"Failed to read outline record {outline_id}: {e}", exc_info=True
            )
            raise Exception(
                f"Cannot retrieve outline step ({outline_id}) at the moment, please try again!"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during outline retrieval {outline_id}: {e}",
                exc_info=True,
            )
            raise Exception(
                f"An unexpected error occurred during outline retrieval: {e}"
            )

    async def run(
        self,
        outline_id: str,
        ideation_result: str,  # Input from the previous ideation step
        topic: str,
        context: str,
        content_type: str,
        platform: str,
        user_id: str,
        studio_api_key: str,
    ):
        logger.info(f"Running outline generation for outline ID: {outline_id}")

        try:
            outline = await self.get(outline_id)
        except Exception as e:
            logger.error(
                f"Failed to get outline record {outline_id} before running generation: {e}"
            )
            raise Exception(
                f"Failed to retrieve outline record {outline_id} to start generation."
            )

        user_message = f"""TOPIC: {topic}
CONTEXT: {context}
PLATFORM TO GENERATE CONTENT FOR: {platform}
Content Type: {content_type}
Ideation Details:
```json
{ideation_result}
User Feedback on Outline (if any - refine based on this): {outline.feedback if outline.feedback else 'None provided.'}
"""

        session_id = f"outline-{user_id}-{generate(size=5)}"
        logger.debug(
            f"Constructed prompt for outline agent (Session: {session_id}). Calling agent manager..."
        )

        try:
            response = await self.agent_manager.generate_outline(
                api_key=studio_api_key,
                user_id=user_id,
                session_id=session_id,
                message=user_message,
            )
            if response is None:
                logger.warning(
                    f"Content agent returned None for outline generation (Session: {session_id})."
                )
                raise Exception("Agent failed to generate outline content.")
            else:
                logger.info(
                    f"Content agent successfully generated outline content for session: {session_id}"
                )

        except Exception as agent_err:
            logger.error(
                f"Error calling agent manager for outline generation (Session: {session_id}): {agent_err}",
                exc_info=True,
            )
            raise Exception(
                f"Failed to generate outline due to agent communication error: {agent_err}"
            )

        try:
            await self.update_outline(outline_id, {"result": response})
            logger.info(
                f"Successfully updated outline record {outline_id} with generated result."
            )
        except Exception as update_err:
            logger.error(
                f"Failed to update outline record {outline_id} with agent result: {update_err}",
                exc_info=True,
            )
            raise Exception(
                f"Agent generated outline, but failed to save result for {outline_id}: {update_err}"
            )

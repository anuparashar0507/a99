import logging
from typing import Any, Dict
from nanoid import generate
from lib.agent_manager.manager import AgentManager
from lib.knowledge_base import KnowledgeBase
from lib.models.content_models import ContentModel
from lib.repositories.exceptions import (
    RepositoryCreateException,
    RepositoryNotFoundException,
    RepositoryReadException,
)
from lib.repositories.repository_manager_protocol import RepositoryManagerProtocol

from lib.content.sources import (
    news_sourcer,
    manufacturing_metrices,
    manufacturing_business_models,
)

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    Generates final content section by section, based on initial inputs,
    ideation results, an outline, and research gathered through Q&A with AI agents.
    """

    def __init__(
        self,
        db: RepositoryManagerProtocol,
        agent_manager: AgentManager,
        kb: KnowledgeBase,
    ):
        """
        Initializes the ContentGenerator.

        Args:
            agent_manager: An instance of the AgentManager class.
            kb: An instance of the KnowledgeBase client for RAG.
        """
        self.db = db
        self.agent_manager = agent_manager
        self.kb = kb
        # content type to source gatherer mapping
        self.sourcers = {
            "News Roundup": news_sourcer,
            "Manufacturing Metrices": manufacturing_metrices,
            "Manufacturing Business Models": manufacturing_business_models,
        }
        logger.info("ContentGenerator service initialized.")

    async def get(self, content_id: str) -> ContentModel:
        try:
            content = await self.db.content_repository.get(content_id)
            return content
        except RepositoryNotFoundException as e:
            logger.error(f"Content with id {content_id} not found.: {e}")
            raise Exception("Content not found.")
        except RepositoryReadException as e:
            logger.error(
                f"Something went wrong when looking for content with ID: {content_id}: {e}"
            )
            raise Exception("Can not get content at them moment.")

    async def update_content(self, content_id, update_data: Dict[str, Any]):
        try:
            content = await self.db.content_repository.update(content_id, update_data)
            return content
        except RepositoryNotFoundException as e:
            logger.error(f"Content with id {content_id} not found.: {e}")
            raise Exception("Content not found.")
        except RepositoryReadException as e:
            logger.error(
                f"Something went wrong when updating content with ID: {content_id}: {e}"
            )
            raise Exception("Can not update content at them moment.")

    async def create_content(self) -> ContentModel:
        """
        Creates a new, empty content record in the database.
        Typically called at the start of the content generation process.
        """
        logger.info("Attempting to create a new outline record.")
        try:
            initial_content = ContentModel(
                feedback="", result=""
            )  # Ensure OutlineModel can be init'd like this
            content = await self.db.content_repository.create(initial_content)
            logger.info(f"Successfully created content record with ID: {content.id}")
            return content
        except RepositoryCreateException as e:
            logger.error(f"Failed to create content record: {e}", exc_info=True)
            raise Exception(
                "Cannot create content step at the moment, please try again!"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during content creation: {e}", exc_info=True
            )
            raise Exception(
                f"An unexpected error occurred during content creation: {e}"
            )

    async def run(
        self,
        content_id: str,
        topic: str,
        context: str,
        content_type: str,
        platform: str,
        studio_api_key: str,
        user_id: str,
    ) -> str:  # Returns the final generated content as a string
        logger.info(f"Starting content generation run for topic: '{topic}'")
        master_session_id = (
            f"content-run-{user_id}-{generate(size=8)}"  # ID for the whole run
        )
        try:
            content_data = await self.db.content_repository.get(content_id)
        except (RepositoryNotFoundException, RepositoryReadException) as e:
            logger.error(
                f"Error fetching content with content id: {content_id}. Reason: {e}"
            )
            content_data = ContentModel(feedback="", result="", qna=[])

        base_context = f"""TOPIC: {topic}
CONTEXT AROUND TOPIC: {context}
FEEDBACK: {content_data.feedback}
"""

        # Step 1: Run apt runner to get source content
        sourcer = None
        try:
            sourcer = self.sourcers[content_type]
            logger.info(
                f"Selected Content Sourcer: {sourcer} for content type: {content_type}"
            )
        except KeyError as e:
            logger.exception(f"Invalid Content Type: {content_type}. Error: {e}")
            raise e
        formatted_content = await sourcer.get(
            studio_api_key, user_id, base_context, content_type, platform
        )

        logger.info(f"Content generation run {master_session_id} complete.")
        content_data.result = formatted_content
        await self.db.content_repository.update(
            content_id, content_data.model_dump(exclude_unset=True)
        )
        return formatted_content

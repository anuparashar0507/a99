from lib.agent_manager import AgentManager
import logging
from nanoid import generate


logger = logging.getLogger(__name__)


class ManufacturingMetrices:
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.logger = logger

    async def get(
        self,
        studio_api_key: str,
        user_id: str,
        context: str,
        content_type: str,
        platform: str,
    ):
        logger.info(f"Getting manufacturing metrices with context: {context}")

        session_id = generate(size=5)
        source_data = await self.agent_manager.source_manufacturing_metrices(
            studio_api_key, user_id, session_id, context
        )
        format_message = f"""{context}
        THE TYPE OF CONTENT THIS IS: {content_type}
        THE CONTENT FORMAT SHOULD BE ACCORDING TO THE PLATFORM: {platform}

DRAFT CONTENT WITH DATA:
{source_data}
        """
        formatted_content = await self.agent_manager.format_source(
            studio_api_key, user_id, session_id, format_message
        )
        return formatted_content

from lib.agent_manager import AgentManager
import logging
from nanoid import generate

logger = logging.getLogger(__name__)


class NewsSourcer:
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.logger = logger

    async def _select_topic(
        self, studio_api_key: str, user_id: str, session_id: str, context: str
    ):
        """
        Selects a relevant topic based on the given context.
        """
        self.logger.info(f"[{session_id}] Selecting topic with context: {context}")
        selected_topic = await self.agent_manager.select_topic(
            api_key=studio_api_key,
            user_id=user_id,
            session_id=session_id,
            message=context,
        )
        self.logger.info(f"[{session_id}] Selected topic: {selected_topic}")
        return selected_topic

    async def _gather_news(
        self, studio_api_key: str, user_id: str, session_id: str, context: str
    ):
        """
        Gathers news articles and information related to the specified topic.
        """
        self.logger.info(f"[{session_id}] Gathering news for topic: {context}")
        raw_news_data = await self.agent_manager.source_news(
            api_key=studio_api_key,
            user_id=user_id,
            session_id=session_id,
            message=context,
        )
        self.logger.info(f"[{session_id}] Successfully gathered raw news data.")
        return raw_news_data

    async def _format_news(
        self,
        studio_api_key: str,
        user_id: str,
        session_id: str,
        context: str,
        platform: str,
    ):
        """
        Formats the gathered news data into the final desired output.
        """
        self.logger.info(f"[{session_id}] Formatting news data.")
        formatted_output = ""
        if platform == "LinkedIn":
            formatted_output = await self.agent_manager.format_news_linkedin(
                api_key=studio_api_key,
                user_id=user_id,
                session_id=session_id,
                message=context,
            )
        elif platform == "Twitter":
            formatted_output = await self.agent_manager.format_news_twitter(
                api_key=studio_api_key,
                user_id=user_id,
                session_id=session_id,
                message=context,
            )
        else:
            raise Exception("Formatter does not exist for platform: " + platform)

        self.logger.info(f"[{session_id}] News data formatted successfully.")
        return formatted_output

    async def get(
        self,
        studio_api_key: str,
        user_id: str,
        context: str,
        content_type: str,
        platform: str,
    ):
        """
        Orchestrates the process of selecting a topic, gathering news,
        and formatting it.
        """
        session_id = generate(size=5)
        self.logger.info(
            f"[{session_id}] Initiating news sourcing process with context: {context}"
        )

        try:
            # Step 1: Select Topic
            selected_topic = await self._select_topic(
                studio_api_key, user_id, session_id, context
            )

            if not selected_topic:
                self.logger.warning(
                    f"[{session_id}] Topic selection failed or returned empty. Aborting."
                )
                # Handle the case where no topic could be selected,
                # perhaps return an error or a default message.
                return {"error": "Could not determine a relevant topic."}

            # Step 2: Gather News
            context = f"""{context}\nThe topic you have to gater the news for: {selected_topic}"""

            raw_news_data = await self._gather_news(
                studio_api_key, user_id, session_id, context
            )

            if not raw_news_data:
                self.logger.warning(
                    f"[{session_id}] News gathering failed or returned empty for topic: {selected_topic}. Aborting."
                )
                # Handle the case where no news could be gathered.
                return {"error": f"Could not gather news for topic: {selected_topic}."}

            # Step 3: Format News
            context = f"""Context for the content: {context}\nInformation to include in the content:{raw_news_data}"""
            final_output = await self._format_news(
                studio_api_key, user_id, session_id, context, platform
            )

            self.logger.info(
                f"[{session_id}] News sourcing process completed successfully."
            )
            return final_output

        except Exception as e:
            self.logger.error(
                f"[{session_id}] An error occurred during the news sourcing process: {e}",
                exc_info=True,
            )
            raise e

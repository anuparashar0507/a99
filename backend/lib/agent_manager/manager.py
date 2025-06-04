import aiohttp
from typing import Optional
from lib.config import Settings


class AgentManager:
    def __init__(self, settings: Settings):
        self.base_url = settings.studio_base_url
        self.agents = {
            "ideation_agent": settings.ideation_agent_id,
            "outline_agent": settings.outline_agent_id,
            "data_sufficiency": settings.data_sufficiency_agent_id,
            "query_research": settings.query_research_agent_id,
            "query_generator": settings.query_generator_agent_id,
            "content_formatter": settings.content_formatter_agent_id,
            "serp_agent": settings.serp_agent_id,
            "content_agent": settings.content_agent_id,
            "news_sourcer": settings.news_sourcer_agent_id,
            "format_source": settings.format_source_agent_id,
            "manufacturing_metrices": settings.manufacturing_metrices_agent_id,
            "manufacturing_models": settings.manufacturing_models_agent_id,
            "news_topic_selector": settings.news_topic_selector_agent_id,
            "format_news_linkedin": settings.format_news_linkedin_agent_id,
            "format_news_twitter": settings.format_news_twitter_agent_id,
        }

    async def chat_with_agent(
        self, api_key: str, user_id: str, agent_key: str, session_id: str, message: str
    ) -> Optional[str]:
        agent_id = self.agents.get(agent_key)
        if not agent_id:
            raise ValueError(f"Agent id for '{agent_key}' is not configured.")

        url = f"{self.base_url}/v3/inference/chat/"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }
        data = {
            "user_id": user_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "message": message,
        }
        timeout = aiohttp.ClientTimeout(total=900)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if not response.ok:
                        error_body = await response.text()
                        print(f"Received non-OK status: {response.status}")
                        print(f"Response body: {error_body}")
                        response.raise_for_status()

                    json_response = await response.json()
                    return json_response.get("response")

        except aiohttp.ClientResponseError as http_err:
            print(
                f"HTTP error occurred after check: {http_err.status} {http_err.message}"
            )
            print(f"URL: {http_err.request_info.url}")
            print(f"Headers: {http_err.headers}")  # Access headers via the exception
            raise http_err

        except aiohttp.ClientConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            raise conn_err
        except (
            aiohttp.ClientError
        ) as client_err:  # Catches other client errors like timeouts
            print(f"AIOHTTP client error occurred: {client_err}")
            raise client_err
        except Exception as err:
            print(f"An unexpected error occurred: {err}")
            raise err

    async def generate_outline(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "outline_agent", session_id, message
        )

    async def check_data_sufficiency(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "data_sufficiency", session_id, message
        )

    async def research_about_query(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "query_research", session_id, message
        )

    async def generate_queries(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "query_generator", session_id, message
        )

    async def format_content(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "content_formatter", session_id, message
        )

    async def generate_content(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "content_agent", session_id, message
        )

    async def analyze_page(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "serp_agent", session_id, message
        )

    async def create_ideas(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "ideation_agent", session_id, message
        )

    async def source_news(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "news_sourcer", session_id, message
        )

    async def select_topic(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "news_topic_selector", session_id, message
        )

    async def source_manufacturing_metrices(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "manufacturing_metrices", session_id, message
        )

    async def source_manufacturing_business_models(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "manufacturing_models", session_id, message
        )

    async def format_news(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "format_news", session_id, message
        )

    async def format_news_linkedin(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "format_news_linkedin", session_id, message
        )

    async def format_news_twitter(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "format_news_twitter", session_id, message
        )

    async def format_source(
        self, api_key: str, user_id: str, session_id: str, message: str
    ) -> Optional[str]:
        return await self.chat_with_agent(
            api_key, user_id, "format_source", session_id, message
        )

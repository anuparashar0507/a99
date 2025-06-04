from typing import Any, Dict
from lib.agent_manager.manager import AgentManager

from lib.models.ideation_models import IdeationModel
from lib.repositories.exceptions import (
    RepositoryCreateException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
)
from lib.repositories.repository_manager_protocol import RepositoryManagerProtocol
from nanoid import generate


class Ideation:
    def __init__(self, db: RepositoryManagerProtocol, agent_manager: AgentManager):
        self.db = db
        self.agent_manager = agent_manager

    async def create_ideation(self) -> IdeationModel:
        try:
            ideation = await self.db.ideation_repository.create(
                IdeationModel(feedback="", result="")
            )
            return ideation
        except RepositoryCreateException as e:
            raise Exception(
                "Can not create ideation step at the moment, please try again!"
            )

    async def update_ideation(
        self, ideation_id: str, update_data: Dict[str, Any]
    ) -> IdeationModel:
        try:
            ideation = await self.db.ideation_repository.update(
                ideation_id, update_data
            )
            return ideation
        except RepositoryUpdateException as e:
            raise Exception(
                "Can not update ideation step at the moment, please try again!"
            )

    async def get(self, ideation_id: str) -> IdeationModel:
        try:
            ideation = await self.db.ideation_repository.get(ideation_id)
            return ideation
        except RepositoryNotFoundException as e:
            raise Exception(
                "Could not find the ideation module with id: " + ideation_id
            )
        except RepositoryReadException as e:
            raise Exception(
                "Can not update ideation step at the moment, please try again!"
            )

    async def run(
        self,
        ideation_id: str,
        topic: str,
        content_type: str,
        platform: str,
        user_id: str,
        studio_api_key: str,
    ):
        ideation = await self.get(ideation_id)

        user_message = f"Topic: {topic}\nContent Type: {content_type}\nPlatform to write content for: {platform}\n\nUser Feedback: {ideation.feedback}"
        session_id = generate(size=5)
        response = await self.agent_manager.create_ideas(
            studio_api_key, user_id, session_id, user_message
        )
        await self.update_ideation(ideation_id, {"result": response})

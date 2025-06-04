from lib.agent_manager import get_agent_manager
from lib.repositories import repository_manager
from .ideation import Ideation


def get_ideation_service():
    am = get_agent_manager()
    i = Ideation(repository_manager, am)
    return i

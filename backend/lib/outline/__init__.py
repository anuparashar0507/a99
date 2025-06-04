from lib.agent_manager import get_agent_manager
from lib.repositories import repository_manager
from .outline import Outline


def get_outline_service():
    am = get_agent_manager()
    o = Outline(repository_manager, am)
    return o

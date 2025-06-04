from .manager import AgentManager
from lib.config import settings


def get_agent_manager():
    am = AgentManager(settings)
    return am

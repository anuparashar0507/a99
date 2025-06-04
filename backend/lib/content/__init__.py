from lib.agent_manager import get_agent_manager
from lib.repositories import repository_manager
from lib.knowledge_base import get_kb_service
from .generation import ContentGenerator


def get_content_service():
    am = get_agent_manager()
    kb = get_kb_service()
    c = ContentGenerator(repository_manager, am, kb)
    return c

from lib.content_desk import get_content_desk_service
from .topic import Topic
from lib.knowledge_base import get_kb_service
from lib.repositories import repository_manager
from lib.user import get_user_service


def get_topic_service():
    user = get_user_service()
    kb = get_kb_service()
    desk = get_content_desk_service()
    t = Topic(repository_manager, kb, user, desk)
    return t

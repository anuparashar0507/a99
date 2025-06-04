from lib.content import get_content_service
from lib.repositories import repository_manager
from .desk import ContentDesk, sse_client_queues


def get_content_desk_service():
    c = get_content_service()
    desk = ContentDesk(repository_manager, c)
    return desk

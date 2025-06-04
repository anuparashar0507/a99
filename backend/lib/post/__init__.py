from lib.repositories import repository_manager
from .post import Post


def get_post_service():
    p = Post(repository_manager)
    return p

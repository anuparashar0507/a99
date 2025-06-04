from .user import UserService
from lib.repositories import repository_manager


def get_user_service():
    user = UserService(repository_manager)
    return user

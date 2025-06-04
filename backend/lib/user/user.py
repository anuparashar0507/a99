from typing import Dict, Any
from lib.repositories.repository_manager_protocol import RepositoryManagerProtocol
from lib.models.user_models import UserModel, UserUpdateModel
import datetime


class UserService:
    def __init__(self, db: RepositoryManagerProtocol):
        self.db = db

    async def get_user_by_email(self, user_id: str) -> UserModel:
        """
        Retrieve user details by email.
        """
        user = await self.db.user_repository.get_where({"user_id": user_id})
        return user

    async def get_user_by_id(self, user_id: str) -> UserModel:
        """
        Retrieve user details by user_id.
        """
        user = await self.db.user_repository.get_where({"user_id": user_id})
        return user

    async def upsert_user(self, user_data: Dict[str, Any]) -> UserModel:
        """
        Insert or update user details based on email.
        """
        user_model = UserModel(**user_data)
        user = await self.db.user_repository.upsert_user(user_model)
        return user

    async def update_user_auth(self, email: str, token: str, api_key: str) -> UserModel:
        """
        Update user's authentication details such as token and API key.
        """
        update_data = UserUpdateModel(
            token=token,
            api_key=api_key,
            last_login=datetime.datetime.now(datetime.timezone.utc),
        )
        user = await self.db.user_repository.update_user_where(
            {"email": email}, update_data
        )
        return user

    async def update_last_login(self, email: str) -> UserModel:
        """
        Update last login timestamp for the user.
        """
        update_data = UserUpdateModel(
            last_login=datetime.datetime.now(datetime.timezone.utc),
        )
        user = await self.db.user_repository.update_user_where(
            {"email": email}, update_data
        )
        return user

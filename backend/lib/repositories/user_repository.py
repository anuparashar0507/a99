from typing import Any, Dict
from pymongo import ReturnDocument
from bson import ObjectId
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryUpdateException,
    RepositoryDeleteException,
    RepositoryNotFoundException,
)
from lib.db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from lib.models.user_models import UserModel, UserUpdateModel


class UserRepository:
    """
    Repository class for user-related database operations.

    Functions:
      - get_where: Find one user based on a given filter.
      - update_user_where: Update a user based on a query.
      - delete_user: Delete a user based on user ID.
      - upsert_user: Insert or update a user based on email.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = self.db.get_collection("users")

    async def get_where(self, query: Dict[str, Any]) -> UserModel:
        """
        Find a single user that matches the given filter.
        """
        try:
            user = await self.collection.find_one(query)
            if not user:
                raise RepositoryNotFoundException(
                    "UserRepository", f"User with id '{query}' not found."
                )
            return UserModel(**user)
        except Exception as e:
            raise RepositoryReadException("UserRepository", e)

    async def update_user_where(
        self, query: Dict[str, Any], update_data: UserUpdateModel
    ) -> UserModel:
        """
        Update user fields where query matches.
        Returns the updated user.
        """
        try:
            update_data.updated_at = datetime.datetime.now(datetime.timezone.utc)
            updated_user = await self.collection.find_one_and_update(
                query,
                {"$set": update_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_user:
                raise RepositoryNotFoundException(
                    "UserRepository", f"Workflow with filter '{query}' not found."
                )
            return UserModel(**updated_user)
        except Exception as e:
            raise RepositoryUpdateException("UserRepository", e)

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user based on user ID.
        Returns True if deletion was successful.
        """
        try:
            delete_result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return delete_result.deleted_count > 0
        except Exception as e:
            raise RepositoryDeleteException("UserRepository", e)

    async def upsert_user(self, user_data: UserModel) -> UserModel:
        """
        Upsert a user (insert if not exists, update if exists) based on email.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            user_data.updated_at = time_now
            if not user_data.created_at:
                user_data.created_at = time_now

            updated_user = await self.collection.find_one_and_update(
                {"email": user_data.email},
                {"$set": user_data.model_dump(exclude_unset=True, by_alias=True)},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            return UserModel(**updated_user)
        except Exception as e:
            raise RepositoryCreateException("UserRepository", e)

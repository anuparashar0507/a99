from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from typing import Optional


class MongoDB:
    _instance: Optional["MongoDB"] = None
    _client: AsyncIOMotorClient  # Declare the client attribute
    db: AsyncIOMotorDatabase  # Declare the database attribute

    def __new__(cls, uri: str, db_name: str) -> "MongoDB":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._client = AsyncIOMotorClient(uri)
            instance.db = instance._client[db_name]
            cls._instance = instance
        return cls._instance

    async def connect(self) -> None:
        """
        Tests the connection to MongoDB by calling server_info().
        Raises an exception if the connection fails.
        """
        try:
            await self._client.server_info()
        except Exception as e:
            raise Exception("Could not connect to MongoDB") from e

    async def close(self) -> None:
        """close the db connection"""
        self._client.close()

    def get_db(self) -> AsyncIOMotorDatabase:
        """
        Returns a db instance
        """
        return self.db

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """
        Returns a Motor collection instance for the given collection name.
        """
        return self.db[name]

from typing import Protocol
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


class Persister(Protocol):
    async def connect(self) -> None:
        """Establish a connection to the database."""
        raise NotImplementedError()

    async def close(self) -> None:
        """close a connection to the database."""
        raise NotImplementedError()

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Retrieve a collection by name."""
        raise NotImplementedError()

    def get_db(self) -> AsyncIOMotorDatabase:
        """Retrieve a db instance."""
        raise NotImplementedError()

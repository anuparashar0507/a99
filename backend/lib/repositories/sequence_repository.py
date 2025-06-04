from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from .exceptions import (
    RepositoryCreateException,
    RepositoryDeleteException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.sequence_models import SequenceModel, SequenceUpdateModel

class SequenceRepository:
    """
    Repository for managing email sequences.
    Provides functions for CRUD operations on sequences and tracking data.
    """
    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("sequences")

    async def create(self, data: Dict[str, Any]) -> SequenceModel:
        """Create a new sequence."""
        try:
            sequence = SequenceModel(**data)
            time_now = datetime.now(timezone.utc)
            sequence.created_at = time_now
            sequence.updated_at = time_now
            
            insert_result = await self.collection.insert_one(sequence.model_dump())
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            
            if not inserted_data:
                raise RepositoryCreateException("Failed to create sequence")
            
            return SequenceModel(**inserted_data)
        except Exception as e:
            raise RepositoryCreateException(f"Failed to create sequence: {str(e)}")

    async def get(self, sequence_id: str) -> SequenceModel:
        """Get a sequence by ID."""
        try:
            sequence_data = await self.collection.find_one({"_id": ObjectId(sequence_id)})
            if not sequence_data:
                raise RepositoryNotFoundException(f"Sequence {sequence_id} not found")
            return SequenceModel(**sequence_data)
        except Exception as e:
            raise RepositoryReadException(f"Failed to read sequence: {str(e)}")

    async def get_by_campaign_prospect(
        self, campaign_id: str, prospect_id: str
    ) -> List[SequenceModel]:
        """Get sequences for a campaign-prospect pair."""
        try:
            cursor = self.collection.find({
                "campaign_id": campaign_id,
                "prospect_id": prospect_id
            })
            sequences = []
            async for doc in cursor:
                sequences.append(SequenceModel(**doc))
            return sequences
        except Exception as e:
            raise RepositoryReadException(f"Failed to read sequences: {str(e)}")

    async def update(
        self, sequence_id: str, update_data: SequenceUpdateModel
    ) -> SequenceModel:
        """Update a sequence."""
        try:
            time_now = datetime.now(timezone.utc)
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = time_now

            updated_data = await self.collection.find_one_and_update(
                {"_id": ObjectId(sequence_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if not updated_data:
                raise RepositoryNotFoundException(f"Sequence {sequence_id} not found")
            
            return SequenceModel(**updated_data)
        except Exception as e:
            raise RepositoryUpdateException(f"Failed to update sequence: {str(e)}")

    async def delete(self, sequence_id: str) -> bool:
        """Delete a sequence."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(sequence_id)})
            if result.deleted_count == 0:
                raise RepositoryNotFoundException(f"Sequence {sequence_id} not found")
            return True
        except Exception as e:
            raise RepositoryDeleteException(f"Failed to delete sequence: {str(e)}")

    async def get_pending_sequences(self, campaign_id: Optional[str] = None) -> List[SequenceModel]:
        """Get all pending sequences, optionally filtered by campaign."""
        try:
            query = {"status": "pending"}
            if campaign_id:
                query["campaign_id"] = campaign_id
                
            cursor = self.collection.find(query)
            sequences = []
            async for doc in cursor:
                sequences.append(SequenceModel(**doc))
            return sequences
        except Exception as e:
            raise RepositoryReadException(f"Failed to read pending sequences: {str(e)}")

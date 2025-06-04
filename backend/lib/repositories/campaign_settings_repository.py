from typing import Any, Dict, Optional
from pymongo import ReturnDocument
from bson import ObjectId
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryNotFoundException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.campaign_settings_models import (
    CampaignSettingsModel,
)


class CampaignSettingsRepository:
    """
    Repository class for persisting campaign settings in the database.

    Each campaign has a settings module, stored as a document in the database.

    Provides the following functions:
      - create: Create a campaign settings document.
      - get: Retrieve campaign settings by _id.
      - get_by_campaign_id: Retrieve campaign settings by campaign_id.
      - update: Update campaign settings by _id.
      - update_by_campaign_id: Update campaign settings by campaign_id.
      - delete: Delete campaign settings by _id.
      - delete_by_campaign_id: Delete campaign settings by campaign_id.
      - get_schedule: Fetch only the schedule field from campaign settings by campaign_id.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("campaign_settings")

    async def create(self, data: Dict[str, Any]) -> CampaignSettingsModel:
        """
        Create a new campaign settings entry.
        The data must contain all required fields of CampaignSettingsModel, including campaign_id.
        """
        try:
            campaign_settings = CampaignSettingsModel(**data)
            time_now = datetime.datetime.now(datetime.timezone.utc)
            campaign_settings.created_at = time_now
            campaign_settings.updated_at = time_now
            insert_result = await self.collection.insert_one(
                campaign_settings.model_dump()
            )
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if inserted_data is None:
                raise RepositoryCreateException(
                    "CampaignSettingsRepository",
                    Exception("Inserted document not found"),
                )
            return CampaignSettingsModel(**inserted_data)
        except Exception as e:
            raise RepositoryCreateException("CampaignSettingsRepository", e)

    def _convert_id(self, settings_id: str) -> ObjectId:
        """Convert string ID to ObjectId, handling both formats."""
        try:
            return ObjectId(settings_id)
        except Exception:
            # If settings_id is not a valid ObjectId, try to find by string ID
            return settings_id

    async def get(self, settings_id: str) -> CampaignSettingsModel:
        """
        Retrieve campaign settings by _id.
        """
        try:
            # Try both ObjectId and string formats
            settings_data = None
            for id_value in [self._convert_id(settings_id), settings_id]:
                settings_data = await self.collection.find_one(
                    {"_id": id_value}
                )
                if settings_data:
                    break

            if not settings_data:
                raise RepositoryNotFoundException(
                    "CampaignSettingsRepository",
                    f"Settings with id '{settings_id}' not found.",
                )
            return CampaignSettingsModel(**settings_data)
        except Exception as e:
            raise RepositoryReadException("CampaignSettingsRepository", e)

    async def update(
        self, settings_id: str, update_data: dict
    ) -> CampaignSettingsModel:
        """
        Update campaign settings identified by _id.
        Only fields provided in update_data will be updated.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data["updated_at"] = time_now
            
            # Try both ObjectId and string formats
            updated_settings = None
            for id_value in [self._convert_id(settings_id), settings_id]:
                updated_settings = await self.collection.find_one_and_update(
                    {"_id": id_value},
                    {"$set": update_data},
                    return_document=ReturnDocument.AFTER,
                )
                if updated_settings:
                    break

            if not updated_settings:
                raise RepositoryNotFoundException(
                    "CampaignSettingsRepository",
                    f"Settings with id '{settings_id}' not found.",
                )
            return CampaignSettingsModel(**updated_settings)
        except Exception as e:
            raise RepositoryUpdateException("CampaignSettingsRepository", e)

    async def delete(self, settings_id: str) -> CampaignSettingsModel:
        """
        Delete campaign settings by _id and return the deleted document.
        """
        try:
            # Try both ObjectId and string formats
            deleted_settings = None
            for id_value in [self._convert_id(settings_id), settings_id]:
                deleted_settings = await self.collection.find_one_and_delete(
                    {"_id": id_value}
                )
                if deleted_settings:
                    break

            if not deleted_settings:
                raise RepositoryNotFoundException(
                    "CampaignSettingsRepository",
                    f"Settings with id '{settings_id}' not found.",
                )
            return CampaignSettingsModel(**deleted_settings)
        except Exception as e:
            raise RepositoryDeleteException("CampaignSettingsRepository", e)

    async def get_schedule(self, settings_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve only the schedule field from campaign settings using campaign_id.
        Returns None if not found.
        """
        try:
            # Try both ObjectId and string formats
            settings_data = None
            for id_value in [self._convert_id(settings_id), settings_id]:
                settings_data = await self.collection.find_one(
                    {"_id": id_value}, {"schedule": 1, "_id": 0}
                )
                if settings_data:
                    break

            if not settings_data:
                raise RepositoryNotFoundException(
                    "CampaignSettingsRepository",
                    f"Schedule for settings id '{settings_id}' not found.",
                )
            return settings_data.get("schedule")
        except Exception as e:
            raise RepositoryReadException("CampaignSettingsRepository", e)

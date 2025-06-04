from typing import Any, Dict, List
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
from ..models.campaign_models import CampaignModel, CampaignUpdateModel


class CampaignRepository:
    """
    Repository for managing campaigns.

    Functions:
      - create: Add a new campaign.
      - get: Fetch a campaign by id.
      - update: Update a campaign by id.
      - delete: Delete a campaign by id.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("campaigns")

    async def create(self, data: Dict[str, Any]) -> CampaignModel:
        """
        Create a new campaign.
        """
        try:
            campaign = CampaignModel(**data)
            time_now = datetime.datetime.now(datetime.timezone.utc)
            campaign.created_at = time_now
            campaign.updated_at = time_now
            insert_result = await self.collection.insert_one(campaign.model_dump())
            inserted_data = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if not inserted_data:
                raise RepositoryCreateException(
                    "CampaignRepository", Exception("Inserted document not found")
                )
            return CampaignModel(**inserted_data)
        except Exception as e:
            raise RepositoryCreateException("CampaignRepository", e)

    async def get(self, campaign_id: str) -> CampaignModel:
        """
        Fetch a campaign by `campaign_id`.
        """
        try:
            campaign_data = await self.collection.find_one(
                {"_id": ObjectId(campaign_id)}
            )
            if not campaign_data:
                raise RepositoryNotFoundException(
                    "CampaignRepository", f"Campaign with id '{campaign_id}' not found."
                )
            return CampaignModel(**campaign_data)
        except Exception as e:
            raise RepositoryReadException("CampaignRepository", e)

    async def get_all_paginated(
        self, query: Dict, skip: int, limit: int
    ) -> List[CampaignModel]:
        """
        Fetch all campaigns with pagination
        """
        try:
            cursor = (
                self.collection.find(query)
                .sort("_id", 1)  # Sorting before execution
                .skip(skip)
                .limit(limit)
            )
            campaigns = await cursor.to_list(length=limit)
            all_campaigns = []
            for campaign in campaigns:
                all_campaigns.append(CampaignModel(**campaign))
            return all_campaigns
        except Exception as e:
            raise RepositoryReadException("CampaignRepository", e)

    async def update(
        self, campaign_id: str, update_data: CampaignUpdateModel
    ) -> CampaignModel:
        """
        Update an existing campaign by `campaign_id`.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            update_data.updated_at = time_now
            updated_campaign = await self.collection.find_one_and_update(
                {"_id": ObjectId(campaign_id)},
                {"$set": update_data.model_dump(exclude_unset=True)},
                return_document=ReturnDocument.AFTER,
            )
            if not updated_campaign:
                raise RepositoryNotFoundException(
                    "CampaignRepository", f"Campaign with id '{campaign_id}' not found."
                )
            return CampaignModel(**updated_campaign)
        except Exception as e:
            raise RepositoryUpdateException("CampaignRepository", e)

    async def delete(self, campaign_id: str) -> CampaignModel:
        """
        Delete a campaign by `campaign_id` and return the deleted document.
        """
        try:
            deleted_campaign = await self.collection.find_one_and_delete(
                {"_id": ObjectId(campaign_id)}
            )
            if not deleted_campaign:
                raise RepositoryNotFoundException(
                    "CampaignRepository", f"Campaign with id '{campaign_id}' not found."
                )
            return CampaignModel(**deleted_campaign)
        except Exception as e:
            raise RepositoryDeleteException("CampaignRepository", e)

    async def increment_prospect_count(
        self, campaign_id: str, count: int = 1
    ) -> CampaignModel:
        """
        Increment the total_prospects count for a campaign.

        Args:
            campaign_id: ID of the campaign
            count: Number to increment by (default: 1)

        Returns:
            Updated campaign model
        """
        try:
            updated_campaign = await self.collection.find_one_and_update(
                {"_id": ObjectId(campaign_id)},
                {
                    "$inc": {"total_prospects": count},
                    "$set": {
                        "updated_at": datetime.datetime.now(datetime.timezone.utc)
                    },
                },
                return_document=ReturnDocument.AFTER,
            )
            if not updated_campaign:
                raise RepositoryNotFoundException(
                    "CampaignRepository", f"Campaign with id '{campaign_id}' not found."
                )
            return CampaignModel(**updated_campaign)
        except Exception as e:
            raise RepositoryUpdateException("CampaignRepository", e)

    async def increment_mails_sent_count(
        self, campaign_id: str, count: int = 1
    ) -> CampaignModel:
        """
        Increment the total_mails_sent count for a campaign.

        Args:
            campaign_id: ID of the campaign
            count: Number to increment by (default: 1)

        Returns:
            Updated campaign model
        """
        try:
            updated_campaign = await self.collection.find_one_and_update(
                {"_id": ObjectId(campaign_id)},
                {
                    "$inc": {"total_mails_sent": count},
                    "$set": {
                        "updated_at": datetime.datetime.now(datetime.timezone.utc)
                    },
                },
                return_document=ReturnDocument.AFTER,
            )
            if not updated_campaign:
                raise RepositoryNotFoundException(
                    "CampaignRepository", f"Campaign with id '{campaign_id}' not found."
                )
            return CampaignModel(**updated_campaign)
        except Exception as e:
            raise RepositoryUpdateException("CampaignRepository", e)

    async def get_total_count(self, query: Dict[str, Any]) -> int:
        try:
            count = await self.collection.count_documents(query)
            return count
        except Exception as e:
            raise RepositoryReadException("CampaignRepository", e)

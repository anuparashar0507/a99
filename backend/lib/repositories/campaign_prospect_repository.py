from typing import Any, Dict, List
from pymongo import ReturnDocument
from bson import ObjectId
import datetime

from .exceptions import (
    RepositoryCreateException,
    RepositoryReadException,
    RepositoryUpdateException,
    RepositoryDeleteException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.prospect_models import CampaignProspectModel


class CampaignProspectsRepository:
    """
    Repository for handling CampaignProspects.

    Functions:
      - get_where: Fetch campaign prospects based on a query.
      - create: Add a new campaign prospect.
      - update_where: Update campaign prospects based on a query.
      - delete_where: Delete campaign prospects matching a query.
      - create_many: Bulk insert multiple campaign prospects.
    """

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("campaign_prospects")

    async def create(self, data: CampaignProspectModel) -> CampaignProspectModel:
        """
        Create a new campaign prospect.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            data.created_at = time_now
            data.updated_at = time_now
            insert_result = await self.collection.update_one(
                {"prospect_id": data.prospect_id},
                {"$set": data.model_dump(by_alias=True, exclude_unset=True)},
                upsert=True,
            )
            return data
        except Exception as e:
            raise RepositoryCreateException("CampaignProspectsRepository", e)

    async def get_where(self, query: Dict[str, Any]) -> List[CampaignProspectModel]:
        """
        Fetch campaign prospects based on a query.
        """
        try:
            prospects = await self.collection.find(query).to_list(length=None)
            return (
                [CampaignProspectModel(**prospect) for prospect in prospects]
                if prospects
                else []
            )
        except Exception as e:
            raise RepositoryReadException("CampaignProspectsRepository", e)

    async def update_where(self, query: Dict[str, Any], update_data: Dict) -> int:
        """
        Update campaign prospects based on a query.
        Returns the count of updated documents.
        """
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
            
            # Handle both model and dictionary inputs
            if hasattr(update_data, "model_dump"):
                update_dict = update_data.model_dump(exclude_unset=True)
            else:
                update_dict = update_data
                
            update_result = await self.collection.update_many(
                query, {"$set": update_dict}
            )
            return update_result.modified_count
        except Exception as e:
            raise RepositoryUpdateException("CampaignProspectsRepository", e)

    async def delete_where(self, query: Dict[str, Any]) -> int:
        """
        Delete campaign prospects based on a query.
        Returns the count of deleted documents.
        """
        try:
            delete_result = await self.collection.delete_many(query)
            return delete_result.deleted_count
        except Exception as e:
            raise RepositoryDeleteException("CampaignProspectsRepository", e)

    async def create_many(
        self, campaign_prospects: List[CampaignProspectModel]
    ) -> List[CampaignProspectModel]:
        """
        Bulk insert multiple campaign prospects.
        Returns a list of successfully inserted prospects.
        """
        try:
            time_now = datetime.datetime.now(datetime.timezone.utc)
            for prospect in campaign_prospects:
                prospect.created_at = time_now
                prospect.updated_at = time_now

            insert_result = await self.collection.insert_many(
                [
                    prospect.model_dump(by_alias=True, exclude_unset=True)
                    for prospect in campaign_prospects
                ]
            )
            inserted_ids = insert_result.inserted_ids
            inserted_prospects = await self.collection.find(
                {"_id": {"$in": inserted_ids}}
            ).to_list(length=None)
            return [
                CampaignProspectModel(**prospect) for prospect in inserted_prospects
            ]
        except Exception as e:
            raise RepositoryCreateException("CampaignProspectsRepository", e)

    async def get_all_paginated(
        self, query: Dict, skip: int, limit: int
    ) -> List[CampaignProspectModel]:
        """
        Fetch all prospects with pagination
        """
        try:
            prospects = (
                await self.collection.find(query)
                .sort("_id", 1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            all_prospects = []
            for prospect in prospects:
                all_prospects.append(CampaignProspectModel(**prospect))
            return all_prospects
        except Exception as e:
            raise RepositoryReadException("CampaignProspectsRepository", e)

    async def count_prospects(self, campaign_id: str) -> int:
        """
        Count the number of prospects in a given campaign.
        
        Args:
            campaign_id: The ID of the campaign to count prospects for.
            
        Returns:
            int: The total number of prospects in the campaign.
        """
        try:
            query = {"campaign_id": campaign_id}
            count = await self.collection.count_documents(query)
            return count
        except Exception as e:
            raise RepositoryReadException("CampaignProspectsRepository", e)

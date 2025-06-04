from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from .exceptions import (
    RepositoryCreateException,
    RepositoryDeleteException,
    RepositoryNotFoundException,
    RepositoryReadException,
    RepositoryUpdateException,
)
from ..db.db_protocol import AsyncIOMotorDatabase, AsyncIOMotorCollection, Persister
from ..models.campaign_mail_models import ActionStatus, CampaignMail, CampaignMailUpdate


class CampaignMailRepository:
    """Repository for managing campaign emails."""

    db: AsyncIOMotorDatabase
    collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.collection = db.get_collection("campaign_mails")

    async def create(self, data: Dict[str, Any]) -> CampaignMail:
        """Create a new campaign mail."""
        try:
            mail = CampaignMail(**data)
            result = await self.collection.insert_one(mail.model_dump())
            inserted = await self.collection.find_one({"_id": result.inserted_id})

            if not inserted:
                raise RepositoryCreateException("Failed to create campaign mail")

            return CampaignMail(**inserted)
        except Exception as e:
            raise RepositoryCreateException(f"Failed to create campaign mail: {str(e)}")

    async def get(self, mail_id: str) -> CampaignMail:
        """Get a campaign mail by ID."""
        try:
            mail_data = await self.collection.find_one({"_id": ObjectId(mail_id)})
            if not mail_data:
                raise RepositoryNotFoundException(f"Campaign mail {mail_id} not found")
            return CampaignMail(**mail_data)
        except Exception as e:
            raise RepositoryReadException(f"Failed to read campaign mail: {str(e)}")

    async def get_prospect_mails(
        self,
        prospect_id: str,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_order: int = -1,  # -1 for newest first, 1 for oldest first
    ) -> List[CampaignMail]:
        """Get all mails for a prospect with optional campaign and date filters."""
        try:
            # Build query
            query = {"prospect_id": prospect_id}
            if campaign_id:
                query["campaign_id"] = campaign_id
            if start_date or end_date:
                query["created_at"] = {}
                if start_date:
                    query["created_at"]["$gte"] = start_date
                if end_date:
                    query["created_at"]["$lte"] = end_date

            # Execute query with sorting
            cursor = self.collection.find(query).sort("created_at", sort_order)

            mails = []
            async for doc in cursor:
                mails.append(CampaignMail(**doc))
            return mails
        except Exception as e:
            raise RepositoryReadException(f"Failed to read prospect mails: {str(e)}")

    async def update(
        self, mail_id: str, update_data: CampaignMailUpdate
    ) -> CampaignMail:
        """Update a campaign mail."""
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            if not update_dict:
                return await self.get(mail_id)

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(mail_id)}, {"$set": update_dict}, return_document=True
            )

            if not result:
                raise RepositoryNotFoundException(f"Campaign mail {mail_id} not found")

            return CampaignMail(**result)
        except Exception as e:
            raise RepositoryUpdateException(f"Failed to update campaign mail: {str(e)}")

    async def get_by_tracking_id(self, tracking_id: str) -> CampaignMail:
        """Get a campaign mail by its tracking ID."""
        try:
            mail_data = await self.collection.find_one({"tracking_id": tracking_id})
            if not mail_data:
                raise RepositoryNotFoundException(
                    f"Campaign mail with tracking ID {tracking_id} not found"
                )
            return CampaignMail(**mail_data)
        except Exception as e:
            raise RepositoryReadException(f"Failed to read campaign mail: {str(e)}")

    async def increment_metric(
        self, mail_id: str, metric: str, amount: int = 1
    ) -> CampaignMail:
        """Increment a numeric metric."""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(mail_id)},
                {"$inc": {metric: amount}},
                return_document=True,
            )

            if not result:
                raise RepositoryNotFoundException(f"Campaign mail {mail_id} not found")

            return CampaignMail(**result)
        except Exception as e:
            raise RepositoryUpdateException(f"Failed to increment metric: {str(e)}")

    async def add_clicked_url(self, mail_id: str, url: str) -> CampaignMail:
        """Add a URL to the list of clicked URLs."""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(mail_id)},
                {"$addToSet": {"urls_clicked": url}},
                return_document=True,
            )

            if not result:
                raise RepositoryNotFoundException(f"Campaign mail {mail_id} not found")

            return CampaignMail(**result)
        except Exception as e:
            raise RepositoryUpdateException(f"Failed to add clicked URL: {str(e)}")

    async def get_campaign_mails(
        self,
        campaign_id: str,
        skip: int = 0,
        limit: int = 50,
        phase: Optional[str] = None,
    ) -> List[CampaignMail]:
        """Get all mails for a campaign with optional phase filter."""
        try:
            query = {"campaign_id": campaign_id}
            if phase:
                query["phase"] = phase

            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            mails = []
            async for doc in cursor:
                mails.append(CampaignMail(**doc))
            return mails
        except Exception as e:
            raise RepositoryReadException(f"Failed to read campaign mails: {str(e)}")

    async def count_campaign_mails(
        self, campaign_id: str, phase: Optional[str] = None
    ) -> int:
        """Count mails in a campaign with optional phase filter."""
        try:
            query = {"campaign_id": campaign_id}
            if phase:
                query["phase"] = phase
            return await self.collection.count_documents(query)
        except Exception as e:
            raise RepositoryReadException(f"Failed to count campaign mails: {str(e)}")

    async def get_filtered_campaign_mails(
        self, query: Dict[str, Any]
    ) -> List[CampaignMail]:
        """
        Get campaign mails with a flexible query filter.
        
        This method allows for more complex queries than the standard get_campaign_mails
        method, supporting filters like date ranges and multiple fields.
        
        Args:
            query: MongoDB query dictionary
            
        Returns:
            List of CampaignMail objects matching the query
        """
        try:
            cursor = self.collection.find(query).sort("created_at", -1)
            
            mails = []
            async for doc in cursor:
                mails.append(CampaignMail(**doc))
            return mails
        except Exception as e:
            raise RepositoryReadException(f"Failed to read filtered campaign mails: {str(e)}")

    async def update_action_status(self, action_id: str, status: ActionStatus):
        try:
            query = {"_id": ObjectId(action_id)}
            data = {"action_status": status.model_dump()}
            await self.collection.update_one(query, {"$set": data})
        except Exception as e:
            raise RepositoryUpdateException(
                "CampaignMailsRepository",
                Exception(f"failed to update action status with id {action_id} | {e}"),
            )

    # action_result_id == mail_id
    def get_status_tracker(self, action_result_id: str):
        async def track_status(update_dict: Dict[str, str]):
            update_data = CampaignMailUpdate(action_status=ActionStatus(**update_dict))
            await self.update(action_result_id, update_data)

        return track_status

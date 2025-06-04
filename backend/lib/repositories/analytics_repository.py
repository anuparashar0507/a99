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
from ..models.analytics_models import EmailEvent, EmailMetrics

class AnalyticsRepository:
    """Repository for managing email analytics data."""
    
    db: AsyncIOMotorDatabase
    events_collection: AsyncIOMotorCollection
    metrics_collection: AsyncIOMotorCollection

    def __init__(self, db: Persister):
        self.db = db.get_db()
        self.events_collection = db.get_collection("email_events")
        self.metrics_collection = db.get_collection("email_metrics")

    async def create_event(self, event_data: Dict[str, Any]) -> EmailEvent:
        """Create a new email event."""
        try:
            event = EmailEvent(**event_data)
            time_now = datetime.now(timezone.utc)
            event.created_at = time_now
            event.updated_at = time_now
            
            result = await self.events_collection.insert_one(event.model_dump())
            inserted = await self.events_collection.find_one({"_id": result.inserted_id})
            
            if not inserted:
                raise RepositoryCreateException("Failed to create email event")
            
            return EmailEvent(**inserted)
        except Exception as e:
            raise RepositoryCreateException(f"Failed to create email event: {str(e)}")

    async def get_campaign_events(self, campaign_id: str) -> List[EmailEvent]:
        """Get all events for a campaign."""
        try:
            cursor = self.events_collection.find({"campaign_id": campaign_id})
            events = []
            async for doc in cursor:
                events.append(EmailEvent(**doc))
            return events
        except Exception as e:
            raise RepositoryReadException(f"Failed to read campaign events: {str(e)}")

    async def get_prospect_events(
        self, campaign_id: str, prospect_id: str
    ) -> List[EmailEvent]:
        """Get all events for a prospect in a campaign."""
        try:
            cursor = self.events_collection.find({
                "campaign_id": campaign_id,
                "prospect_id": prospect_id
            })
            events = []
            async for doc in cursor:
                events.append(EmailEvent(**doc))
            return events
        except Exception as e:
            raise RepositoryReadException(f"Failed to read prospect events: {str(e)}")

    async def get_or_create_metrics(self, campaign_id: str) -> EmailMetrics:
        """Get or create metrics for a campaign."""
        try:
            metrics_data = await self.metrics_collection.find_one(
                {"campaign_id": campaign_id}
            )
            
            if not metrics_data:
                time_now = datetime.now(timezone.utc)
                metrics = EmailMetrics(
                    campaign_id=campaign_id,
                    created_at=time_now,
                    updated_at=time_now
                )
                await self.metrics_collection.insert_one(metrics.model_dump())
                return metrics
            
            return EmailMetrics(**metrics_data)
        except Exception as e:
            raise RepositoryReadException(f"Failed to get/create metrics: {str(e)}")

    async def update_metrics(self, campaign_id: str, update_data: Dict[str, Any]) -> EmailMetrics:
        """Update metrics for a campaign."""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)
            result = await self.metrics_collection.find_one_and_update(
                {"campaign_id": campaign_id},
                {"$set": update_data},
                return_document=True
            )
            
            if not result:
                raise RepositoryNotFoundException(f"Metrics for campaign {campaign_id} not found")
            
            return EmailMetrics(**result)
        except Exception as e:
            raise RepositoryUpdateException(f"Failed to update metrics: {str(e)}")

    async def increment_metrics(
        self, campaign_id: str, field: str, amount: int = 1
    ) -> EmailMetrics:
        """Increment a specific metric field."""
        try:
            result = await self.metrics_collection.find_one_and_update(
                {"campaign_id": campaign_id},
                {
                    "$inc": {field: amount},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                return_document=True
            )
            
            if not result:
                raise RepositoryNotFoundException(f"Metrics for campaign {campaign_id} not found")
            
            return EmailMetrics(**result)
        except Exception as e:
            raise RepositoryUpdateException(f"Failed to increment metrics: {str(e)}")

    async def get_events_by_type(
        self,
        campaign_id: str,
        event_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EmailEvent]:
        """Get events of a specific type within a date range."""
        try:
            cursor = self.events_collection.find({
                "campaign_id": campaign_id,
                "event_type": event_type,
                "event_timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("event_timestamp", 1)  # Sort by timestamp ascending
            
            events = []
            async for doc in cursor:
                events.append(EmailEvent(**doc))
            return events
        except Exception as e:
            raise RepositoryReadException(f"Failed to read events: {str(e)}")

    async def get_campaign_events_in_range(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EmailEvent]:
        """Get all campaign events within a date range."""
        try:
            cursor = self.events_collection.find({
                "campaign_id": campaign_id,
                "event_timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("event_timestamp", 1)
            
            events = []
            async for doc in cursor:
                events.append(EmailEvent(**doc))
            return events
        except Exception as e:
            raise RepositoryReadException(f"Failed to read campaign events: {str(e)}")

    async def get_unique_prospect_events(
        self,
        campaign_id: str,
        event_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """Get unique prospect IDs that performed a specific event type."""
        try:
            cursor = self.events_collection.aggregate([
                {
                    "$match": {
                        "campaign_id": campaign_id,
                        "event_type": event_type,
                        "event_timestamp": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$prospect_id"
                    }
                }
            ])
            
            prospect_ids = []
            async for doc in cursor:
                prospect_ids.append(doc["_id"])
            return prospect_ids
        except Exception as e:
            raise RepositoryReadException(f"Failed to read unique prospects: {str(e)}")

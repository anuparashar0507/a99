from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

class EmailEventType(str):
    SEND = "send"
    DELIVERY = "delivery"
    OPEN = "open"
    CLICK = "click"
    BOUNCE = "bounce"
    COMPLAINT = "complaint"

class EmailEvent(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    campaign_id: str
    prospect_id: str
    email_id: str
    event_type: str
    event_timestamp: datetime
    event_data: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

class EmailTrackingData(BaseModel):
    campaign_id: str
    prospect_id: str
    email_id: str
    tracking_id: str
    open_tracking_url: str
    click_tracking_urls: Dict[str, str]  # original_url -> tracking_url
    unsubscribe_url: str

class EmailMetrics(BaseModel):
    campaign_id: str
    total_sent: int = 0
    total_delivered: int = 0
    total_opens: int = 0
    total_clicks: int = 0
    total_bounces: int = 0
    total_complaints: int = 0
    unique_opens: int = 0
    unique_clicks: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

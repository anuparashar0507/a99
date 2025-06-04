from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from bson import ObjectId


class CampaignProspectModel(BaseModel):
    """
    Pydantic model for CampaignProspects.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    campaign_id: str
    prospect_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    engagement_score: int = Field(default=0, description="Prospect engagement score")
    engagement_status: str = Field(
        default="cold", description="Engagement status (cold, warm, hot)"
    )
    warm_timestamp: Optional[datetime] = Field(
        default=None, description="When prospect became warm"
    )
    hot_timestamp: Optional[datetime] = Field(
        default=None, description="When prospect became hot"
    )
    phase: str = "Not Started"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value


class ProspectModel(BaseModel):
    """
    Pydantic model for Prospects.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value


class ProspectScoreEventModel(BaseModel):
    """
    Pydantic model for prospect scoring events.
    """

    event_type: str
    timestamp: datetime
    points: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

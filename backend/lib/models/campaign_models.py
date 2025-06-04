from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from bson import ObjectId


class CampaignModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    workflow_id: str
    kb_id: str
    user_id: str
    settings_id: str
    name: Optional[str] = None
    is_active: Optional[bool] = None
    total_prospects: int = Field(
        default=0, description="Total number of prospects in this campaign"
    )
    total_mails_sent: int = Field(
        default=0, description="Total number of emails sent in this campaign"
    )

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


class CampaignPaginatedResponse(BaseModel):
    items: List[CampaignModel]
    total_items: int
    page_no: int
    page_size: int


class CampaignUpdateModel(BaseModel):
    updated_at: Optional[datetime] = None
    workflow_id: str
    kb_id: str
    settings_id: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

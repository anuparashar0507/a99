from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from datetime import datetime
from typing import Optional, Annotated, List, Dict, Any
from bson import ObjectId


class ObjectIdStrField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")
        return field_schema


# Type alias for ObjectId fields
ObjectIdStr = Annotated[str, BeforeValidator(ObjectIdStrField.validate)]


class ActionStatus(BaseModel):
    status_text: str
    error_text: str
    success_text: str


class CampaignMail(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id")
    mail_type: str  # 'mail' for assistant/agent, 'reply' for prospect
    from_email: str
    to_email: str
    subject: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    campaign_id: ObjectIdStr
    workflow_id: ObjectIdStr
    prospect_id: ObjectIdStr
    action_status: Optional[ActionStatus] = (
        None  # used to keep track of the ongoing status of the action
    )
    phase: Optional[str] = None  # Phase/tag of the campaign
    reference: Optional[str] = None  # Reference identifier for tracking purposes
    status: Optional[str] = None  # E.g., 'sent', 'opened', 'bounced'
    tracking_id: Optional[str] = None  # For analytics tracking

    # Analytics fields
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None  # First open
    clicked_at: Optional[datetime] = None  # First click
    replied_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None

    open_count: int = Field(default=0)
    click_count: int = Field(default=0)
    urls_clicked: List[str] = Field(default_factory=list)
    bounce_info: Optional[Dict] = None
    ip_addresses: List[str] = Field(default_factory=list)  # Track IP addresses of email opens

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class CampaignMailUpdate(BaseModel):
    status: Optional[str] = None
    tracking_id: Optional[str] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    open_count: Optional[int] = None
    click_count: Optional[int] = None
    urls_clicked: Optional[List[str]] = None
    bounce_info: Optional[Dict] = None
    ip_addresses: Optional[List[str]] = None
    action_status: Optional[ActionStatus] = (
        None  # used to keep track of the ongoing status of the action
    )
    to_email: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    phase: Optional[str] = None

    model_config = {"populate_by_name": True}


class CampaignMailResponse(BaseModel):
    id: str
    mail_type: str
    subject: str
    content: str
    created_at: datetime
    phase: Optional[str] = None
    status: Optional[str] = None
    analytics: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

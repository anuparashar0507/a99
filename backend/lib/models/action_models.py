from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class ActionType(Enum):
    EMAIL_SENDING = "EmailSending"
    MANUAL = "Manual"
    # LINKEDIN_OUTREACH = "LinkedinOutReach"
    # TWITTER_MESSAGE = "TwitterMessage"


# TODO: actions should also store a date range within which the action needs to be executed.
class ActionModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    workflow_id: str
    name: str
    description: str
    action_type: ActionType
    action_payload: Dict[str, Any]
    time_interval: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value


class ActionUpdateDataModel(BaseModel):
    name: str
    description: str
    action_type: Optional[ActionType] = None
    action_payload: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None
    time_interval: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from lib.models.action_models import ActionModel
from bson import ObjectId

"""
{status_text}: {success_text | error_text}
Eg: `Mail Delivered: The email was successfully delivered to dash@dash.com`
"""


class ActionRuntimeStatus(BaseModel):
    success_text: str
    error_text: str
    status_text: str


class WorkflowRuntimeModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    campaign_id: str
    prospect_id: str
    status: Optional[ActionRuntimeStatus] = None  # store the status of previous runtime
    current_action: ActionModel  # TODO: store action id instead of the model so that updates can be used
    last_action_run_time: Optional[datetime] = None

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


class WorkflowRuntimeUpdateDataModel(BaseModel):
    updated_at: Optional[datetime] = None
    status: Optional[ActionRuntimeStatus] = None  # store the status of previous runtime
    current_action: Optional[ActionModel] = None
    last_action_run_time: Optional[datetime] = None

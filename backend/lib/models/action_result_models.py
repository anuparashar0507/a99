from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId


class ActionResultModel(BaseModel):
    """
    Pydantic model representing an action result.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    action_id: str
    status: str  # e.g., "success", "failed", "pending"
    result_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ActionResultUpdateModel(BaseModel):
    """
    Pydantic model for updating an action result.
    """

    status: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

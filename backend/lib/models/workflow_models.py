from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class WorkflowModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    action_graph: List[
        str
    ]  # list of action ids in sequence of executon; for branching can use 2D list

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


class WorkflowUpdateDataModel(BaseModel):
    updated_at: Optional[datetime] = None
    action_graph: List[
        str
    ]  # list of action ids in sequence of executon; for branching can use 2D list

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

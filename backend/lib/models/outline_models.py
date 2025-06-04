from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId


class OutlineModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    feedback: str
    result: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True  # Needed if validator wasn't perfect
        json_encoders = {ObjectId: str}  # Ensure ObjectId is str in JSON output

    # This validator correctly handles converting ObjectId from DB to str for the model
    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        # Allow None or already string values to pass through
        return value

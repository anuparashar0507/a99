from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId


class IdeationModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    feedback: str
    result: str

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

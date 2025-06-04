from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId


class GenerationPhase(Enum):
    IDEATION = "ideation"
    OUTLINE = "outline"
    CONTENT = "content"
    NOT_RUNNING = "not_running"


class StatusText(Enum):
    ERROR = "error"
    PROCESSING = "processing"
    SUCCESS = "success"


class GenerationStatus(BaseModel):
    phase: GenerationPhase
    message: str
    status_text: StatusText

    model_config = ConfigDict(use_enum_values=True)


class ContentDeskModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    topic: str
    context: str
    platform: str
    content_type: str
    content_id: str
    status: GenerationStatus

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

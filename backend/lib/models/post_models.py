from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class PostStatus(Enum):
    PENDING_REVIEW = "pending"
    APPROVED = "approved"


class PostModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    topic: str
    context: str
    platform: str
    content_type: str
    content: str
    qna: List[str]
    topic_id: str
    feedback: str
    status: PostStatus

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


class PostsPaginatedResponse(BaseModel):
    """
    Response model for paginated lists of Posts.
    """

    items: List[PostModel]
    total_items: int
    page_no: int
    page_size: int
    total_pages: int

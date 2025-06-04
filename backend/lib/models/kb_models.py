from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class KbFileType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    TEXT = "text"
    WEBSITE = "website"


class KnowledgeBaseModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: str
    doc_type: KbFileType
    doc_link: Optional[str] = None
    kb_id: str

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

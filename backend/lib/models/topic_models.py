from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class TopicModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    topic: str
    context: str
    user_id: str
    desk_id: str

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


class TopicsPaginatedResponse(BaseModel):
    items: List[TopicModel]
    total_items: int
    page_no: int
    page_size: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TopicCreateRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=3,
        description="The main name or subject of the topic.",
        examples=["Quantum Computing Basics"],
    )
    context: Optional[str] = Field(
        None,
        description="An optional brief description of the topic.",
        examples=["Exploring qubits, superposition, and entanglement."],
    )

    class Config:
        # Example for OpenAPI documentation
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "context": "Covering basic concepts like supervised and unsupervised learning.",
            }
        }


class TopicUpdateRequest(BaseModel):
    topic: Optional[str] = Field(
        None,
        min_length=3,
        description="The updated name or subject of the topic.",
        examples=["Advanced Quantum Computing"],
    )
    context: Optional[str] = Field(
        None,
        description="The updated description of the topic.",
        examples=["Delving into quantum algorithms and error correction."],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Deep Learning Fundamentals",
                "description": "Focusing on neural networks and backpropagation.",
            }
        }

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from bson import ObjectId


class SigninInput(BaseModel):
    email: str
    password: str


class Me(BaseModel):
    token: str


class UserModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    email: str
    user_id: str
    organization_id: Optional[str] = None
    token: str
    api_key: str
    organization_ids: List[str]
    current_org_id: str
    last_login: Optional[datetime] = None

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


class UserUpdateModel(BaseModel):
    updated_at: Optional[datetime] = None
    email: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    token: Optional[str] = None
    api_key: Optional[str] = None
    organization_ids: Optional[List[str]] = None
    current_org_id: Optional[str] = None
    last_login: Optional[datetime] = None

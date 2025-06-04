from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import Field, BaseModel, field_validator
from bson import ObjectId


class SettingsFieldType(Enum):
    SINGLE_FIELD = "single_field"
    MULTIPLE_FIELD = "multiple_field"
    SELECTABLE = "selectable"
    BOOLEAN = "boolean"


class SettingsField(BaseModel):
    field_name: str
    field_type: SettingsFieldType
    field_value: Union[str, List, int, bool]
    field_options: Optional[List[str]] = None  # filled when field is a selectable

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True


class CampaignSettingsModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    general: Dict[str, SettingsField]
    materials: Dict[str, SettingsField]
    schedule: Dict[str, SettingsField]
    others: Dict[str, SettingsField]

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


class CampaignSettingsUpdateModel(BaseModel):
    updated_at: Optional[datetime] = None
    general: Optional[Dict[str, SettingsField]] = None
    materials: Optional[Dict[str, SettingsField]] = None
    schedule: Optional[Dict[str, SettingsField]] = None
    others: Optional[Dict[str, SettingsField]] = None

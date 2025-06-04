from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId


class ResearchCacheModel(BaseModel):
    """
    Pydantic model representing a cached research response.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    cache_key: str
    data: Dict[str, Any]
    expires_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


CACHE_EXPIRY_HOURS = 24  # Default cache expiration time

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class EmailContent(BaseModel):
    content: str

class SequenceInstructions(BaseModel):
    construct_instructions: str
    format_instructions: str
    sample_emails: str

class SequenceModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    campaign_id: str
    prospect_id: str
    email_content: str
    status: str = "pending"  # pending, sent, failed
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    from_email: str
    to_email: str
    subject: str
    tracking_data: Optional[Dict[str, Any]] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

class SequenceUpdateModel(BaseModel):
    status: Optional[str] = None
    tracking_data: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

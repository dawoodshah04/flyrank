from enum import Enum
from pydantic import BaseModel, Field

class Category(str, Enum):
    BILLING = "billing"
    BUG = "bug"
    FEATURE = "feature"
    OTHER = "other"

class Urgency(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class TriageReq(BaseModel):
    text:str = Field(min_length=1,max_length=2000)

class TriageRes(BaseModel):
    category:Category
    urgency:Urgency
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
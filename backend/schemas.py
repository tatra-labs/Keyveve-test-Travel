from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Destination schemas
class DestinationBase(BaseModel):
    name: str

class DestinationCreate(DestinationBase):
    pass

class Destination(DestinationBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Knowledge Base schemas
class KnowledgeBaseBase(BaseModel):
    content: str

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBase(KnowledgeBaseBase):
    id: int
    destination_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI Query schemas
class AIQuery(BaseModel):
    destination_id: int
    question: str

class AIResponse(BaseModel):
    answer: str
    weather_info: Optional[str] = None

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from config.schema import schema_config
from models.dynamic_model import get_dynamic_models

# Get the dynamically generated models
DynamicCreate, DynamicResponse = get_dynamic_models()

# Legacy models for backward compatibility (these will be replaced by dynamic models)
class RecordCreate(BaseModel):
    """Generic record creation model - dynamically generated from schema"""
    pass

class RecordResponse(BaseModel):
    """Generic record response model - dynamically generated from schema"""
    pass

# Export the dynamic models as the main models
RecordCreate = DynamicCreate
RecordResponse = DynamicResponse

def get_record_models():
    """Get the record models for the current schema"""
    return get_dynamic_models() 
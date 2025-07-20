from pydantic import BaseModel, Field, create_model, validator
from typing import Dict, Any, Type, Optional, List, Union
from datetime import datetime
import logging
import re
import uuid

from config.schema import schema_config, FieldType

logger = logging.getLogger(__name__)

class DynamicModelGenerator:
    """Generate Pydantic models dynamically based on schema configuration"""
    
    @staticmethod
    def _get_field_type(field_type: FieldType) -> Type:
        """Convert FieldType to Python type"""
        if field_type == FieldType.STRING:
            return str
        elif field_type == FieldType.INTEGER:
            return int
        elif field_type == FieldType.FLOAT:
            return float
        elif field_type == FieldType.BOOLEAN:
            return bool
        elif field_type == FieldType.DATETIME:
            return datetime
        elif field_type == FieldType.EMAIL:
            return str
        elif field_type == FieldType.URL:
            return str
        elif field_type == FieldType.PHONE:
            return str
        elif field_type == FieldType.UUID:
            return str
        elif field_type == FieldType.JSON:
            return Dict[str, Any]
        elif field_type == FieldType.ARRAY:
            return List[Any]
        elif field_type == FieldType.ENUM:
            return str
        else:
            return str
    
    @staticmethod
    def _create_field_definition(field_config) -> tuple:
        """Create field definition for Pydantic model"""
        field_type = DynamicModelGenerator._get_field_type(field_config.type)
        
        # Build field arguments
        field_args = {
            'description': field_config.description or f"{field_config.name} field"
        }
        
        # Set required/optional
        if not field_config.required:
            field_type = Optional[field_type]
        
        # Add validation constraints
        if field_config.type == FieldType.STRING:
            if field_config.min_length:
                field_args['min_length'] = field_config.min_length
            if field_config.max_length:
                field_args['max_length'] = field_config.max_length
            if field_config.pattern:
                field_args['regex'] = field_config.pattern
        elif field_config.type in [FieldType.INTEGER, FieldType.FLOAT]:
            if field_config.min_value is not None:
                field_args['ge'] = field_config.min_value
            if field_config.max_value is not None:
                field_args['le'] = field_config.max_value
        
        # Add default value
        if field_config.default is not None:
            field_args['default'] = field_config.default
        
        return (field_type, Field(**field_args))
    
    @classmethod
    def create_create_model(cls) -> Type[BaseModel]:
        """Create the Create model dynamically"""
        fields = {}
        validators = {}
        
        for field_config in schema_config.fields:
            if field_config.required:
                fields[field_config.name] = cls._create_field_definition(field_config)
            else:
                # For optional fields, use Optional type
                field_type, field_def = cls._create_field_definition(field_config)
                fields[field_config.name] = (Optional[field_type], field_def)
            
            # Add custom validators for special field types
            if field_config.type == FieldType.EMAIL:
                validators[f'validate_{field_config.name}'] = cls._create_email_validator(field_config.name)
            elif field_config.type == FieldType.URL:
                validators[f'validate_{field_config.name}'] = cls._create_url_validator(field_config.name)
            elif field_config.type == FieldType.PHONE:
                validators[f'validate_{field_config.name}'] = cls._create_phone_validator(field_config.name)
            elif field_config.type == FieldType.UUID:
                validators[f'validate_{field_config.name}'] = cls._create_uuid_validator(field_config.name)
            elif field_config.type == FieldType.ENUM and field_config.enum_values:
                validators[f'validate_{field_config.name}'] = cls._create_enum_validator(field_config.name, field_config.enum_values)
        
        model = create_model('DynamicCreate', **fields)
        
        # Add validators to the model
        for validator_name, validator_func in validators.items():
            setattr(model, validator_name, validator_func)
        
        return model
    
    @classmethod
    def create_update_model(cls) -> Type[BaseModel]:
        """Create the Update model dynamically (all fields optional except key)"""
        fields = {}
        
        for field_config in schema_config.fields:
            if field_config.name == schema_config.key_field:
                continue  # Skip key field in update
            
            # For update, make all fields optional strings initially
            # This avoids complex validation issues during updates
            fields[field_config.name] = (Optional[str], Field(required=False, description=field_config.description))
        
        model = create_model('DynamicUpdate', **fields)
        return model
    
    @classmethod
    def create_response_model(cls) -> Type[BaseModel]:
        """Create the Response model dynamically"""
        fields = {}
        validators = {}
        
        for field_config in schema_config.fields:
            # Make all fields optional in response to handle None values from DB
            field_type = DynamicModelGenerator._get_field_type(field_config.type)
            field_type = Optional[field_type]
            fields[field_config.name] = (field_type, Field(description=field_config.description))
            
            # Add custom validators for special field types
            if field_config.type == FieldType.EMAIL:
                validators[f'validate_{field_config.name}'] = cls._create_email_validator(field_config.name)
            elif field_config.type == FieldType.URL:
                validators[f'validate_{field_config.name}'] = cls._create_url_validator(field_config.name)
            elif field_config.type == FieldType.PHONE:
                validators[f'validate_{field_config.name}'] = cls._create_phone_validator(field_config.name)
            elif field_config.type == FieldType.UUID:
                validators[f'validate_{field_config.name}'] = cls._create_uuid_validator(field_config.name)
            elif field_config.type == FieldType.ENUM and field_config.enum_values:
                validators[f'validate_{field_config.name}'] = cls._create_enum_validator(field_config.name, field_config.enum_values)
        
        # Add timestamp fields
        fields['created_at'] = (datetime, Field(description="Creation timestamp"))
        fields['updated_at'] = (datetime, Field(description="Last update timestamp"))
        
        model = create_model('DynamicResponse', **fields)
        
        # Add validators to the model
        for validator_name, validator_func in validators.items():
            setattr(model, validator_name, validator_func)
        
        # Add JSON encoders for datetime
        class Config:
            json_encoders = {
                datetime: lambda v: v.isoformat()
            }
        
        model.Config = Config
        return model
    
    @staticmethod
    def _create_email_validator(field_name: str):
        """Create email validation function"""
        def validate_email(cls, v):
            if v is None:
                return v
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError(f'{field_name} must be a valid email address')
            return v
        return validator(field_name, allow_reuse=True)(validate_email)
    
    @staticmethod
    def _create_url_validator(field_name: str):
        """Create URL validation function"""
        def validate_url(cls, v):
            if v is None:
                return v
            url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
            if not re.match(url_pattern, v):
                raise ValueError(f'{field_name} must be a valid URL')
            return v
        return validator(field_name, allow_reuse=True)(validate_url)
    
    @staticmethod
    def _create_phone_validator(field_name: str):
        """Create phone validation function"""
        def validate_phone(cls, v):
            if v is None:
                return v
            phone_pattern = r'^\+?[\d\s\-\(\)]+$'
            if not re.match(phone_pattern, v):
                raise ValueError(f'{field_name} must be a valid phone number')
            return v
        return validator(field_name, allow_reuse=True)(validate_phone)
    
    @staticmethod
    def _create_uuid_validator(field_name: str):
        """Create UUID validation function"""
        def validate_uuid(cls, v):
            if v is None:
                return v
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError(f'{field_name} must be a valid UUID')
        return validator(field_name, allow_reuse=True)(validate_uuid)
    
    @staticmethod
    def _create_enum_validator(field_name: str, enum_values: List[str]):
        """Create enum validation function"""
        def validate_enum(cls, v):
            if v is None:
                return v
            if v not in enum_values:
                raise ValueError(f'{field_name} must be one of: {", ".join(enum_values)}')
            return v
        return validator(field_name, allow_reuse=True)(validate_enum)

# Generate models
DynamicCreate = DynamicModelGenerator.create_create_model()
DynamicUpdate = DynamicModelGenerator.create_update_model()
DynamicResponse = DynamicModelGenerator.create_response_model()

def get_dynamic_models():
    """Get the dynamically generated models"""
    return DynamicCreate, DynamicUpdate, DynamicResponse 
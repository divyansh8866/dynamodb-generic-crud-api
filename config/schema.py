import os
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FieldType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    UUID = "uuid"
    JSON = "json"
    ARRAY = "array"
    ENUM = "enum"

@dataclass
class FieldConfig:
    """Configuration for a single field"""
    name: str
    type: FieldType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    default: Optional[Any] = None
    unique: bool = False
    index: bool = False
    enum_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    format: Optional[str] = None

class SchemaConfig:
    """Dynamic schema configuration for any DynamoDB table"""
    
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'default_table')
        self.key_field = os.getenv('KEY_FIELD', 'item_id')
        self.sort_key_field = os.getenv('SORT_KEY_FIELD', None)  # Optional sort key
        self.fields = self._load_field_config()
        self._validate_schema()
    
    def _load_field_config(self) -> List[FieldConfig]:
        """Load field configuration from multiple sources with priority order"""
        
        # Priority 1: JSON file
        schema_file = os.getenv('SCHEMA_FILE', 'schema.json')
        if os.path.exists(schema_file):
            return self._load_from_json_file(schema_file)
        
        # Priority 2: Environment variable with JSON
        schema_json = os.getenv('SCHEMA_JSON', '')
        if schema_json:
            return self._load_from_json_string(schema_json)
        
        # Priority 3: Environment variable with simple format
        fields_config = os.getenv('TABLE_FIELDS', '')
        if fields_config:
            return self._load_from_simple_format(fields_config)
        
        # Priority 4: Default schema
        return self._get_default_schema()
    
    def _load_from_json_file(self, file_path: str) -> List[FieldConfig]:
        """Load schema from JSON file"""
        try:
            with open(file_path, 'r') as f:
                schema_data = json.load(f)
            return self._parse_json_schema(schema_data)
        except Exception as e:
            logger.error(f"Error loading schema from file {file_path}: {str(e)}")
            return self._get_default_schema()
    
    def _load_from_json_string(self, json_string: str) -> List[FieldConfig]:
        """Load schema from JSON string"""
        try:
            schema_data = json.loads(json_string)
            return self._parse_json_schema(schema_data)
        except Exception as e:
            logger.error(f"Error loading schema from JSON string: {str(e)}")
            return self._get_default_schema()
    
    def _parse_json_schema(self, schema_data: Dict) -> List[FieldConfig]:
        """Parse JSON schema format"""
        fields = []
        
        # Handle both array and object formats
        if isinstance(schema_data, list):
            fields_data = schema_data
        elif isinstance(schema_data, dict):
            fields_data = schema_data.get('fields', [])
            self.table_name = schema_data.get('table_name', self.table_name)
            self.key_field = schema_data.get('key_field', self.key_field)
            self.sort_key_field = schema_data.get('sort_key_field', self.sort_key_field)
        else:
            raise ValueError("Invalid schema format")
        
        for field_data in fields_data:
            if isinstance(field_data, dict):
                field = self._create_field_from_dict(field_data)
                fields.append(field)
            else:
                logger.warning(f"Skipping invalid field data: {field_data}")
        
        return fields
    
    def _create_field_from_dict(self, field_data: Dict) -> FieldConfig:
        """Create FieldConfig from dictionary"""
        name = field_data.get('name')
        if not name:
            raise ValueError("Field name is required")
        
        field_type = FieldType(field_data.get('type', 'string'))
        
        # Handle enum type
        if field_type == FieldType.ENUM:
            enum_values = field_data.get('enum_values', [])
            if not enum_values:
                raise ValueError("enum_values required for enum type")
        
        return FieldConfig(
            name=name,
            type=field_type,
            required=field_data.get('required', True),
            min_length=field_data.get('min_length'),
            max_length=field_data.get('max_length'),
            min_value=field_data.get('min_value'),
            max_value=field_data.get('max_value'),
            description=field_data.get('description', ''),
            default=field_data.get('default'),
            unique=field_data.get('unique', False),
            index=field_data.get('index', False),
            enum_values=field_data.get('enum_values'),
            pattern=field_data.get('pattern'),
            format=field_data.get('format')
        )
    
    def _load_from_simple_format(self, fields_config: str) -> List[FieldConfig]:
        """Load fields from simple colon-separated format"""
        fields = []
        
        # Format: "field1:type:required:min:max:desc,field2:type:required:min:max:desc"
        field_definitions = fields_config.split(',')
        
        for field_def in field_definitions:
            parts = field_def.strip().split(':')
            if len(parts) >= 2:
                field_name = parts[0]
                field_type = FieldType(parts[1])
                required = parts[2].lower() == 'true' if len(parts) > 2 else True
                
                min_val = None
                max_val = None
                description = ""
                
                if len(parts) > 3 and parts[3]:
                    min_val = int(parts[3]) if field_type in [FieldType.INTEGER, FieldType.FLOAT] else int(parts[3])
                if len(parts) > 4 and parts[4]:
                    max_val = int(parts[4]) if field_type in [FieldType.INTEGER, FieldType.FLOAT] else int(parts[4])
                if len(parts) > 5:
                    description = parts[5]
                
                fields.append(FieldConfig(
                    name=field_name,
                    type=field_type,
                    required=required,
                    min_length=min_val if field_type == FieldType.STRING else None,
                    max_length=max_val if field_type == FieldType.STRING else None,
                    min_value=min_val if field_type in [FieldType.INTEGER, FieldType.FLOAT] else None,
                    max_value=max_val if field_type in [FieldType.INTEGER, FieldType.FLOAT] else None,
                    description=description
                ))
        
        return fields
    
    def _get_default_schema(self) -> List[FieldConfig]:
        """Get default schema if none specified"""
        return [
            FieldConfig('item_id', FieldType.STRING, True, description="Unique identifier"),
            FieldConfig('name', FieldType.STRING, True, 1, 100, description="Name field"),
            FieldConfig('age', FieldType.INTEGER, True, min_value=0, max_value=150, description="Age field"),
            FieldConfig('address', FieldType.STRING, True, 1, 500, description="Address field")
        ]
    
    def _validate_schema(self):
        """Validate the schema configuration"""
        if not self.fields:
            raise ValueError("No fields defined in schema")
        
        # Check for key field
        key_field_exists = any(field.name == self.key_field for field in self.fields)
        if not key_field_exists:
            raise ValueError(f"Key field '{self.key_field}' not found in schema")
        
        # Check for sort key field if it exists
        if self.sort_key_field:
            sort_key_field_exists = any(field.name == self.sort_key_field for field in self.fields)
            if not sort_key_field_exists:
                raise ValueError(f"Sort key field '{self.sort_key_field}' not found in schema")
        
        # Check for duplicate field names
        field_names = [field.name for field in self.fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError("Duplicate field names found in schema")
        
        # Validate enum fields
        for field in self.fields:
            if field.type == FieldType.ENUM and not field.enum_values:
                raise ValueError(f"Enum field '{field.name}' must have enum_values defined")
    
    def get_field_names(self) -> List[str]:
        """Get list of field names"""
        return [field.name for field in self.fields]
    
    def get_queryable_fields(self) -> List[str]:
        """Get list of fields that can be queried"""
        return [field.name for field in self.fields if field.name != self.key_field]
    
    def get_indexed_fields(self) -> List[str]:
        """Get list of indexed fields"""
        return [field.name for field in self.fields if field.index]
    
    def get_unique_fields(self) -> List[str]:
        """Get list of unique fields"""
        return [field.name for field in self.fields if field.unique]
    
    def get_field_config(self, field_name: str) -> Optional[FieldConfig]:
        """Get configuration for a specific field"""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def validate_field_value(self, field_name: str, value: Any) -> bool:
        """Validate a field value against its configuration"""
        field_config = self.get_field_config(field_name)
        if not field_config:
            return False
        
        try:
            if field_config.type == FieldType.STRING:
                if not isinstance(value, str):
                    return False
                if field_config.min_length and len(value) < field_config.min_length:
                    return False
                if field_config.max_length and len(value) > field_config.max_length:
                    return False
                if field_config.pattern:
                    import re
                    if not re.match(field_config.pattern, value):
                        return False
            elif field_config.type == FieldType.INTEGER:
                int_val = int(value)
                if field_config.min_value and int_val < field_config.min_value:
                    return False
                if field_config.max_value and int_val > field_config.max_value:
                    return False
            elif field_config.type == FieldType.FLOAT:
                float_val = float(value)
                if field_config.min_value and float_val < field_config.min_value:
                    return False
                if field_config.max_value and float_val > field_config.max_value:
                    return False
            elif field_config.type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    return False
            elif field_config.type == FieldType.DATETIME:
                if not isinstance(value, str):
                    return False
            elif field_config.type == FieldType.EMAIL:
                if not isinstance(value, str):
                    return False
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, value):
                    return False
            elif field_config.type == FieldType.URL:
                if not isinstance(value, str):
                    return False
                import re
                url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
                if not re.match(url_pattern, value):
                    return False
            elif field_config.type == FieldType.PHONE:
                if not isinstance(value, str):
                    return False
                import re
                phone_pattern = r'^\+?[\d\s\-\(\)]+$'
                if not re.match(phone_pattern, value):
                    return False
            elif field_config.type == FieldType.UUID:
                if not isinstance(value, str):
                    return False
                import re
                uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                if not re.match(uuid_pattern, value.lower()):
                    return False
            elif field_config.type == FieldType.JSON:
                if not isinstance(value, (dict, list)):
                    return False
            elif field_config.type == FieldType.ARRAY:
                if not isinstance(value, list):
                    return False
            elif field_config.type == FieldType.ENUM:
                if not isinstance(value, str):
                    return False
                if field_config.enum_values and value not in field_config.enum_values:
                    return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the schema configuration"""
        return {
            'table_name': self.table_name,
            'key_field': self.key_field,
            'sort_key_field': self.sort_key_field,
            'total_fields': len(self.fields),
            'required_fields': len([f for f in self.fields if f.required]),
            'optional_fields': len([f for f in self.fields if not f.required]),
            'indexed_fields': self.get_indexed_fields(),
            'unique_fields': self.get_unique_fields(),
            'field_types': {f.name: f.type.value for f in self.fields}
        }

# Global schema instance
schema_config = SchemaConfig() 
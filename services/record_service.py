from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from botocore.exceptions import ClientError

from config.dynamodb import dynamodb_config
from config.schema import schema_config, FieldType
from models.dynamic_model import get_dynamic_models

logger = logging.getLogger(__name__)

class RecordService:
    """Generic service layer for any DynamoDB table CRUD operations"""
    
    def __init__(self):
        self.table = dynamodb_config.get_table()
        self.DynamicCreate, self.DynamicResponse = get_dynamic_models()
    
    def insert_record(self, record_data) -> Any:
        """Insert a new record with user-provided key"""
        try:
            now = datetime.utcnow()
            
            # Build item from record data
            item = {}
            for field_config in schema_config.fields:
                if hasattr(record_data, field_config.name):
                    value = getattr(record_data, field_config.name)
                    if field_config.type.value == 'datetime' and isinstance(value, datetime):
                        item[field_config.name] = value.isoformat()
                    else:
                        item[field_config.name] = value
            
            # Add timestamps
            item['created_at'] = now.isoformat()
            item['updated_at'] = now.isoformat()
            
            # Check if item already exists
            existing = self.table.get_item(Key={schema_config.key_field: item[schema_config.key_field]})
            if 'Item' in existing:
                raise Exception(f"Record with {schema_config.key_field} {item[schema_config.key_field]} already exists")
            
            self.table.put_item(Item=item)
            logger.info(f"Inserted record with {schema_config.key_field}: {item[schema_config.key_field]}")
            
            # Return response object
            response_data = {}
            for field_config in schema_config.fields:
                response_data[field_config.name] = item[field_config.name]
            response_data['created_at'] = now
            response_data['updated_at'] = now
            
            return self.DynamicResponse(**response_data)
            
        except ClientError as e:
            logger.error(f"Error inserting record: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting record: {str(e)}")
            raise
    
    def get_record(self, key_value: str) -> Optional[Any]:
        """Get a record by key value"""
        try:
            response = self.table.get_item(Key={schema_config.key_field: key_value})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Convert to response object
            response_data = {}
            for field_config in schema_config.fields:
                value = item.get(field_config.name)
                if field_config.type.value == 'datetime' and value:
                    response_data[field_config.name] = datetime.fromisoformat(value)
                else:
                    response_data[field_config.name] = value
            
            response_data['created_at'] = datetime.fromisoformat(item['created_at'])
            response_data['updated_at'] = datetime.fromisoformat(item['updated_at'])
            
            return self.DynamicResponse(**response_data)
            
        except ClientError as e:
            logger.error(f"Error getting record {key_value}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting record {key_value}: {str(e)}")
            raise
    
    def query_records(self, field: str, value: str, limit: int = 10, last_token: Optional[str] = None) -> Dict[str, Any]:
        """Query records by any field with pagination"""
        try:
            # Validate field
            if field not in schema_config.get_queryable_fields():
                raise Exception(f"Field '{field}' is not queryable")
            
            field_config = schema_config.get_field_config(field)
            if not field_config:
                raise Exception(f"Field '{field}' not found in schema")
            
            # Build filter expression based on field type
            if field_config.type == FieldType.INTEGER:
                try:
                    int_value = int(value)
                    filter_expression = f"#{field} = :{field}"
                    expression_attribute_names = {f'#{field}': field}
                    expression_attribute_values = {f':{field}': int_value}
                except ValueError:
                    raise Exception(f"Field '{field}' expects a number")
            elif field_config.type == FieldType.FLOAT:
                try:
                    float_value = float(value)
                    filter_expression = f"#{field} = :{field}"
                    expression_attribute_names = {f'#{field}': field}
                    expression_attribute_values = {f':{field}': float_value}
                except ValueError:
                    raise Exception(f"Field '{field}' expects a number")
            else:
                # For string fields, use contains for partial matching
                filter_expression = f"contains(#{field}, :{field})"
                expression_attribute_names = {f'#{field}': field}
                expression_attribute_values = {f':{field}': value.lower()}
            
            scan_kwargs = {
                'FilterExpression': filter_expression,
                'ExpressionAttributeNames': expression_attribute_names,
                'ExpressionAttributeValues': expression_attribute_values,
                'Limit': limit
            }
            
            if last_token:
                scan_kwargs['ExclusiveStartKey'] = {schema_config.key_field: last_token}
            
            response = self.table.scan(**scan_kwargs)
            
            records = []
            for item in response.get('Items', []):
                # Convert to response object
                response_data = {}
                for field_config in schema_config.fields:
                    value = item.get(field_config.name)
                    if field_config.type.value == 'datetime' and value:
                        response_data[field_config.name] = datetime.fromisoformat(value)
                    else:
                        response_data[field_config.name] = value
                
                response_data['created_at'] = datetime.fromisoformat(item['created_at'])
                response_data['updated_at'] = datetime.fromisoformat(item['updated_at'])
                
                records.append(self.DynamicResponse(**response_data))
            
            return {
                'records': records,
                'total_count': len(records),
                'next_token': response.get('LastEvaluatedKey', {}).get(schema_config.key_field) if response.get('LastEvaluatedKey') else None
            }
            
        except ClientError as e:
            logger.error(f"Error querying records: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error querying records: {str(e)}")
            raise
    
    def delete_record(self, key_value: str) -> bool:
        """Delete a record by key value"""
        try:
            response = self.table.delete_item(
                Key={schema_config.key_field: key_value},
                ReturnValues='ALL_OLD'
            )
            
            if 'Attributes' in response:
                logger.info(f"Deleted record with {schema_config.key_field}: {key_value}")
                return True
            else:
                logger.warning(f"Record with {schema_config.key_field} {key_value} not found for deletion")
                return False
                
        except ClientError as e:
            logger.error(f"Error deleting record {key_value}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting record {key_value}: {str(e)}")
            raise 
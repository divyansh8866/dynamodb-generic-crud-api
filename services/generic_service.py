from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from botocore.exceptions import ClientError

from config.dynamodb import dynamodb_config
from config.schema import schema_config, FieldType
from models.dynamic_model import get_dynamic_models

logger = logging.getLogger(__name__)

class GenericService:
    """Generic service layer for any DynamoDB table CRUD operations"""
    
    def __init__(self):
        self.table = dynamodb_config.get_table()
        self.DynamicCreate, self.DynamicUpdate, self.DynamicResponse = get_dynamic_models()
    
    def _build_key(self, partition_key: str, sort_key: Optional[str] = None) -> Dict[str, Any]:
        """Build DynamoDB key dictionary"""
        key = {schema_config.key_field: partition_key}
        if schema_config.sort_key_field and sort_key:
            key[schema_config.sort_key_field] = sort_key
        return key
    
    def _extract_keys_from_data(self, data) -> Tuple[str, Optional[str]]:
        """Extract partition and sort keys from data object"""
        partition_key = getattr(data, schema_config.key_field)
        sort_key = None
        if schema_config.sort_key_field:
            sort_key = getattr(data, schema_config.sort_key_field, None)
        return partition_key, sort_key
    
    def _validate_composite_key(self, partition_key: str, sort_key: Optional[str] = None):
        """Validate that composite key is properly provided"""
        if schema_config.sort_key_field and not sort_key:
            raise ValueError(f"Sort key '{schema_config.sort_key_field}' is required for this table")
    
    def insert_record(self, record_data) -> Any:
        """Insert a new record with user-provided key"""
        try:
            now = datetime.utcnow()
            
            # Extract keys
            partition_key, sort_key = self._extract_keys_from_data(record_data)
            self._validate_composite_key(partition_key, sort_key)
            
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
            key = self._build_key(partition_key, sort_key)
            existing = self.table.get_item(Key=key)
            if 'Item' in existing:
                key_description = f"{schema_config.key_field}={partition_key}"
                if sort_key:
                    key_description += f", {schema_config.sort_key_field}={sort_key}"
                raise Exception(f"Record with {key_description} already exists")
            
            self.table.put_item(Item=item)
            logger.info(f"Inserted record with key: {key}")
            
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
    
    def update_record(self, partition_key: str, update_data, sort_key: Optional[str] = None) -> Any:
        """Update an existing record"""
        try:
            now = datetime.utcnow()
            
            # Validate composite key
            self._validate_composite_key(partition_key, sort_key)
            
            # Build key
            key = self._build_key(partition_key, sort_key)
            
            # First check if record exists
            existing_response = self.table.get_item(Key=key)
            if 'Item' not in existing_response:
                key_description = f"{schema_config.key_field}={partition_key}"
                if sort_key:
                    key_description += f", {schema_config.sort_key_field}={sort_key}"
                raise Exception(f"Record with {key_description} not found")
            
            existing_item = existing_response['Item']
            
            # Build update expression and attribute values
            update_expression_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            # Process each field in update data
            for field_config in schema_config.fields:
                if field_config.name in [schema_config.key_field, schema_config.sort_key_field]:
                    continue  # Skip key fields
                
                if hasattr(update_data, field_config.name):
                    value = getattr(update_data, field_config.name)
                    
                    if value is not None:  # Only update if value is provided
                        # Convert datetime to string for storage if needed
                        if field_config.type == FieldType.DATETIME and isinstance(value, datetime):
                            value = value.isoformat()
                        
                        # Add to update expression
                        field_placeholder = f"#{field_config.name}"
                        value_placeholder = f":{field_config.name}"
                        
                        update_expression_parts.append(f"{field_placeholder} = {value_placeholder}")
                        expression_attribute_names[field_placeholder] = field_config.name
                        expression_attribute_values[value_placeholder] = value
            
            # Add updated_at timestamp
            update_expression_parts.append("#updated_at = :updated_at")
            expression_attribute_names["#updated_at"] = "updated_at"
            expression_attribute_values[":updated_at"] = now.isoformat()
            
            # Combine update expression
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            # Perform update
            response = self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            updated_item = response['Attributes']
            logger.info(f"Updated record with key: {key}")
            
            # Return response object
            response_data = {}
            for field_config in schema_config.fields:
                value = updated_item.get(field_config.name)
                if field_config.type.value == 'datetime' and value:
                    response_data[field_config.name] = datetime.fromisoformat(value)
                else:
                    response_data[field_config.name] = value
            
            response_data['created_at'] = datetime.fromisoformat(updated_item['created_at'])
            response_data['updated_at'] = datetime.fromisoformat(updated_item['updated_at'])
            
            return self.DynamicResponse(**response_data)
            
        except ClientError as e:
            logger.error(f"Error updating record {partition_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating record {partition_key}: {str(e)}")
            raise
    
    def get_record(self, partition_key: str, sort_key: Optional[str] = None) -> Optional[Any]:
        """Get a record by key value"""
        try:
            # Validate composite key
            self._validate_composite_key(partition_key, sort_key)
            
            # Build key
            key = self._build_key(partition_key, sort_key)
            
            response = self.table.get_item(Key=key)
            
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
            logger.error(f"Error getting record {partition_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting record {partition_key}: {str(e)}")
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
    
    def delete_record(self, partition_key: str, sort_key: Optional[str] = None) -> bool:
        """Delete a record by key value"""
        try:
            # Validate composite key
            self._validate_composite_key(partition_key, sort_key)
            
            # Build key
            key = self._build_key(partition_key, sort_key)
            
            response = self.table.delete_item(
                Key=key,
                ReturnValues='ALL_OLD'
            )
            
            if 'Attributes' in response:
                logger.info(f"Deleted record with key: {key}")
                return True
            else:
                key_description = f"{schema_config.key_field}={partition_key}"
                if sort_key:
                    key_description += f", {schema_config.sort_key_field}={sort_key}"
                logger.warning(f"Record with {key_description} not found for deletion")
                return False
                
        except ClientError as e:
            logger.error(f"Error deleting record {partition_key}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting record {partition_key}: {str(e)}")
            raise 
from flask import request
from flask_restx import Namespace, Resource, fields
from http import HTTPStatus
import logging
import uuid
from datetime import datetime

from services.generic_service import GenericService
from config.schema import schema_config
from models.dynamic_model import get_dynamic_models

logger = logging.getLogger(__name__)

# Get dynamic models
DynamicCreate, DynamicUpdate, DynamicResponse = get_dynamic_models()

# Create namespace
api = Namespace('records', description='Generic CRUD operations for any DynamoDB table')

def generate_request_id():
    """Generate a unique request ID for tracing"""
    return str(uuid.uuid4())

def create_error_response(message, status_code, request_id, details=None):
    """Create a consistent error response format"""
    error_response = {
        "success": False,
        "message": message,
        "status_code": status_code,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.path,
        "method": request.method
    }
    
    if details:
        error_response["details"] = details
    
    return error_response

def convert_datetime_to_iso(obj):
    """Convert datetime objects to ISO strings for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_iso(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_iso(item) for item in obj]
    else:
        return obj

def create_success_response(data, status_code, request_id, message=None):
    """Create a consistent success response format"""
    # Convert datetime objects to ISO strings
    serializable_data = convert_datetime_to_iso(data)
    
    response = {
        "success": True,
        "data": serializable_data,
        "status_code": status_code,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.path,
        "method": request.method
    }
    
    if message:
        response["message"] = message
    
    return response

# Create dynamic Swagger models
def create_swagger_models():
    """Create Swagger models dynamically based on schema"""
    
    # Create record model
    record_fields = {}
    for field_config in schema_config.fields:
        if field_config.type.value == 'string':
            record_fields[field_config.name] = fields.String(
                required=field_config.required,
                description=field_config.description,
                min_length=field_config.min_length,
                max_length=field_config.max_length
            )
        elif field_config.type.value == 'integer':
            record_fields[field_config.name] = fields.Integer(
                required=field_config.required,
                description=field_config.description,
                min=field_config.min_value,
                max=field_config.max_value
            )
        elif field_config.type.value == 'float':
            record_fields[field_config.name] = fields.Float(
                required=field_config.required,
                description=field_config.description,
                min=field_config.min_value,
                max=field_config.max_value
            )
        elif field_config.type.value == 'boolean':
            record_fields[field_config.name] = fields.Boolean(
                required=field_config.required,
                description=field_config.description
            )
        elif field_config.type.value == 'datetime':
            record_fields[field_config.name] = fields.DateTime(
                required=field_config.required,
                description=field_config.description
            )
    
    # Add timestamp fields
    record_fields['created_at'] = fields.DateTime(required=True, description='Creation timestamp')
    record_fields['updated_at'] = fields.DateTime(required=True, description='Last update timestamp')
    
    record_model = api.model('Record', record_fields)
    
    # Create create model (without timestamps)
    create_fields = {}
    for field_config in schema_config.fields:
        if field_config.type.value == 'string':
            create_fields[field_config.name] = fields.String(
                required=field_config.required,
                description=field_config.description,
                min_length=field_config.min_length,
                max_length=field_config.max_length
            )
        elif field_config.type.value == 'integer':
            create_fields[field_config.name] = fields.Integer(
                required=field_config.required,
                description=field_config.description,
                min=field_config.min_value,
                max=field_config.max_value
            )
        elif field_config.type.value == 'float':
            create_fields[field_config.name] = fields.Float(
                required=field_config.required,
                description=field_config.description,
                min=field_config.min_value,
                max=field_config.max_value
            )
        elif field_config.type.value == 'boolean':
            create_fields[field_config.name] = fields.Boolean(
                required=field_config.required,
                description=field_config.description
            )
        elif field_config.type.value == 'datetime':
            create_fields[field_config.name] = fields.DateTime(
                required=field_config.required,
                description=field_config.description
            )
    
    create_model = api.model('CreateRecord', create_fields)
    
    # Create update model (all fields optional except key)
    update_fields = {}
    for field_config in schema_config.fields:
        if field_config.name == schema_config.key_field:
            continue  # Skip key field in update
        
        # Match the same field types as create model for consistency
        if field_config.type.value == 'string':
            update_fields[field_config.name] = fields.String(
                required=False,
                description=field_config.description,
                min_length=field_config.min_length,
                max_length=field_config.max_length
            )
        elif field_config.type.value == 'integer':
            update_fields[field_config.name] = fields.Integer(
                required=False,
                description=field_config.description,
                min=field_config.min_value,
                max=field_config.max_value
            )
        elif field_config.type.value == 'float':
            update_fields[field_config.name] = fields.Float(
                required=False,
                description=field_config.description,
                min=field_config.min_value,
                max=field_config.max_value
            )
        elif field_config.type.value == 'boolean':
            update_fields[field_config.name] = fields.Boolean(
                required=False,
                description=field_config.description
            )
        elif field_config.type.value == 'datetime':
            update_fields[field_config.name] = fields.DateTime(
                required=False,
                description=field_config.description
            )
    
    update_model = api.model('UpdateRecord', update_fields)
    
    # Create query response model
    query_response_model = api.model('QueryResponse', {
        'records': fields.List(fields.Nested(record_model), description='List of records'),
        'total_count': fields.Integer(description='Total number of records returned'),
        'next_token': fields.String(description='Token for next page pagination')
    })
    
    return record_model, create_model, update_model, query_response_model

# Create models
record_model, create_model, update_model, query_response_model = create_swagger_models()

# Professional error response model
error_response_model = api.model('ErrorResponse', {
    'success': fields.Boolean(description='Operation success status', example=False),
    'message': fields.String(description='Human-readable error message'),
    'status_code': fields.Integer(description='HTTP status code'),
    'request_id': fields.String(description='Unique request identifier for tracing'),
    'timestamp': fields.String(description='ISO timestamp of the error'),
    'path': fields.String(description='Request path'),
    'method': fields.String(description='HTTP method'),
    'details': fields.Raw(description='Additional error details', required=False)
})

# Professional success response model
success_response_model = api.model('SuccessResponse', {
    'success': fields.Boolean(description='Operation success status', example=True),
    'data': fields.Raw(description='Response data'),
    'status_code': fields.Integer(description='HTTP status code'),
    'request_id': fields.String(description='Unique request identifier for tracing'),
    'timestamp': fields.String(description='ISO timestamp of the response'),
    'path': fields.String(description='Request path'),
    'method': fields.String(description='HTTP method'),
    'message': fields.String(description='Success message', required=False)
})

@api.route('/')
class RecordInsert(Resource):
    """Insert a new record"""
    
    @api.doc('insert_record')
    @api.expect(create_model, validate=True)
    @api.marshal_with(success_response_model, code=HTTPStatus.CREATED)
    @api.response(HTTPStatus.BAD_REQUEST, 'Invalid input data', error_response_model)
    @api.response(HTTPStatus.CONFLICT, f'Record with this {schema_config.key_field} already exists', error_response_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_response_model)
    def post(self):
        """Insert a new record with user-provided key"""
        request_id = generate_request_id()
        
        try:
            data = request.get_json()
            
            # Validate input data
            record_data = DynamicCreate(**data)
            
            generic_service = GenericService()
            new_record = generic_service.insert_record(record_data)
            
            response = create_success_response(
                data=new_record.dict() if hasattr(new_record, 'dict') else new_record,
                status_code=HTTPStatus.CREATED,
                request_id=request_id,
                message=f"Record created successfully with {schema_config.key_field}: {getattr(new_record, schema_config.key_field)}"
            )
            
            return response, HTTPStatus.CREATED
            
        except ValueError as e:
            logger.error(f"[{request_id}] Validation error: {str(e)}")
            error_response = create_error_response(
                message="Invalid input data provided",
                status_code=HTTPStatus.BAD_REQUEST,
                request_id=request_id,
                details={"validation_errors": str(e)}
            )
            return error_response, HTTPStatus.BAD_REQUEST
        except Exception as e:
            if "already exists" in str(e):
                logger.warning(f"[{request_id}] Duplicate record attempt: {str(e)}")
                error_response = create_error_response(
                    message=f"A record with this {schema_config.key_field} already exists",
                    status_code=HTTPStatus.CONFLICT,
                    request_id=request_id,
                    details={"conflict_field": schema_config.key_field}
                )
                return error_response, HTTPStatus.CONFLICT
            else:
                logger.error(f"[{request_id}] Error inserting record: {str(e)}")
                error_response = create_error_response(
                    message="An internal server error occurred while creating the record",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    request_id=request_id
                )
                return error_response, HTTPStatus.INTERNAL_SERVER_ERROR

@api.route(f'/<string:partition_key>')
@api.param('partition_key', f'The record {schema_config.key_field}')
class RecordGetUpdateDelete(Resource):
    """Get, update and delete record operations"""
    
    @api.doc('get_record')
    @api.marshal_with(success_response_model, code=HTTPStatus.OK)
    @api.response(HTTPStatus.NOT_FOUND, 'Record not found', error_response_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_response_model)
    def get(self, partition_key):
        """Get a record by partition key (and sort key if configured)"""
        request_id = generate_request_id()
        
        try:
            # Get sort key from query parameter if table uses composite key
            sort_key = None
            if schema_config.sort_key_field:
                sort_key = request.args.get(schema_config.sort_key_field)
                if not sort_key:
                    logger.warning(f"[{request_id}] Missing sort key parameter: {schema_config.sort_key_field}")
                    error_response = create_error_response(
                        message=f"Sort key parameter '{schema_config.sort_key_field}' is required",
                        status_code=HTTPStatus.BAD_REQUEST,
                        request_id=request_id,
                        details={"missing_parameter": schema_config.sort_key_field, "key_field": schema_config.key_field}
                    )
                    return error_response, HTTPStatus.BAD_REQUEST
            
            generic_service = GenericService()
            record = generic_service.get_record(partition_key, sort_key)
            
            if not record:
                key_description = f"{schema_config.key_field}={partition_key}"
                if sort_key:
                    key_description += f", {schema_config.sort_key_field}={sort_key}"
                logger.info(f"[{request_id}] Record not found: {key_description}")
                error_response = create_error_response(
                    message=f"Record with {key_description} not found",
                    status_code=HTTPStatus.NOT_FOUND,
                    request_id=request_id,
                    details={"searched_key": key_description, "key_field": schema_config.key_field}
                )
                return error_response, HTTPStatus.NOT_FOUND
            
            response = create_success_response(
                data=record.dict() if hasattr(record, 'dict') else record,
                status_code=HTTPStatus.OK,
                request_id=request_id,
                message=f"Record retrieved successfully"
            )
            
            return response, HTTPStatus.OK
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting record {partition_key}: {str(e)}")
            error_response = create_error_response(
                message="An internal server error occurred while retrieving the record",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                request_id=request_id
            )
            return error_response, HTTPStatus.INTERNAL_SERVER_ERROR
    
    @api.doc('update_record')
    @api.expect(update_model, validate=True)
    @api.marshal_with(success_response_model, code=HTTPStatus.OK)
    @api.response(HTTPStatus.BAD_REQUEST, 'Invalid input data', error_response_model)
    @api.response(HTTPStatus.NOT_FOUND, 'Record not found', error_response_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_response_model)
    def put(self, partition_key):
        """Update a record by partition key (and sort key if configured)"""
        request_id = generate_request_id()
        
        try:
            data = request.get_json()
            
            # Get sort key from query parameter if table uses composite key
            sort_key = None
            if schema_config.sort_key_field:
                sort_key = request.args.get(schema_config.sort_key_field)
                if not sort_key:
                    logger.warning(f"[{request_id}] Missing sort key parameter: {schema_config.sort_key_field}")
                    error_response = create_error_response(
                        message=f"Sort key parameter '{schema_config.sort_key_field}' is required",
                        status_code=HTTPStatus.BAD_REQUEST,
                        request_id=request_id,
                        details={"missing_parameter": schema_config.sort_key_field, "key_field": schema_config.key_field}
                    )
                    return error_response, HTTPStatus.BAD_REQUEST
            
            # Create a simple object with the update data
            # Bypass Pydantic validation for updates to avoid required field issues
            class UpdateData:
                def __init__(self, data_dict):
                    for key, value in data_dict.items():
                        setattr(self, key, value)
            
            update_data = UpdateData(data)
            
            generic_service = GenericService()
            updated_record = generic_service.update_record(partition_key, update_data, sort_key)
            
            response = create_success_response(
                data=updated_record.dict() if hasattr(updated_record, 'dict') else updated_record,
                status_code=HTTPStatus.OK,
                request_id=request_id,
                message=f"Record updated successfully"
            )
            
            return response, HTTPStatus.OK
            
        except ValueError as e:
            logger.error(f"[{request_id}] Validation error: {str(e)}")
            error_response = create_error_response(
                message="Invalid input data provided",
                status_code=HTTPStatus.BAD_REQUEST,
                request_id=request_id,
                details={"validation_errors": str(e)}
            )
            return error_response, HTTPStatus.BAD_REQUEST
        except Exception as e:
            if "not found" in str(e):
                key_description = f"{schema_config.key_field}={partition_key}"
                if sort_key:
                    key_description += f", {schema_config.sort_key_field}={sort_key}"
                logger.info(f"[{request_id}] Update attempt on non-existent record: {key_description}")
                error_response = create_error_response(
                    message=f"Record with {key_description} not found",
                    status_code=HTTPStatus.NOT_FOUND,
                    request_id=request_id,
                    details={"searched_key": key_description, "key_field": schema_config.key_field}
                )
                return error_response, HTTPStatus.NOT_FOUND
            else:
                logger.error(f"[{request_id}] Error updating record {partition_key}: {str(e)}")
                error_response = create_error_response(
                    message="An internal server error occurred while updating the record",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    request_id=request_id
                )
                return error_response, HTTPStatus.INTERNAL_SERVER_ERROR
    
    @api.doc('delete_record')
    @api.marshal_with(success_response_model, code=HTTPStatus.OK)
    @api.response(HTTPStatus.NOT_FOUND, 'Record not found', error_response_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_response_model)
    def delete(self, partition_key):
        """Delete a record by partition key (and sort key if configured)"""
        request_id = generate_request_id()
        
        try:
            # Get sort key from query parameter if table uses composite key
            sort_key = None
            if schema_config.sort_key_field:
                sort_key = request.args.get(schema_config.sort_key_field)
                if not sort_key:
                    logger.warning(f"[{request_id}] Missing sort key parameter: {schema_config.sort_key_field}")
                    error_response = create_error_response(
                        message=f"Sort key parameter '{schema_config.sort_key_field}' is required",
                        status_code=HTTPStatus.BAD_REQUEST,
                        request_id=request_id,
                        details={"missing_parameter": schema_config.sort_key_field, "key_field": schema_config.key_field}
                    )
                    return error_response, HTTPStatus.BAD_REQUEST
            
            generic_service = GenericService()
            deleted = generic_service.delete_record(partition_key, sort_key)
            
            if not deleted:
                key_description = f"{schema_config.key_field}={partition_key}"
                if sort_key:
                    key_description += f", {schema_config.sort_key_field}={sort_key}"
                logger.info(f"[{request_id}] Delete attempt on non-existent record: {key_description}")
                error_response = create_error_response(
                    message=f"Record with {key_description} not found",
                    status_code=HTTPStatus.NOT_FOUND,
                    request_id=request_id,
                    details={"searched_key": key_description, "key_field": schema_config.key_field}
                )
                return error_response, HTTPStatus.NOT_FOUND
            
            key_description = f"{schema_config.key_field}={partition_key}"
            if sort_key:
                key_description += f", {schema_config.sort_key_field}={sort_key}"
            
            response = create_success_response(
                data={"deleted_key": key_description},
                status_code=HTTPStatus.OK,
                request_id=request_id,
                message=f"Record deleted successfully"
            )
            
            return response, HTTPStatus.OK
            
        except Exception as e:
            logger.error(f"[{request_id}] Error deleting record {partition_key}: {str(e)}")
            error_response = create_error_response(
                message="An internal server error occurred while deleting the record",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                request_id=request_id
            )
            return error_response, HTTPStatus.INTERNAL_SERVER_ERROR

@api.route('/query')
class RecordQuery(Resource):
    """Query records by any field"""
    
    @api.doc('query_records')
    @api.param('field', f'Field to query ({", ".join(schema_config.get_queryable_fields())})', required=True)
    @api.param('value', 'Value to search for', required=True)
    @api.param('limit', 'Number of records to return (default: 10, max: 100)', type=int)
    @api.param('last_token', 'Token for pagination', type=str)
    @api.marshal_with(success_response_model, code=HTTPStatus.OK)
    @api.response(HTTPStatus.BAD_REQUEST, 'Invalid query parameters', error_response_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_response_model)
    def get(self):
        """Query records by any field with pagination"""
        request_id = generate_request_id()
        
        try:
            field = request.args.get('field')
            value = request.args.get('value')
            limit = request.args.get('limit', 10, type=int)
            last_token = request.args.get('last_token', type=str)
            
            # Validate required parameters
            if not field or not value:
                logger.warning(f"[{request_id}] Missing required query parameters")
                error_response = create_error_response(
                    message="Both 'field' and 'value' parameters are required",
                    status_code=HTTPStatus.BAD_REQUEST,
                    request_id=request_id,
                    details={"missing_parameters": [p for p in ['field', 'value'] if not request.args.get(p)]}
                )
                return error_response, HTTPStatus.BAD_REQUEST
            
            # Validate field
            queryable_fields = schema_config.get_queryable_fields()
            if field not in queryable_fields:
                logger.warning(f"[{request_id}] Invalid query field: {field}")
                error_response = create_error_response(
                    message=f"Invalid query field. Must be one of: {', '.join(queryable_fields)}",
                    status_code=HTTPStatus.BAD_REQUEST,
                    request_id=request_id,
                    details={"invalid_field": field, "valid_fields": queryable_fields}
                )
                return error_response, HTTPStatus.BAD_REQUEST
            
            # Validate limit
            if limit > 100:
                limit = 100
            if limit < 1:
                limit = 10
            
            generic_service = GenericService()
            result = generic_service.query_records(field, value, limit, last_token)
            
            # Convert records to dictionaries for JSON serialization
            serializable_result = {
                'records': [record.dict() if hasattr(record, 'dict') else record for record in result['records']],
                'total_count': result['total_count'],
                'next_token': result['next_token']
            }
            
            response = create_success_response(
                data=serializable_result,
                status_code=HTTPStatus.OK,
                request_id=request_id,
                message=f"Query completed successfully. Found {result['total_count']} records."
            )
            
            return response, HTTPStatus.OK
            
        except Exception as e:
            logger.error(f"[{request_id}] Error querying records: {str(e)}")
            error_response = create_error_response(
                message="An internal server error occurred while querying records",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                request_id=request_id
            )
            return error_response, HTTPStatus.INTERNAL_SERVER_ERROR 
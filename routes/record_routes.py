from flask import request
from flask_restx import Namespace, Resource, fields
from http import HTTPStatus
import logging

from services.generic_service import GenericService
from config.schema import schema_config
from models.dynamic_model import get_dynamic_models

logger = logging.getLogger(__name__)

# Get dynamic models
DynamicCreate, DynamicResponse = get_dynamic_models()

# Create namespace
api = Namespace('records', description='Generic CRUD operations for any DynamoDB table')

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
    
    # Create query response model
    query_response_model = api.model('QueryResponse', {
        'records': fields.List(fields.Nested(record_model), description='List of records'),
        'total_count': fields.Integer(description='Total number of records returned'),
        'next_token': fields.String(description='Token for next page pagination')
    })
    
    return record_model, create_model, query_response_model

# Create models
record_model, create_model, query_response_model = create_swagger_models()

error_model = api.model('Error', {
    'message': fields.String(description='Error message'),
    'status': fields.String(description='Error status')
})

@api.route('/')
class RecordInsert(Resource):
    """Insert a new record"""
    
    @api.doc('insert_record')
    @api.expect(create_model, validate=True)
    @api.marshal_with(record_model, code=HTTPStatus.CREATED)
    @api.response(HTTPStatus.BAD_REQUEST, 'Invalid input data', error_model)
    @api.response(HTTPStatus.CONFLICT, f'Record with this {schema_config.key_field} already exists', error_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_model)
    def post(self):
        """Insert a new record with user-provided key"""
        try:
            data = request.get_json()
            
            # Validate input data
            record_data = DynamicCreate(**data)
            
            generic_service = GenericService()
            new_record = generic_service.insert_record(record_data)
            
            return new_record, HTTPStatus.CREATED
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            api.abort(HTTPStatus.BAD_REQUEST, f"Invalid input data: {str(e)}")
        except Exception as e:
            if "already exists" in str(e):
                api.abort(HTTPStatus.CONFLICT, str(e))
            logger.error(f"Error inserting record: {str(e)}")
            api.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Internal server error: {str(e)}")

@api.route(f'/<string:key_value>')
@api.param('key_value', f'The record {schema_config.key_field}')
class RecordGetDelete(Resource):
    """Get and delete record operations"""
    
    @api.doc('get_record')
    @api.marshal_with(record_model, code=HTTPStatus.OK)
    @api.response(HTTPStatus.NOT_FOUND, 'Record not found', error_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_model)
    def get(self, key_value):
        """Get a record by key value"""
        try:
            generic_service = GenericService()
            record = generic_service.get_record(key_value)
            
            if not record:
                api.abort(HTTPStatus.NOT_FOUND, f"Record with {schema_config.key_field} {key_value} not found")
            
            return record, HTTPStatus.OK
            
        except Exception as e:
            logger.error(f"Error getting record {key_value}: {str(e)}")
            api.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Internal server error: {str(e)}")
    
    @api.doc('delete_record')
    @api.response(HTTPStatus.NO_CONTENT, 'Record deleted successfully')
    @api.response(HTTPStatus.NOT_FOUND, 'Record not found', error_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_model)
    def delete(self, key_value):
        """Delete a record by key value"""
        try:
            generic_service = GenericService()
            deleted = generic_service.delete_record(key_value)
            
            if not deleted:
                api.abort(HTTPStatus.NOT_FOUND, f"Record with {schema_config.key_field} {key_value} not found")
            
            return '', HTTPStatus.NO_CONTENT
            
        except Exception as e:
            logger.error(f"Error deleting record {key_value}: {str(e)}")
            api.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Internal server error: {str(e)}")

@api.route('/query')
class RecordQuery(Resource):
    """Query records by any field"""
    
    @api.doc('query_records')
    @api.param('field', f'Field to query ({", ".join(schema_config.get_queryable_fields())})', required=True)
    @api.param('value', 'Value to search for', required=True)
    @api.param('limit', 'Number of records to return (default: 10, max: 100)', type=int)
    @api.param('last_token', 'Token for pagination', type=str)
    @api.marshal_with(query_response_model, code=HTTPStatus.OK)
    @api.response(HTTPStatus.BAD_REQUEST, 'Invalid query parameters', error_model)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', error_model)
    def get(self):
        """Query records by any field with pagination"""
        try:
            field = request.args.get('field')
            value = request.args.get('value')
            limit = request.args.get('limit', 10, type=int)
            last_token = request.args.get('last_token', type=str)
            
            # Validate required parameters
            if not field or not value:
                api.abort(HTTPStatus.BAD_REQUEST, "Both 'field' and 'value' parameters are required")
            
            # Validate field
            queryable_fields = schema_config.get_queryable_fields()
            if field not in queryable_fields:
                api.abort(HTTPStatus.BAD_REQUEST, f"Invalid field. Must be one of: {', '.join(queryable_fields)}")
            
            # Validate limit
            if limit > 100:
                limit = 100
            if limit < 1:
                limit = 10
            
            generic_service = GenericService()
            result = generic_service.query_records(field, value, limit, last_token)
            
            return result, HTTPStatus.OK
            
        except Exception as e:
            logger.error(f"Error querying records: {str(e)}")
            api.abort(HTTPStatus.INTERNAL_SERVER_ERROR, f"Internal server error: {str(e)}") 
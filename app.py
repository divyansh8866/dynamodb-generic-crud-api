from flask import Flask, request
from flask_restx import Api
import logging
import uuid
from datetime import datetime

from config.dynamodb import dynamodb_config
from config.schema import schema_config
from routes.generic_routes import api as generic_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_request_id():
    """Generate a unique request ID for tracing"""
    return str(uuid.uuid4())

def create_success_response(data, status_code, request_id, message=None):
    """Create a consistent success response format"""
    response = {
        "success": True,
        "data": data,
        "status_code": status_code,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.path,
        "method": request.method
    }
    
    if message:
        response["message"] = message
    
    return response

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

# Create Flask app
app = Flask(__name__)

# Create API
api = Api(
    app,
    version='1.0',
    title='Generic DynamoDB CRUD API',
    description='A production-ready, generic CRUD API for DynamoDB tables with flexible schema support',
    doc='/docs',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key'
        }
    },
    security='apikey'
)

# Add namespaces
api.add_namespace(generic_api, path='/api/v1')

@app.route('/health')
def health_check():
    """Health check endpoint with professional response format"""
    request_id = generate_request_id()
    
    try:
        # Test DynamoDB connection
        table = dynamodb_config.get_table()
        table.table_status
        
        # Get table info
        table_name = schema_config.table_name
        key_field = schema_config.key_field
        sort_key_field = schema_config.sort_key_field
        field_count = len(schema_config.fields)
        
        health_data = {
            "status": "healthy",
            "service": "Generic DynamoDB CRUD API",
            "version": "1.0",
            "database": {
                "status": "connected",
                "table": table_name,
                "key_field": key_field,
                "sort_key_field": sort_key_field,
                "field_count": field_count,
                "key_type": "composite" if sort_key_field else "simple"
            },
            "uptime": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = create_success_response(
            data=health_data,
            status_code=200,
            request_id=request_id,
            message="Service is healthy and ready to handle requests"
        )
        
        logger.info(f"[{request_id}] Health check successful")
        return response, 200
        
    except Exception as e:
        logger.error(f"[{request_id}] Health check failed: {str(e)}")
        
        error_response = create_error_response(
            message="Service health check failed",
            status_code=503,
            request_id=request_id,
            details={
                "error": str(e),
                "service": "Generic DynamoDB CRUD API",
                "version": "1.0"
            }
        )
        
        return error_response, 503

if __name__ == '__main__':
    # Verify DynamoDB connection on startup
    logger.info("Verifying DynamoDB connection...")
    try:
        table = dynamodb_config.get_table()
        table.table_status
        logger.info(f"Successfully connected to DynamoDB table: {schema_config.table_name}")
        
        # Log table schema
        field_names = [field.name for field in schema_config.fields]
        logger.info(f"Table schema: {field_names}")
        
    except Exception as e:
        logger.error(f"Failed to connect to DynamoDB: {str(e)}")
        raise
    
    # Start the application
    app.run(host='0.0.0.0', port=8001, debug=True) 
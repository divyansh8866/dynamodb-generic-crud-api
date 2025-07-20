import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DynamoDBConfig:
    """DynamoDB configuration and connection management"""
    
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'test-api')
        self.region_name = os.getenv('AWS_REGION', 'us-east-1')
        self.endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')  # For local development
        
        logger.info(f"Initializing DynamoDB config - Table: {self.table_name}, Region: {self.region_name}")
        
        # Initialize DynamoDB client
        self.dynamodb = self._create_dynamodb_client()
        self.table = self.dynamodb.Table(self.table_name)
    
    def _create_dynamodb_client(self):
        """Create DynamoDB client with proper configuration"""
        try:
            # For local development, you might use DynamoDB Local
            if self.endpoint_url:
                logger.info(f"Using local DynamoDB endpoint: {self.endpoint_url}")
                return boto3.resource(
                    'dynamodb',
                    endpoint_url=self.endpoint_url,
                    region_name=self.region_name
                )
            
            # For production, use AWS credentials
            logger.info("Using AWS DynamoDB with credentials")
            return boto3.resource(
                'dynamodb',
                region_name=self.region_name
            )
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to create DynamoDB client: {str(e)}")
            raise
    
    def get_table(self):
        """Get the DynamoDB table instance"""
        return self.table

# Global instance
dynamodb_config = DynamoDBConfig() 
# Generic DynamoDB CRUD API

A **completely configurable** REST API built with Flask and Flask-RestX for CRUD operations on **any DynamoDB table**. This API automatically adapts to your table schema and provides instant CRUD functionality without any code changes.

## 🚀 **Key Features**

- **🔧 Zero Code Changes**: Just configure environment variables and run
- **📊 Any Table Schema**: Works with any DynamoDB table structure
- **🔄 Dynamic Models**: Automatically generates Pydantic models from schema
- **📝 Interactive Swagger**: Auto-generated documentation for your schema
- **🔍 Smart Querying**: Query any field with pagination
- **✅ Validation**: Built-in field validation based on your schema
- **🐳 Docker Ready**: One command deployment

## 📋 **4 Simple Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/records/` | Insert a new record |
| GET | `/api/v1/records/{key}` | Get a record by key |
| GET | `/api/v1/records/query` | Query records by any field |
| DELETE | `/api/v1/records/{key}` | Delete a record by key |

## ⚙️ **Configuration**

### **1. Basic Setup**
```bash
# Required
DYNAMODB_TABLE_NAME=your_table_name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
KEY_FIELD=item_id  # Your primary key field name
```

### **2. Define Your Schema**
```bash
# Format: "field:type:required:min:max:description"
TABLE_FIELDS=item_id:string:true:1:100:Unique ID,name:string:true:1:200:Full name,age:integer:true:0:150:Age,price:float:true:0:999999:Price,active:boolean:true:Active status
```

### **3. Field Types Supported**
- `string` - Text fields with min/max length
- `integer` - Whole numbers with min/max values
- `float` - Decimal numbers with min/max values
- `boolean` - True/false values
- `datetime` - Date and time values

## 🎯 **Usage Examples**

### **Example 1: Person Management**
```bash
# Configuration
DYNAMODB_TABLE_NAME=persons
KEY_FIELD=person_id
TABLE_FIELDS=person_id:string:true:1:50:Person ID,name:string:true:1:100:Full name,age:integer:true:0:150:Age,email:string:true:1:255:Email address

# Insert a person
POST /api/v1/records/
{
  "person_id": "user123",
  "name": "John Doe",
  "age": 30,
  "email": "john@example.com"
}

# Query by name
GET /api/v1/records/query?field=name&value=John&limit=10
```

### **Example 2: Product Catalog**
```bash
# Configuration
DYNAMODB_TABLE_NAME=products
KEY_FIELD=product_id
TABLE_FIELDS=product_id:string:true:1:50:Product ID,name:string:true:1:200:Product name,price:float:true:0:999999:Price,stock:integer:true:0:999999:Stock,category:string:true:1:100:Category

# Insert a product
POST /api/v1/records/
{
  "product_id": "PROD001",
  "name": "iPhone 15",
  "price": 999.99,
  "stock": 50,
  "category": "Electronics"
}

# Query by category
GET /api/v1/records/query?field=category&value=Electronics&limit=20
```

### **Example 3: User Management**
```bash
# Configuration
DYNAMODB_TABLE_NAME=users
KEY_FIELD=user_id
TABLE_FIELDS=user_id:string:true:1:50:User ID,email:string:true:1:255:Email,username:string:true:3:50:Username,age:integer:false:13:120:Age,is_active:boolean:true:Active status

# Insert a user
POST /api/v1/records/
{
  "user_id": "U12345",
  "email": "user@example.com",
  "username": "john_doe",
  "age": 25,
  "is_active": true
}
```

## 🐳 **Quick Start with Docker**

### **1. Create Environment File**
```bash
cp env.example .env
```

### **2. Configure Your Schema**
```bash
# Edit .env with your configuration
DYNAMODB_TABLE_NAME=my_table
KEY_FIELD=id
TABLE_FIELDS=id:string:true:1:50:Unique ID,name:string:true:1:100:Name,value:integer:true:0:999999:Value
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### **3. Run the API**
```bash
docker-compose up --build
```

### **4. Access Your API**
- **API Base**: `http://localhost:8001/api/v1`
- **Swagger Docs**: `http://localhost:8001/docs`

## 📊 **API Endpoints**

### **Insert Record**
```bash
POST /api/v1/records/
Content-Type: application/json

{
  "your_key_field": "value",
  "field1": "value1",
  "field2": 123
}
```

### **Get Record**
```bash
GET /api/v1/records/{key_value}
```

### **Query Records**
```bash
GET /api/v1/records/query?field=name&value=John&limit=10&last_token=abc123
```

### **Delete Record**
```bash
DELETE /api/v1/records/{key_value}
```

## 🔍 **Query Examples**

### **String Fields (Partial Match)**
```bash
GET /api/v1/records/query?field=name&value=John
# Finds: "John Doe", "Johnny", "Johnson"
```

### **Numeric Fields (Exact Match)**
```bash
GET /api/v1/records/query?field=age&value=30
# Finds: records with age = 30
```

### **Boolean Fields**
```bash
GET /api/v1/records/query?field=active&value=true
# Finds: records with active = true
```

### **With Pagination**
```bash
GET /api/v1/records/query?field=category&value=Electronics&limit=5&last_token=abc123
```

## 📝 **Response Format**

### **Single Record**
```json
{
  "your_key_field": "value",
  "field1": "value1",
  "field2": 123,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### **Query Response**
```json
{
  "records": [...],
  "total_count": 5,
  "next_token": "abc123"
}
```

## 🛠️ **Advanced Configuration**

### **Optional Fields**
```bash
# Make age optional
TABLE_FIELDS=id:string:true:1:50:ID,name:string:true:1:100:Name,age:integer:false:0:150:Age
```

### **Custom Validation**
```bash
# String with length limits
TABLE_FIELDS=email:string:true:5:255:Email address

# Integer with value limits
TABLE_FIELDS=score:integer:true:0:100:Test score

# Float with precision
TABLE_FIELDS=price:float:true:0:999999.99:Product price
```

### **Multiple Field Types**
```bash
TABLE_FIELDS=id:string:true:1:50:ID,name:string:true:1:100:Name,age:integer:false:0:150:Age,price:float:true:0:999999:Price,active:boolean:true:Status,created:datetime:true:Created date
```

## 🔧 **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `DYNAMODB_TABLE_NAME` | Your DynamoDB table name | Required |
| `KEY_FIELD` | Primary key field name | `item_id` |
| `TABLE_FIELDS` | Schema definition | Default fields |
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `PORT` | API port | `8001` |

## 🚀 **Benefits**

- ✅ **Instant API**: No coding required
- ✅ **Schema Agnostic**: Works with any table structure
- ✅ **Auto Documentation**: Swagger docs generated automatically
- ✅ **Production Ready**: Error handling, validation, logging
- ✅ **Scalable**: Built on DynamoDB
- ✅ **Docker Native**: Easy deployment
- ✅ **Cost Effective**: Pay-per-request DynamoDB

## 🔒 **Security**

- Use HTTPS in production
- Implement proper authentication
- Use IAM roles when possible
- Validate all inputs
- Monitor API usage

## 📈 **Production Deployment**

```bash
# Build production image
docker build -t generic-dynamodb-api .

# Run with environment variables
docker run -d \
  -p 8001:8001 \
  -e DYNAMODB_TABLE_NAME=your_table \
  -e TABLE_FIELDS="your:schema:here" \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  generic-dynamodb-api
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License.

---

**🎉 You now have a fully functional, configurable API for any DynamoDB table! Just set your environment variables and run.** 

## 🔑 Sort Key Support

The API now supports **composite keys** (partition key + sort key) for more flexible DynamoDB data modeling. This enables efficient queries and better data organization.

### Configuration

#### Simple Key (Partition Key Only)
```json
{
  "table_name": "users",
  "key_field": "user_id",
  "fields": [
    {
      "name": "user_id",
      "type": "string",
      "required": true,
      "description": "Unique user identifier"
    },
    {
      "name": "name",
      "type": "string",
      "required": true,
      "description": "User name"
    }
  ]
}
```

#### Composite Key (Partition Key + Sort Key)
```json
{
  "table_name": "user-events",
  "key_field": "user_id",
  "sort_key_field": "timestamp",
  "fields": [
    {
      "name": "user_id",
      "type": "string",
      "required": true,
      "description": "User identifier (partition key)"
    },
    {
      "name": "timestamp",
      "type": "string",
      "required": true,
      "description": "Event timestamp (sort key)"
    },
    {
      "name": "event_type",
      "type": "string",
      "required": true,
      "description": "Type of event"
    }
  ]
}
```

### API Usage

#### Simple Key Operations
```bash
# Create record
curl -X POST "http://localhost:8001/api/v1/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "name": "John Doe"}'

# Get record
curl -X GET "http://localhost:8001/api/v1/user123"

# Update record
curl -X PUT "http://localhost:8001/api/v1/user123" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith"}'

# Delete record
curl -X DELETE "http://localhost:8001/api/v1/user123"
```

#### Composite Key Operations
```bash
# Create record with sort key
curl -X POST "http://localhost:8001/api/v1/" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "timestamp": "2025-07-20T10:00:00Z", "event_type": "login"}'

# Get record with sort key
curl -X GET "http://localhost:8001/api/v1/user123?timestamp=2025-07-20T10:00:00Z"

# Update record with sort key
curl -X PUT "http://localhost:8001/api/v1/user123?timestamp=2025-07-20T10:00:00Z" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "logout"}'

# Delete record with sort key
curl -X DELETE "http://localhost:8001/api/v1/user123?timestamp=2025-07-20T10:00:00Z"
```

### Use Cases

#### 1. Time-Series Data
```json
{
  "key_field": "device_id",
  "sort_key_field": "timestamp",
  "fields": [
    {"name": "device_id", "type": "string", "required": true},
    {"name": "timestamp", "type": "string", "required": true},
    {"name": "temperature", "type": "float", "required": true},
    {"name": "humidity", "type": "float", "required": true}
  ]
}
```

#### 2. User Sessions
```json
{
  "key_field": "user_id",
  "sort_key_field": "session_id",
  "fields": [
    {"name": "user_id", "type": "string", "required": true},
    {"name": "session_id", "type": "string", "required": true},
    {"name": "start_time", "type": "string", "required": true},
    {"name": "end_time", "type": "string", "required": false}
  ]
}
```

#### 3. Order Items
```json
{
  "key_field": "order_id",
  "sort_key_field": "item_id",
  "fields": [
    {"name": "order_id", "type": "string", "required": true},
    {"name": "item_id", "type": "string", "required": true},
    {"name": "quantity", "type": "integer", "required": true},
    {"name": "price", "type": "float", "required": true}
  ]
}
```

### Benefits

1. **Efficient Queries**: Sort keys enable efficient range queries and sorting
2. **Data Organization**: Better data modeling for hierarchical relationships
3. **Scalability**: Improved performance for large datasets
4. **Flexibility**: Support for both simple and complex data structures

### Error Handling

The API provides clear error messages for sort key operations:

```json
{
  "success": false,
  "message": "Sort key parameter 'timestamp' is required",
  "status_code": 400,
  "details": {
    "missing_parameter": "timestamp",
    "key_field": "user_id"
  }
}
```

### Health Check

The health endpoint shows key configuration:

```json
{
  "database": {
    "key_type": "composite",
    "key_field": "user_id",
    "sort_key_field": "timestamp"
  }
}
``` 
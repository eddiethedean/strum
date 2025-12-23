# FastAPI Integration Guide

This guide shows how to use `stringent` with FastAPI to parse and validate string inputs in your API endpoints.

## Overview

`stringent` integrates seamlessly with FastAPI by using `ParsableModel` as request/response models. This allows you to:

- Parse complex string formats in query parameters, request bodies, and path parameters
- Leverage Pydantic's validation (which FastAPI uses) for type safety
- Handle multiple input formats with pattern chaining
- Automatically parse JSON strings with `JsonParsableModel`

## Basic Setup

### Installation

```bash
pip install stringent fastapi uvicorn
```

### Simple Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
from stringent import parse, ParsableModel

app = FastAPI()

class Info(BaseModel):
    name: str
    age: int
    city: str

class User(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

@app.post("/users")
async def create_user(user: User):
    """Create a user with pipe-separated info field."""
    return {
        "id": user.id,
        "name": user.info.name,
        "age": user.info.age,
        "city": user.info.city,
        "email": user.email
    }
```

**Request:**
```json
{
  "id": 1,
  "info": "Alice | 30 | NYC",
  "email": "alice@example.com"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Alice",
  "age": 30,
  "city": "NYC",
  "email": "alice@example.com"
}
```

## Request Body Parsing

### Using JsonParsableModel

When your API accepts JSON strings, use `JsonParsableModel`:

```python
from fastapi import FastAPI
from stringent import JsonParsableModel

app = FastAPI()

class User(JsonParsableModel):
    name: str
    age: int
    email: str

@app.post("/users")
async def create_user(user: User):
    """Accepts both JSON objects and JSON strings."""
    return {
        "message": f"Created user {user.name}",
        "age": user.age,
        "email": user.email
    }
```

**Request (JSON object):**
```json
{
  "name": "Alice",
  "age": 30,
  "email": "alice@example.com"
}
```

**Request (JSON string):**
```json
"{\"name\": \"Bob\", \"age\": 25, \"email\": \"bob@example.com\"}"
```

Both formats work automatically!

### Parsing Nested String Fields

Parse complex nested structures:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from stringent import parse, ParsableModel

app = FastAPI()

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class Contact(BaseModel):
    name: str
    phone: str

class User(ParsableModel):
    id: int
    address: Address = parse('{street} | {city} | {zip_code}')
    contact: Contact = parse('{name} | {phone}')

@app.post("/users")
async def create_user(user: User):
    return {
        "id": user.id,
        "address": {
            "street": user.address.street,
            "city": user.address.city,
            "zip": user.address.zip_code
        },
        "contact": {
            "name": user.contact.name,
            "phone": user.contact.phone
        }
    }
```

**Request:**
```json
{
  "id": 1,
  "address": "123 Main St | NYC | 10001",
  "contact": "Alice | 555-0100"
}
```

## Query Parameters

### Parsing Query String Parameters

Parse complex query parameters using pattern matching:

```python
from fastapi import FastAPI, Query
from pydantic import BaseModel
from stringent import parse, ParsableModel

app = FastAPI()

class DateRange(BaseModel):
    start: str
    end: str

class SearchParams(ParsableModel):
    query: str
    date_range: DateRange = parse('{start} to {end}')
    limit: int = 10

@app.get("/search")
async def search(params: SearchParams = Query(...)):
    """Search with date range in query parameter."""
    return {
        "query": params.query,
        "start_date": params.date_range.start,
        "end_date": params.date_range.end,
        "limit": params.limit
    }
```

**Request:**
```
GET /search?query=python&date_range=2024-01-01 to 2024-12-31&limit=20
```

### Using Optional Fields

Handle optional query parameters:

```python
from typing import Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel
from stringent import parse, ParsableModel

app = FastAPI()

class Filter(BaseModel):
    category: str
    tags: Optional[str] = None

class SearchParams(ParsableModel):
    query: str
    filter: Filter = parse('{category} | {tags?}')

@app.get("/search")
async def search(params: SearchParams = Query(...)):
    result = {
        "query": params.query,
        "category": params.filter.category,
    }
    if params.filter.tags:
        result["tags"] = params.filter.tags
    return result
```

**Request:**
```
GET /search?query=python&filter=tech | tutorial
GET /search?query=python&filter=tech
```

## Path Parameters

### Parsing Path Parameters

Parse complex path parameters by accepting them as strings and parsing manually:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from stringent import parse, ParsableModel

app = FastAPI()

class UserInfo(BaseModel):
    name: str
    id: int

class UserPath(ParsableModel):
    _model_parse_pattern = "{name}-{id}"
    name: str
    id: int

@app.get("/users/{user_str}")
async def get_user(user_str: str):
    """Get user by name-id format."""
    user = UserPath.parse(user_str)
    return {
        "name": user.name,
        "id": user.id
    }
```

**Request:**
```
GET /users/Alice-123
```

## Pattern Chaining

Handle multiple input formats gracefully:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from stringent import parse, parse_json, ParsableModel

app = FastAPI()

class Info(BaseModel):
    name: str
    age: int
    city: str

class User(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}') | parse_json()
    email: str

@app.post("/users")
async def create_user(user: User):
    """Accepts info as pipe-separated string or JSON."""
    return {
        "id": user.id,
        "name": user.info.name,
        "age": user.info.age,
        "city": user.info.city,
        "email": user.email
    }
```

**Request (pipe-separated):**
```json
{
  "id": 1,
  "info": "Alice | 30 | NYC",
  "email": "alice@example.com"
}
```

**Request (JSON):**
```json
{
  "id": 1,
  "info": "{\"name\": \"Bob\", \"age\": 25, \"city\": \"Chicago\"}",
  "email": "bob@example.com"
}
```

## Regex Patterns for Validation

Use regex patterns for complex validation:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from stringent import parse_regex, ParsableModel

app = FastAPI()

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

class LogRequest(ParsableModel):
    log: LogEntry = parse_regex(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
    )

@app.post("/logs")
async def create_log(log_request: LogRequest):
    """Parse log entries from structured strings."""
    return {
        "timestamp": log_request.log.timestamp,
        "level": log_request.log.level,
        "message": log_request.log.message
    }
```

**Request:**
```json
{
  "log": "2024-01-15 [ERROR] Database connection failed"
}
```

## Error Handling

### Custom Error Responses

Handle parsing errors gracefully:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from stringent import parse, ParsableModel

app = FastAPI()

class Info(BaseModel):
    name: str
    age: int
    city: str

class User(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

@app.post("/users")
async def create_user(user: User):
    try:
        return {
            "id": user.id,
            "name": user.info.name,
            "age": user.info.age,
            "city": user.info.city,
            "email": user.email
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid input format",
                "errors": e.errors()
            }
        )
```

### Using Error Recovery

Use error recovery mode to get partial results:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from stringent import parse, ParsableModel, ParseResult

app = FastAPI()

class Info(BaseModel):
    name: str
    age: int
    city: str

class User(ParsableModel):
    _model_parse_pattern = "{id} | {name} | {age} | {city} | {email}"
    id: int
    name: str
    age: int
    city: str
    email: str

@app.post("/users")
async def create_user(user_string: str):
    """Create user with error recovery."""
    result = User.parse_with_recovery(user_string, strict=False)
    
    if result:
        # Success - result is a User instance
        return {
            "message": "User created successfully",
            "user": {
                "id": result.id,
                "name": result.name,
                "age": result.age,
                "city": result.city,
                "email": result.email
            }
        }
    else:
        # Partial success - result is a ParseResult
        return {
            "message": "Partial data parsed",
            "data": result.data,
            "errors": result.errors,
            "status": "partial"
        }
```

## Response Models

Use `ParsableModel` in response models for consistent formatting:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from stringent import parse, ParsableModel

app = FastAPI()

class Info(BaseModel):
    name: str
    age: int
    city: str

class UserResponse(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user and return in structured format."""
    # In real app, fetch from database
    return UserResponse(
        id=user_id,
        info="Alice | 30 | NYC",
        email="alice@example.com"
    )
```

## Real-World Example

Complete example with multiple endpoints:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from stringent import parse, parse_json, JsonParsableModel, ParsableModel
from typing import Optional

app = FastAPI(title="User API with Stringent")

# Models
class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class Contact(BaseModel):
    name: str
    phone: Optional[str] = None

class UserCreate(ParsableModel):
    """Accepts flexible input formats."""
    id: int
    address: Address = parse('{street} | {city} | {zip_code}')
    contact: Contact = parse('{name} | {phone?}')
    email: EmailStr

class UserResponse(JsonParsableModel):
    """Can serialize to JSON string if needed."""
    id: int
    address: dict
    contact: dict
    email: str

# In-memory storage
users_db = {}

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user with flexible address/contact formats."""
    user_data = {
        "id": user.id,
        "address": {
            "street": user.address.street,
            "city": user.address.city,
            "zip_code": user.address.zip_code
        },
        "contact": {
            "name": user.contact.name,
            "phone": user.contact.phone
        },
        "email": user.email
    }
    users_db[user.id] = user_data
    return UserResponse(**user_data)

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**users_db[user_id])

@app.get("/users")
async def list_users():
    """List all users."""
    return [UserResponse(**user) for user in users_db.values()]
```

**Create User Request:**
```json
{
  "id": 1,
  "address": "123 Main St | NYC | 10001",
  "contact": "Alice | 555-0100",
  "email": "alice@example.com"
}
```

**Create User Request (optional phone):**
```json
{
  "id": 2,
  "address": "456 Oak Ave | Chicago | 60601",
  "contact": "Bob",
  "email": "bob@example.com"
}
```

## Best Practices

1. **Use JsonParsableModel for JSON-heavy APIs** - Simplifies handling of JSON strings

2. **Chain patterns for flexibility** - Allow multiple input formats when appropriate

3. **Handle errors gracefully** - Use FastAPI's exception handling with ValidationError

4. **Document your API** - FastAPI automatically generates docs, but document expected string formats

5. **Use type hints** - Leverage Pydantic's type validation for better error messages

6. **Test edge cases** - Test with malformed strings, missing fields, etc.

7. **Consider error recovery** - Use `parse_with_recovery()` for APIs that need partial success

## Performance Considerations

- `stringent` parsing happens during Pydantic validation, which FastAPI already does
- Pattern compilation is cached, so repeated parsing is efficient
- For high-throughput APIs, consider caching parsed patterns
- JSON parsing with `JsonParsableModel` uses Pydantic's built-in JSON parser (very fast)

## See Also

- **[Basic Usage](basic-usage.md)** - Core parsing patterns
- **[JSON Parsing](json-parsing.md)** - JSON string parsing
- **[Regex Parsing](regex-parsing.md)** - Regex pattern matching
- **[Error Handling](error-handling.md)** - Error recovery and partial parsing
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)** - Official FastAPI docs


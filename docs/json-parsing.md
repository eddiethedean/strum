# JSON Parsing Guide

This guide covers automatic JSON parsing with `JsonParsableModel`, a specialized class that automatically parses JSON strings when creating model instances.

## Overview

`JsonParsableModel` extends `ParsableModel` to automatically detect and parse JSON strings. This is especially useful when working with APIs, message queues, or any system that sends data as JSON strings.

## Basic Usage

### Simple JSON Parsing

```python
from stringent import JsonParsableModel

class User(JsonParsableModel):
    name: str
    age: int
    email: str

# Automatically parses JSON string
json_str = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'
user = User.model_validate(json_str)

print(user.name)   # Alice
print(user.age)    # 30
print(user.email)  # alice@example.com
```

**Output:**
```
Alice
30
alice@example.com
```

### Using model_validate_json()

You can also use the explicit `model_validate_json()` method:

```python
user = User.model_validate_json(json_str)
```

Both methods work identically - `JsonParsableModel` automatically detects JSON strings in `model_validate()`.

## Combining with Pattern Parsing

`JsonParsableModel` works seamlessly with field-level parse patterns:

```python
from stringent import JsonParsableModel, parse
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class User(JsonParsableModel):
    id: int
    info: Info = parse("{name} | {age} | {city}")
    email: str

# JSON string with nested string that needs parsing
json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}'
user = User.model_validate(json_str)

print(f"{user.id}: {user.info.name} ({user.info.age}) in {user.info.city}")
```

**Output:**
```
1: Alice (30) in NYC
```

## Multiple Input Formats

`JsonParsableModel` handles multiple input formats:

```python
class User(JsonParsableModel):
    name: str
    age: int
    email: str

# JSON string
json_str = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'
user1 = User.model_validate(json_str)

# Dictionary
user2 = User.model_validate({"name": "Bob", "age": 25, "email": "bob@example.com"})

# Keyword arguments (normal Pydantic behavior)
user3 = User(name="Charlie", age=35, email="charlie@example.com")
```

All three approaches work seamlessly!

## When to Use JsonParsableModel

Use `JsonParsableModel` when:

- **API Integration** - Receiving JSON strings from HTTP APIs
- **Message Queues** - Processing JSON messages from RabbitMQ, Kafka, etc.
- **File Processing** - Reading JSON lines or JSON files
- **Webhooks** - Handling JSON payloads from webhook services
- **Database JSON Columns** - Working with JSON stored as strings

Use regular `ParsableModel` when:

- You need format string parsing only
- You want explicit control over when JSON parsing happens
- You're working primarily with dictionaries and keyword arguments

## Comparison with ParsableModel

### ParsableModel

```python
from stringent import ParsableModel

class User(ParsableModel):
    name: str
    age: int

# Must use explicit method for JSON
json_str = '{"name": "Alice", "age": 30}'
user = User.model_validate_json(json_str)  # Explicit method required
```

### JsonParsableModel

```python
from stringent import JsonParsableModel

class User(JsonParsableModel):
    name: str
    age: int

# Automatically detects JSON
json_str = '{"name": "Alice", "age": 30}'
user = User.model_validate(json_str)  # Automatically parses JSON!
```

## Error Handling

Invalid JSON strings will raise validation errors:

```python
from stringent import JsonParsableModel
from pydantic import ValidationError

class User(JsonParsableModel):
    name: str
    age: int

try:
    invalid_json = '{"name": "Alice"'  # Missing closing brace
    user = User.model_validate(invalid_json)
except ValidationError as e:
    print("Invalid JSON or data")
```

## Advanced Example: API Response Parsing

```python
from stringent import JsonParsableModel, parse
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class User(JsonParsableModel):
    id: int
    name: str
    email: str
    addresses: List[Address]

# Simulate API response
api_response = '''
{
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "addresses": [
        {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
        {"street": "456 Oak Ave", "city": "Boston", "zip_code": "02101"}
    ]
}
'''

user = User.model_validate(api_response)
print(f"{user.name} has {len(user.addresses)} addresses")
```

**Output:**
```
Alice has 2 addresses
```

## Best Practices

1. **Use for JSON-heavy workflows** - If you're primarily working with JSON strings, `JsonParsableModel` simplifies your code

2. **Combine with parse patterns** - Field-level parsing still works, so you can mix JSON with format strings

3. **Handle errors gracefully** - Always wrap JSON parsing in try/except blocks for production code

4. **Use type hints** - Leverage Pydantic's validation by using proper type annotations

## See Also

- **[Basic Usage](basic-usage.md)** - Field-level parsing and pattern chaining
- **[Advanced Patterns](advanced-patterns.md)** - Union types and complex scenarios
- **[API Reference](api-reference.md)** - Complete API documentation


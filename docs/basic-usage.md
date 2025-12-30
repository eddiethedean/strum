# Basic Usage Guide

This comprehensive guide covers the fundamental features of `stringent` with practical examples and real-world use cases. Learn how to parse strings into Pydantic models efficiently and effectively.

## Field-Level Parsing

The most common use case is parsing string values for specific fields in your model.

### Simple Pattern Matching

```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

# Parse a string into the nested Info model
data = {
    "id": 1,
    "info": "Alice | 30 | New York",
    "email": "alice@example.com"
}

record = Record(**data)
print(record.info.name)
print(record.info.age)
print(record.info.city)
```

**Output:**
```
Alice
30
New York
```

### Multiple Patterns (Chaining)

When your data might come in different formats, you can chain multiple patterns:

```python
class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
    email: str

# Both formats work
data1 = {"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}
data2 = {"id": 2, "info": "Bob 25 Chicago", "email": "bob@example.com"}

record1 = Record(**data1)  # Uses pipe-separated pattern
record2 = Record(**data2)  # Uses space-separated pattern
```

Patterns are tried in order until one succeeds.

### Handling Different Data Types

The parser automatically handles different input types:

```python
class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')

# Already a dict - no parsing needed
data1 = {"id": 1, "info": {"name": "Alice", "age": 30, "city": "NYC"}}

# String - will be parsed
data2 = {"id": 2, "info": "Bob | 25 | Chicago"}

record1 = Record(**data1)  # Works with dict
record2 = Record(**data2)   # Parses string automatically
```

## Parsing Entire Models

You can also parse an entire model instance from a single string using the `parse()` class method.

### Using Class-Defined Patterns

```python
class SimpleRecord(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int

# Parse using the class-defined pattern
record = SimpleRecord.parse('1 | Alice | 30')
print(record.id)
print(record.name)
print(record.age)
```

**Output:**
```
1
Alice
30
```

### Providing Pattern as Argument

```python
class SimpleRecord(ParsableModel):
    id: int
    name: str
    age: int

# Provide pattern as argument
record = SimpleRecord.parse('2 | Bob | 25', pattern='{id} | {name} | {age}')
```

### Nested Parsing

When parsing entire models, nested fields with parse patterns are automatically handled:

```python
class Info(BaseModel):
    name: str
    age: int
    city: str

class RecordWithNested(ParsableModel):
    _model_parse_pattern = '{id} || {info} || {email}'
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

# Parse - nested fields are automatically parsed
record = RecordWithNested.parse('1 || Alice | 30 | NYC || alice@example.com')
print(record.info.name)
print(record.info.age)
```

**Output:**
```
Alice
30
```

## JSON Parsing

### Parsing from JSON Strings

You can parse model instances directly from JSON strings:

```python
class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}'
record = Record.parse_json(json_str)
```

The `parse_json()` method is a convenience wrapper around Pydantic's `model_validate_json()`. Field-level parse patterns are automatically applied to string values in the JSON.

### Using JSON Parse Pattern

You can also use JSON parsing as a pattern option:

```python
from stringent import parse_json

class Record(ParsableModel):
    id: int
    info: Info = parse_json() | parse('{name} | {age} | {city}')
    email: str

# JSON string will be parsed
data = {"id": 1, "info": '{"name": "Alice", "age": 30, "city": "NYC"}', "email": "alice@example.com"}
record = Record(**data)
```

## Common Patterns

### Pipe-Separated Values

```python
pattern = parse('{name} | {age} | {city}')
```

### Space-Separated Values

```python
pattern = parse('{name} {age} {city}')
```

### Custom Delimiters

```python
pattern = parse('{name}:::{age}:::{city}')
```

### With Extra Spaces

The parser automatically handles extra whitespace:

```python
pattern = parse('{name} | {age} | {city}')
result = pattern.parse('  Alice  |  30  |  NYC  ')
# Result: {'name': 'Alice', 'age': '30', 'city': 'NYC'}
```

### Optional Fields

You can mark fields as optional in patterns using the `?` suffix:

```python
from typing import Optional
from stringent import parse, ParsableModel
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: Optional[int] = None
    city: str

class Record(ParsableModel):
    info: Info = parse('{name} | {age?} | {city}')

# Works with all fields
record1 = Record(info="Alice | 30 | NYC")
assert record1.info.age == 30

# Works with missing optional field
record2 = Record(info="Bob | NYC")
assert record2.info.age is None  # Optional field is None
```

**Important:** Fields marked as optional in patterns must be typed as `Optional[T]` or `T | None` in your Pydantic model.

## Error Handling

When parsing fails, Pydantic will raise a `ValidationError`:

```python
from pydantic import ValidationError

try:
    record = Record(**{"id": 1, "info": "Invalid format", "email": "test@example.com"})
except ValidationError as e:
    print(e)
```

**Output:**
```
1 validation error for Record
info
  Input should be a valid dictionary or instance of Info [type=model_type, input_value='Invalid format', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/model_type
```

If a string doesn't match any pattern in a chain, the last pattern's error will be raised, and Pydantic will handle the validation error.


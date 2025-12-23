# Getting Started

This guide will help you get started with `strum`, a library that makes it easy to parse strings into Pydantic models using pattern matching.

## Installation

Install `strum` using pip:

```bash
pip install strum
```

## Requirements

- Python 3.10 or higher
- Pydantic 2.0 or higher
- parse 1.20 or higher

## Quick Example

Here's a simple example to get you started:

```python
from pydantic import BaseModel, EmailStr
from strum import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: EmailStr

# Parse a string into the model
data = {
    "id": 1,
    "info": "Alice | 30 | New York",
    "email": "alice@example.com"
}

record = Record(**data)
print(record.info.name)
print(record.info.age)
```

**Output:**
```
Alice
30
```

## Key Concepts

### ParsePattern

A `ParsePattern` is created using the `parse()` function with a format string:

```python
from strum import parse

pattern = parse('{name} | {age} | {city}')
```

The format string uses the same syntax as Python's `str.format()` method, with field names in curly braces.

### ParsableModel

`ParsableModel` is a base class that extends Pydantic's `BaseModel` with automatic string parsing capabilities. When you define a field with a `ParsePattern`, the model will automatically parse string values using that pattern.

### Pattern Chaining

You can chain multiple patterns together using the `|` operator:

```python
info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

This allows the model to handle multiple string formats for the same field.

## Next Steps

- Read the [Basic Usage Guide](basic-usage.md) for detailed examples
- Check out [Advanced Patterns](advanced-patterns.md) for union types and more complex scenarios
- See the [API Reference](api-reference.md) for detailed documentation


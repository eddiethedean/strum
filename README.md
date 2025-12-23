# strum

Parse strings into Pydantic models using pattern matching.

## Installation

```bash
pip install strum
```

## Quick Start

```python
from pydantic import BaseModel, EmailStr
from typing import Literal
from strum import parse, parse_json, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse_json() | parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
    email: EmailStr
    status: Literal['Active', 'Inactive']

# Parse the data - handles dicts, strings, and JSON automatically
data = [
    {'id': 1, 'info': {'name': 'Alice', 'age': 30, 'city': 'New York'}, 'email': 'alice@example.com', 'status': 'Active'},
    {'id': 3, 'info': 'Charlie | 27 | Chicago', 'email': 'charlie@example.com', 'status': 'Active'},
    {'id': 5, 'info': 'Eve 35 Dallas', 'email': 'eve@example.com', 'status': 'Inactive'},
    {'id': 8, 'info': '{"name": "Joe", "age": 55, "city": "Tampa"}', 'email': 'joe@example.com', 'status': 'Active'},
]

for item in data:
    record = Record(**item)
    print(record)
```

**Output:**
```
id=1 info=Info(name='Alice', age=30, city='New York') email='alice@example.com' status='Active'
id=3 info=Info(name='Charlie', age=27, city='Chicago') email='charlie@example.com' status='Active'
id=5 info=Info(name='Eve', age=35, city='Dallas') email='eve@example.com' status='Inactive'
id=8 info=Info(name='Joe', age=55, city='Tampa') email='joe@example.com' status='Active'
```

## Features

- Parse strings using format-like patterns (e.g., `{name} | {age} | {city}`)
- Chain multiple patterns using the `|` operator to try patterns in order
- Automatically handles both dictionary and string inputs
- Integrates seamlessly with Pydantic models
- Supports flexible spacing in patterns
- Union types for organizing parsing strategies
- JSON parsing support

## Documentation

Comprehensive documentation is available in the [docs directory](https://github.com/eddiethedean/strum/tree/main/docs):

- **[Getting Started](https://github.com/eddiethedean/strum/blob/main/docs/getting-started.md)** - Installation and basic concepts
- **[Basic Usage](https://github.com/eddiethedean/strum/blob/main/docs/basic-usage.md)** - Field-level parsing, pattern chaining, and common patterns
- **[Advanced Patterns](https://github.com/eddiethedean/strum/blob/main/docs/advanced-patterns.md)** - Union types, inheritance, and complex scenarios
- **[API Reference](https://github.com/eddiethedean/strum/blob/main/docs/api-reference.md)** - Complete API documentation
- **[Documentation Index](https://github.com/eddiethedean/strum/blob/main/docs/index.md)** - Overview and quick links

## Requirements

- Python 3.10+
- Pydantic 2.0+
- parse 1.20+

## Dependencies

- `pydantic>=2.0.0` - For Pydantic model integration
- `parse>=1.20.0` - For string parsing functionality

## License

MIT

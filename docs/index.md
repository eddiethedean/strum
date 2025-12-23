# strum Documentation

Welcome to the `strum` documentation! This library makes it easy to parse strings into Pydantic models using pattern matching.

## What is strum?

`strum` extends Pydantic models with automatic string parsing capabilities. It allows you to:

- Parse strings into nested Pydantic models using format patterns
- Chain multiple parsing patterns for flexible input handling
- Use union types with class-based parsing configurations
- Support JSON parsing alongside format string patterns

## Quick Start

```python
from pydantic import BaseModel
from strum import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: str

# Parse a string into the nested model
data = {"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}
record = Record(**data)
print(record.info.name)
```

**Output:**
```
Alice
```

## Documentation

- **[Getting Started](getting-started.md)** - Installation and basic concepts
- **[Basic Usage](basic-usage.md)** - Field-level parsing, pattern chaining, and common patterns
- **[Advanced Patterns](advanced-patterns.md)** - Union types, inheritance, and complex scenarios
- **[API Reference](api-reference.md)** - Complete API documentation

## Key Features

### Pattern Matching

Parse strings using format patterns similar to Python's `str.format()`:

```python
pattern = parse('{name} | {age} | {city}')
```

### Pattern Chaining

Chain multiple patterns to handle different input formats:

```python
info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

### Union Types

Define parsing strategies using union types:

```python
class PipeInfo(Info):
    _model_parse_pattern = '{name} | {age} | {city}'

class JsonInfo(Info):
    _json_parse = True

class Record(ParsableModel):
    info: Union[JsonInfo, PipeInfo]
```

### JSON Support

Parse JSON strings alongside format patterns:

```python
class Record(ParsableModel):
    info: Info = parse_json() | parse('{name} | {age} | {city}')
```

## Examples

See the [Basic Usage Guide](basic-usage.md) for detailed examples, or check out the [Advanced Patterns](advanced-patterns.md) guide for more complex scenarios.

## Requirements

- Python 3.10+
- Pydantic 2.0+
- parse 1.20+

## Installation

```bash
pip install strum
```

## Contributing

Contributions are welcome! Please see the project repository for contribution guidelines.

## License

MIT License - see LICENSE file for details.


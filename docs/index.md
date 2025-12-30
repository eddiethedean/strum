# stringent Documentation

Welcome to the `stringent` documentation! This library makes it easy to parse strings into Pydantic models using pattern matching.

## What is stringent?

`stringent` extends Pydantic models with automatic string parsing capabilities. It allows you to:

- Parse strings into nested Pydantic models using format patterns
- Chain multiple parsing patterns for flexible input handling
- Use union types with class-based parsing configurations
- Support JSON parsing alongside format string patterns

## Quick Start

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

### Getting Started
- **[Getting Started](getting-started.md)** - Installation, quick start, and key concepts

### Core Guides
- **[Basic Usage](basic-usage.md)** - Field-level parsing, pattern chaining, and common patterns
- **[JSON Parsing](json-parsing.md)** - Automatic JSON parsing with JsonParsableModel
- **[Regex Parsing](regex-parsing.md)** - Parse strings using regular expressions with named groups
- **[Error Handling](error-handling.md)** - Error recovery and partial parsing
- **[Advanced Patterns](advanced-patterns.md)** - Union types, inheritance, and complex scenarios

### Integration Guides
- **[FastAPI Integration](fastapi-integration.md)** - Using stringent with FastAPI

### User Guides
- **[Migration Guide](user-guides/migration-guide.md)** - Migrating from other libraries or upgrading versions
- **[Best Practices](user-guides/best-practices.md)** - Tips, patterns, and recommendations
- **[Troubleshooting](user-guides/troubleshooting.md)** - Common issues and solutions

### Reference
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

### JsonParsableModel

Automatic JSON string parsing for models:

```python
from stringent import JsonParsableModel

class User(JsonParsableModel):
    name: str
    age: int

# Automatically parses JSON strings
json_str = '{"name": "Alice", "age": 30}'
user = User.model_validate(json_str)
```

### Regex Patterns

Parse strings using regular expressions:

```python
from stringent import parse_regex, ParsableModel
from pydantic import BaseModel

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

class Record(ParsableModel):
    entry: LogEntry = parse_regex(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
    )
```

### Error Recovery

Collect errors and get partial results:

```python
from stringent import ParsableModel, ParseResult

class Record(ParsableModel):
    _model_parse_pattern = "{name} | {age} | {city}"
    name: str
    age: int
    city: str

result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
if not result:
    print("Partial data:", result.data)
    print("Errors:", result.errors)
```

## Examples

See the [Basic Usage Guide](basic-usage.md) for detailed examples, or check out the [Advanced Patterns](advanced-patterns.md) guide for more complex scenarios.

## Requirements

- Python 3.10+
- Pydantic 2.0+
- formatparse 0.6.0+

## Installation

```bash
pip install stringent
```

## Contributing

Contributions are welcome! Please see the project repository for contribution guidelines.

## License

MIT License - see LICENSE file for details.


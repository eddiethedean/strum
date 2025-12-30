# Quick Reference

A quick reference guide for common `stringent` patterns and usage.

## Pattern Syntax

### Basic Patterns

```python
# Pipe-separated
parse('{name} | {age} | {city}')

# Space-separated
parse('{name} {age} {city}')

# Custom delimiter
parse('{id}:::{name}:::{status}')

# With optional field
parse('{name} | {age?} | {city}')
```

### Pattern Chaining

```python
# Try multiple patterns in order
parse_json() | parse('{name} | {age}') | parse('{name} {age}')
```

### Regex Patterns

```python
from stringent import parse_regex

# Must use named groups
parse_regex(r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\]')
```

## Model Definitions

### Field-Level Parsing

```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')
```

### Model-Level Parsing

```python
class Record(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int
```

### JSON Parsing

```python
from pydantic import BaseModel
from stringent import parse_json, ParsableModel, JsonParsableModel

class Info(BaseModel):
    name: str
    age: int

# Field-level
class Record(ParsableModel):
    info: Info = parse_json()

# Model-level
class User(JsonParsableModel):
    name: str
    age: int
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

### CSV-like (Comma-Separated)

```python
pattern = parse('{name}, {age}, {city}')
```

### Key-Value Pairs

```python
pattern = parse('name: {name}, age: {age}, city: {city}')
```

### Log Format

```python
pattern = parse_regex(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
)
```

## Pattern Chaining Examples

### JSON with Fallback

```python
info: Info = parse_json() | parse('{name} | {age} | {city}')
```

### Multiple Delimiters

```python
info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

### JSON, Pipe, Space

```python
info: Info = parse_json() | parse('{name} | {age}') | parse('{name} {age}')
```

## Union Types

### Class-Based Parsing

```python
class PipeInfo(Info):
    _model_parse_pattern = '{name} | {age} | {city}'

class SpaceInfo(Info):
    _model_parse_pattern = '{name} {age} {city}'

class Record(ParsableModel):
    info: PipeInfo | SpaceInfo
```

### JSON with Pattern

```python
class JsonInfo(Info):
    _json_parse = True

class PipeInfo(Info):
    _model_parse_pattern = '{name} | {age} | {city}'

class Record(ParsableModel):
    info: JsonInfo | PipeInfo
```

## Error Handling

### Error Recovery

```python
from stringent import ParsableModel

class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age} | {city}'
    name: str
    age: int
    city: str

result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
if not result:
    print(result.errors)
    # Use partial data: result.data
```

### Validation with Recovery

```python
from stringent import ParsableModel

class Record(ParsableModel):
    name: str
    age: int

data = {"name": "Alice", "age": "invalid"}  # age should be int
result = Record.model_validate_with_recovery(data, strict=False)
if not result:
    # Handle errors: result.errors
    pass
```

## Common Methods

### Parsing

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

# Field-level (automatic)
record = Record(id=1, info="Alice | 30 | NYC")

# Model-level
class Record2(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int

record2 = Record2.parse("1 | Alice | 30")

# With explicit pattern
record3 = Record2.parse("1 | Alice | 30", pattern='{id} | {name} | {age}')

# JSON
record4 = Record2.parse_json('{"id": 1, "name": "Alice", "age": 30}')
```

### Pattern Usage

```python
# Create pattern
pattern = parse('{name} | {age}')

# Parse string
result = pattern.parse("Alice | 30")
# Returns: {'name': 'Alice', 'age': '30'}

# Chain patterns
chained = parse('{name} | {age}') | parse('{name} {age}')
result = chained.parse("Bob 25")
```

## Type Hints

### Required Fields

```python
class Info(BaseModel):
    name: str
    age: int
    city: str
```

### Optional Fields

```python
from typing import Optional

class Info(BaseModel):
    name: str
    age: Optional[int] = None
    city: str

# Pattern
pattern = parse('{name} | {age?} | {city}')
```

### Literal Types

```python
from typing import Literal

class Record(ParsableModel):
    status: Literal["Active", "Inactive"]
```

## Tips

- **Pattern order matters** - Most specific patterns first
- **Use delimiters** - Avoid ambiguous patterns
- **Optional fields** - Must match model type (`Optional[T]` or `T | None`)
- **Whitespace** - Automatically handled and stripped
- **Reuse patterns** - Compile once, use many times

## See Also

- [API Reference](../api-reference.md) - Complete API documentation
- [Best Practices](best-practices.md) - Detailed best practices
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Basic Usage](../basic-usage.md) - Detailed usage examples


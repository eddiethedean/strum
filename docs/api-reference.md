# API Reference

Complete reference documentation for `strum`.

## Core Functions

### `parse(pattern: str) -> ParsePattern`

Create a `ParsePattern` from a format string.

**Parameters:**
- `pattern` (str): Format string like `'{name} | {age} | {city}'` or `'{name} {age} {city}'`

**Returns:**
- `ParsePattern`: A pattern object that can parse strings matching the format

**Example:**
```python
from strum import parse

pattern = parse('{name} | {age} | {city}')
result = pattern.parse('Alice | 30 | NYC')
# Result: {'name': 'Alice', 'age': '30', 'city': 'NYC'}
```

### `parse_json() -> ParsePattern`

Create a pattern that parses JSON strings into dictionaries.

**Returns:**
- `ParsePattern`: A pattern object that parses JSON strings

**Example:**
```python
from strum import parse_json

pattern = parse_json()
result = pattern.parse('{"name": "Alice", "age": 30, "city": "NYC"}')
# Result: {'name': 'Alice', 'age': 30, 'city': 'NYC'}
```

## Classes

### `ParsePattern`

A pattern that can parse strings into dictionaries based on format strings.

#### Methods

##### `parse(value: str) -> Dict[str, Any]`

Parse a string value according to the pattern.

**Parameters:**
- `value` (str): String to parse

**Returns:**
- `Dict[str, Any]`: Dictionary with parsed values (with whitespace stripped)

**Raises:**
- `ValueError`: If the string doesn't match the pattern

**Example:**
```python
pattern = parse('{name} | {age}')
result = pattern.parse('Alice | 30')
# Result: {'name': 'Alice', 'age': '30'}
```

##### `__or__(other: ParsePattern) -> ChainedParsePattern`

Support `|` operator for chaining patterns.

**Parameters:**
- `other` (ParsePattern): Another pattern to chain

**Returns:**
- `ChainedParsePattern`: A chain of patterns that will be tried in order

**Example:**
```python
pattern1 = parse('{name} | {age}')
pattern2 = parse('{name} {age}')
chained = pattern1 | pattern2
```

### `ChainedParsePattern`

A chain of patterns that will be tried in order.

#### Methods

##### `parse(value: str) -> Dict[str, Any]`

Try each pattern in order until one succeeds.

**Parameters:**
- `value` (str): String to parse

**Returns:**
- `Dict[str, Any]`: Dictionary with parsed values

**Raises:**
- `ValueError`: If none of the patterns match

##### `__or__(other: Union[ParsePattern, ChainedParsePattern]) -> ChainedParsePattern`

Support chaining more patterns.

**Parameters:**
- `other`: Another pattern or chain to add

**Returns:**
- `ChainedParsePattern`: A new chain with the additional pattern(s)

### `ParsableModel`

Base model class that supports parse patterns in field definitions. Extends Pydantic's `BaseModel`.

#### Class Attributes

##### `_model_parse_pattern`

Optional class attribute defining a format string pattern for parsing entire model instances.

**Example:**
```python
class Record(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int
```

##### `_json_parse`

Optional class attribute (boolean) that enables JSON parsing for the class.

**Example:**
```python
class JsonRecord(ParsableModel):
    _json_parse = True
    name: str
    age: int
```

#### Class Methods

##### `parse(value: str, pattern: str = None) -> ParsableModel`

Parse a string into a model instance.

**Parameters:**
- `value` (str): String to parse
- `pattern` (str, optional): Format string pattern. If not provided, uses `_model_parse_pattern` if defined, otherwise raises `ValueError`.

**Returns:**
- `ParsableModel`: Instance of the model class

**Raises:**
- `ValueError`: If pattern is not provided and `_model_parse_pattern` is not defined, or if the string doesn't match the pattern.

**Example:**
```python
class Record(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int

record = Record.parse('1 | Alice | 30')
```

##### `parse_json(value: str) -> ParsableModel`

Parse a JSON string into a model instance.

**Parameters:**
- `value` (str): JSON string to parse

**Returns:**
- `ParsableModel`: Instance of the model class

**Raises:**
- `ValidationError`: If the string is not valid JSON or doesn't match the model schema

**Example:**
```python
class Record(ParsableModel):
    id: int
    name: str
    age: int

json_str = '{"id": 1, "name": "Alice", "age": 30}'
record = Record.parse_json(json_str)
```

**Note:** This method uses Pydantic's `model_validate_json()` internally. You can also use `Record.model_validate_json(json_str)` directly.

#### Model Validators

The `ParsableModel` class includes a `model_validator` that automatically:

1. Parses string values for fields with `ParsePattern` or `ChainedParsePattern` definitions
2. Handles union types of `ParsableModel` subclasses
3. Applies `_json_parse` and `_model_parse_pattern` configurations

This validator runs in `mode="before"`, so parsing happens before Pydantic's validation.

## Union Type Support

When a field has a union type of `ParsableModel` subclasses, the validator automatically:

1. Detects the union type
2. Tries each type in order
3. For each type, checks:
   - `_json_parse = True` flag (tries JSON parsing first)
   - `_model_parse_pattern` (tries format string parsing)
4. Uses the first successful parse result

**Example:**
```python
from typing import Union

class Info(ParsableModel):
    name: str
    age: int

class PipeInfo(Info):
    _model_parse_pattern = '{name} | {age}'

class JsonInfo(Info):
    _json_parse = True

class Record(ParsableModel):
    info: Union[JsonInfo, PipeInfo]

# Automatically tries JsonInfo first, then PipeInfo
record = Record(**{"info": '{"name": "Alice", "age": 30}'})
```

## Error Handling

### ParsePattern Errors

When a `ParsePattern` fails to match a string, it raises `ValueError`:

```python
try:
    pattern = parse('{name} | {age}')
    result = pattern.parse('Invalid format')
except ValueError as e:
    print(f"Parse error: {e}")
```

### Validation Errors

When model validation fails (including parsing failures), Pydantic raises `ValidationError`:

```python
from pydantic import ValidationError

try:
    record = Record(**{"info": "Invalid format"})
except ValidationError as e:
    print(e)
```

## Type Hints

All classes and functions are fully typed. The library uses:

- `typing.Union` for union types (Python 3.8+)
- `A | B` syntax supported in Python 3.10+ (but `Union[A, B]` works everywhere)
- Standard Pydantic type hints for model fields


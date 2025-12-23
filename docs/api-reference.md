# API Reference

Complete reference documentation for `stringent`.

## Core Functions

### `parse(pattern: str) -> ParsePattern`

Create a `ParsePattern` from a format string.

**Parameters:**
- `pattern` (str): Format string like `'{name} | {age} | {city}'` or `'{name} {age} {city}'`

**Returns:**
- `ParsePattern`: A pattern object that can parse strings matching the format

**Example:**
```python
from stringent import parse

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
from stringent import parse_json

pattern = parse_json()
result = pattern.parse('{"name": "Alice", "age": 30, "city": "NYC"}')
# Result: {'name': 'Alice', 'age': 30, 'city': 'NYC'}
```

### `parse_regex(pattern: str) -> ParsePattern`

Create a pattern that parses strings using regular expressions with named groups.

**Parameters:**
- `pattern` (str): Regular expression pattern with named groups (e.g., `r'(?P<name>\w+)'`)

**Returns:**
- `ParsePattern`: A pattern object that parses strings using regex

**Raises:**
- `ValueError`: If the pattern doesn't contain named groups or is invalid regex

**Example:**
```python
from stringent import parse_regex

pattern = parse_regex(r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)')
result = pattern.parse("2024-01-15 [ERROR] Database connection failed")
# Result: {'timestamp': '2024-01-15', 'level': 'ERROR', 'message': 'Database connection failed'}
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
- `Dict[str, Any]`: Dictionary with parsed values (with whitespace stripped). Optional fields that are missing will not be included in the result.

**Raises:**
- `ValueError`: If the string doesn't match the pattern
- `TypeError`: If value is not a string

**Example:**
```python
pattern = parse('{name} | {age}')
result = pattern.parse('Alice | 30')
# Result: {'name': 'Alice', 'age': '30'}

# With optional field
pattern_optional = parse('{name} | {age?} | {city}')
result2 = pattern_optional.parse('Bob | NYC')
# Result: {'name': 'Bob', 'city': 'NYC'}  # age is missing (optional)
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

##### `parse_with_recovery(value: str, pattern: str = None, strict: bool = False) -> ParsableModel | ParseResult`

Parse a string into a model instance with error recovery.

**Parameters:**
- `value` (str): String to parse
- `pattern` (str, optional): Format string pattern. If not provided, uses `_model_parse_pattern` if defined.
- `strict` (bool): If `True`, raises errors immediately. If `False`, returns `ParseResult` with errors.

**Returns:**
- `ParsableModel`: Instance of the model class if `strict=True` and parsing succeeds
- `ParseResult`: Object containing parsed data and errors if `strict=False`

**Raises:**
- `ValueError`: If pattern is not provided and `_model_parse_pattern` is not defined
- `ValidationError`: If `strict=True` and parsing fails

**Example:**
```python
class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age} | {city}'
    name: str
    age: int
    city: str

# Recovery mode
result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
if not result:
    print("Partial data:", result.data)
    print("Errors:", result.errors)
```

##### `model_validate_with_recovery(data: Any, strict: bool = False) -> ParsableModel | ParseResult`

Validate data with error recovery.

**Parameters:**
- `data` (Any): Data to validate (dict, string, etc.)
- `strict` (bool): If `True`, raises errors immediately. If `False`, returns `ParseResult` with errors.

**Returns:**
- `ParsableModel`: Instance of the model class if `strict=True` and validation succeeds
- `ParseResult`: Object containing parsed data and errors if `strict=False`

**Raises:**
- `ValidationError`: If `strict=True` and validation fails

**Example:**
```python
result = Record.model_validate_with_recovery(
    {"name": "Alice", "age": "invalid", "city": "NYC"},
    strict=False
)
if not result:
    print("Errors:", result.errors)
```

### `JsonParsableModel`

A `ParsableModel` subclass that automatically parses JSON strings when instantiated. Extends `ParsableModel` with automatic JSON detection.

#### Class Methods

##### `from_json(json_str: str) -> JsonParsableModel`

Parse a JSON string into a model instance. This is a convenience method that explicitly indicates JSON parsing intent.

**Parameters:**
- `json_str` (str): JSON string to parse

**Returns:**
- `JsonParsableModel`: Instance of the model class

**Raises:**
- `ValidationError`: If the string is not valid JSON or doesn't match the model schema

**Example:**
```python
from stringent import JsonParsableModel

class User(JsonParsableModel):
    name: str
    age: int
    email: str

json_str = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'
user = User.from_json(json_str)
```

**Note:** This method is equivalent to `User.model_validate(json_str)`. `JsonParsableModel` automatically detects JSON strings in `model_validate()`, so all three methods work identically:
- `User.model_validate(json_str)`
- `User.model_validate_json(json_str)`
- `User.from_json(json_str)`

### `ParseResult`

A dataclass that holds parsed data and errors when using error recovery mode.

#### Attributes

- `data` (dict[str, Any]): Successfully parsed data
- `errors` (list[dict[str, Any]]): List of errors encountered during parsing

Each error in the `errors` list contains:
- `field` (str): The field path where the error occurred
- `error` (str): Error message describing what went wrong
- `type` (str): Error type (e.g., "validation_error", "pattern_error")
- `input` (Any): The input value that caused the error (if available)

#### Methods

##### `__bool__() -> bool`

Return `True` if parsing was successful (no errors), `False` otherwise.

**Example:**
```python
result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
if not result:  # Has errors
    print("Partial data:", result.data)
    print("Errors:", result.errors)
```

#### Model Validators

The `JsonParsableModel` class includes a `model_validator` that automatically:

1. Detects JSON strings in the input (strings starting with `{`)
2. Parses JSON strings into dictionaries before validation
3. Falls back to parent `ParsableModel` behavior for non-JSON strings
4. Works seamlessly with field-level parse patterns

This validator runs in `mode="before"`, before the parent class's `_parse_string_fields` validator, so JSON parsing happens at the model level while field-level parsing happens afterward.

**Example:**
```python
from stringent import JsonParsableModel, parse
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int

class User(JsonParsableModel):
    id: int
    info: Info = parse("{name} | {age}")
    email: str

# Top-level JSON string is automatically parsed
# Field-level pattern parsing still works for nested strings
json_str = '{"id": 1, "info": "Alice | 30", "email": "alice@example.com"}'
user = User.model_validate(json_str)
```

## Model Validators

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

**Output:**
```
Parse error: String 'Invalid format' does not match pattern '{name} | {age}'
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

**Output:**
```
2 validation errors for Record
info.JsonInfo
  Input should be a valid dictionary or instance of JsonInfo [type=model_type, input_value='Invalid format', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/model_type
info.PipeInfo
  Input should be a valid dictionary or instance of PipeInfo [type=model_type, input_value='Invalid format', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/model_type
```

## Type Hints

All classes and functions are fully typed. The library uses:

- `typing.Union` for union types (Python 3.8+)
- `A | B` syntax supported in Python 3.10+ (but `Union[A, B]` works everywhere)
- Standard Pydantic type hints for model fields


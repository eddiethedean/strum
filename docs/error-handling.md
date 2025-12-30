# Error Handling Guide

This comprehensive guide covers error handling and recovery modes in `stringent`. Learn how to gracefully handle parsing errors, collect partial results, and provide better user feedback when validation fails.

## Overview

By default, `stringent` raises validation errors immediately when parsing fails. However, you can enable **error recovery mode** to collect errors and return partial results, allowing you to process valid data even when some fields fail validation.

## Default Behavior (Strict Mode)

In strict mode (the default), parsing errors raise `ValidationError` immediately:

```python
from stringent import ParsableModel, parse
from pydantic import BaseModel, ValidationError

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')

# Raises ValidationError immediately
try:
    record = Record(info="Alice | invalid | NYC")
except ValidationError as e:
    print("Validation failed:", e)
```

## Error Recovery Mode

### Using parse_with_recovery()

The `parse_with_recovery()` method allows you to collect errors instead of raising them:

```python
from stringent import ParsableModel, ParseResult, parse
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    _model_parse_pattern = "{name} | {age} | {city}"
    name: str
    age: int
    city: str

# Recovery mode - returns ParseResult
result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)

if result:
    # No errors - result is a Record instance
    print(f"Parsed: {result.name}")
else:
    # Has errors - result is a ParseResult
    print(f"Partial data: {result.data}")
    print(f"Errors: {result.errors}")
```

### ParseResult Structure

When `strict=False`, `parse_with_recovery()` returns a `ParseResult` object:

```python
from stringent import ParseResult

# ParseResult has two attributes:
# - data: dict[str, Any] - Successfully parsed data
# - errors: list[dict[str, Any]] - List of errors encountered
```

The `ParseResult` is falsy when there are errors, truthy when parsing succeeded:

```python
result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)

if not result:  # Has errors
    print(f"Successfully parsed: {result.data}")
    for error in result.errors:
        print(f"Field: {error['field']}, Error: {error['error']}")
```

### Error Information

Each error in the `errors` list contains:

- `field`: The field path where the error occurred (e.g., "age" or "info.name")
- `error`: Error message describing what went wrong
- `type`: Error type (e.g., "validation_error", "pattern_error")
- `input`: The input value that caused the error (if available)

```python
result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)

for error in result.errors:
    print(f"Field: {error.get('field')}")
    print(f"Error: {error.get('error')}")
    print(f"Type: {error.get('type')}")
    print(f"Input: {error.get('input')}")
```

## Using model_validate_with_recovery()

For model-level validation with error recovery:

```python
class Record(ParsableModel):
    name: str
    age: int
    city: str
    info: Info = parse('{name} | {age} | {city}')

# Recovery mode
result = Record.model_validate_with_recovery(
    {"name": "Alice", "age": "invalid", "city": "NYC", "info": "Bob | invalid | Chicago"},
    strict=False
)

if not result:
    print("Partial data:", result.data)
    print("Errors:", len(result.errors), "errors found")
    for error in result.errors:
        print(f"  - {error['field']}: {error['error']}")
```

## Real-World Examples

### Processing Batch Data

When processing multiple records, error recovery allows you to continue processing valid records:

```python
from stringent import ParsableModel, ParseResult

class Record(ParsableModel):
    _model_parse_pattern = "{name} | {age} | {city}"
    name: str
    age: int
    city: str

records_data = [
    "Alice | 30 | NYC",
    "Bob | invalid | Chicago",  # Invalid age
    "Charlie | 35 | Boston",
    "David | not_a_number | Seattle",  # Invalid age
]

valid_records = []
errors = []

for data in records_data:
    result = Record.parse_with_recovery(data, strict=False)
    if result:
        valid_records.append(result)
    else:
        errors.append({
            "input": data,
            "errors": result.errors
        })

print(f"Processed {len(valid_records)} valid records")
print(f"Found {len(errors)} records with errors")
```

### Partial Data Extraction

Extract what you can from malformed data:

```python
class ComplexRecord(ParsableModel):
    _model_parse_pattern = "{id} | {name} | {age} | {email} | {city}"
    id: int
    name: str
    age: int
    email: str
    city: str

malformed_data = "1 | Alice | invalid_age | alice@example.com | NYC"

result = ComplexRecord.parse_with_recovery(malformed_data, strict=False)

if not result:
    # Extract valid fields
    valid_id = result.data.get("id")
    valid_name = result.data.get("name")
    valid_email = result.data.get("email")
    valid_city = result.data.get("city")
    
    print(f"Extracted: {valid_name} ({valid_email}) in {valid_city}")
    print(f"Failed to parse: age")
```

### Error Reporting

Collect detailed error information for logging or user feedback:

```python
def process_with_error_reporting(data: str) -> dict:
    """Process data and return detailed error report."""
    result = Record.parse_with_recovery(data, strict=False)
    
    if result:
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else result.data
        }
    else:
        return {
            "success": False,
            "partial_data": result.data,
            "errors": [
                {
                    "field": err["field"],
                    "message": err["error"],
                    "type": err.get("type", "unknown")
                }
                for err in result.errors
            ],
            "error_count": len(result.errors)
        }
```

## Strict vs Recovery Mode

### When to Use Strict Mode (default)

- **Production validation** - When data must be completely valid
- **API endpoints** - When you need to reject invalid requests immediately
- **Data import** - When partial data could cause issues downstream

```python
from stringent import ParsableModel
from pydantic import ValidationError

class Record(ParsableModel):
    _model_parse_pattern = "{name} | {age} | {city}"
    name: str
    age: int
    city: str

# Strict mode - fail fast (default behavior)
try:
    record = Record.parse("Alice | invalid | NYC")
except ValidationError:
    # Handle error immediately
    pass  # In real code, return error response
```

### When to Use Recovery Mode

- **Data cleaning** - When you want to extract valid data from messy inputs
- **Log processing** - When some log entries may be malformed
- **User input** - When you want to show users what was successfully parsed
- **Batch processing** - When you want to process valid records and report errors

```python
from stringent import ParsableModel

class Record(ParsableModel):
    _model_parse_pattern = "{name} | {age} | {city}"
    name: str
    age: int
    city: str

# Recovery mode - collect errors
result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
if not result:
    # Process partial data and report errors
    print("Partial data:", result.data)
    print("Errors:", result.errors)
```

## Combining with Pattern Chaining

Error recovery works with pattern chaining - if one pattern fails, others are tried:

```python
from stringent import parse_json, parse

class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}') | parse_json()

# If pipe-separated pattern fails, tries JSON
# Error recovery collects errors from all failed attempts
result = Record.model_validate_with_recovery(
    {"info": "invalid format"},
    strict=False
)
```

## Best Practices

1. **Use strict mode by default** - Only use recovery mode when you specifically need partial results

2. **Validate error data** - Even in recovery mode, validate that partial data is usable

3. **Log errors** - Always log errors collected in recovery mode for debugging

4. **User feedback** - Use error information to provide helpful feedback to users

5. **Error thresholds** - Consider rejecting data if too many fields fail validation

6. **Type safety** - Remember that partial data may not match your model structure

## See Also

- **[Basic Usage](basic-usage.md)** - Basic parsing and validation
- **[Advanced Patterns](advanced-patterns.md)** - Complex parsing scenarios
- **[API Reference](api-reference.md)** - Complete API documentation


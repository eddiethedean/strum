# Troubleshooting Guide

Common issues and solutions when using `stringent`.

## Pattern Matching Issues

### Pattern Not Matching

**Symptom:** `ValueError: String '...' does not match pattern '...'`

**Possible Causes:**

1. **Pattern syntax error**

```python
# Wrong: Missing closing brace
pattern = parse('{name | {age}')

# Correct
pattern = parse('{name} | {age}')
```

2. **Field name mismatch**

```python
# Pattern expects 'name' but model has 'user_name'
from pydantic import BaseModel
from stringent import parse

pattern = parse('{name} | {age}')
class Info(BaseModel):
    user_name: str  # Mismatch!
```

3. **Delimiter mismatch**

```python
from stringent import parse

# Pattern uses '|' but data uses spaces
pattern = parse('{name} | {age}')
data = "Alice 30"  # No pipe separator

# Solution: Use pattern chaining
pattern = parse('{name} | {age}') | parse('{name} {age}')
```

**Solution:**
- Check pattern syntax carefully
- Ensure field names match model fields
- Use pattern chaining for multiple formats
- Test pattern standalone: `pattern.parse("test string")`

### Optional Fields Not Working

**Symptom:** Optional field still required or not parsed correctly

**Problem:**
```python
pattern = parse('{name} | {age?} | {city}')
# But model doesn't allow None
class Info(BaseModel):
    name: str
    age: int  # Not Optional!
    city: str
```

**Solution:**
```python
from typing import Optional

class Info(BaseModel):
    name: str
    age: Optional[int] = None  # Must be Optional
    city: str
```

## Validation Errors

### Type Conversion Errors

**Symptom:** `ValidationError: Input should be a valid integer`

**Problem:**
```python
class Info(BaseModel):
    age: int

pattern = parse('{name} | {age}')
result = pattern.parse("Alice | thirty")  # "thirty" can't convert to int
```

**Solution:**
```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int

# Pattern returns strings - Pydantic handles conversion
# Ensure input data is valid
pattern = parse('{name} | {age}')
result = pattern.parse("Alice | 30")  # "30" can convert to int
info = Info(**result)

# Or use error recovery
class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age}'
    name: str
    age: int

result = Record.parse_with_recovery("Alice | thirty", strict=False)
if not result:
    # Handle error
    print(result.errors)
```

### Missing Required Fields

**Symptom:** `ValidationError: Field required`

**Problem:**
```python
from pydantic import BaseModel
from stringent import parse

class Info(BaseModel):
    name: str
    age: int
    city: str

pattern = parse('{name} | {age}')  # Missing city
result = pattern.parse("Alice | 30")
# info = Info(**result)  # Error: city missing
```

**Solution:**
```python
# Include all required fields in pattern
pattern = parse('{name} | {age} | {city}')

# Or make field optional
class Info(BaseModel):
    name: str
    age: int
    city: Optional[str] = None

pattern = parse('{name} | {age} | {city?}')
```

## Import Errors

### ModuleNotFoundError: No module named 'formatparse'

**Solution:**
```bash
pip install formatparse>=0.6.0
```

### ImportError with _formatparse

**Problem:** Code tries to import `_formatparse` directly

**Solution:**
```python
# Don't import _formatparse directly
# import _formatparse  # Wrong!

# Use stringent's public API
from stringent import parse, ParsableModel  # Correct
```

## Performance Issues

### Slow Parsing

**Problem:** Parsing is slower than expected

**Possible Causes:**

1. **Recompiling patterns**

```python
from stringent import parse

# Bad: Recompiles every time
records = ["Alice | 30", "Bob | 25"]
for data in records:
    pattern = parse('{name} | {age}')  # Recompiles!
    result = pattern.parse(data)
```

2. **Too many pattern variations**

```python
from stringent import parse

# Bad: Too many patterns to try
pattern = parse('{name} | {age}') | parse('{name} {age}') | parse('{name}, {age}') | parse('name: {name}') | parse('age: {age}')
```

**Solution:**
```python
# Good: Compile once
class Record(ParsableModel):
    info: Info = parse('{name} | {age}')  # Compiled once

# Good: Limit pattern chain
pattern = parse_json() | parse('{name} | {age}') | parse('{name} {age}')
```

## Regex Pattern Issues

### Regex Not Matching

**Symptom:** `ValueError: String '...' does not match regex pattern`

**Problem:**
```python
from stringent import parse_regex

# Pattern uses search() but regex uses match()
pattern = parse_regex(r'(?P<name>\w+)')
result = pattern.parse("  Alice")  # Leading space causes failure
```

**Solution:**
```python
from stringent import parse_regex

# Regex uses match() - must match from start
# Include optional whitespace in pattern
pattern = parse_regex(r'\s*(?P<name>\w+)\s*')

# Or trim input manually
result = pattern.parse("  Alice".strip())
```

### Missing Named Groups

**Symptom:** `ValueError: Regex pattern must contain named groups`

**Problem:**
```python
from stringent import parse_regex

# No named groups - this will raise ValueError
# pattern = parse_regex(r'(\w+) (\d+)')  # Unnamed groups
```

**Solution:**
```python
from stringent import parse_regex

# Use named groups
pattern = parse_regex(r'(?P<name>\w+) (?P<age>\d+)')
result = pattern.parse("Alice 30")  # Works correctly
```

## Model Definition Issues

### Pattern Not Applied

**Symptom:** String not parsed, passed through as-is

**Problem:**
```python
# Wrong: Not using ParsableModel
class Record(BaseModel):  # Should be ParsableModel!
    info: Info = parse('{name} | {age}')
```

**Solution:**
```python
# Correct: Use ParsableModel
class Record(ParsableModel):
    info: Info = parse('{name} | {age}')
```

### Inheritance Issues

**Problem:** Child class doesn't inherit patterns

**Solution:**
```python
# Patterns are inherited automatically
class BaseRecord(ParsableModel):
    info: Info = parse('{name} | {age}')

class DerivedRecord(BaseRecord):
    extra: str
    # info pattern is inherited automatically
```

## JSON Parsing Issues

### JSON Not Parsing

**Symptom:** JSON string not recognized

**Problem:**
```python
# JSON string not starting with '{'
json_str = '  {"name": "Alice"}'  # Leading whitespace
```

**Solution:**
```python
from stringent import JsonParsableModel, parse_json, ParsableModel
from pydantic import BaseModel

# JsonParsableModel handles this automatically
class User(JsonParsableModel):
    name: str

# Or use parse_json() pattern
class Info(BaseModel):
    name: str
    age: int

class Record(ParsableModel):
    info: Info = parse_json() | parse('{name} | {age}')
```

### JSON Array Instead of Object

**Symptom:** `ValueError: JSON value must be an object`

**Problem:**
```python
from stringent import parse_json
import json

pattern = parse_json()
# This will raise ValueError: JSON value must be an object
# result = pattern.parse('[{"name": "Alice"}]')  # Array, not object
```

**Solution:**
```python
from stringent import ParsableModel
import json

class Record(ParsableModel):
    name: str

# parse_json() only supports objects
# For arrays, parse manually or use different approach
data = json.loads('[{"name": "Alice"}]')
for item in data:
    record = Record(**item)
```

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed parsing information
```

### Test Pattern Standalone

```python
# Test pattern before using in model
pattern = parse('{name} | {age}')
try:
    result = pattern.parse("Alice | 30")
    print("Pattern works:", result)
except ValueError as e:
    print("Pattern error:", e)
```

### Use Error Recovery

```python
from stringent import ParsableModel

class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age} | {city}'
    name: str
    age: int
    city: str

# Get detailed error information
input_string = "Alice | invalid | NYC"
result = Record.parse_with_recovery(input_string, strict=False)
if not result:
    for error in result.errors:
        print(f"Field: {error['field']}")
        print(f"Error: {error['error']}")
        print(f"Type: {error['type']}")
```

### Check Pattern Compilation

```python
# Verify pattern compiles
try:
    pattern = parse('{name} | {age}')
    print("Pattern compiled successfully")
except Exception as e:
    print(f"Pattern compilation failed: {e}")
```

## Getting Help

If you're still stuck:

1. **Check the documentation:**
   - [API Reference](../api-reference.md)
   - [Basic Usage](../basic-usage.md)
   - [Examples](../getting-started.md)

2. **Review error messages:**
   - Pydantic validation errors are usually very descriptive
   - Pattern matching errors show the pattern and input

3. **Test with simple examples:**
   - Start with a minimal pattern
   - Gradually add complexity

4. **Open an issue:**
   - Include minimal reproducible example
   - Show error messages
   - Describe expected vs actual behavior

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `String '...' does not match pattern` | Pattern syntax or data format mismatch | Check pattern syntax, use pattern chaining |
| `Field required` | Missing required field | Add field to pattern or make optional |
| `Input should be a valid integer` | Type conversion failed | Ensure input can convert to target type |
| `Regex pattern must contain named groups` | Regex missing `(?P<name>...)` | Add named groups to regex |
| `No parse pattern provided` | Missing `_model_parse_pattern` | Define pattern or pass as argument |


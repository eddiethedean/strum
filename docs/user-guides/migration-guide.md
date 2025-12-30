# Migration Guide

This guide helps you migrate from other parsing libraries or upgrade from earlier versions of `stringent`.

## Migrating from `parse` library

If you're using the `parse` library directly and want to switch to `stringent`:

### Before (using `parse` directly)

```python
import parse

pattern = parse.compile('{name} | {age} | {city}')
result = pattern.parse("Alice | 30 | NYC")
data = result.named
```

### After (using `stringent`)

```python
from stringent import parse

pattern = parse('{name} | {age} | {city}')
result = pattern.parse("Alice | 30 | NYC")
# result is already a dict, no need for .named
data = result
```

**Key Differences:**
- `stringent.parse()` returns a `ParsePattern` directly (no need for `compile()`)
- `parse()` returns a dictionary directly (no `.named` attribute needed)
- Better integration with Pydantic models
- More features (pattern chaining, JSON parsing, regex support)

## Upgrading from stringent 0.3.x to 0.4.0

### Dependency Change

**Before:**
```toml
dependencies = [
    "pydantic>=2.0.0",
    "parse>=1.20.0",
]
```

**After:**
```toml
dependencies = [
    "pydantic>=2.0.0",
    "formatparse>=0.6.0",
]
```

### No Code Changes Required

The API remains the same! Your existing code will work without modifications:

```python
# This code works in both 0.3.x and 0.4.0
from stringent import parse, ParsableModel
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int

class Record(ParsableModel):
    info: Info = parse('{name} | {age}')

record = Record(info="Alice | 30")
```

### Performance Improvements

Version 0.4.0 uses `formatparse` instead of `parse`, which provides:
- **1.6x faster** parsing performance
- Better concurrent performance
- Lower memory usage
- Same API compatibility

## Migrating from Manual Parsing

If you're currently doing manual string parsing, here's how to migrate:

### Before (Manual Parsing)

```python
def parse_record(data):
    if isinstance(data['info'], str):
        parts = data['info'].split(' | ')
        data['info'] = {
            'name': parts[0],
            'age': int(parts[1]),
            'city': parts[2]
        }
    return Record(**data)
```

### After (using stringent)

```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')

# Automatic parsing - no manual code needed!
data = {'info': 'Alice | 30 | NYC'}
record = Record(**data)
```

**Benefits:**
- Less code to maintain
- Automatic validation
- Type safety
- Support for multiple formats via chaining

## Migrating from Custom Parsers

If you have custom parsing logic:

### Before (Custom Parser)

```python
class CustomParser:
    def parse(self, text):
        # Complex parsing logic
        if text.startswith('{'):
            return json.loads(text)
        elif '|' in text:
            return self.parse_pipe(text)
        else:
            return self.parse_space(text)
```

### After (using stringent)

```python
from stringent import parse, parse_json, ParsableModel

class Record(ParsableModel):
    info: Info = parse_json() | parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

**Benefits:**
- Declarative syntax
- Automatic fallback
- Better error handling
- Type validation

## Common Migration Patterns

### Pattern 1: Multiple Format Support

**Before:**
```python
def parse_info(text):
    if '|' in text:
        return parse_pipe(text)
    elif ' ' in text and text.count(' ') >= 2:
        return parse_space(text)
    else:
        raise ValueError("Unknown format")
```

**After:**
```python
info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

### Pattern 2: JSON with Fallback

**Before:**
```python
def parse_info(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return parse_format_string(text)
```

**After:**
```python
info: Info = parse_json() | parse('{name} | {age} | {city}')
```

### Pattern 3: Optional Fields

**Before:**
```python
def parse_info(text):
    parts = text.split(' | ')
    result = {'name': parts[0]}
    if len(parts) > 1:
        result['age'] = parts[1]
    if len(parts) > 2:
        result['city'] = parts[2]
    return result
```

**After:**
```python
info: Info = parse('{name} | {age?} | {city}')
```

## Troubleshooting Migration

### Issue: "ModuleNotFoundError: No module named 'parse'"

**Solution:** Update your dependencies to use `formatparse`:

```bash
pip uninstall parse
pip install formatparse>=0.6.0
```

### Issue: Pattern not matching

**Solution:** Check that your pattern syntax is correct. Remember:
- Use `{field}` for required fields
- Use `{field?}` for optional fields
- Patterns are case-sensitive
- Whitespace is automatically handled

### Issue: Type errors after migration

**Solution:** Ensure you're using the correct types:

```python
# Correct
from stringent import parse, ParsableModel

# Incorrect (old import)
from parse import parse  # Wrong!
```

## Getting Help

If you encounter issues during migration:

1. Check the [API Reference](../api-reference.md) for correct usage
2. Review [Basic Usage](../basic-usage.md) examples
3. See [Error Handling](../error-handling.md) for debugging tips
4. Open an issue on [GitHub](https://github.com/eddiethedean/stringent/issues)


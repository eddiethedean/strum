# Best Practices

This guide covers best practices for using `stringent` effectively in your projects.

## Pattern Design

### Use Descriptive Field Names

**Good:**
```python
pattern = parse('{user_name} | {user_age} | {user_city}')
```

**Avoid:**
```python
pattern = parse('{a} | {b} | {c}')  # Unclear what fields represent
```

### Choose Appropriate Delimiters

**Good:**
```python
# Pipe separator for structured data
pattern = parse('{name} | {age} | {city}')

# Space separator for simple cases
pattern = parse('{first_name} {last_name}')

# Custom delimiter when needed
pattern = parse('{id}:::{name}:::{status}')
```

**Avoid:**
```python
# Using characters that might appear in data
pattern = parse('{name}:{age}:{city}')  # What if name contains ':'?
```

### Use Optional Fields Sparingly

**Good:**
```python
# Only mark truly optional fields
pattern = parse('{name} | {age?} | {city}')  # age is optional
```

**Avoid:**
```python
# Don't make everything optional
pattern = parse('{name?} | {age?} | {city?}')  # Hard to match anything
```

## Model Design

### Keep Patterns Close to Usage

**Good:**
```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')  # Pattern defined where used
```

**Avoid:**
```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

# Pattern defined far from usage
INFO_PATTERN = parse('{name} | {age} | {city}')

class Record(ParsableModel):
    info: Info = INFO_PATTERN  # Harder to understand context
```

### Use Type Hints

**Good:**
```python
from typing import Literal
from pydantic import EmailStr

class Record(ParsableModel):
    id: int
    email: EmailStr
    status: Literal["Active", "Inactive"]
```

**Avoid:**
```python
# Missing type hints - Pydantic requires type annotations
# This will raise an error:
# class Record(ParsableModel):
#     id = None  # Error: missing type annotation
#     email = None
#     status = None
```

## Pattern Chaining

### Order Matters

**Good:**
```python
# Most specific first, most general last
info: Info = parse_json() | parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

**Avoid:**
```python
# Vague pattern might match before specific one
info: Info = parse('{name} {age}') | parse('{name} | {age} | {city}')  # Wrong order
```

### Limit Chain Length

**Good:**
```python
# 2-3 patterns is usually enough
info: Info = parse_json() | parse('{name} | {age} | {city}')
```

**Avoid:**
```python
# Too many patterns can be confusing
info: Info = parse_json() | parse('...') | parse('...') | parse('...') | parse('...') | parse('...')
```

## Performance

### Reuse Compiled Patterns

**Good:**
```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

# Compile once, reuse many times
class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')

# Reuse the same model class
many_records = [
    {"info": "Alice | 30 | NYC"},
    {"info": "Bob | 25 | Chicago"},
]
for data in many_records:
    record = Record(**data)  # Pattern compiled once per class
```

**Avoid:**
```python
# Don't recompile patterns unnecessarily
for data in many_records:
    pattern = parse('{name} | {age} | {city}')  # Recompiles every time!
    result = pattern.parse(data['info'])
```

### Use Model-Level Patterns for Bulk Parsing

**Good:**
```python
from stringent import ParsableModel

class Record(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int

# Efficient for parsing many records
file_lines = ["1 | Alice | 30", "2 | Bob | 25", "3 | Charlie | 35"]
records = [Record.parse(line) for line in file_lines]
```

**Avoid:**
```python
from stringent import ParsableModel

class Record(ParsableModel):
    id: int
    name: str
    age: int

# Less efficient for bulk parsing
file_lines = ["1 | Alice | 30", "2 | Bob | 25"]
for line in file_lines:
    parts = line.split(' | ')
    record = Record(id=int(parts[0]), name=parts[1], age=int(parts[2]))
```

## Error Handling

### Use Error Recovery for User Input

**Good:**
```python
from stringent import ParsableModel

class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age} | {city}'
    name: str
    age: int
    city: str

user_input = "Alice | invalid | NYC"
result = Record.parse_with_recovery(user_input, strict=False)
if not result:
    # Show partial data and errors to user
    # show_errors(result.errors)
    # use_partial_data(result.data)
    pass
```

**Avoid:**
```python
from stringent import ParsableModel
from pydantic import ValidationError

class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age} | {city}'
    name: str
    age: int
    city: str

# Crashes on any error
user_input = "Alice | invalid | NYC"
try:
    record = Record.parse(user_input)
except ValidationError:
    # User sees generic error
    # show_error("Invalid input")
    pass
```

### Provide Clear Error Messages

**Good:**
```python
from pydantic import Field
from stringent import ParsableModel

class Record(ParsableModel):
    _model_parse_pattern = '{name} | {age} | {city}'
    name: str
    age: int = Field(description="Age in years")
    city: str
```

**Avoid:**
```python
# No context for errors
class Record(ParsableModel):
    _model_parse_pattern = '{a} | {b} | {c}'
    a: str
    b: int
    c: str
```

## Testing

### Test Pattern Matching

**Good:**
```python
def test_pattern_matching():
    pattern = parse('{name} | {age} | {city}')
    result = pattern.parse("Alice | 30 | NYC")
    assert result == {'name': 'Alice', 'age': '30', 'city': 'NYC'}
```

### Test Pattern Chaining

**Good:**
```python
def test_pattern_chaining():
    pattern = parse('{name} | {age}') | parse('{name} {age}')
    
    # Test first pattern
    assert pattern.parse("Alice | 30") == {'name': 'Alice', 'age': '30'}
    
    # Test second pattern
    assert pattern.parse("Bob 25") == {'name': 'Bob', 'age': '25'}
```

### Test Error Cases

**Good:**
```python
def test_invalid_input():
    pattern = parse('{name} | {age}')
    with pytest.raises(ValueError):
        pattern.parse("Invalid format")
```

## Documentation

### Document Your Patterns

**Good:**
```python
class Record(ParsableModel):
    """
    Record model for parsing user data.
    
    Supports two formats:
    - Pipe-separated: "name | age | city"
    - Space-separated: "name age city"
    """
    info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

**Avoid:**
```python
# No documentation
class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

## Common Pitfalls

### Pitfall 1: Pattern Too Greedy

**Problem:**
```python
pattern = parse('{name} {age}')  # Might match "Alice 30 Bob" incorrectly
```

**Solution:**
```python
pattern = parse('{name} | {age}')  # Use delimiter
# Or be more specific
pattern = parse('{name} {age} {city}')  # More fields = more specific
```

### Pitfall 2: Optional Fields in Wrong Order

**Problem:**
```python
pattern = parse('{name?} | {age} | {city}')  # name optional but age required
```

**Solution:**
```python
# Make optional fields at the end
pattern = parse('{name} | {age} | {city?}')  # city optional
# Or use proper typing
class Info(BaseModel):
    name: str
    age: int
    city: str | None = None
```

### Pitfall 3: Not Handling Whitespace

**Problem:**
```python
# Assuming exact spacing
pattern = parse('{name}|{age}|{city}')  # No spaces
```

**Solution:**
```python
# Stringent handles whitespace automatically
pattern = parse('{name} | {age} | {city}')  # Works with any spacing
result = pattern.parse("  Alice  |  30  |  NYC  ")  # Automatically trimmed
```

## Summary

1. **Design patterns carefully** - Use descriptive names and appropriate delimiters
2. **Keep models simple** - Define patterns where they're used
3. **Order patterns correctly** - Most specific first in chains
4. **Reuse compiled patterns** - Don't recompile unnecessarily
5. **Handle errors gracefully** - Use error recovery for user input
6. **Test thoroughly** - Test matching, chaining, and error cases
7. **Document your patterns** - Help others understand your code

Following these best practices will help you write maintainable, performant code with `stringent`.


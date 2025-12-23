# strum

Parse strings into Pydantic models using pattern matching.

> 📚 **Documentation**: See the [docs directory](docs/) for comprehensive user guides and API reference.

## Installation

```bash
pip install strum
```

## Usage

```python
from pydantic import BaseModel, EmailStr
from typing import Literal
from strum import parse, parse_json, ParsableModel

data = [
    {'id': 1, 'info': {'name': 'Alice', 'age': 30, 'city': 'New York'}, 'email': 'alice@example.com', 'status': 'Active'},
    {'id': 3, 'info': 'Charlie | 27 | Chicago', 'email': 'charlie@example.com', 'status': 'Active'},
    {'id': 5, 'info': 'Eve 35 Dallas', 'email': 'eve@example.com', 'status': 'Inactive'},
    {'id': 8, 'info': '{"name": "Joe", "age": 55, "city": "Tampa"}', 'email': 'joe@example.com', 'status': 'Active'},
]

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse_json() | parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
    email: EmailStr
    status: Literal['Active', 'Inactive']

# Parse the data
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

### Parsing Entire Models from Strings

You can parse an entire model instance from a single string using the `parse()` class method:

```python
class SimpleRecord(ParsableModel):
    _model_parse_pattern = '{id} | {name} | {age}'
    id: int
    name: str
    age: int

# Parse from string using class-defined pattern
record = SimpleRecord.parse('1 | Alice | 30')
print(record)
# Output: id=1 name='Alice' age=30

# Or provide pattern as argument
record2 = SimpleRecord.parse('2 | Bob | 25', pattern='{id} | {name} | {age}')
print(record2)
# Output: id=2 name='Bob' age=25
```

**With nested parsing:**
```python
class RecordWithNested(ParsableModel):
    _model_parse_pattern = '{id} || {info} || {email}'
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: EmailStr

# Parse - nested fields are automatically parsed
record = RecordWithNested.parse('1 || Alice | 30 | NYC || alice@example.com')
print(record.info.name)  # Output: 'Alice'
print(record.info.age)   # Output: 30
print(record.email)      # Output: 'alice@example.com'
```

### Parsing from JSON

You can also parse model instances directly from JSON strings:

```python
class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: EmailStr
    status: str

# Parse from JSON string using the convenience method
json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com", "status": "Active"}'
record = Record.parse_json(json_str)
print(record)
# Output: id=1 info=Info(name='Alice', age=30, city='NYC') email='alice@example.com' status='Active'

# Nested parsing works automatically
print(record.info.name)  # Output: 'Alice'
print(record.info.age)   # Output: 30
```

**Note:** The `parse_json()` method is a convenience wrapper around Pydantic's `model_validate_json()`. It parses the JSON and then applies field-level parse patterns to string values. You can also use `Record.model_validate_json(json_str)` directly, which works the same way.

### Using Union Types for Multiple Parsing Strategies

Instead of chaining parse patterns with `|`, you can define separate subclasses with their own parsing configurations and use union types. This approach is more intuitive and allows you to organize parsing logic by type:

```python
from typing import Union
from pydantic import BaseModel, EmailStr
from typing import Literal
from strum import ParsableModel

class Info(ParsableModel):
    name: str
    age: int
    city: str

class PipeInfo(Info):
    _model_parse_pattern = '{name} | {age} | {city}'

class SpaceInfo(Info):
    _model_parse_pattern = '{name} {age} {city}'

class JsonInfo(Info):
    _json_parse = True

class Record(ParsableModel):
    id: int
    info: Union[JsonInfo, PipeInfo, SpaceInfo]
    email: EmailStr
    status: Literal['Active', 'Inactive']

# All formats work automatically
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
id=3 info=PipeInfo(name='Charlie', age=27, city='Chicago') email='charlie@example.com' status='Active'
id=5 info=SpaceInfo(name='Eve', age=35, city='Dallas') email='eve@example.com' status='Inactive'
id=8 info=JsonInfo(name='Joe', age=55, city='Tampa') email='joe@example.com' status='Active'
```

**Key features:**
- **`_model_parse_pattern`**: Defines a format string pattern for parsing (e.g., `'{name} | {age} | {city}'`)
- **`_json_parse = True`**: Enables JSON parsing for the class
- **Union order matters**: Types are tried in the order specified in the union
- **Both flags can be combined**: A class with both `_json_parse = True` and `_model_parse_pattern` will try JSON first, then fall back to the pattern

**Note:** In Python 3.10+, you can use `JsonInfo | PipeInfo | SpaceInfo` instead of `Union[JsonInfo, PipeInfo, SpaceInfo]`.

### Standalone Parsing

You can also use the parsing functionality directly without Pydantic models:

```python
from strum import parse

# Create a parse pattern
pattern = parse('{name} | {age} | {city}')

# Parse a string
result = pattern.parse('Alice | 30 | New York')
print(result)
# Output: {'name': 'Alice', 'age': '30', 'city': 'New York'}

# Chain multiple patterns
chained = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
result1 = chained.parse('Bob | 25 | NYC')  # Uses first pattern
print(result1)
# Output: {'name': 'Bob', 'age': '25', 'city': 'NYC'}

result2 = chained.parse('Eve 35 Dallas')   # Uses second pattern
print(result2)
# Output: {'name': 'Eve', 'age': '35', 'city': 'Dallas'}
```

## Features

- Parse strings using format-like patterns (e.g., `{name} | {age} | {city}`)
- Chain multiple patterns using the `|` operator to try patterns in order
- Automatically handles both dictionary and string inputs
- Integrates seamlessly with Pydantic models
- Supports flexible spacing in patterns

## Pattern Syntax

Patterns use `{field_name}` placeholders to extract values from strings. The parsing is powered by the [`parse`](https://github.com/r1chardj0n3s/parse) library, which supports Python's format string syntax.

### Basic Patterns

```python
from strum import parse

# Simple named placeholders
pattern = parse('{name} | {age} | {city}')
result = pattern.parse('Alice | 30 | New York')
# {'name': 'Alice', 'age': '30', 'city': 'New York'}

# Space-separated values
pattern = parse('{name} {age} {city}')
result = pattern.parse('Bob 25 NYC')
# {'name': 'Bob', 'age': '25', 'city': 'NYC'}

# Custom delimiters
pattern = parse('{name},{age},{city}')
result = pattern.parse('Charlie,27,Chicago')
# {'name': 'Charlie', 'age': '27', 'city': 'Chicago'}
```

### Type Conversion

The underlying `parse` library supports automatic type conversion using format specifiers. For type conversion with named fields, use the `parse` library directly:

```python
# Named fields with type conversion (using parse library directly)
import parse as parse_lib

# Integer conversion
pattern_obj = parse_lib.compile('{name} is {age:d} years old')
result = pattern_obj.parse('Bob is 25 years old')
# Access the parsed values
name = result['name']  # 'Bob' (string)
age = result['age']    # 25 (integer!)
print(f"{name} is {age} years old")  # Bob is 25 years old

# Float conversion
pattern_obj = parse_lib.compile('Price {price:f} dollars')
result = pattern_obj.parse('Price 99.99 dollars')
price = result['price']  # 99.99 (float!)
print(f"Price: ${price:.2f}")  # Price: $99.99

# Multiple type conversions
pattern_obj = parse_lib.compile('{product} costs ${price:f} and we have {stock:d} in stock')
result = pattern_obj.parse('Laptop costs $999.99 and we have 42 in stock')
# result['product'] = 'Laptop' (str)
# result['price'] = 999.99 (float)
# result['stock'] = 42 (int)
```

**Note**: The `strum.parse()` wrapper returns only named fields as strings. For type conversion, use `parse_lib.compile()` directly as shown above.

### Complex Patterns

```python
from strum import parse

# Patterns with fixed text
pattern = parse('User: {username} (ID: {user_id})')
result = pattern.parse('User: alice (ID: 12345)')
# {'username': 'alice', 'user_id': '12345'}

# Date/time patterns
pattern = parse('{date} at {time}')
result = pattern.parse('2024-01-15 at 14:30')
# {'date': '2024-01-15', 'time': '14:30'}

# URL-like patterns
pattern = parse('{protocol}://{host}/{path}')
result = pattern.parse('https://example.com/api/users')
# {'protocol': 'https', 'host': 'example.com', 'path': 'api/users'}

# Log file patterns
pattern = parse('[{level}] {message} at {timestamp}')
result = pattern.parse('[ERROR] Connection failed at 2024-01-15 10:30:00')
# {'level': 'ERROR', 'message': 'Connection failed', 'timestamp': '2024-01-15 10:30:00'}
```

### Pattern Chaining

Chain multiple patterns to handle different input formats:

```python
from strum import parse

# Try multiple formats
chained = (
    parse('{name} | {age} | {city}') |
    parse('{name},{age},{city}') |
    parse('{name} {age} {city}')
)

# All of these will work:
chained.parse('Alice | 30 | NYC')
chained.parse('Bob,25,Chicago')
chained.parse('Charlie 27 Dallas')
```

### Real-World Examples

```python
from strum import parse

# Parse log entries
log_pattern = parse('[{timestamp}] {level}: {message}')
log_entry = '[2024-01-15 10:30:00] INFO: User logged in'
result = log_pattern.parse(log_entry)
# {'timestamp': '2024-01-15 10:30:00', 'level': 'INFO', 'message': 'User logged in'}

# Parse command-line style arguments
cmd_pattern = parse('{command} {arg1} {arg2}')
cmd = 'git commit -m "Initial commit"'
result = cmd_pattern.parse(cmd)
# {'command': 'git', 'arg1': 'commit', 'arg2': '-m "Initial commit"'}

# Parse configuration strings
config_pattern = parse('{key}={value}')
config = 'database_url=postgresql://localhost/mydb'
result = config_pattern.parse(config)
# {'key': 'database_url', 'value': 'postgresql://localhost/mydb'}

# Parse structured data from unstructured text
data_pattern = parse('Product: {product}, Price: {price}, Stock: {stock}')
data = 'Product: Laptop, Price: 999.99, Stock: 42'
result = data_pattern.parse(data)
# {'product': 'Laptop', 'price': '999.99', 'stock': '42'}
```

## Dependencies

- `pydantic>=2.0.0` - For Pydantic model integration
- `parse>=1.20.0` - For string parsing functionality

## License

MIT


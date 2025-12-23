# Advanced Patterns

This guide covers advanced features including union types, inheritance, and complex parsing scenarios.

## Union Types

Instead of chaining parse patterns with `|`, you can define separate subclasses with their own parsing configurations and use union types. This approach is more intuitive and allows you to organize parsing logic by type.

### Basic Union Type Example

```python
from typing import Union
from pydantic import BaseModel, EmailStr
from stringent import ParsableModel

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
    status: str

# All formats work automatically
data = [
    {'id': 1, 'info': {'name': 'Alice', 'age': 30, 'city': 'New York'}, 'email': 'alice@example.com', 'status': 'Active'},
    {'id': 3, 'info': 'Charlie | 27 | Chicago', 'email': 'charlie@example.com', 'status': 'Active'},
    {'id': 5, 'info': 'Eve 35 Dallas', 'email': 'eve@example.com', 'status': 'Inactive'},
    {'id': 8, 'info': '{"name": "Joe", "age": 55, "city": "Tampa"}', 'email': 'joe@example.com', 'status': 'Active'},
]

for item in data:
    record = Record(**item)
    print(f"{record.id}: {record.info.name} ({type(record.info).__name__})")
```

**Output:**
```
1: Alice (JsonInfo)
3: Charlie (PipeInfo)
5: Eve (SpaceInfo)
8: Joe (JsonInfo)
```

### Union Type Order Matters

Types are tried in the order specified in the union:

```python
class FirstInfo(Info):
    _model_parse_pattern = '{name} | {age} | {city}'

class SecondInfo(Info):
    _model_parse_pattern = '{name} {age} {city}'

class Record(ParsableModel):
    info: Union[FirstInfo, SecondInfo]  # FirstInfo tried first
```

If a string matches multiple patterns, the first matching type in the union will be used.

### Combining JSON and Pattern Parsing

A class can have both `_json_parse = True` and `_model_parse_pattern`. JSON parsing is tried first, then the pattern:

```python
class FlexibleInfo(Info):
    _json_parse = True
    _model_parse_pattern = '{name} | {age} | {city}'

class Record(ParsableModel):
    info: FlexibleInfo

# JSON string
data1 = {"info": '{"name": "Alice", "age": 30, "city": "NYC"}'}
record1 = Record(**data1)  # Uses JSON parsing

# Pattern string
data2 = {"info": "Bob | 25 | Chicago"}
record2 = Record(**data2)  # Uses pattern parsing
```

## Inheritance

Parse patterns can be inherited from parent classes and overridden in child classes.

### Inheriting Parse Patterns

```python
class BaseRecord(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')

class DerivedRecord(BaseRecord):
    extra: str

# DerivedRecord inherits the info parse pattern
data = {"info": "Alice | 30 | NYC", "extra": "test"}
record = DerivedRecord(**data)
assert record.info.name == "Alice"
```

### Overriding Parse Patterns

```python
class BaseRecord(ParsableModel):
    info: Info = parse('{name} | {age} | {city}')

class DerivedRecord(BaseRecord):
    info: Info = parse('{name} {age} {city}')  # Override with different pattern

# Uses the overridden pattern
data = {"info": "Bob 25 Chicago"}
record = DerivedRecord(**data)
assert record.info.name == "Bob"
```

## Complex Nested Structures

You can combine union types with nested parsing for complex data structures:

```python
class Address(ParsableModel):
    street: str
    city: str
    zip_code: str

class PipeAddress(Address):
    _model_parse_pattern = '{street} | {city} | {zip_code}'

class SpaceAddress(Address):
    _model_parse_pattern = '{street} {city} {zip_code}'

class Person(ParsableModel):
    name: str
    age: int
    address: Union[PipeAddress, SpaceAddress]

# Nested parsing works automatically
data = {
    "name": "Alice",
    "age": 30,
    "address": "123 Main St | NYC | 10001"
}

person = Person(**data)
print(person.address.city)
```

**Output:**
```
NYC
```

## Real-World Example

Here's a complete example showing how to handle multiple data formats:

```python
from typing import Union, Literal
from pydantic import BaseModel, EmailStr
from stringent import ParsableModel

class ContactInfo(ParsableModel):
    name: str
    email: EmailStr
    phone: str

class PipeContact(ContactInfo):
    _model_parse_pattern = '{name} | {email} | {phone}'

class CommaContact(ContactInfo):
    _model_parse_pattern = '{name}, {email}, {phone}'

class JsonContact(ContactInfo):
    _json_parse = True

class Customer(ParsableModel):
    id: int
    contact: Union[JsonContact, PipeContact, CommaContact]
    status: Literal['Active', 'Inactive']

# Handle various input formats
customers = [
    {"id": 1, "contact": "Alice | alice@example.com | 555-0100", "status": "Active"},
    {"id": 2, "contact": "Bob, bob@example.com, 555-0200", "status": "Active"},
    {"id": 3, "contact": '{"name": "Charlie", "email": "charlie@example.com", "phone": "555-0300"}', "status": "Inactive"},
]

for data in customers:
    customer = Customer(**data)
    print(f"{customer.id}: {customer.contact.name} - {customer.contact.email}")
```

**Output:**
```
1: Alice - alice@example.com
2: Bob - bob@example.com
3: Charlie - charlie@example.com
```

## Best Practices

1. **Use union types for clear separation**: When you have distinct parsing strategies, use union types with separate classes rather than chaining many patterns.

2. **Order matters**: Place the most common or specific patterns first in union types.

3. **Combine JSON and patterns**: Use `_json_parse = True` with `_model_parse_pattern` when you need to handle both JSON and format strings.

4. **Inherit common fields**: Use inheritance to share common fields while allowing different parsing strategies.

5. **Test edge cases**: Make sure to test with various input formats, including already-parsed dictionaries.


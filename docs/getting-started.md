# Getting Started

Welcome to `stringent`! This guide will help you get started with parsing strings into Pydantic models using flexible pattern matching.

## What is stringent?

`stringent` is a powerful Python library that seamlessly parses strings into Pydantic models using pattern matching. It eliminates the need for manual parsing logic by automatically handling multiple data formats (dictionaries, strings, JSON) with a single, declarative definition.

### Key Benefits

- **Flexible Pattern Matching** - Parse strings using format-like patterns
- **Pattern Chaining** - Support multiple formats with automatic fallback
- **Type Safety** - Built on Pydantic 2.0+ for robust validation
- **Zero Boilerplate** - Automatic parsing without manual code
- **High Performance** - Powered by `formatparse` (Rust-based, 1.6x faster than alternatives)

## Installation

Install `stringent` using pip:

```bash
pip install stringent
```

## Requirements

- **Python** 3.10 or higher
- **Pydantic** 2.0 or higher
- **formatparse** 0.6.0 or higher

## Quick Example

Here's a simple example to get you started:

```python
from pydantic import BaseModel, EmailStr
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')
    email: EmailStr

# Parse a string into the model
data = {
    "id": 1,
    "info": "Alice | 30 | New York",
    "email": "alice@example.com"
}

record = Record(**data)
print(record.info.name)
print(record.info.age)
```

**Output:**
```
Alice
30
```

## Key Concepts

### ParsePattern

A `ParsePattern` is created using the `parse()` function with a format string:

```python
from stringent import parse

pattern = parse('{name} | {age} | {city}')
```

The format string uses the same syntax as Python's `str.format()` method, with field names in curly braces.

### ParsableModel

`ParsableModel` is a base class that extends Pydantic's `BaseModel` with automatic string parsing capabilities. When you define a field with a `ParsePattern`, the model will automatically parse string values using that pattern.

### Pattern Chaining

You can chain multiple patterns together using the `|` operator:

```python
info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
```

This allows the model to handle multiple string formats for the same field.

## Common Use Cases

### API Integration
Handle inconsistent data formats from different endpoints without writing custom parsers.

### Data Migration
Parse legacy data formats while maintaining type safety and validation.

### Log Processing
Parse structured log entries into validated models for analysis.

### ETL Pipelines
Transform unstructured strings into typed data structures automatically.

## Next Steps

- **[Basic Usage Guide](basic-usage.md)** - Detailed examples and common patterns
- **[Advanced Patterns](advanced-patterns.md)** - Union types, inheritance, and complex scenarios
- **[User Guides](user-guides/quick-reference.md)** - Quick reference, migration, best practices, and troubleshooting
- **[API Reference](api-reference.md)** - Complete API documentation

## Need Help?

- Check the [Troubleshooting Guide](user-guides/troubleshooting.md) for common issues
- Review [Best Practices](user-guides/best-practices.md) for tips and patterns
- See [Examples](basic-usage.md) for real-world usage patterns


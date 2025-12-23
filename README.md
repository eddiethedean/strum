# stringent

[![CI](https://github.com/eddiethedean/stringent/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/stringent/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/stringent.svg)](https://pypi.org/project/stringent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/eddiethedean/stringent/blob/main/LICENSE)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**stringent** is a powerful Python library that seamlessly parses strings into Pydantic models using flexible pattern matching. Whether you're working with pipe-separated values, space-separated data, JSON strings, or custom formats, stringent makes it easy to convert unstructured strings into validated, type-safe Python objects.

## Features

✨ **Flexible Pattern Matching** - Parse strings using format-like patterns (e.g., `{name} | {age} | {city}`)

🔗 **Pattern Chaining** - Chain multiple patterns using the `|` operator to try patterns in order until one matches

🔄 **Automatic Input Handling** - Seamlessly handles both dictionary and string inputs without code changes

🎯 **Pydantic Integration** - Built on Pydantic 2.0+ for robust validation and type safety

📦 **JSON Support** - Built-in JSON parsing with automatic fallback to pattern matching

🚀 **JsonParsableModel** - Automatic JSON string parsing for API integrations and message queues

🔀 **Union Types** - Organize parsing strategies using union types for maximum flexibility

🧬 **Inheritance Support** - Parse patterns are inherited and can be overridden in subclasses

## Installation

```bash
pip install stringent
```

## Quick Start

```python
from pydantic import BaseModel, EmailStr
from typing import Literal
from stringent import parse, parse_json, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse_json() | parse('{name} | {age} | {city}') | parse('{name} {age} {city}')
    email: EmailStr
    status: Literal['Active', 'Inactive']

# Parse the data - handles dicts, strings, and JSON automatically
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
id=3 info=Info(name='Charlie', age=27, city='Chicago') email='charlie@example.com' status='Active'
id=5 info=Info(name='Eve', age=35, city='Dallas') email='eve@example.com' status='Inactive'
id=8 info=Info(name='Joe', age=55, city='Tampa') email='joe@example.com' status='Active'
```

## Why stringent?

Working with mixed data formats is a common challenge in data processing. You might receive:
- Dictionary objects from APIs
- Pipe-separated strings from legacy systems
- Space-separated values from log files
- JSON strings from message queues

**stringent** eliminates the need for manual parsing logic by automatically handling all these formats with a single, declarative definition.

## Key Use Cases

- **API Integration** - Handle inconsistent data formats from different endpoints
- **Data Migration** - Parse legacy data formats while maintaining type safety
- **Log Processing** - Parse structured log entries into validated models
- **ETL Pipelines** - Transform unstructured strings into typed data structures
- **Configuration Parsing** - Support multiple configuration formats with fallback patterns

## Documentation

Comprehensive documentation is available in the [docs directory](https://github.com/eddiethedean/stringent/tree/main/docs):

- **[Getting Started](https://github.com/eddiethedean/stringent/blob/main/docs/getting-started.md)** - Installation and basic concepts
- **[Basic Usage](https://github.com/eddiethedean/stringent/blob/main/docs/basic-usage.md)** - Field-level parsing, pattern chaining, and common patterns
- **[JSON Parsing](https://github.com/eddiethedean/stringent/blob/main/docs/json-parsing.md)** - Automatic JSON parsing with JsonParsableModel
- **[Regex Parsing](https://github.com/eddiethedean/stringent/blob/main/docs/regex-parsing.md)** - Parse strings using regular expressions with named groups
- **[Error Handling](https://github.com/eddiethedean/stringent/blob/main/docs/error-handling.md)** - Error recovery and partial parsing
- **[FastAPI Integration](https://github.com/eddiethedean/stringent/blob/main/docs/fastapi-integration.md)** - Using stringent with FastAPI
- **[Advanced Patterns](https://github.com/eddiethedean/stringent/blob/main/docs/advanced-patterns.md)** - Union types, inheritance, and complex scenarios
- **[API Reference](https://github.com/eddiethedean/stringent/blob/main/docs/api-reference.md)** - Complete API documentation
- **[Documentation Index](https://github.com/eddiethedean/stringent/blob/main/docs/index.md)** - Overview and quick links

## Requirements

- **Python** 3.10 or higher
- **Pydantic** 2.0 or higher
- **parse** 1.20 or higher

## Dependencies

- `pydantic>=2.0.0` - For Pydantic model integration and validation
- `parse>=1.20.0` - For string parsing functionality

## Examples

### Pattern Chaining

Try multiple patterns in order until one matches:

```python
from stringent import parse, ParsableModel
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}')

# Both formats work automatically
record1 = Record(info="Alice | 30 | NYC")
record2 = Record(info="Bob 25 Chicago")
```

### JSON Parsing

Automatically parse JSON strings with fallback to pattern matching:

```python
from stringent import parse_json, parse, ParsableModel
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int

class Record(ParsableModel):
    info: Info = parse_json() | parse('{name} | {age}')

# JSON string
record1 = Record(info='{"name": "Alice", "age": 30}')

# Pattern string (fallback)
record2 = Record(info="Bob | 25")
```

### Union Types

Use union types to organize parsing strategies:

```python
from typing import Union
from stringent import ParsableModel
from pydantic import BaseModel

class Info(ParsableModel):
    name: str
    age: int

class PipeInfo(Info):
    _model_parse_pattern = '{name} | {age}'

class SpaceInfo(Info):
    _model_parse_pattern = '{name} {age}'

class Record(ParsableModel):
    info: Union[PipeInfo, SpaceInfo]

# Automatically selects the correct type
record1 = Record(info="Alice | 30")  # Uses PipeInfo
record2 = Record(info="Bob 25")      # Uses SpaceInfo
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Getting Started

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Open Issues

Looking for something to work on? Check out our [open issues](https://github.com/eddiethedean/stringent/issues)! We have many enhancement ideas organized by priority:

- **[High Priority Features](https://github.com/eddiethedean/stringent/issues?q=is%3Aissue+is%3Aopen+label%3A%22priority%3A+high%22)** - Core functionality improvements
- **[Medium Priority Features](https://github.com/eddiethedean/stringent/issues?q=is%3Aissue+is%3Aopen+label%3A%22priority%3A+medium%22)** - Additional capabilities and optimizations
- **[Documentation & Infrastructure](https://github.com/eddiethedean/stringent/issues?q=is%3Aissue+is%3Aopen+label%3Adocumentation+label%3Ainfrastructure)** - Docs, examples, and tooling improvements

Issues labeled with `good first issue` are great for newcomers. See the full list of [enhancement issues](https://github.com/eddiethedean/stringent/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement) for more ideas.

## Development

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/eddiethedean/stringent.git
cd stringent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Run type checking
mypy stringent/
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/eddiethedean/stringent/blob/main/LICENSE) file for details.

## Author

**Odos Matthews**

- GitHub: [@eddiethedean](https://github.com/eddiethedean)
- Email: odosmatthews@gmail.com

## Acknowledgments

- Built on [Pydantic](https://pydantic.dev/) for robust data validation
- Uses [parse](https://github.com/r1chardj0n3s/parse) for flexible string parsing

---

**Made with ❤️ for the Python community**

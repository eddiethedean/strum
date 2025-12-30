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

⚡ **High Performance** - Powered by `formatparse` (Rust-based) for 1.6x faster parsing than alternatives

🛡️ **Error Recovery** - Collect errors and get partial results for graceful error handling

## Installation

```bash
pip install stringent
```

## Quick Start

```python
from pydantic import BaseModel
from stringent import parse, ParsableModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    id: int
    info: Info = parse('{name} | {age} | {city}')

# Automatically parses string into nested model
record = Record(id=1, info="Alice | 30 | NYC")
print(record.info.name)  # "Alice"
```

See the [Getting Started guide](https://py-stringent.readthedocs.io/en/latest/getting-started.html) for more examples and detailed usage.

## Why stringent?

Working with mixed data formats is a common challenge. You might receive dictionaries from APIs, pipe-separated strings from legacy systems, or JSON strings from message queues.

**stringent** eliminates manual parsing logic by automatically handling all these formats with a single, declarative definition. No custom parsers needed—just define your patterns and let `stringent` do the work.

## Key Use Cases

- **API Integration** - Handle inconsistent data formats from different endpoints
- **Data Migration** - Parse legacy formats while maintaining type safety
- **Log Processing** - Parse structured log entries into validated models
- **ETL Pipelines** - Transform unstructured strings into typed data structures

See [use cases and examples](https://py-stringent.readthedocs.io/en/latest/getting-started.html#common-use-cases) in the documentation.

## Documentation

📚 **Full documentation: [py-stringent.readthedocs.io](https://py-stringent.readthedocs.io/)**

Comprehensive guides, examples, and API reference are available in the documentation:

- **[Getting Started](https://py-stringent.readthedocs.io/en/latest/getting-started.html)** - Installation and quick start
- **[Basic Usage](https://py-stringent.readthedocs.io/en/latest/basic-usage.html)** - Field-level parsing and pattern chaining
- **[JSON Parsing](https://py-stringent.readthedocs.io/en/latest/json-parsing.html)** - Automatic JSON parsing
- **[Regex Parsing](https://py-stringent.readthedocs.io/en/latest/regex-parsing.html)** - Regular expression patterns
- **[Error Handling](https://py-stringent.readthedocs.io/en/latest/error-handling.html)** - Error recovery and partial parsing
- **[Advanced Patterns](https://py-stringent.readthedocs.io/en/latest/advanced-patterns.html)** - Union types and inheritance
- **[FastAPI Integration](https://py-stringent.readthedocs.io/en/latest/fastapi-integration.html)** - Using with FastAPI
- **[User Guides](https://py-stringent.readthedocs.io/en/latest/user-guides/)** - Migration, best practices, troubleshooting
- **[API Reference](https://py-stringent.readthedocs.io/en/latest/api-reference.html)** - Complete API documentation

## Requirements

- **Python** 3.10 or higher
- **Pydantic** 2.0 or higher
- **formatparse** 0.6.0 or higher

## Dependencies

- `pydantic>=2.0.0` - For Pydantic model integration and validation
- `formatparse>=0.6.0` - For string parsing functionality

## More Examples

For detailed examples and use cases, see the [documentation](https://py-stringent.readthedocs.io/):

- **[Pattern Chaining](https://py-stringent.readthedocs.io/en/latest/basic-usage.html#pattern-chaining)** - Try multiple patterns in order
- **[JSON Parsing](https://py-stringent.readthedocs.io/en/latest/json-parsing.html)** - Automatic JSON with fallback patterns
- **[Union Types](https://py-stringent.readthedocs.io/en/latest/advanced-patterns.html#union-types)** - Organize parsing strategies
- **[Regex Patterns](https://py-stringent.readthedocs.io/en/latest/regex-parsing.html)** - Parse with regular expressions
- **[Error Recovery](https://py-stringent.readthedocs.io/en/latest/error-handling.html)** - Graceful error handling

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
- Powered by [formatparse](https://github.com/astral-sh/formatparse) for high-performance string parsing (1.6x faster than alternatives)

---

**Made with ❤️ for the Python community**

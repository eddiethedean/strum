"""
Stringent - Parse strings into Pydantic models using pattern matching.

Stringent is a powerful Python library that seamlessly parses strings into Pydantic models
using flexible pattern matching. Whether you're working with pipe-separated values,
space-separated data, JSON strings, or custom formats, stringent makes it easy to convert
unstructured strings into validated, type-safe Python objects.

Key Features:
    - Flexible pattern matching with format-like patterns
    - Pattern chaining for multiple format support
    - Automatic input handling (dicts, strings, JSON)
    - Pydantic 2.0+ integration for robust validation
    - JSON parsing with automatic fallback
    - Regex pattern support with named groups
    - Union types for organizing parsing strategies
    - Inheritance support for parse patterns

Example:
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
        email: str

    # Parse string automatically
    record = Record(
        id=1,
        info="Alice | 30 | NYC",
        email="alice@example.com"
    )
    print(record.info.name)  # "Alice"
    ```

For more information, see the documentation at https://py-stringent.readthedocs.io/
"""

from stringent.parser import (
    JsonParsableModel,
    ParsableModel,
    ParsePattern,
    ParseResult,
    parse,
    parse_json,
    parse_regex,
)

__all__ = [
    "JsonParsableModel",
    "ParsableModel",
    "ParsePattern",
    "ParseResult",
    "parse",
    "parse_json",
    "parse_regex",
]
__version__ = "0.4.0"

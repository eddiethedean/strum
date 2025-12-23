"""Core parsing logic for stringent."""

import contextlib
import json
import re
import sys
import types
from dataclasses import dataclass
from typing import Any, ClassVar, Union, get_args, get_origin

import parse as parse_lib
from pydantic import BaseModel, ValidationError, model_validator


@dataclass
class ParseResult:
    """Result of parsing with error recovery enabled."""

    data: dict[str, Any]
    errors: list[dict[str, Any]]

    def __bool__(self) -> bool:
        """Return True if parsing was successful (no errors)."""
        return len(self.errors) == 0


class ParsePattern:
    """A pattern that can parse strings into dictionaries based on format strings."""

    def __init__(self, pattern: str):
        """
        Initialize a ParsePattern with a format string.

        Args:
            pattern: Format string like '{name} | {age} | {city}' or '{name} {age} {city}'
                    Optional fields can be marked with '?': '{name} | {age?} | {city}'
        """
        self.original_pattern = pattern
        # Extract optional fields (those ending with ?)
        self.optional_fields = self._extract_optional_fields(pattern)
        # Create normalized pattern without ? for the parse library
        self.pattern = self._normalize_pattern(pattern)
        # Compile the pattern using the parse library
        self.compiled_pattern = parse_lib.compile(self.pattern)
        # Pre-generate pattern variations for optional fields
        self.pattern_variations = self._generate_pattern_variations()

    @staticmethod
    def _extract_optional_fields(pattern: str) -> set[str]:
        """Extract field names that are marked as optional (ending with ?)."""
        optional_fields = set()
        # Match {field?} patterns
        matches = re.findall(r"\{(\w+)\?\}", pattern)
        optional_fields.update(matches)
        return optional_fields

    @staticmethod
    def _normalize_pattern(pattern: str) -> str:
        """Remove ? from optional fields to create a pattern the parse library can use."""
        # Replace {field?} with {field}
        return re.sub(r"\{(\w+)\?\}", r"{\1}", pattern)

    def _generate_pattern_variations(self) -> list[parse_lib.Parser]:
        """Generate pattern variations with optional fields removed."""
        if not self.optional_fields:
            return []

        variations = []
        # For each optional field, create a pattern without it
        for optional_field in self.optional_fields:
            # Remove the optional field and its surrounding delimiters
            # This is a simplified approach - remove "{field?}" and adjacent delimiters
            pattern_without_field = re.sub(
                r"\s*\|?\s*\{" + re.escape(optional_field) + r"\?\}\s*\|?\s*",
                " | ",
                self.original_pattern,
            )
            pattern_without_field = re.sub(
                r"\s+\{" + re.escape(optional_field) + r"\?\}\s+",
                " ",
                pattern_without_field,
            )
            pattern_without_field = re.sub(
                r"\s+\{" + re.escape(optional_field) + r"\?\}",
                "",
                pattern_without_field,
            )
            pattern_without_field = re.sub(
                r"\{" + re.escape(optional_field) + r"\?\}\s+",
                "",
                pattern_without_field,
            )
            # Clean up multiple spaces/delimiters
            pattern_without_field = re.sub(r"\s*\|\s*\|\s*", " | ", pattern_without_field)
            pattern_without_field = re.sub(r"\s+", " ", pattern_without_field)
            pattern_without_field = pattern_without_field.strip()

            if pattern_without_field and pattern_without_field != self.pattern:
                with contextlib.suppress(Exception):
                    # If pattern compilation fails, skip this variation
                    variations.append(parse_lib.compile(pattern_without_field))

        return variations

    def parse(self, value: str) -> dict[str, Any]:
        """
        Parse a string value according to the pattern.

        Args:
            value: String to parse

        Returns:
            Dictionary with parsed values (with whitespace stripped).
            Optional fields that are missing will not be included in the result.

        Raises:
            ValueError: If the string doesn't match the pattern
            TypeError: If value is not a string
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")

        # Try the main pattern first
        result = self.compiled_pattern.parse(value.strip())
        if result is not None:
            parsed_dict = {
                k: v.strip() if isinstance(v, str) else v for k, v in result.named.items()
            }
            # Mark optional fields that are present
            return parsed_dict

        # If main pattern fails and we have optional fields, try variations
        if self.optional_fields and self.pattern_variations:
            for variation in self.pattern_variations:
                result = variation.parse(value.strip())
                if result is not None:
                    parsed_dict = {
                        k: v.strip() if isinstance(v, str) else v for k, v in result.named.items()
                    }
                    # Optional fields not in the result are simply missing
                    return parsed_dict

        raise ValueError(f"String '{value}' does not match pattern '{self.original_pattern}'")

    def __or__(self, other: "ParsePattern") -> "ChainedParsePattern":
        """Support | operator for chaining patterns."""
        if isinstance(other, ParsePattern):
            return ChainedParsePattern([self, other])
        return NotImplemented

    def __ror__(self, other: Any) -> "ChainedParsePattern":
        """Support | operator when pattern is on the right side."""
        if isinstance(other, ParsePattern):
            return ChainedParsePattern([other, self])
        return NotImplemented


class ChainedParsePattern:
    """A chain of patterns that will be tried in order."""

    def __init__(self, patterns: list[ParsePattern]):
        # Validate that patterns list is not empty
        if not patterns:
            raise ValueError("ChainedParsePattern requires at least one pattern")
        # Validate that all patterns are ParsePattern instances
        for i, pattern in enumerate(patterns):
            if not isinstance(pattern, ParsePattern):
                raise TypeError(
                    f"All patterns must be ParsePattern instances, "
                    f"but got {type(pattern).__name__} at index {i}"
                )
        self.patterns = patterns

    def parse(self, value: str) -> dict[str, Any]:
        """
        Try each pattern in order until one succeeds.

        Args:
            value: String to parse

        Returns:
            Dictionary with parsed values

        Raises:
            ValueError: If none of the patterns match
            TypeError: If value is not a string
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")
        for pattern in self.patterns:
            try:
                return pattern.parse(value)
            except ValueError:
                pass

        raise ValueError(f"String '{value}' did not match any pattern")

    def __or__(self, other: Union[ParsePattern, "ChainedParsePattern"]) -> "ChainedParsePattern":
        """Support chaining more patterns."""
        if isinstance(other, ParsePattern):
            return ChainedParsePattern([*self.patterns, other])
        elif isinstance(other, ChainedParsePattern):
            return ChainedParsePattern(self.patterns + other.patterns)
        return NotImplemented

    def __ror__(self, other: Any) -> "ChainedParsePattern":
        """Support | operator when chain is on the right side."""
        if isinstance(other, ParsePattern):
            return ChainedParsePattern([other, *self.patterns])
        elif isinstance(other, ChainedParsePattern):
            return ChainedParsePattern(other.patterns + self.patterns)
        return NotImplemented


class JsonParsePattern(ParsePattern):
    """A pattern that parses JSON strings into dictionaries."""

    def __init__(self) -> None:
        # Use a placeholder pattern name; no compiled pattern is needed for JSON
        self.original_pattern = "<json>"
        self.pattern = "<json>"
        self.optional_fields: set[str] = set()
        self.compiled_pattern: Any = None
        self.pattern_variations: list[Any] = []

    def parse(self, value: str) -> dict[str, Any]:
        """
        Parse a JSON string into a dictionary.

        Args:
            value: JSON string to parse

        Returns:
            Dictionary parsed from the JSON object

        Raises:
            ValueError: If the string is not valid JSON or is not a JSON object
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a JSON string")

        try:
            data = json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("JSON value must be an object")

        return data


def parse(pattern: str) -> ParsePattern:
    """
    Create a ParsePattern from a format string.

    Args:
        pattern: Format string like '{name} | {age} | {city}'

    Returns:
        ParsePattern instance
    """
    return ParsePattern(pattern)


def parse_json() -> ParsePattern:
    """
    Create a pattern that parses JSON strings into dictionaries.

    This can be chained with other patterns using the | operator, e.g.:

        info: Info = parse('{name} | {age} | {city}') | parse('{name} {age} {city}') | parse_json()

    Returns:
        A pattern object that parses JSON strings.
    """
    return JsonParsePattern()


class RegexParsePattern(ParsePattern):
    """A pattern that parses strings using regular expressions with named groups."""

    def __init__(self, pattern: str) -> None:
        r"""
        Initialize a regex parse pattern.

        Args:
            pattern: Regular expression pattern with named groups, e.g.
                    r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
        """
        self.regex_pattern = pattern
        # Compile the regex pattern
        try:
            self.compiled_regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

        # Check if pattern has named groups
        if not self.compiled_regex.groupindex:
            raise ValueError(
                "Regex pattern must contain named groups (e.g., (?P<name>...)) "
                "to map to model fields"
            )

        # Initialize parent with placeholder (regex patterns don't use parse library format)
        super().__init__("{regex}")

    def parse(self, value: str) -> dict[str, Any]:
        """
        Parse a string value using the regex pattern.

        Args:
            value: String to parse

        Returns:
            Dictionary with parsed values from named groups

        Raises:
            ValueError: If the string doesn't match the pattern
            TypeError: If value is not a string
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")

        match = self.compiled_regex.match(value.strip())
        if match is None:
            raise ValueError(
                f"String '{value}' does not match regex pattern '{self.regex_pattern}'"
            )

        # Extract named groups
        result = {}
        for name, value in match.groupdict().items():
            if value is not None:
                result[name] = value.strip() if isinstance(value, str) else value

        return result


def parse_regex(pattern: str) -> ParsePattern:
    r"""
    Create a pattern that parses strings using regular expressions with named groups.

    Args:
        pattern: Regular expression pattern with named groups

    Returns:
        A pattern object that parses strings using regex

    Example:
        entry: LogEntry = parse_regex(
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
        )
    """
    return RegexParsePattern(pattern)


class ParsableModel(BaseModel):
    """Base model class that supports parse patterns in field definitions."""

    _parse_patterns: ClassVar[
        dict[str, tuple[ParsePattern | ChainedParsePattern, type[BaseModel]]]
    ] = {}

    def __init_subclass__(cls: type["ParsableModel"], **kwargs: Any) -> None:
        """Automatically set up parse patterns for fields."""
        super().__init_subclass__(**kwargs)

        # Inherit parse patterns from parent classes
        cls._parse_patterns = {}
        for base in cls.__mro__[1:]:  # Skip cls itself, start from first parent
            if hasattr(base, "_parse_patterns"):
                cls._parse_patterns.update(base._parse_patterns.copy())

        # Find fields with parse patterns and store them
        annotations = getattr(cls, "__annotations__", {})

        # Check class attributes for parse patterns
        for field_name in annotations:
            if hasattr(cls, field_name):
                default_value = getattr(cls, field_name)
                if isinstance(default_value, (ParsePattern, ChainedParsePattern)):
                    field_type = annotations.get(field_name)
                    if (
                        field_type
                        and isinstance(field_type, type)
                        and issubclass(field_type, BaseModel)
                    ):
                        cls._parse_patterns[field_name] = (default_value, field_type)
                        # Remove parse pattern from class attributes
                        # so it doesn't become a default
                        delattr(cls, field_name)

    @staticmethod
    def _extract_model_parse_pattern(cls: type["ParsableModel"]) -> str | None:
        """
        Extract the _model_parse_pattern from a class, handling Pydantic's ModelPrivateAttr wrapper.

        Args:
            cls: The ParsableModel class to extract the pattern from

        Returns:
            The pattern string if found, None otherwise
        """
        if not hasattr(cls, "_model_parse_pattern"):
            return None
        attr = cls._model_parse_pattern
        # Handle Pydantic's ModelPrivateAttr wrapper
        if hasattr(attr, "default"):
            default_value = attr.default
            if isinstance(default_value, str):
                return default_value
            return None
        if isinstance(attr, str):
            return attr
        return None

    @staticmethod
    def _extract_parsable_union_types(field_type: Any) -> list[type]:
        """
        Extract ParsableModel subclasses from a union type.

        Returns:
            List of ParsableModel subclasses found in the union, in order
        """
        # Handle Python 3.10+ union syntax (A | B)
        origin = get_origin(field_type)
        if origin is Union or (
            sys.version_info >= (3, 10)
            and hasattr(types, "UnionType")
            and origin is types.UnionType
        ):
            args = get_args(field_type)
            return [arg for arg in args if isinstance(arg, type) and issubclass(arg, ParsableModel)]
        # Fallback: check if it has __args__ directly (for older Python versions or custom types)
        if hasattr(field_type, "__args__"):
            args = field_type.__args__
            if len(args) > 1:
                return [
                    arg for arg in args if isinstance(arg, type) and issubclass(arg, ParsableModel)
                ]
        return []

    @classmethod
    def _try_parse_with_subclass(
        cls, subclass: type[BaseModel], value: str
    ) -> "ParsableModel | None":
        """
        Try to parse a string value using a ParsableModel subclass's configuration.

        Checks for:
        1. _json_parse = True flag (try JSON parsing first)
        2. _model_parse_pattern (try format string parsing)

        Returns:
            Parsed model instance if successful, None otherwise
        """
        # Check if subclass is actually a ParsableModel
        if not issubclass(subclass, ParsableModel):
            return None

        # Type narrowing: subclass is now known to be ParsableModel
        parsable_subclass: type[ParsableModel] = subclass

        # Check for _json_parse flag
        if getattr(parsable_subclass, "_json_parse", False):
            try:
                data = json.loads(value)
                if isinstance(data, dict):
                    parsed = parsable_subclass(**data)
                    # Type narrowing: we know it's a ParsableModel
                    if isinstance(parsed, ParsableModel):
                        return parsed
            except (json.JSONDecodeError, ValidationError, ValueError):
                pass  # Fall through to pattern parsing

        # Check for _model_parse_pattern
        pattern = cls._extract_model_parse_pattern(parsable_subclass)
        if pattern:
            try:
                parsed = parsable_subclass.parse(value, pattern=pattern)
                if isinstance(parsed, ParsableModel):
                    return parsed
            except (ValueError, ValidationError):
                pass

        # All parsing attempts failed
        return None

    @model_validator(mode="before")
    @classmethod
    def _parse_string_fields(cls, data: Any) -> Any:
        """Parse string values for fields that have parse patterns defined."""
        if not isinstance(data, dict):
            return data

        result = data.copy()
        annotations = getattr(cls, "__annotations__", {})

        # First, handle existing parse patterns (backward compatibility)
        if hasattr(cls, "_parse_patterns"):
            for field_name, (pattern_obj, _target_type) in cls._parse_patterns.items():
                if field_name in result:
                    value = result[field_name]
                    if isinstance(value, str):
                        try:
                            parsed_dict = pattern_obj.parse(value)
                            result[field_name] = parsed_dict
                        except ValueError:
                            pass

        # Then, handle union types and single ParsableModel subclasses
        for field_name, field_type in annotations.items():
            if field_name in result:
                value = result[field_name]
                if isinstance(value, str):
                    # Check if field type is a union of ParsableModel subclasses
                    union_types = cls._extract_parsable_union_types(field_type)
                    if union_types:
                        # Try each type in order until one succeeds
                        for subclass in union_types:
                            parsed = cls._try_parse_with_subclass(subclass, value)
                            if parsed is not None:
                                result[field_name] = parsed
                                break
                    # Also handle single ParsableModel subclass with parsing config
                    elif isinstance(field_type, type) and issubclass(field_type, ParsableModel):
                        parsed = cls._try_parse_with_subclass(field_type, value)
                        if parsed is not None:
                            result[field_name] = parsed

        return result

    @classmethod
    def parse(cls, value: str, pattern: str | None = None) -> "ParsableModel":
        """
        Parse a string into a model instance.

        Args:
            value: String to parse
            pattern: Optional format string pattern. If not provided, uses cls._model_parse_pattern
                    if defined, otherwise raises ValueError.

        Returns:
            Instance of the model class

        Raises:
            ValueError: If pattern is not provided and cls._model_parse_pattern is not defined,
                       or if the string doesn't match the pattern.

        Example:
            class Record(ParsableModel):
                _model_parse_pattern = '{id} | {info} | {email} | {status}'
                id: int
                info: Info = parse('{name} | {age} | {city}')
                email: EmailStr
                status: str

            record = Record.parse('1 | Alice | 30 | NYC | alice@example.com | Active')
        """
        if pattern is None:
            # Get _model_parse_pattern - Pydantic wraps it in ModelPrivateAttr
            pattern = cls._extract_model_parse_pattern(cls)

            if pattern is None:
                raise ValueError(
                    f"No parse pattern provided and "
                    f"{cls.__name__}._model_parse_pattern is not defined. "
                    "Either provide a pattern argument or define "
                    "_model_parse_pattern on the class."
                )

        # Parse the string using the pattern
        parse_pattern = ParsePattern(pattern)
        parsed_dict = parse_pattern.parse(value)

        # Create model instance from parsed dictionary
        # The _parse_string_fields validator will handle any nested string parsing
        return cls(**parsed_dict)

    @classmethod
    def parse_json(cls, value: str) -> "ParsableModel":
        """
        Parse a JSON string into a model instance.

        This is a convenience method that wraps Pydantic's `model_validate_json()`.
        Field-level parse patterns are automatically applied via the model validator.

        Args:
            value: JSON string to parse

        Returns:
            Instance of the model class

        Raises:
            ValidationError: If the string is not valid JSON or doesn't match the model schema

        Example:
            class Record(ParsableModel):
                id: int
                info: Info = parse('{name} | {age} | {city}')
                email: EmailStr

            json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}'
            record = Record.parse_json(json_str)

        Note:
            This method uses Pydantic's `model_validate_json()` internally.
            You can also use `Record.model_validate_json(json_str)` directly.
        """
        # Use Pydantic's built-in JSON parsing
        # The _parse_string_fields validator will handle any nested string parsing
        return cls.model_validate_json(value)

    @classmethod
    def parse_with_recovery(
        cls, value: str, pattern: str | None = None, strict: bool = False
    ) -> "ParsableModel | ParseResult":
        """
        Parse a string into a model instance with error recovery.

        Args:
            value: String to parse
            pattern: Optional format string pattern. If not provided, uses cls._model_parse_pattern
                    if defined, otherwise raises ValueError.
            strict: If True, raises errors immediately. If False, returns ParseResult with errors.

        Returns:
            Instance of the model class if strict=True and parsing succeeds,
            or ParseResult with data and errors if strict=False

        Raises:
            ValueError: If pattern is not provided and cls._model_parse_pattern is not defined
            ValidationError: If strict=True and parsing fails

        Example:
            class Record(ParsableModel):
                _model_parse_pattern = '{name} | {age} | {city}'
                name: str
                age: int
                city: str

            # Recovery mode
            result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
            # result.data = {'name': 'Alice', 'city': 'NYC'}
            # result.errors = [{'field': 'age', 'error': '...', 'value': 'invalid'}]
        """
        if pattern is None:
            pattern = cls._extract_model_parse_pattern(cls)
            if pattern is None:
                raise ValueError(
                    f"No parse pattern provided and "
                    f"{cls.__name__}._model_parse_pattern is not defined. "
                    "Either provide a pattern argument or define "
                    "_model_parse_pattern on the class."
                )

        if strict:
            # Strict mode: raise errors immediately
            parse_pattern = ParsePattern(pattern)
            parsed_dict = parse_pattern.parse(value)
            return cls(**parsed_dict)

        # Recovery mode: collect errors
        errors = []
        parsed_dict = {}

        try:
            parse_pattern = ParsePattern(pattern)
            parsed_dict = parse_pattern.parse(value)
            # Try to create model instance
            try:
                return cls(**parsed_dict)
            except ValidationError as e:
                # Collect validation errors
                for error in e.errors():
                    errors.append(
                        {
                            "field": ".".join(str(loc) for loc in error.get("loc", [])),
                            "error": error.get("msg", "Validation error"),
                            "type": error.get("type", "validation_error"),
                        }
                    )
                # Return partial result
                return ParseResult(data=parsed_dict, errors=errors)
        except ValueError as e:
            # Pattern matching failed
            errors.append(
                {
                    "field": "pattern",
                    "error": str(e),
                    "type": "pattern_error",
                }
            )
            return ParseResult(data=parsed_dict, errors=errors)

    @classmethod
    def model_validate_with_recovery(
        cls, data: Any, strict: bool = False
    ) -> "ParsableModel | ParseResult":
        """
        Validate data with error recovery.

        Args:
            data: Data to validate (dict, string, etc.)
            strict: If True, raises errors immediately. If False, returns ParseResult with errors.

        Returns:
            Instance of the model class if strict=True and validation succeeds,
            or ParseResult with data and errors if strict=False

        Raises:
            ValidationError: If strict=True and validation fails

        Example:
            class Record(ParsableModel):
                name: str
                age: int
                city: str
                info: Info = parse('{name} | {age} | {city}')

            # Recovery mode
            result = Record.model_validate_with_recovery(
                {"info": "Alice | invalid | NYC"}, strict=False
            )
            # result.data contains successfully parsed fields
            # result.errors contains validation errors
        """
        if strict:
            return cls.model_validate(data)

        # Recovery mode: collect errors
        errors = []
        parsed_data = {}

        try:
            # Try to validate
            return cls.model_validate(data)
        except ValidationError as e:
            # Collect validation errors
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error.get("loc", []))
                errors.append(
                    {
                        "field": field_path,
                        "error": error.get("msg", "Validation error"),
                        "type": error.get("type", "validation_error"),
                        "input": error.get("input"),
                    }
                )

            # Try to extract what we can from the input
            if isinstance(data, dict):
                parsed_data = data.copy()
            elif isinstance(data, str):
                # Try to parse as much as possible
                parsed_data = {}

            return ParseResult(data=parsed_data, errors=errors)


class JsonParsableModel(ParsableModel):
    """
    A ParsableModel that automatically parses JSON strings when instantiated.

    This class extends ParsableModel to automatically handle JSON string inputs.
    Use `model_validate()`, `model_validate_json()`, or `from_json()` to parse JSON strings.

    Example:
        class User(JsonParsableModel):
            name: str
            age: int
            email: str

        # Works with kwargs
        user1 = User(name="Alice", age=30, email="alice@example.com")

        # Works with JSON string - automatically parsed!
        json_str = '{"name": "Bob", "age": 25, "email": "bob@example.com"}'
        user2 = User.model_validate(json_str)  # Automatically detects and parses JSON

        # Also works with dict
        user3 = User.model_validate({"name": "Charlie", "age": 35, "email": "charlie@example.com"})

        # Or use the convenience method
        user4 = User.model_validate_json(json_str)

        # Or use the explicit from_json() method
        user5 = User.from_json(json_str)
    """

    @model_validator(mode="before")
    @classmethod
    def _auto_parse_json(cls, data: Any) -> Any:
        """
        Automatically parse JSON strings if the input is a string.

        This validator runs before the parent class's _parse_string_fields validator,
        so it handles JSON strings at the model level, while the parent handles
        field-level parsing.

        Uses a fast path check (starts with '{') to avoid unnecessary JSON parsing
        for clearly non-JSON strings.
        """
        # Fast path: only attempt JSON parsing if string looks like JSON object
        if isinstance(data, str):
            stripped = data.strip()
            # Quick check: JSON objects start with '{'
            if stripped.startswith("{"):
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, dict):
                        return parsed
                    # If parsed JSON is not a dict (e.g., array, string, number),
                    # let Pydantic handle the validation error
                except json.JSONDecodeError:
                    # Not valid JSON, let parent class handle it
                    pass

        # For non-strings or non-JSON strings, return as-is
        # The parent class's validator will handle field-level parsing
        return data

    @classmethod
    def from_json(cls, json_str: str) -> "JsonParsableModel":
        """
        Parse a JSON string into a model instance.

        This is a convenience method that explicitly indicates JSON parsing intent.
        It's equivalent to `model_validate(json_str)` but makes the intent clearer.

        Args:
            json_str: JSON string to parse

        Returns:
            Instance of the model class

        Raises:
            ValidationError: If the string is not valid JSON or doesn't match the model schema

        Example:
            class User(JsonParsableModel):
                name: str
                age: int

            json_str = '{"name": "Alice", "age": 30}'
            user = User.from_json(json_str)
        """
        return cls.model_validate(json_str)

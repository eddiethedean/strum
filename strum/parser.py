"""Core parsing logic for strum."""

import json
import sys
import types
from typing import Any, ClassVar, Union, get_args, get_origin

import parse as parse_lib
from pydantic import BaseModel, ValidationError, model_validator


class ParsePattern:
    """A pattern that can parse strings into dictionaries based on format strings."""

    def __init__(self, pattern: str):
        """
        Initialize a ParsePattern with a format string.

        Args:
            pattern: Format string like '{name} | {age} | {city}' or '{name} {age} {city}'
        """
        self.pattern = pattern
        # Compile the pattern using the parse library
        self.compiled_pattern = parse_lib.compile(pattern)

    def parse(self, value: str) -> dict[str, Any]:
        """
        Parse a string value according to the pattern.

        Args:
            value: String to parse

        Returns:
            Dictionary with parsed values (with whitespace stripped)

        Raises:
            ValueError: If the string doesn't match the pattern
        """
        result = self.compiled_pattern.parse(value.strip())
        if result is None:
            raise ValueError(f"String '{value}' does not match pattern '{self.pattern}'")

        # Convert ParseResult to dictionary and strip whitespace from values
        return {k: v.strip() if isinstance(v, str) else v for k, v in result.named.items()}

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
        """
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
        self.pattern = "<json>"
        self.compiled_pattern: Any = None

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


class ParsableModel(BaseModel):
    """Base model class that supports parse patterns in field definitions."""

    _parse_patterns: ClassVar[
        dict[str, tuple[ParsePattern | ChainedParsePattern, type[BaseModel]]]
    ] = {}

    def __init_subclass__(cls, **kwargs):
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
    def _try_parse_with_subclass(cls, subclass: type[BaseModel], value: str) -> BaseModel | None:
        """
        Try to parse a string value using a ParsableModel subclass's configuration.

        Checks for:
        1. _json_parse = True flag (try JSON parsing first)
        2. _model_parse_pattern (try format string parsing)

        Returns:
            Parsed model instance if successful, None otherwise
        """
        if not isinstance(value, str):
            return None  # type: ignore[unreachable]

        # Check for _json_parse flag
        if getattr(subclass, "_json_parse", False):
            try:
                data = json.loads(value)
                if isinstance(data, dict):
                    return subclass(**data)
            except (json.JSONDecodeError, ValidationError, ValueError):
                pass  # Fall through to pattern parsing

        # Check for _model_parse_pattern
        if hasattr(subclass, "_model_parse_pattern"):
            attr = subclass._model_parse_pattern
            pattern = (
                attr.default
                if hasattr(attr, "default")
                else (attr if isinstance(attr, str) else None)
            )
            if pattern:
                try:
                    # Type check: subclass should be ParsableModel
                    if issubclass(subclass, ParsableModel):
                        return subclass.parse(value, pattern=pattern)
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
            if hasattr(cls, "_model_parse_pattern"):
                attr = cls._model_parse_pattern
                # Handle Pydantic's ModelPrivateAttr wrapper
                if hasattr(attr, "default"):
                    pattern = attr.default
                elif isinstance(attr, str):
                    pattern = attr
                else:
                    pattern = None
            else:
                pattern = None

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

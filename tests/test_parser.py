"""Tests for the parser functionality."""

from typing import Literal

import pytest
from pydantic import BaseModel, EmailStr, ValidationError

from stringent import ParsableModel, ParseResult, parse, parse_json


class Info(BaseModel):
    name: str
    age: int
    city: str


class Record(ParsableModel):
    id: int
    info: Info = parse("{name} | {age} | {city}") | parse("{name} {age} {city}")  # type: ignore[assignment]
    email: EmailStr
    status: Literal["Active", "Inactive"]


def test_parse_dict_input() -> None:
    """Test parsing when input is already a dictionary."""
    data = {
        "id": 1,
        "info": {"name": "Alice", "age": 30, "city": "New York"},
        "email": "alice@example.com",
        "status": "Active",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert record.id == 1  # type: ignore[attr-defined]
    assert record.info.name == "Alice"  # type: ignore[attr-defined]
    assert record.info.age == 30  # type: ignore[attr-defined]
    assert record.info.city == "New York"  # type: ignore[attr-defined]
    assert record.email == "alice@example.com"  # type: ignore[attr-defined]
    assert record.status == "Active"


def test_parse_pipe_separated_string() -> None:
    """Test parsing pipe-separated string."""
    data = {
        "id": 3,
        "info": "Charlie | 27 | Chicago",
        "email": "charlie@example.com",
        "status": "Active",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert record.id == 3  # type: ignore[attr-defined]
    assert record.info.name == "Charlie"  # type: ignore[attr-defined]
    assert record.info.age == 27  # type: ignore[attr-defined]
    assert record.info.city == "Chicago"  # type: ignore[attr-defined]


def test_parse_space_separated_string() -> None:
    """Test parsing space-separated string."""
    data = {
        "id": 5,
        "info": "Eve 35 Dallas",
        "email": "eve@example.com",
        "status": "Inactive",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert record.id == 5  # type: ignore[attr-defined]
    assert record.info.name == "Eve"  # type: ignore[attr-defined]
    assert record.info.age == 35  # type: ignore[attr-defined]
    assert record.info.city == "Dallas"  # type: ignore[attr-defined]


def test_parse_invalid_string() -> None:
    """Test that invalid strings raise validation errors."""
    data = {
        "id": 1,
        "info": "Invalid format",
        "email": "test@example.com",
        "status": "Active",
    }
    with pytest.raises(ValidationError):
        Record(**data)  # type: ignore[arg-type]


def test_parse_pattern_chaining() -> None:
    """Test that pattern chaining works correctly."""
    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    # First pattern should match
    result1 = chained.parse("Alice | 30")
    assert result1 == {"name": "Alice", "age": "30"}

    # Second pattern should match if first fails
    result2 = chained.parse("Bob 25")
    assert result2 == {"name": "Bob", "age": "25"}


def test_json_parse_pattern_standalone() -> None:
    """Test that the JSON parse pattern works on its own."""
    pattern = parse_json()
    result = pattern.parse('{"name": "Alice", "age": 30, "city": "NYC"}')
    assert result == {"name": "Alice", "age": 30, "city": "NYC"}


def test_json_parse_pattern_chained_in_model_field() -> None:
    """Test that parse_json() can be chained for model fields."""

    class RecordWithJsonInfo(ParsableModel):
        id: int
        info: Info = parse_json() | parse("{name} | {age} | {city}") | parse("{name} {age} {city}")  # type: ignore[assignment]
        email: EmailStr
        status: Literal["Active", "Inactive"]

    data = {
        "id": 8,
        "info": '{"name": "Joe", "age": 55, "city": "Tampa"}',
        "email": "joe@example.com",
        "status": "Active",
    }
    record = RecordWithJsonInfo(**data)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert record.id == 8  # type: ignore[attr-defined]
    assert record.info.name == "Joe"  # type: ignore[attr-defined]
    assert record.info.age == 55  # type: ignore[attr-defined]
    assert record.info.city == "Tampa"  # type: ignore[attr-defined]
    assert record.email == "joe@example.com"  # type: ignore[attr-defined]
    assert record.status == "Active"


def test_parse_pattern_single() -> None:
    """Test single parse pattern."""
    pattern = parse("{name} | {age} | {city}")
    result = pattern.parse("John | 25 | NYC")
    assert result == {"name": "John", "age": "25", "city": "NYC"}


def test_parse_with_extra_spaces() -> None:
    """Test that extra spaces are handled correctly."""
    pattern = parse("{name} | {age} | {city}")
    result = pattern.parse("  John  |  25  |  NYC  ")
    assert result == {"name": "John", "age": "25", "city": "NYC"}


def test_parse_pattern_or_with_invalid_type() -> None:
    """Test that ParsePattern.__or__ with invalid_type returns NotImplemented."""

    pattern = parse("{name}")
    # Call __or__ directly to test the NotImplemented path
    result = pattern.__or__(42)  # type: ignore[operator]  # int is not a ParsePattern
    assert result is NotImplemented


def test_parse_pattern_ror_with_invalid_type() -> None:
    """Test that ParsePattern.__ror__ with invalid_type returns NotImplemented."""

    pattern = parse("{name}")
    # Call __ror__ directly to test the NotImplemented path
    result = pattern.__ror__(42)  # int is not a ParsePattern
    assert result is NotImplemented


def test_chained_pattern_or_with_invalid_type() -> None:
    """Test that ChainedParsePattern.__or__ with invalid_type returns NotImplemented."""

    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    # Call __or__ directly to test the NotImplemented path
    result = chained.__or__("invalid")  # type: ignore[operator]  # str is not ParsePattern or ChainedParsePattern
    assert result is NotImplemented


def test_chained_pattern_ror_with_invalid_type() -> None:
    """Test that ChainedParsePattern.__ror__ with invalid_type returns NotImplemented."""

    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    # Call __ror__ directly to test the NotImplemented path
    result = chained.__ror__("invalid")  # str is not ParsePattern or ChainedParsePattern
    assert result is NotImplemented


def test_chained_pattern_empty_list() -> None:
    """Test that ChainedParsePattern raises ValueError for empty patterns list."""
    from stringent.parser import ChainedParsePattern

    with pytest.raises(ValueError, match="requires at least one pattern"):
        ChainedParsePattern([])


def test_parse_pattern_type_error() -> None:
    """Test that ParsePattern.parse raises TypeError for non-string values."""
    pattern = parse("{name} | {age}")

    with pytest.raises(TypeError, match="Expected string"):
        pattern.parse(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected string"):
        pattern.parse(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected string"):
        pattern.parse({"name": "Alice"})  # type: ignore[arg-type]


def test_chained_pattern_type_error() -> None:
    """Test that ChainedParsePattern.parse raises TypeError for non-string values."""
    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    with pytest.raises(TypeError, match="Expected string"):
        chained.parse(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected string"):
        chained.parse(123)  # type: ignore[arg-type]


def test_parse_pattern_ror_with_valid_type() -> None:
    """Test that ParsePattern.__ror__ with valid ParsePattern works correctly."""
    pattern1 = parse("{name}")
    pattern2 = parse("{age}")

    # Call __ror__ directly: pattern2.__ror__(pattern1) means pattern1 | pattern2
    result = pattern2.__ror__(pattern1)
    from stringent.parser import ChainedParsePattern

    assert isinstance(result, ChainedParsePattern)
    assert len(result.patterns) == 2
    assert result.patterns[0] == pattern1
    assert result.patterns[1] == pattern2


def test_chained_pattern_or_with_parse_pattern() -> None:
    """Test that ChainedParsePattern.__or__ with ParsePattern works correctly."""
    from stringent.parser import ChainedParsePattern

    pattern1 = parse("{name}")
    pattern2 = parse("{age}")
    pattern3 = parse("{city}")
    chained = pattern1 | pattern2

    # Call __or__ directly to test the valid path
    result = chained.__or__(pattern3)
    assert isinstance(result, ChainedParsePattern)
    assert len(result.patterns) == 3
    assert result.patterns[0] == pattern1
    assert result.patterns[1] == pattern2
    assert result.patterns[2] == pattern3


def test_chained_pattern_or_with_chained_pattern() -> None:
    """Test that ChainedParsePattern.__or__ with ChainedParsePattern works correctly."""
    from stringent.parser import ChainedParsePattern

    pattern1 = parse("{name}")
    pattern2 = parse("{age}")
    pattern3 = parse("{city}")
    pattern4 = parse("{id}")
    chained1 = pattern1 | pattern2
    chained2 = pattern3 | pattern4

    # Call __or__ directly to test the valid path
    result = chained1.__or__(chained2)
    assert isinstance(result, ChainedParsePattern)
    assert len(result.patterns) == 4
    assert result.patterns[0] == pattern1
    assert result.patterns[1] == pattern2
    assert result.patterns[2] == pattern3
    assert result.patterns[3] == pattern4


def test_chained_pattern_ror_with_parse_pattern() -> None:
    """Test that ChainedParsePattern.__ror__ with ParsePattern works correctly."""
    from stringent.parser import ChainedParsePattern

    pattern1 = parse("{name}")
    pattern2 = parse("{age}")
    pattern3 = parse("{city}")
    chained = pattern1 | pattern2

    # Call __ror__ directly: chained.__ror__(pattern3) means pattern3 | chained
    result = chained.__ror__(pattern3)
    assert isinstance(result, ChainedParsePattern)
    assert len(result.patterns) == 3
    assert result.patterns[0] == pattern3
    assert result.patterns[1] == pattern1
    assert result.patterns[2] == pattern2


def test_chained_pattern_ror_with_chained_pattern() -> None:
    """Test that ChainedParsePattern.__ror__ with ChainedParsePattern works correctly."""
    from stringent.parser import ChainedParsePattern

    pattern1 = parse("{name}")
    pattern2 = parse("{age}")
    pattern3 = parse("{city}")
    pattern4 = parse("{id}")
    chained1 = pattern1 | pattern2
    chained2 = pattern3 | pattern4

    # Call __ror__ directly: chained1.__ror__(chained2) means chained2 | chained1
    result = chained1.__ror__(chained2)
    assert isinstance(result, ChainedParsePattern)
    assert len(result.patterns) == 4
    assert result.patterns[0] == pattern3
    assert result.patterns[1] == pattern4
    assert result.patterns[2] == pattern1
    assert result.patterns[3] == pattern2


def test_parse_string_fields_with_non_dict() -> None:
    """Test that _parse_string_fields handles non-dict data correctly."""
    from stringent.parser import ParsableModel

    class SimpleModel(ParsableModel):
        name: str

    # Test with list
    result = SimpleModel._parse_string_fields([1, 2, 3])  # type: ignore[operator]
    assert result == [1, 2, 3]

    # Test with string
    result = SimpleModel._parse_string_fields("not a dict")  # type: ignore[operator]
    assert result == "not a dict"

    # Test with None
    result = SimpleModel._parse_string_fields(None)  # type: ignore[operator]
    assert result is None

    # Test with int
    result = SimpleModel._parse_string_fields(42)  # type: ignore[operator]
    assert result == 42


def test_parse_string_fields_no_patterns() -> None:
    """Test that _parse_string_fields works with models that have no parse patterns."""
    from stringent.parser import ParsableModel

    class ModelWithoutPatterns(ParsableModel):
        name: str
        age: int

    # Should return data as-is since there are no parse patterns
    data = {"name": "Alice", "age": 30}
    result = ModelWithoutPatterns._parse_string_fields(data)  # type: ignore[operator]
    assert result == data


def test_parse_string_fields_no_parse_patterns_attribute() -> None:
    """Test that _parse_string_fields handles missing _parse_patterns attribute."""
    from stringent.parser import ParsableModel

    class ModelWithoutPatterns(ParsableModel):
        name: str
        age: int

    # Manually remove _parse_patterns to test the defensive check
    if hasattr(ModelWithoutPatterns, "_parse_patterns"):
        delattr(ModelWithoutPatterns, "_parse_patterns")

    data = {"name": "Alice", "age": 30}
    result = ModelWithoutPatterns._parse_string_fields(data)  # type: ignore[operator]
    assert result == data


def test_parse_with_non_string_values() -> None:
    """Test that non-string values in parse results are preserved correctly."""
    from stringent.parser import ParsePattern

    # The ParsePattern.parse method should handle non-string values
    # Since parse library returns strings by default, we test the isinstance check
    # by creating a pattern that returns strings with whitespace
    pattern = ParsePattern("{name} is {age} years old")

    # Test with a value that has whitespace (string case)
    result = pattern.parse("Alice is 30 years old")
    assert isinstance(result["age"], str)
    assert result["age"] == "30"

    # Test that strings are stripped correctly
    result2 = pattern.parse("  Bob  is  25  years old")
    assert result2["name"] == "Bob"  # Should be stripped
    assert result2["age"] == "25"  # Should be stripped


def test_parse_pattern_inheritance() -> None:
    """Test that parse patterns are inherited from parent classes."""

    class BaseRecord(ParsableModel):
        info: Info = parse("{name} | {age} | {city}")  # type: ignore[assignment]

    class DerivedRecord(BaseRecord):
        extra: str

    # DerivedRecord should inherit the info parse pattern
    assert "info" in DerivedRecord._parse_patterns
    assert DerivedRecord._parse_patterns["info"][1] == Info

    # Test that inherited pattern works
    data = {"info": "Alice | 30 | NYC", "extra": "test"}
    record = DerivedRecord(**data)  # type: ignore[arg-type]
    assert record.info.name == "Alice"  # type: ignore[attr-defined]
    assert record.info.age == 30  # type: ignore[attr-defined]
    assert record.info.city == "NYC"  # type: ignore[attr-defined]
    assert record.extra == "test"


def test_parse_pattern_override() -> None:
    """Test that child classes can override parent parse patterns."""

    class BaseRecord(ParsableModel):
        info: Info = parse("{name} | {age} | {city}")  # type: ignore[assignment]

    class DerivedRecord(BaseRecord):
        info: Info = parse("{name} {age} {city}")  # type: ignore[assignment]  # Override with different pattern  # type: ignore[assignment]

    # DerivedRecord should have its own pattern, not the parent's
    assert "info" in DerivedRecord._parse_patterns
    pattern_obj = DerivedRecord._parse_patterns["info"][0]
    # The pattern should match space-separated, not pipe-separated
    result = pattern_obj.parse("Bob 25 Chicago")
    assert result == {"name": "Bob", "age": "25", "city": "Chicago"}

    # Test that the overridden pattern works
    data = {"info": "Eve 35 Dallas"}
    record = DerivedRecord(**data)  # type: ignore[arg-type]
    assert record.info.name == "Eve"  # type: ignore[attr-defined]
    assert record.info.age == 35  # type: ignore[attr-defined]
    assert record.info.city == "Dallas"  # type: ignore[attr-defined]


def test_parsable_model_parse_with_pattern() -> None:
    """Test that ParsableModel.parse() works with a provided pattern."""

    class SimpleRecord(ParsableModel):
        id: int
        name: str
        age: int

    # Parse with explicit pattern
    record = SimpleRecord.parse("1 | Alice | 30", pattern="{id} | {name} | {age}")
    assert record.id == 1  # type: ignore[attr-defined]
    assert record.name == "Alice"  # type: ignore[attr-defined]
    assert record.age == 30  # type: ignore[attr-defined]


def test_parsable_model_parse_with_class_pattern() -> None:
    """Test that ParsableModel.parse() works with _model_parse_pattern class attribute."""

    class SimpleRecord(ParsableModel):
        _model_parse_pattern = "{id} | {name} | {age}"
        id: int
        name: str
        age: int

    # Parse using class-defined pattern
    record = SimpleRecord.parse("2 | Bob | 25")
    assert record.id == 2  # type: ignore[attr-defined]
    assert record.name == "Bob"  # type: ignore[attr-defined]
    assert record.age == 25  # type: ignore[attr-defined]


def test_parsable_model_parse_with_nested_parsing() -> None:
    """Test that ParsableModel.parse() works with nested parse patterns."""

    class RecordWithNested(ParsableModel):
        # Use a different delimiter for the outer pattern to avoid conflicts
        _model_parse_pattern = "{id} || {info} || {email}"
        id: int
        info: Info = parse("{name} | {age} | {city}")  # type: ignore[assignment]
        email: EmailStr

    # Parse - the info field should be automatically parsed from string
    # The pattern matches: id="1", info="Alice | 30 | NYC", email="alice@example.com"
    record = RecordWithNested.parse("1 || Alice | 30 | NYC || alice@example.com")
    assert record.id == 1  # type: ignore[attr-defined]
    assert record.info.name == "Alice"  # type: ignore[attr-defined]
    assert record.info.age == 30  # type: ignore[attr-defined]
    assert record.info.city == "NYC"  # type: ignore[attr-defined]
    assert record.email == "alice@example.com"  # type: ignore[attr-defined]


def test_parsable_model_parse_no_pattern_error() -> None:
    """Test that ParsableModel.parse() raises error when no pattern is provided."""

    class SimpleRecord(ParsableModel):
        id: int
        name: str

    # Should raise ValueError when no pattern provided and _model_parse_pattern not defined
    with pytest.raises(ValueError, match="No parse pattern provided"):
        SimpleRecord.parse("1 | Alice")


def test_parsable_model_parse_invalid_string() -> None:
    """Test that ParsableModel.parse() raises error when string doesn't match pattern."""

    class SimpleRecord(ParsableModel):
        _model_parse_pattern = "{id} | {name} | {age}"
        id: int
        name: str
        age: int

    # Should raise ValueError when string doesn't match pattern
    with pytest.raises(ValueError, match="does not match pattern"):
        SimpleRecord.parse("invalid string")


def test_parsable_model_parse_json() -> None:
    """Test that ParsableModel.parse_json() works with JSON strings."""

    class SimpleRecord(ParsableModel):
        id: int
        name: str
        age: int

    json_str = '{"id": 1, "name": "Alice", "age": 30}'
    record = SimpleRecord.parse_json(json_str)
    assert record.id == 1  # type: ignore[attr-defined]
    assert record.name == "Alice"  # type: ignore[attr-defined]
    assert record.age == 30  # type: ignore[attr-defined]


def test_parsable_model_parse_json_with_nested_parsing() -> None:
    """Test that ParsableModel.parse_json() works with nested parse patterns."""

    class RecordWithNested(ParsableModel):
        id: int
        info: Info = parse("{name} | {age} | {city}")  # type: ignore[assignment]
        email: EmailStr

    json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}'
    record = RecordWithNested.parse_json(json_str)
    assert record.id == 1  # type: ignore[attr-defined]
    assert record.info.name == "Alice"  # type: ignore[attr-defined]
    assert record.info.age == 30  # type: ignore[attr-defined]
    assert record.info.city == "NYC"  # type: ignore[attr-defined]
    assert record.email == "alice@example.com"  # type: ignore[attr-defined]


def test_parsable_model_parse_json_invalid_json() -> None:
    """Test that ParsableModel.parse_json() raises error for invalid JSON."""
    from pydantic import ValidationError

    class SimpleRecord(ParsableModel):
        id: int
        name: str

    # Should raise ValidationError for invalid JSON (Pydantic's error)
    with pytest.raises(ValidationError):
        SimpleRecord.parse_json("not valid json")


def test_union_type_with_model_parse_pattern() -> None:
    """Test union types with _model_parse_pattern."""

    class Info(ParsableModel):
        name: str
        age: int
        city: str

    class PipeInfo(Info):
        _model_parse_pattern = "{name} | {age} | {city}"

    class SpaceInfo(Info):
        _model_parse_pattern = "{name} {age} {city}"

    class Record(ParsableModel):
        id: int
        info: PipeInfo | SpaceInfo
        email: EmailStr

    # Test pipe-separated parsing
    data1 = {
        "id": 1,
        "info": "Alice | 30 | NYC",
        "email": "alice@example.com",
    }
    record1 = Record(**data1)  # type: ignore[arg-type]
    assert isinstance(record1.info, PipeInfo)
    assert record1.info.name == "Alice"  # type: ignore[attr-defined]
    assert record1.info.age == 30  # type: ignore[attr-defined]
    assert record1.info.city == "NYC"  # type: ignore[attr-defined]

    # Test space-separated parsing
    data2 = {
        "id": 2,
        "info": "Bob 25 Chicago",
        "email": "bob@example.com",
    }
    record2 = Record(**data2)  # type: ignore[arg-type]
    assert isinstance(record2.info, SpaceInfo)
    assert record2.info.name == "Bob"  # type: ignore[attr-defined]
    assert record2.info.age == 25  # type: ignore[attr-defined]
    assert record2.info.city == "Chicago"  # type: ignore[attr-defined]


def test_union_type_with_json_parse_flag() -> None:
    """Test union types with _json_parse = True."""

    class Info(ParsableModel):
        name: str
        age: int
        city: str

    class JsonInfo(Info):
        _json_parse = True

    class PipeInfo(Info):
        _model_parse_pattern = "{name} | {age} | {city}"

    class Record(ParsableModel):
        id: int
        info: JsonInfo | PipeInfo
        email: EmailStr

    # Test JSON parsing
    data = {
        "id": 1,
        "info": '{"name": "Joe", "age": 55, "city": "Tampa"}',
        "email": "joe@example.com",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert isinstance(record.info, JsonInfo)
    assert record.info.name == "Joe"  # type: ignore[attr-defined]
    assert record.info.age == 55  # type: ignore[attr-defined]
    assert record.info.city == "Tampa"  # type: ignore[attr-defined]


def test_union_type_with_both_flags() -> None:
    """Test class with both _json_parse and _model_parse_pattern."""

    class Info(ParsableModel):
        name: str
        age: int
        city: str

    class FlexibleInfo(Info):
        _json_parse = True
        _model_parse_pattern = "{name} | {age} | {city}"

    class Record(ParsableModel):
        id: int
        info: FlexibleInfo
        email: EmailStr

    # Test JSON parsing (should be tried first)
    data1 = {
        "id": 1,
        "info": '{"name": "Alice", "age": 30, "city": "NYC"}',
        "email": "alice@example.com",
    }
    record1 = Record(**data1)  # type: ignore[arg-type]
    assert record1.info.name == "Alice"  # type: ignore[attr-defined]
    assert record1.info.age == 30  # type: ignore[attr-defined]
    assert record1.info.city == "NYC"  # type: ignore[attr-defined]

    # Test pattern parsing (fallback when JSON fails)
    data2 = {
        "id": 2,
        "info": "Bob | 25 | Chicago",
        "email": "bob@example.com",
    }
    record2 = Record(**data2)  # type: ignore[arg-type]
    assert record2.info.name == "Bob"  # type: ignore[attr-defined]
    assert record2.info.age == 25  # type: ignore[attr-defined]
    assert record2.info.city == "Chicago"  # type: ignore[attr-defined]


def test_union_type_parsing_order() -> None:
    """Test that union types are tried in order."""

    class Info(ParsableModel):
        name: str
        age: int
        city: str

    class FirstInfo(Info):
        _model_parse_pattern = "{name} | {age} | {city}"

    class SecondInfo(Info):
        _model_parse_pattern = "{name} {age} {city}"

    class Record(ParsableModel):
        id: int
        info: FirstInfo | SecondInfo
        email: EmailStr

    # This string matches FirstInfo pattern, so it should use FirstInfo
    data = {
        "id": 1,
        "info": "Alice | 30 | NYC",
        "email": "alice@example.com",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert isinstance(record.info, FirstInfo)
    assert record.info.name == "Alice"  # type: ignore[attr-defined]


def test_union_type_fallback_behavior() -> None:
    """Test fallback when first type fails."""

    class Info(ParsableModel):
        name: str
        age: int
        city: str

    class PipeInfo(Info):
        _model_parse_pattern = "{name} | {age} | {city}"

    class SpaceInfo(Info):
        _model_parse_pattern = "{name} {age} {city}"

    class Record(ParsableModel):
        id: int
        info: PipeInfo | SpaceInfo
        email: EmailStr

    # This string doesn't match PipeInfo pattern, so should fall back to SpaceInfo
    data = {
        "id": 1,
        "info": "Eve 35 Dallas",
        "email": "eve@example.com",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert isinstance(record.info, SpaceInfo)
    assert record.info.name == "Eve"  # type: ignore[attr-defined]
    assert record.info.age == 35  # type: ignore[attr-defined]
    assert record.info.city == "Dallas"  # type: ignore[attr-defined]


def test_union_type_with_dict_input() -> None:
    """Test that dict inputs still work (no parsing needed)."""

    class Info(ParsableModel):
        name: str
        age: int
        city: str

    class PipeInfo(Info):
        _model_parse_pattern = "{name} | {age} | {city}"

    class JsonInfo(Info):
        _json_parse = True

    class Record(ParsableModel):
        id: int
        info: JsonInfo | PipeInfo
        email: EmailStr

    # Dict input should work without parsing
    data = {
        "id": 1,
        "info": {"name": "Alice", "age": 30, "city": "NYC"},
        "email": "alice@example.com",
    }
    record = Record(**data)  # type: ignore[arg-type]
    assert record.info.name == "Alice"  # type: ignore[attr-defined]
    assert record.info.age == 30  # type: ignore[attr-defined]
    assert record.info.city == "NYC"  # type: ignore[attr-defined]


def test_json_parsable_model_auto_parse() -> None:
    """Test that JsonParsableModel automatically parses JSON strings."""

    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int
        email: str

    # Test with JSON string via model_validate
    json_str = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'
    user1 = User.model_validate(json_str)
    assert user1.name == "Alice"  # type: ignore[attr-defined]
    assert user1.age == 30  # type: ignore[attr-defined]
    assert user1.email == "alice@example.com"  # type: ignore[attr-defined]

    # Test with model_validate_json
    user2 = User.model_validate_json(json_str)
    assert user2.name == "Alice"  # type: ignore[attr-defined]
    assert user2.age == 30  # type: ignore[attr-defined]
    assert user2.email == "alice@example.com"  # type: ignore[attr-defined]

    # Test with dict (should still work)
    user3 = User.model_validate({"name": "Bob", "age": 25, "email": "bob@example.com"})
    assert user3.name == "Bob"  # type: ignore[attr-defined]
    assert user3.age == 25  # type: ignore[attr-defined]
    assert user3.email == "bob@example.com"  # type: ignore[attr-defined]

    # Test with kwargs (normal Pydantic behavior)
    user4 = User(name="Charlie", age=35, email="charlie@example.com")
    assert user4.name == "Charlie"  # type: ignore[attr-defined]
    assert user4.age == 35  # type: ignore[attr-defined]
    assert user4.email == "charlie@example.com"  # type: ignore[attr-defined]


def test_json_parsable_model_with_nested_parsing() -> None:
    """Test that JsonParsableModel works with nested parse patterns."""

    from pydantic import BaseModel

    from stringent import JsonParsableModel, parse

    class Info(BaseModel):
        name: str
        age: int
        city: str

    class User(JsonParsableModel):
        id: int
        info: Info = parse("{name} | {age} | {city}")  # type: ignore[assignment]
        email: str

    # JSON string with nested string that needs parsing
    json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}'
    user = User.model_validate(json_str)
    assert user.id == 1  # type: ignore[attr-defined]
    assert user.info.name == "Alice"  # type: ignore[attr-defined]
    assert user.info.age == 30  # type: ignore[attr-defined]
    assert user.info.city == "NYC"  # type: ignore[attr-defined]
    assert user.email == "alice@example.com"  # type: ignore[attr-defined]


def test_json_parsable_model_invalid_json_array() -> None:
    """Test that JsonParsableModel rejects JSON arrays."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int

    # JSON array should fail (not a dict)
    with pytest.raises(ValidationError):
        User.model_validate('[{"name": "Alice", "age": 30}]')


def test_json_parsable_model_invalid_json_string() -> None:
    """Test that JsonParsableModel rejects JSON string primitives."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int

    # JSON string primitive should fail
    with pytest.raises(ValidationError):
        User.model_validate('"just a string"')

    # JSON number should fail
    with pytest.raises(ValidationError):
        User.model_validate("42")

    # JSON boolean should fail
    with pytest.raises(ValidationError):
        User.model_validate("true")

    # JSON null should fail
    with pytest.raises(ValidationError):
        User.model_validate("null")


def test_json_parsable_model_malformed_json() -> None:
    """Test that JsonParsableModel handles malformed JSON gracefully."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int

    # Missing closing brace
    with pytest.raises(ValidationError):
        User.model_validate('{"name": "Alice", "age": 30')

    # Invalid JSON syntax
    with pytest.raises(ValidationError):
        User.model_validate('{"name": "Alice", age: 30}')


def test_json_parsable_model_empty_string() -> None:
    """Test that JsonParsableModel handles empty strings."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int

    # Empty string should fail (not valid JSON)
    with pytest.raises(ValidationError):
        User.model_validate("")


def test_json_parsable_model_whitespace_string() -> None:
    """Test that JsonParsableModel handles whitespace-only strings."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int

    # Whitespace-only string should fail (not valid JSON)
    with pytest.raises(ValidationError):
        User.model_validate("   ")


def test_json_parsable_model_with_parse_json_field() -> None:
    """Test that JsonParsableModel works with parse_json() field pattern."""
    from pydantic import BaseModel

    from stringent import JsonParsableModel, parse_json

    class Info(BaseModel):
        name: str
        age: int

    class User(JsonParsableModel):
        id: int
        info: Info = parse_json()  # type: ignore[assignment]
        email: str

    # Top-level JSON with nested JSON string field
    json_str = (
        '{"id": 1, "info": "{\\"name\\": \\"Alice\\", \\"age\\": 30}", '
        '"email": "alice@example.com"}'
    )
    user = User.model_validate(json_str)
    assert user.id == 1  # type: ignore[attr-defined]
    assert user.info.name == "Alice"  # type: ignore[attr-defined]
    assert user.info.age == 30  # type: ignore[attr-defined]
    assert user.email == "alice@example.com"  # type: ignore[attr-defined]


def test_json_parsable_model_with_chained_parse_json() -> None:
    """Test that JsonParsableModel works with chained patterns including parse_json()."""
    from pydantic import BaseModel

    from stringent import JsonParsableModel, parse, parse_json

    class Info(BaseModel):
        name: str
        age: int
        city: str

    class User(JsonParsableModel):
        id: int
        info: Info = parse_json() | parse("{name} | {age} | {city}")  # type: ignore[assignment]
        email: str

    # Test with JSON string in field (should use parse_json())
    json_str = (
        '{"id": 1, "info": "{\\"name\\": \\"Alice\\", \\"age\\": 30, '
        '\\"city\\": \\"NYC\\"}", "email": "alice@example.com"}'
    )
    user1 = User.model_validate(json_str)
    assert user1.info.name == "Alice"  # type: ignore[attr-defined]
    assert user1.info.age == 30  # type: ignore[attr-defined]
    assert user1.info.city == "NYC"  # type: ignore[attr-defined]

    # Test with pattern string in field (should use parse())
    json_str2 = '{"id": 2, "info": "Bob | 25 | Chicago", "email": "bob@example.com"}'
    user2 = User.model_validate(json_str2)
    assert user2.info.name == "Bob"  # type: ignore[attr-defined]
    assert user2.info.age == 25  # type: ignore[attr-defined]
    assert user2.info.city == "Chicago"  # type: ignore[attr-defined]


def test_json_parsable_model_inheritance() -> None:
    """Test that JsonParsableModel inheritance works correctly."""
    from stringent import JsonParsableModel

    class BaseUser(JsonParsableModel):
        name: str
        age: int

    class DerivedUser(BaseUser):
        email: str

    # Should work with JSON string
    json_str = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'
    user = DerivedUser.model_validate(json_str)
    assert user.name == "Alice"  # type: ignore[attr-defined]
    assert user.age == 30  # type: ignore[attr-defined]
    assert user.email == "alice@example.com"  # type: ignore[attr-defined]


def test_json_parsable_model_with_union_types() -> None:
    """Test that JsonParsableModel works with union types."""
    from stringent import JsonParsableModel

    class JsonUser(JsonParsableModel):
        name: str
        age: int

    class PatternUser(ParsableModel):
        _model_parse_pattern = "{name} | {age}"
        name: str
        age: int

    class Record(ParsableModel):
        id: int
        user: JsonUser | PatternUser

    # Test with JSON string (should use JsonUser)
    data = {"id": 1, "user": '{"name": "Alice", "age": 30}'}
    record = Record(**data)  # type: ignore[arg-type]
    assert isinstance(record.user, JsonUser)
    assert record.user.name == "Alice"  # type: ignore[attr-defined]
    assert record.user.age == 30  # type: ignore[attr-defined]

    # Test with pattern string (should use PatternUser)
    data2 = {"id": 2, "user": "Bob | 25"}
    record2 = Record(**data2)  # type: ignore[arg-type]
    assert isinstance(record2.user, PatternUser)
    assert record2.user.name == "Bob"  # type: ignore[attr-defined]
    assert record2.user.age == 25  # type: ignore[attr-defined]


def test_json_parsable_model_with_model_parse_pattern() -> None:
    """Test that JsonParsableModel works with _model_parse_pattern (should prioritize JSON)."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        _model_parse_pattern = "{name} | {age}"
        name: str
        age: int

    # JSON string should be parsed as JSON (not pattern)
    json_str = '{"name": "Alice", "age": 30}'
    user = User.model_validate(json_str)
    assert user.name == "Alice"  # type: ignore[attr-defined]
    assert user.age == 30  # type: ignore[attr-defined]

    # Pattern string should still work via model_validate with dict
    # (but not as string since JsonParsableModel intercepts strings as JSON)
    user2 = User.model_validate({"name": "Bob", "age": 25})
    assert user2.name == "Bob"  # type: ignore[attr-defined]
    assert user2.age == 25  # type: ignore[attr-defined]


def test_json_parsable_model_non_json_string_fallback() -> None:
    """Test that JsonParsableModel falls back gracefully for non-JSON strings."""
    from pydantic import BaseModel

    from stringent import JsonParsableModel, parse

    class Info(BaseModel):
        name: str
        age: int

    class User(JsonParsableModel):
        id: int
        info: Info = parse("{name} | {age}")  # type: ignore[assignment]
        email: str

    # Non-JSON string at top level should fail (not a dict)
    # But field-level parsing should still work if we pass a dict
    data = {"id": 1, "info": "Alice | 30", "email": "alice@example.com"}
    user = User.model_validate(data)
    assert user.info.name == "Alice"  # type: ignore[attr-defined]
    assert user.info.age == 30  # type: ignore[attr-defined]


def test_json_parsable_model_from_json_method() -> None:
    """Test the from_json() convenience method."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int
        email: str

    json_str = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'
    user = User.from_json(json_str)
    assert user.name == "Alice"  # type: ignore[attr-defined]
    assert user.age == 30  # type: ignore[attr-defined]
    assert user.email == "alice@example.com"  # type: ignore[attr-defined]

    # Should be equivalent to model_validate
    user2 = User.model_validate(json_str)
    assert user.name == user2.name  # type: ignore[attr-defined]
    assert user.age == user2.age  # type: ignore[attr-defined]
    assert user.email == user2.email  # type: ignore[attr-defined]


def test_json_parsable_model_fast_path_check() -> None:
    """Test that JsonParsableModel uses fast path for non-JSON strings."""
    from stringent import JsonParsableModel

    class User(JsonParsableModel):
        name: str
        age: int

    # String that doesn't start with '{' should not attempt JSON parsing
    # This should fail with ValidationError (not JSONDecodeError)
    with pytest.raises(ValidationError):
        User.model_validate("not a json string")

    # String that starts with '{' but isn't valid JSON should fail gracefully
    with pytest.raises(ValidationError):
        User.model_validate("{invalid json")


def test_optional_fields_in_pattern() -> None:
    """Test optional fields in patterns."""

    from pydantic import BaseModel

    from stringent import ParsableModel, parse

    class Info(BaseModel):
        name: str
        age: int | None = None
        city: str

    class Record(ParsableModel):
        info: Info = parse("{name} | {age?} | {city}")  # type: ignore[assignment]

    # Works with all fields
    record1 = Record(info="Alice | 30 | NYC")  # type: ignore[arg-type]
    assert record1.info.name == "Alice"  # type: ignore[attr-defined]
    assert record1.info.age == 30  # type: ignore[attr-defined]
    assert record1.info.city == "NYC"  # type: ignore[attr-defined]

    # Works with missing optional field
    record2 = Record(info="Bob | NYC")  # type: ignore[arg-type]
    assert record2.info.name == "Bob"  # type: ignore[attr-defined]
    assert record2.info.age is None  # type: ignore[attr-defined]
    assert record2.info.city == "NYC"  # type: ignore[attr-defined]


def test_regex_parsing() -> None:
    """Test regex parsing pattern."""
    from pydantic import BaseModel

    from stringent import ParsableModel, parse_regex

    class LogEntry(BaseModel):
        timestamp: str
        level: str
        message: str

    class Record(ParsableModel):
        entry: LogEntry = parse_regex(  # type: ignore[assignment]
            r"(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)"
        )

    # Parse log line
    record = Record(entry="2024-01-15 [ERROR] Database connection failed")  # type: ignore[arg-type]
    assert record.entry.timestamp == "2024-01-15"  # type: ignore[attr-defined]
    assert record.entry.level == "ERROR"  # type: ignore[attr-defined]
    assert record.entry.message == "Database connection failed"  # type: ignore[attr-defined]


def test_error_recovery() -> None:
    """Test error recovery mode."""
    from pydantic import BaseModel

    from stringent import ParsableModel, ParseResult

    class Info(BaseModel):
        name: str
        age: int
        city: str

    class Record(ParsableModel):
        _model_parse_pattern = "{name} | {age} | {city}"
        name: str
        age: int
        city: str

    # Recovery mode - returns partial result
    result = Record.parse_with_recovery("Alice | invalid | NYC", strict=False)
    assert isinstance(result, ParseResult)
    assert result.data["name"] == "Alice"
    assert result.data["city"] == "NYC"
    assert len(result.errors) > 0
    assert not result  # ParseResult is falsy when there are errors

    # Strict mode - raises error
    with pytest.raises(ValidationError):
        Record.parse_with_recovery("Alice | invalid | NYC", strict=True)


def test_chained_pattern_type_error_non_parse_pattern() -> None:
    """Test that ChainedParsePattern raises TypeError for non-ParsePattern instances."""
    from stringent.parser import ChainedParsePattern

    pattern1 = parse("{name}")
    # Try to create with a non-ParsePattern
    with pytest.raises(TypeError, match="All patterns must be ParsePattern instances"):
        ChainedParsePattern([pattern1, "not a pattern"])  # type: ignore[list-item]


def test_json_parse_pattern_non_string_input() -> None:
    """Test that JsonParsePattern.parse raises ValueError for non-string input."""
    pattern = parse_json()

    with pytest.raises(ValueError, match="Value must be a JSON string"):
        pattern.parse(123)  # type: ignore[arg-type]


def test_regex_parse_pattern_non_string_input() -> None:
    """Test that RegexParsePattern.parse raises TypeError for non-string input."""
    from stringent import parse_regex

    pattern = parse_regex(r"(?P<name>\w+)")

    with pytest.raises(TypeError, match="Expected string"):
        pattern.parse(123)  # type: ignore[arg-type]


def test_parsable_model_extract_pattern_edge_cases() -> None:
    """Test edge cases in _extract_model_parse_pattern."""
    from stringent.parser import ParsableModel

    # Test with a class that has _model_parse_pattern as a non-string default
    class ModelWithNonStringPattern(ParsableModel):
        """Model with non-string pattern attribute."""

        _model_parse_pattern = 123  # type: ignore[assignment]

        name: str

    # Should return None for non-string patterns
    pattern = ParsableModel._extract_model_parse_pattern(ModelWithNonStringPattern)
    assert pattern is None


def test_try_parse_with_subclass_non_parsable() -> None:
    """Test _try_parse_with_subclass with non-ParsableModel subclass."""
    from pydantic import BaseModel

    from stringent.parser import ParsableModel

    class RegularModel(BaseModel):
        """Regular Pydantic model, not ParsableModel."""

        name: str

    # Should return None for non-ParsableModel subclasses
    result = ParsableModel._try_parse_with_subclass(RegularModel, "test")
    assert result is None


def test_parse_with_recovery_no_pattern() -> None:
    """Test parse_with_recovery when no pattern is provided."""

    class ModelWithoutPattern(ParsableModel):
        """Model without _model_parse_pattern defined."""

        name: str
        age: int

    with pytest.raises(ValueError, match="No parse pattern provided"):
        ModelWithoutPattern.parse_with_recovery("test", strict=False)


def test_parse_with_recovery_pattern_matching_failure() -> None:
    """Test parse_with_recovery when pattern matching fails."""

    class ModelWithPattern(ParsableModel):
        """Model with pattern."""

        _model_parse_pattern = "{name} | {age}"

        name: str
        age: int

    # Use a string that doesn't match the pattern
    result = ModelWithPattern.parse_with_recovery("invalid format", strict=False)

    assert isinstance(result, ParseResult)
    assert len(result.errors) > 0
    assert any(error.get("type") == "pattern_error" for error in result.errors)


def test_model_validate_with_recovery_strict_mode() -> None:
    """Test model_validate_with_recovery in strict mode."""

    class TestModel(ParsableModel):
        """Test model."""

        name: str
        age: int

    # Strict mode should raise ValidationError on invalid data
    with pytest.raises(ValidationError):
        TestModel.model_validate_with_recovery({"name": "Alice"}, strict=True)


def test_model_validate_with_recovery_string_input() -> None:
    """Test model_validate_with_recovery with string input that fails validation."""

    class TestModel(ParsableModel):
        """Test model."""

        name: str
        age: int

    # String input that can't be parsed
    result = TestModel.model_validate_with_recovery("not a dict", strict=False)

    assert isinstance(result, ParseResult)
    assert len(result.errors) > 0
    assert result.data == {}  # Should be empty dict for string input


def test_json_parse_pattern_non_object() -> None:
    """Test that JsonParsePattern.parse raises ValueError for non-object JSON."""
    pattern = parse_json()

    # JSON array (not an object)
    with pytest.raises(ValueError, match="JSON value must be an object"):
        pattern.parse("[1, 2, 3]")

    # JSON string (not an object)
    with pytest.raises(ValueError, match="JSON value must be an object"):
        pattern.parse('"just a string"')

    # JSON number (not an object)
    with pytest.raises(ValueError, match="JSON value must be an object"):
        pattern.parse("123")


def test_extract_model_parse_pattern_string_attribute() -> None:
    """Test _extract_model_parse_pattern when _model_parse_pattern is a plain string."""
    from stringent.parser import ParsableModel

    # Create a class with _model_parse_pattern as a plain string attribute
    # This tests the path where attr is a string (not wrapped in ModelPrivateAttr)
    class ModelWithStringPattern:
        """Mock class with string pattern attribute."""

        _model_parse_pattern = "{name} | {age}"

    # We need to test this indirectly since Pydantic wraps attributes
    # Let's test by creating a model and checking if it works
    class TestModel(ParsableModel):
        """Model that should work with pattern extraction."""

        _model_parse_pattern = "{name} | {age}"  # type: ignore[assignment]

        name: str
        age: int

    # Note: Pydantic wraps this, so we test the actual usage
    # If the pattern is set correctly, parse() should work
    instance = TestModel.parse("Alice | 30")
    assert instance.name == "Alice"  # type: ignore[attr-defined]
    assert instance.age == 30  # type: ignore[attr-defined]

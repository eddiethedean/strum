"""Tests for the parser functionality."""

import pytest
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Literal, Union
from strum import parse, parse_json, ParsableModel


class Info(BaseModel):
    name: str
    age: int
    city: str


class Record(ParsableModel):
    id: int
    info: Info = parse("{name} | {age} | {city}") | parse("{name} {age} {city}")
    email: EmailStr
    status: Literal["Active", "Inactive"]


def test_parse_dict_input():
    """Test parsing when input is already a dictionary."""
    data = {
        "id": 1,
        "info": {"name": "Alice", "age": 30, "city": "New York"},
        "email": "alice@example.com",
        "status": "Active",
    }
    record = Record(**data)
    assert record.id == 1
    assert record.info.name == "Alice"
    assert record.info.age == 30
    assert record.info.city == "New York"
    assert record.email == "alice@example.com"
    assert record.status == "Active"


def test_parse_pipe_separated_string():
    """Test parsing pipe-separated string."""
    data = {
        "id": 3,
        "info": "Charlie | 27 | Chicago",
        "email": "charlie@example.com",
        "status": "Active",
    }
    record = Record(**data)
    assert record.id == 3
    assert record.info.name == "Charlie"
    assert record.info.age == 27
    assert record.info.city == "Chicago"


def test_parse_space_separated_string():
    """Test parsing space-separated string."""
    data = {
        "id": 5,
        "info": "Eve 35 Dallas",
        "email": "eve@example.com",
        "status": "Inactive",
    }
    record = Record(**data)
    assert record.id == 5
    assert record.info.name == "Eve"
    assert record.info.age == 35
    assert record.info.city == "Dallas"


def test_parse_invalid_string():
    """Test that invalid strings raise validation errors."""
    data = {
        "id": 1,
        "info": "Invalid format",
        "email": "test@example.com",
        "status": "Active",
    }
    with pytest.raises(ValidationError):
        Record(**data)


def test_parse_pattern_chaining():
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


def test_json_parse_pattern_standalone():
    """Test that the JSON parse pattern works on its own."""
    pattern = parse_json()
    result = pattern.parse('{"name": "Alice", "age": 30, "city": "NYC"}')
    assert result == {"name": "Alice", "age": 30, "city": "NYC"}


def test_json_parse_pattern_chained_in_model_field():
    """Test that parse_json() can be chained for model fields."""

    class RecordWithJsonInfo(ParsableModel):
        id: int
        info: Info = parse_json() | parse("{name} | {age} | {city}") | parse(
            "{name} {age} {city}"
        )
        email: EmailStr
        status: Literal["Active", "Inactive"]

    data = {
        "id": 8,
        "info": '{"name": "Joe", "age": 55, "city": "Tampa"}',
        "email": "joe@example.com",
        "status": "Active",
    }
    record = RecordWithJsonInfo(**data)
    assert record.id == 8
    assert record.info.name == "Joe"
    assert record.info.age == 55
    assert record.info.city == "Tampa"
    assert record.email == "joe@example.com"
    assert record.status == "Active"


def test_parse_pattern_single():
    """Test single parse pattern."""
    pattern = parse("{name} | {age} | {city}")
    result = pattern.parse("John | 25 | NYC")
    assert result == {"name": "John", "age": "25", "city": "NYC"}


def test_parse_with_extra_spaces():
    """Test that extra spaces are handled correctly."""
    pattern = parse("{name} | {age} | {city}")
    result = pattern.parse("  John  |  25  |  NYC  ")
    assert result == {"name": "John", "age": "25", "city": "NYC"}


def test_parse_pattern_or_with_invalid_type():
    """Test that ParsePattern.__or__ with invalid_type returns NotImplemented."""

    pattern = parse("{name}")
    # Call __or__ directly to test the NotImplemented path
    result = pattern.__or__(42)  # int is not a ParsePattern
    assert result is NotImplemented


def test_parse_pattern_ror_with_invalid_type():
    """Test that ParsePattern.__ror__ with invalid_type returns NotImplemented."""

    pattern = parse("{name}")
    # Call __ror__ directly to test the NotImplemented path
    result = pattern.__ror__(42)  # int is not a ParsePattern
    assert result is NotImplemented


def test_chained_pattern_or_with_invalid_type():
    """Test that ChainedParsePattern.__or__ with invalid_type returns NotImplemented."""

    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    # Call __or__ directly to test the NotImplemented path
    result = chained.__or__("invalid")  # str is not ParsePattern or ChainedParsePattern
    assert result is NotImplemented


def test_chained_pattern_ror_with_invalid_type():
    """Test that ChainedParsePattern.__ror__ with invalid_type returns NotImplemented."""

    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    # Call __ror__ directly to test the NotImplemented path
    result = chained.__ror__("invalid")  # str is not ParsePattern or ChainedParsePattern
    assert result is NotImplemented


def test_parse_pattern_ror_with_valid_type():
    """Test that ParsePattern.__ror__ with valid ParsePattern works correctly."""
    pattern1 = parse("{name}")
    pattern2 = parse("{age}")

    # Call __ror__ directly: pattern2.__ror__(pattern1) means pattern1 | pattern2
    result = pattern2.__ror__(pattern1)
    from strum.parser import ChainedParsePattern

    assert isinstance(result, ChainedParsePattern)
    assert len(result.patterns) == 2
    assert result.patterns[0] == pattern1
    assert result.patterns[1] == pattern2


def test_chained_pattern_or_with_parse_pattern():
    """Test that ChainedParsePattern.__or__ with ParsePattern works correctly."""
    from strum.parser import ChainedParsePattern

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


def test_chained_pattern_or_with_chained_pattern():
    """Test that ChainedParsePattern.__or__ with ChainedParsePattern works correctly."""
    from strum.parser import ChainedParsePattern

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


def test_chained_pattern_ror_with_parse_pattern():
    """Test that ChainedParsePattern.__ror__ with ParsePattern works correctly."""
    from strum.parser import ChainedParsePattern

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


def test_chained_pattern_ror_with_chained_pattern():
    """Test that ChainedParsePattern.__ror__ with ChainedParsePattern works correctly."""
    from strum.parser import ChainedParsePattern

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


def test_parse_string_fields_with_non_dict():
    """Test that _parse_string_fields handles non-dict data correctly."""
    from strum.parser import ParsableModel

    class SimpleModel(ParsableModel):
        name: str

    # Test with list
    result = SimpleModel._parse_string_fields([1, 2, 3])
    assert result == [1, 2, 3]

    # Test with string
    result = SimpleModel._parse_string_fields("not a dict")
    assert result == "not a dict"

    # Test with None
    result = SimpleModel._parse_string_fields(None)
    assert result is None

    # Test with int
    result = SimpleModel._parse_string_fields(42)
    assert result == 42


def test_parse_string_fields_no_patterns():
    """Test that _parse_string_fields works with models that have no parse patterns."""
    from strum.parser import ParsableModel

    class ModelWithoutPatterns(ParsableModel):
        name: str
        age: int

    # Should return data as-is since there are no parse patterns
    data = {"name": "Alice", "age": 30}
    result = ModelWithoutPatterns._parse_string_fields(data)
    assert result == data


def test_parse_string_fields_no_parse_patterns_attribute():
    """Test that _parse_string_fields handles missing _parse_patterns attribute."""
    from strum.parser import ParsableModel

    class ModelWithoutPatterns(ParsableModel):
        name: str
        age: int

    # Manually remove _parse_patterns to test the defensive check
    if hasattr(ModelWithoutPatterns, "_parse_patterns"):
        delattr(ModelWithoutPatterns, "_parse_patterns")

    data = {"name": "Alice", "age": 30}
    result = ModelWithoutPatterns._parse_string_fields(data)
    assert result == data


def test_parse_with_non_string_values():
    """Test that non-string values in parse results are preserved correctly."""
    from strum.parser import ParsePattern

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


def test_parse_pattern_inheritance():
    """Test that parse patterns are inherited from parent classes."""
    class BaseRecord(ParsableModel):
        info: Info = parse("{name} | {age} | {city}")

    class DerivedRecord(BaseRecord):
        extra: str

    # DerivedRecord should inherit the info parse pattern
    assert "info" in DerivedRecord._parse_patterns
    assert DerivedRecord._parse_patterns["info"][1] == Info

    # Test that inherited pattern works
    data = {"info": "Alice | 30 | NYC", "extra": "test"}
    record = DerivedRecord(**data)
    assert record.info.name == "Alice"
    assert record.info.age == 30
    assert record.info.city == "NYC"
    assert record.extra == "test"


def test_parse_pattern_override():
    """Test that child classes can override parent parse patterns."""
    class BaseRecord(ParsableModel):
        info: Info = parse("{name} | {age} | {city}")

    class DerivedRecord(BaseRecord):
        info: Info = parse("{name} {age} {city}")  # Override with different pattern

    # DerivedRecord should have its own pattern, not the parent's
    assert "info" in DerivedRecord._parse_patterns
    pattern_obj = DerivedRecord._parse_patterns["info"][0]
    # The pattern should match space-separated, not pipe-separated
    result = pattern_obj.parse("Bob 25 Chicago")
    assert result == {"name": "Bob", "age": "25", "city": "Chicago"}

    # Test that the overridden pattern works
    data = {"info": "Eve 35 Dallas"}
    record = DerivedRecord(**data)
    assert record.info.name == "Eve"
    assert record.info.age == 35
    assert record.info.city == "Dallas"


def test_parsable_model_parse_with_pattern():
    """Test that ParsableModel.parse() works with a provided pattern."""
    class SimpleRecord(ParsableModel):
        id: int
        name: str
        age: int

    # Parse with explicit pattern
    record = SimpleRecord.parse("1 | Alice | 30", pattern="{id} | {name} | {age}")
    assert record.id == 1
    assert record.name == "Alice"
    assert record.age == 30


def test_parsable_model_parse_with_class_pattern():
    """Test that ParsableModel.parse() works with _model_parse_pattern class attribute."""
    class SimpleRecord(ParsableModel):
        _model_parse_pattern = "{id} | {name} | {age}"
        id: int
        name: str
        age: int

    # Parse using class-defined pattern
    record = SimpleRecord.parse("2 | Bob | 25")
    assert record.id == 2
    assert record.name == "Bob"
    assert record.age == 25


def test_parsable_model_parse_with_nested_parsing():
    """Test that ParsableModel.parse() works with nested parse patterns."""
    class RecordWithNested(ParsableModel):
        # Use a different delimiter for the outer pattern to avoid conflicts
        _model_parse_pattern = "{id} || {info} || {email}"
        id: int
        info: Info = parse("{name} | {age} | {city}")
        email: EmailStr

    # Parse - the info field should be automatically parsed from string
    # The pattern matches: id="1", info="Alice | 30 | NYC", email="alice@example.com"
    record = RecordWithNested.parse("1 || Alice | 30 | NYC || alice@example.com")
    assert record.id == 1
    assert record.info.name == "Alice"
    assert record.info.age == 30
    assert record.info.city == "NYC"
    assert record.email == "alice@example.com"


def test_parsable_model_parse_no_pattern_error():
    """Test that ParsableModel.parse() raises error when no pattern is provided."""
    class SimpleRecord(ParsableModel):
        id: int
        name: str

    # Should raise ValueError when no pattern provided and _model_parse_pattern not defined
    with pytest.raises(ValueError, match="No parse pattern provided"):
        SimpleRecord.parse("1 | Alice")


def test_parsable_model_parse_invalid_string():
    """Test that ParsableModel.parse() raises error when string doesn't match pattern."""
    class SimpleRecord(ParsableModel):
        _model_parse_pattern = "{id} | {name} | {age}"
        id: int
        name: str
        age: int

    # Should raise ValueError when string doesn't match pattern
    with pytest.raises(ValueError, match="does not match pattern"):
        SimpleRecord.parse("invalid string")


def test_parsable_model_parse_json():
    """Test that ParsableModel.parse_json() works with JSON strings."""
    class SimpleRecord(ParsableModel):
        id: int
        name: str
        age: int

    json_str = '{"id": 1, "name": "Alice", "age": 30}'
    record = SimpleRecord.parse_json(json_str)
    assert record.id == 1
    assert record.name == "Alice"
    assert record.age == 30


def test_parsable_model_parse_json_with_nested_parsing():
    """Test that ParsableModel.parse_json() works with nested parse patterns."""
    class RecordWithNested(ParsableModel):
        id: int
        info: Info = parse("{name} | {age} | {city}")
        email: EmailStr

    json_str = '{"id": 1, "info": "Alice | 30 | NYC", "email": "alice@example.com"}'
    record = RecordWithNested.parse_json(json_str)
    assert record.id == 1
    assert record.info.name == "Alice"
    assert record.info.age == 30
    assert record.info.city == "NYC"
    assert record.email == "alice@example.com"


def test_parsable_model_parse_json_invalid_json():
    """Test that ParsableModel.parse_json() raises error for invalid JSON."""
    from pydantic import ValidationError

    class SimpleRecord(ParsableModel):
        id: int
        name: str

    # Should raise ValidationError for invalid JSON (Pydantic's error)
    with pytest.raises(ValidationError):
        SimpleRecord.parse_json("not valid json")


def test_union_type_with_model_parse_pattern():
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
        info: Union[PipeInfo, SpaceInfo]
        email: EmailStr

    # Test pipe-separated parsing
    data1 = {
        "id": 1,
        "info": "Alice | 30 | NYC",
        "email": "alice@example.com",
    }
    record1 = Record(**data1)
    assert isinstance(record1.info, PipeInfo)
    assert record1.info.name == "Alice"
    assert record1.info.age == 30
    assert record1.info.city == "NYC"

    # Test space-separated parsing
    data2 = {
        "id": 2,
        "info": "Bob 25 Chicago",
        "email": "bob@example.com",
    }
    record2 = Record(**data2)
    assert isinstance(record2.info, SpaceInfo)
    assert record2.info.name == "Bob"
    assert record2.info.age == 25
    assert record2.info.city == "Chicago"


def test_union_type_with_json_parse_flag():
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
        info: Union[JsonInfo, PipeInfo]
        email: EmailStr

    # Test JSON parsing
    data = {
        "id": 1,
        "info": '{"name": "Joe", "age": 55, "city": "Tampa"}',
        "email": "joe@example.com",
    }
    record = Record(**data)
    assert isinstance(record.info, JsonInfo)
    assert record.info.name == "Joe"
    assert record.info.age == 55
    assert record.info.city == "Tampa"


def test_union_type_with_both_flags():
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
    record1 = Record(**data1)
    assert record1.info.name == "Alice"
    assert record1.info.age == 30
    assert record1.info.city == "NYC"

    # Test pattern parsing (fallback when JSON fails)
    data2 = {
        "id": 2,
        "info": "Bob | 25 | Chicago",
        "email": "bob@example.com",
    }
    record2 = Record(**data2)
    assert record2.info.name == "Bob"
    assert record2.info.age == 25
    assert record2.info.city == "Chicago"


def test_union_type_parsing_order():
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
        info: Union[FirstInfo, SecondInfo]
        email: EmailStr

    # This string matches FirstInfo pattern, so it should use FirstInfo
    data = {
        "id": 1,
        "info": "Alice | 30 | NYC",
        "email": "alice@example.com",
    }
    record = Record(**data)
    assert isinstance(record.info, FirstInfo)
    assert record.info.name == "Alice"


def test_union_type_fallback_behavior():
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
        info: Union[PipeInfo, SpaceInfo]
        email: EmailStr

    # This string doesn't match PipeInfo pattern, so should fall back to SpaceInfo
    data = {
        "id": 1,
        "info": "Eve 35 Dallas",
        "email": "eve@example.com",
    }
    record = Record(**data)
    assert isinstance(record.info, SpaceInfo)
    assert record.info.name == "Eve"
    assert record.info.age == 35
    assert record.info.city == "Dallas"


def test_union_type_with_dict_input():
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
        info: Union[JsonInfo, PipeInfo]
        email: EmailStr

    # Dict input should work without parsing
    data = {
        "id": 1,
        "info": {"name": "Alice", "age": 30, "city": "NYC"},
        "email": "alice@example.com",
    }
    record = Record(**data)
    assert record.info.name == "Alice"
    assert record.info.age == 30
    assert record.info.city == "NYC"

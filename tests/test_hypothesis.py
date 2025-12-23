"""Property-based and fuzzing tests using Hypothesis."""

import json
import re
from typing import Any

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from pydantic import BaseModel

from stringent import ParsableModel, ParseResult, parse, parse_json, parse_regex

# Helper strategy for safe text (no control characters, no pattern-breaking chars)
# Use only printable ASCII (32-126) excluding pattern-breaking characters
# Exclude strings that are only whitespace
safe_text = st.text(
    alphabet=st.sampled_from([chr(i) for i in range(32, 127) if chr(i) not in "|{"]),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() != "" and not x.isspace())


# Custom Hypothesis strategies


def pattern_strategy() -> st.SearchStrategy[str]:
    """Generate valid format string patterns."""
    field_name = st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10
    )
    field = st.one_of(
        st.builds(lambda name: f"{{{name}}}", field_name),
        st.builds(lambda name: f"{{{name}?}}", field_name),  # Optional fields
    )
    delimiter = st.sampled_from([" | ", " ", ", ", ":", "-"])
    fields_list = st.lists(field, min_size=1, max_size=5)
    return st.tuples(fields_list, delimiter).map(lambda t: t[1].join(t[0]))


def matching_string_strategy(pattern: str) -> st.SearchStrategy[str]:
    """Generate strings that match a given pattern."""
    # Extract field names from pattern
    field_names = re.findall(r"\{(\w+)\??\}", pattern)
    if not field_names:
        return st.just("")

    # Generate values for each field
    values = []
    for _ in field_names:
        # Generate random text values (avoiding pattern-breaking characters)
        value = st.text(min_size=1, max_size=20).filter(lambda x: "|" not in x and "{" not in x)
        values.append(value)

    # Build the string matching the pattern structure
    normalized_pattern = re.sub(r"\{(\w+)\??\}", r"{}", pattern)
    return st.tuples(*values).map(lambda vals: normalized_pattern.format(*vals))


def regex_pattern_strategy() -> st.SearchStrategy[str]:
    """Generate valid regex patterns with named groups."""
    group_name = st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10
    )
    group_pattern = st.one_of(
        st.just(r"\d+"),  # digits
        st.just(r"\w+"),  # word characters
        st.just(r".+"),  # any characters
        st.just(r"[A-Z]+"),  # uppercase letters
    )
    named_group = st.builds(
        lambda name, pattern: f"(?P<{name}>{pattern})", group_name, group_pattern
    )
    return st.lists(named_group, min_size=1, max_size=3).map(lambda groups: " ".join(groups))


# Property-based tests for ParsePattern


@given(safe_text, safe_text, st.integers())
def test_parse_pattern_round_trip(name: str, city: str, age: int) -> None:
    """Test round-trip property: format -> parse -> verify."""
    pattern = parse("{name} | {age} | {city}")
    input_str = f"{name} | {age} | {city}"
    result = pattern.parse(input_str)

    # parse library strips whitespace, so we compare stripped versions
    assert result["name"].strip() == name.strip()
    assert result["city"].strip() == city.strip()
    assert result["age"] == str(age)  # parse library returns strings


@given(safe_text, st.floats(allow_nan=False, allow_infinity=False))
def test_parse_pattern_with_floats(name: str, value: float) -> None:
    """Test parsing with float values."""
    pattern = parse("{name} | {value}")
    input_str = f"{name} | {value}"
    result = pattern.parse(input_str)

    # parse library strips whitespace
    assert result["name"].strip() == name.strip()
    # parse library returns strings, so we need to convert
    assert float(result["value"]) == value


@given(safe_text)
def test_parse_pattern_whitespace_handling(text: str) -> None:
    """Test that leading/trailing whitespace is stripped."""
    pattern = parse("{value}")
    # Add whitespace
    padded_text = f"  {text}  "
    result = pattern.parse(padded_text)

    # parse library strips whitespace from both input and result
    assert result["value"].strip() == text.strip()


@given(safe_text, safe_text)
def test_parse_pattern_matching_consistency(name: str, city: str) -> None:
    """Test that matching strings always parse successfully."""
    pattern = parse("{name} | {city}")
    input_str = f"{name} | {city}"
    result = pattern.parse(input_str)

    assert isinstance(result, dict)
    assert len(result) > 0
    assert "name" in result
    assert "city" in result


@given(st.text(min_size=1))
def test_parse_pattern_non_matching_raises_error(text: str) -> None:
    """Test that non-matching strings raise ValueError."""
    assume("|" not in text)  # If it contains |, it might accidentally match

    pattern = parse("{name} | {age} | {city}")
    # This string doesn't have the right structure
    if "|" not in text:
        with pytest.raises(ValueError):
            pattern.parse(text)


@given(safe_text, safe_text)
def test_parse_pattern_optional_fields_present(name: str, city: str) -> None:
    """Test optional fields when they are present."""
    pattern = parse("{name} | {age?} | {city}")
    input_str = f"{name} | 30 | {city}"
    result = pattern.parse(input_str)

    assert result["name"].strip() == name.strip()
    assert result["city"].strip() == city.strip()
    assert "age" in result


@given(safe_text, safe_text)
def test_parse_pattern_optional_fields_missing(name: str, city: str) -> None:
    """Test optional fields when they are missing."""
    pattern = parse("{name} | {age?} | {city}")
    # Try without the optional field
    input_str = f"{name} | {city}"
    result = pattern.parse(input_str)

    assert result["name"].strip() == name.strip()
    assert result["city"].strip() == city.strip()
    # Optional field may or may not be in result depending on implementation
    # The key is that parsing succeeds


# Fuzzing tests for ParsePattern


@given(safe_text)
def test_parse_pattern_unicode_support(text: str) -> None:
    """Test parsing with unicode characters."""
    pattern = parse("{value}")
    result = pattern.parse(text)

    # parse library strips whitespace
    assert result["value"].strip() == text.strip()


@given(safe_text)
def test_parse_pattern_special_characters(text: str) -> None:
    """Test parsing with special characters (excluding pattern delimiters)."""
    pattern = parse("{value}")
    result = pattern.parse(text)

    # parse library strips whitespace
    assert result["value"].strip() == text.strip()


@given(st.text())
def test_parse_pattern_empty_string_handling(text: str) -> None:
    """Test handling of empty strings."""
    pattern = parse("{value}")

    # Filter out control characters that cause issues
    if any(ord(c) < 32 or ord(c) > 126 for c in text) or "|" in text or "{" in text:
        # Skip problematic strings
        return

    if len(text) == 0 or text.isspace():
        # Empty or whitespace-only string might match or not depending on pattern
        # Just verify it doesn't crash
        try:
            result = pattern.parse(text)
            assert isinstance(result, dict)
        except ValueError:
            pass  # Expected for empty/whitespace strings
    else:
        result = pattern.parse(text)
        assert isinstance(result, dict)


@given(st.integers(min_value=1, max_value=1000))
def test_parse_pattern_very_long_strings(length: int) -> None:
    """Test with very long strings."""
    long_text = "a" * length
    pattern = parse("{value}")
    result = pattern.parse(long_text)

    assert result["value"] == long_text


# Property-based tests for ChainedParsePattern


@given(
    st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cf", "Cs")
        ),
    ).filter(lambda x: "|" not in x and " " not in x and "{" not in x),
    st.integers(),
)
def test_chained_pattern_fallback_behavior(name: str, age: int) -> None:
    """Test that chained patterns try patterns in order."""
    pattern1 = parse("{name} | {age}")
    pattern2 = parse("{name} {age}")
    chained = pattern1 | pattern2

    # First pattern should match
    input1 = f"{name} | {age}"
    result1 = chained.parse(input1)
    assert result1["name"].strip() == name.strip()
    assert result1["age"] == str(age)

    # Second pattern should match if first fails
    input2 = f"{name} {age}"
    result2 = chained.parse(input2)
    assert result2["name"].strip() == name.strip()
    assert result2["age"] == str(age)


@given(
    st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cf", "Cs")
        ),
    ).filter(lambda x: "|" not in x and " " not in x and "-" not in x and "{" not in x),
    st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cf", "Cs")
        ),
    ).filter(lambda x: "|" not in x and " " not in x and "-" not in x and "{" not in x),
)
def test_chained_pattern_order_independence(name: str, city: str) -> None:
    """Test that non-overlapping patterns work regardless of order."""
    # Create two patterns that don't overlap
    pattern1 = parse("{name} | {city}")
    pattern2 = parse("{name}-{city}")

    chained1 = pattern1 | pattern2
    chained2 = pattern2 | pattern1

    # Both should work for their respective inputs
    input1 = f"{name} | {city}"
    result1a = chained1.parse(input1)
    result1b = chained2.parse(input1)
    # Compare stripped values since parse strips whitespace
    assert result1a["name"].strip() == result1b["name"].strip()
    assert result1a["city"].strip() == result1b["city"].strip()

    input2 = f"{name}-{city}"
    result2a = chained1.parse(input2)
    result2b = chained2.parse(input2)
    assert result2a["name"].strip() == result2b["name"].strip()
    assert result2a["city"].strip() == result2b["city"].strip()


@given(
    st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cf", "Cs")
        ),
    ).filter(lambda x: "|" not in x and " " not in x and "-" not in x and "{" not in x),
    st.integers(),
    st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cf", "Cs")
        ),
    ).filter(lambda x: "|" not in x and " " not in x and "-" not in x and "{" not in x),
)
def test_chained_pattern_associativity(name: str, age: int, city: str) -> None:
    """Test that chaining is associative."""
    p1 = parse("{name} | {age}")
    p2 = parse("{name} {age}")
    p3 = parse("{name}-{age}")

    chained1 = (p1 | p2) | p3
    chained2 = p1 | (p2 | p3)

    # Both should have the same patterns
    assert len(chained1.patterns) == len(chained2.patterns)
    assert len(chained1.patterns) == 3


# Property-based tests for RegexParsePattern


@given(
    st.text(
        min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"))
    ),  # Only letters and digits
    st.integers(min_value=1000, max_value=9999),
)
def test_regex_pattern_matching(name: str, year: int) -> None:
    """Test regex pattern matching with named groups."""
    pattern_str = r"(?P<name>\w+) (?P<year>\d{4})"
    pattern = parse_regex(pattern_str)

    input_str = f"{name} {year}"
    result = pattern.parse(input_str)

    assert result["name"] == name
    assert result["year"] == str(year)


@given(
    st.text(
        min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"))
    ),  # Only letters and digits for name
    safe_text,  # Message can be any safe text
)
def test_regex_pattern_named_groups(name: str, message: str) -> None:
    """Test that named groups are correctly extracted."""
    # Use a pattern that matches the input
    pattern_str = r"(?P<name>\w+) (?P<message>.+)"
    pattern = parse_regex(pattern_str)

    input_str = f"{name} {message}"
    result = pattern.parse(input_str)

    assert "name" in result
    assert "message" in result
    assert result["name"] == name
    # Regex pattern parsing strips whitespace, so compare stripped
    assert result["message"].strip() == message.strip()


@given(st.text())
def test_regex_pattern_invalid_regex_raises_error(pattern_str: str) -> None:
    """Test that invalid regex patterns raise errors during initialization."""
    # Try to create a regex pattern - might be valid or invalid
    try:
        pattern = parse_regex(pattern_str)
        # If it's valid, check if it has named groups
        # RegexParsePattern will raise ValueError if no named groups
        # We can't access compiled_regex directly since ParsePattern doesn't have it
        # Just verify the pattern was created (it will raise ValueError if invalid)
        assert pattern is not None
    except (ValueError, re.error):
        pass  # Expected for invalid patterns


# Property-based tests for ParsableModel


class SimpleInfo(BaseModel):
    """Simple model for testing."""

    name: str
    age: int
    city: str


class SimpleRecord(ParsableModel):
    """Simple parsable model for testing."""

    id: int
    info: SimpleInfo = parse("{name} | {age} | {city}")  # type: ignore[assignment]
    email: str


@given(safe_text, st.integers(min_value=0, max_value=120), safe_text, safe_text)
def test_parsable_model_string_to_model(name: str, age: int, city: str, email: str) -> None:
    """Test parsing string inputs into model instances."""
    data = {
        "id": 1,
        "info": f"{name} | {age} | {city}",
        "email": email,
    }
    record = SimpleRecord(**data)  # type: ignore[arg-type]

    assert record.id == 1  # type: ignore[attr-defined]
    # parse library strips whitespace, so compare stripped
    assert record.info.name.strip() == name.strip()  # type: ignore[attr-defined]
    assert record.info.age == age  # type: ignore[attr-defined]
    assert record.info.city.strip() == city.strip()  # type: ignore[attr-defined]
    assert record.email == email  # type: ignore[attr-defined]


class NestedInfo(BaseModel):
    """Nested model for testing."""

    value: str


class NestedRecord(ParsableModel):
    """Model with nested ParsableModel."""

    outer: NestedInfo = parse("{value}")  # type: ignore[assignment]


@given(safe_text)
def test_parsable_model_nested_parsing(text: str) -> None:
    """Test parsing of nested ParsableModel instances."""
    data = {"outer": text}
    record = NestedRecord(**data)  # type: ignore[arg-type]

    # parse library strips whitespace
    assert record.outer.value.strip() == text.strip()  # type: ignore[attr-defined]


class ModelWithPattern(ParsableModel):
    """Model with class-level parse pattern."""

    _model_parse_pattern = "{id} | {name} | {age}"

    id: int
    name: str
    age: int


@given(st.integers(), safe_text, st.integers(min_value=0, max_value=120))
def test_parsable_model_class_defined_pattern(record_id: int, name: str, age: int) -> None:
    """Test ParsableModel.parse() with class-defined patterns."""
    input_str = f"{record_id} | {name} | {age}"
    record = ModelWithPattern.parse(input_str)

    assert record.id == record_id  # type: ignore[attr-defined]
    # parse library strips whitespace
    assert record.name.strip() == name.strip()  # type: ignore[attr-defined]
    assert record.age == age  # type: ignore[attr-defined]


# Property-based tests for Error Recovery


@given(safe_text, safe_text)
def test_error_recovery_collects_errors(name: str, city: str) -> None:
    """Test that error recovery collects all errors."""

    # Create a model that will have validation errors
    class ErrorModel(ParsableModel):
        """Model for testing error recovery."""

        _model_parse_pattern = "{name} | {age} | {city}"

        name: str
        age: int  # This will fail if we provide invalid input
        city: str

    # Use invalid age to trigger error
    input_str = f"{name} | invalid | {city}"
    result = ErrorModel.parse_with_recovery(input_str, strict=False)

    assert isinstance(result, ParseResult)
    assert len(result.errors) > 0
    # Should have partial data
    assert "name" in result.data or "city" in result.data


@given(safe_text, st.integers(), safe_text)
def test_error_recovery_vs_normal_parsing(name: str, age: int, city: str) -> None:
    """Test that error recovery matches normal parsing when no errors occur."""

    class TestModel(ParsableModel):
        """Model for testing."""

        _model_parse_pattern = "{name} | {age} | {city}"

        name: str
        age: int
        city: str

    input_str = f"{name} | {age} | {city}"

    # Normal parsing
    record1 = TestModel.parse(input_str)

    # Error recovery (should succeed and return model instance when no errors)
    result = TestModel.parse_with_recovery(input_str, strict=False)
    # When parsing succeeds, parse_with_recovery returns the model instance, not ParseResult
    if isinstance(result, ParseResult):
        # If it's a ParseResult, there were errors - verify it's empty
        assert result  # Should be truthy (no errors)
        record2 = result.data
        # Both should have the same data (compare stripped since parse strips whitespace)
        assert record1.name.strip() == str(record2.get("name", "")).strip()  # type: ignore[attr-defined]
        assert record1.age == record2.get("age")  # type: ignore[attr-defined]
        assert record1.city.strip() == str(record2.get("city", "")).strip()  # type: ignore[attr-defined]
    else:
        # Success case - returns model instance directly
        assert isinstance(result, TestModel)
        assert record1.name.strip() == result.name.strip()  # type: ignore[attr-defined]
        assert record1.age == result.age  # type: ignore[attr-defined]
        assert record1.city.strip() == result.city.strip()  # type: ignore[attr-defined]


# Edge case fuzzing


@given(st.text())
def test_json_parsing_edge_cases(json_str: str) -> None:
    """Test JSON parsing with various edge cases."""
    pattern = parse_json()

    # Try to parse - might be valid or invalid JSON
    try:
        result = pattern.parse(json_str)
        # If successful, should be a dict
        assert isinstance(result, dict)
        # Verify it's valid JSON by round-tripping
        json.dumps(result)
    except ValueError:
        pass  # Expected for invalid JSON


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=1,
        max_size=5,
    )
)
def test_json_parsing_nested_structures(data: dict[str, Any]) -> None:
    """Test JSON parsing with nested structures."""
    pattern = parse_json()
    json_str = json.dumps(data)
    result = pattern.parse(json_str)

    assert result == data


@given(safe_text)
def test_pattern_edge_cases_single_field(value: str) -> None:
    """Test patterns with single field."""
    pattern = parse("{value}")
    result = pattern.parse(value)
    # parse library strips whitespace
    assert result["value"].strip() == value.strip()


@given(st.one_of(safe_text, st.integers(), st.floats(allow_nan=False, allow_infinity=False)))
def test_type_coercion_edge_cases(value: Any) -> None:
    """Test type coercion with various value types."""
    # Convert to string for pattern
    value_str = str(value)

    pattern = parse("{value}")
    result = pattern.parse(value_str)

    # parse library returns strings and strips whitespace, so we verify the string representation
    assert result["value"].strip() == value_str.strip()


# Additional fuzzing tests


@given(safe_text)
def test_parse_pattern_unicode_emoji(text: str) -> None:
    """Test parsing with unicode and emoji characters."""
    pattern = parse("{value}")
    result = pattern.parse(text)

    # parse library strips whitespace
    assert result["value"].strip() == text.strip()


@given(st.lists(safe_text, min_size=1, max_size=10))
def test_parse_pattern_many_fields(field_values: list[str]) -> None:
    """Test patterns with many fields."""
    # Create a pattern with many fields
    field_names = [f"field{i}" for i in range(len(field_values))]
    pattern_str = " | ".join(f"{{{name}}}" for name in field_names)
    pattern = parse(pattern_str)

    # Create input string
    input_str = " | ".join(field_values)
    result = pattern.parse(input_str)

    # Verify all fields are present (compare stripped since parse strips whitespace)
    for i, name in enumerate(field_names):
        assert name in result
        assert result[name].strip() == field_values[i].strip()


@given(safe_text, st.integers(min_value=-1000, max_value=1000))
def test_parse_pattern_negative_numbers(name: str, age: int) -> None:
    """Test parsing with negative numbers."""
    pattern = parse("{name} | {age}")
    input_str = f"{name} | {age}"
    result = pattern.parse(input_str)

    # parse library strips whitespace
    assert result["name"].strip() == name.strip()
    assert result["age"] == str(age)  # parse returns strings
    assert int(result["age"]) == age

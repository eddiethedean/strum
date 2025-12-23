# Regex Parsing Guide

This guide covers parsing strings using regular expressions with named groups in `stringent`.

## Overview

`parse_regex()` allows you to parse strings using Python's regular expressions with named groups. This is particularly useful for:

- Log file parsing
- Unstructured text extraction
- Complex pattern matching that format strings can't handle
- Legacy data formats with irregular patterns

## Basic Usage

### Simple Regex Pattern

Use `parse_regex()` with a pattern containing named groups:

```python
from stringent import parse_regex, ParsableModel
from pydantic import BaseModel

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

class Record(ParsableModel):
    entry: LogEntry = parse_regex(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
    )

# Parse log line
log_line = "2024-01-15 [ERROR] Database connection failed"
record = Record(entry=log_line)

print(record.entry.timestamp)  # 2024-01-15
print(record.entry.level)       # ERROR
print(record.entry.message)      # Database connection failed
```

### Named Groups Required

The regex pattern **must** contain named groups (using `(?P<name>...)` syntax) to map to model fields:

```python
# Valid - has named groups
pattern = parse_regex(r'(?P<name>\w+) is (?P<age>\d+) years old')

# Invalid - no named groups (will raise ValueError)
try:
    pattern = parse_regex(r'(\w+) is (\d+) years old')
except ValueError as e:
    print("Pattern must contain named groups")
```

## Common Patterns

### Log Parsing

Parse structured log entries:

```python
class ApacheLog(BaseModel):
    ip: str
    timestamp: str
    method: str
    path: str
    status: str

class LogRecord(ParsableModel):
    log: ApacheLog = parse_regex(
        r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\w+) (?P<path>[^"]+)" (?P<status>\d+)'
    )

log_line = '192.168.1.1 - - [15/Jan/2024:10:30:45 +0000] "GET /api/users HTTP/1.1" 200'
record = LogRecord(log=log_line)
```

### Email Parsing

Extract components from email addresses or headers:

```python
class EmailHeader(BaseModel):
    from_addr: str
    to_addr: str
    subject: str

class EmailRecord(ParsableModel):
    header: EmailHeader = parse_regex(
        r'From: (?P<from_addr>[^\n]+)\nTo: (?P<to_addr>[^\n]+)\nSubject: (?P<subject>.*)'
    )
```

### Date/Time Extraction

Extract date and time components:

```python
class DateTimeComponents(BaseModel):
    year: str
    month: str
    day: str
    hour: str
    minute: str
    second: str

class TimeRecord(ParsableModel):
    time: DateTimeComponents = parse_regex(
        r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) '
        r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})'
    )

time_str = "2024-01-15 14:30:45"
record = TimeRecord(time=time_str)
```

## Chaining with Other Patterns

Regex patterns can be chained with other patterns:

```python
from stringent import parse_regex, parse, ParsableModel
from pydantic import BaseModel

class Info(BaseModel):
    name: str
    age: int
    city: str

class Record(ParsableModel):
    info: Info = (
        parse_regex(r'Name: (?P<name>\w+), Age: (?P<age>\d+), City: (?P<city>\w+)') |
        parse('{name} | {age} | {city}') |
        parse_json()
    )

# Tries regex first, then pipe-separated, then JSON
record1 = Record(info="Name: Alice, Age: 30, City: NYC")
record2 = Record(info="Bob | 25 | Chicago")
record3 = Record(info='{"name": "Charlie", "age": 35, "city": "Boston"}')
```

## Pattern Compilation

Regex patterns are compiled and cached for performance:

```python
# Pattern is compiled once
pattern = parse_regex(r'(?P<name>\w+)')

# Reusing the same pattern is efficient
result1 = pattern.parse("Alice")
result2 = pattern.parse("Bob")
```

## Error Handling

When a regex pattern doesn't match, it raises a `ValueError`:

```python
pattern = parse_regex(r'(?P<name>\w+) is (?P<age>\d+)')

try:
    result = pattern.parse("Invalid format")
except ValueError as e:
    print(f"Pattern didn't match: {e}")
```

## Advanced Examples

### Multi-line Parsing

Parse multi-line text blocks:

```python
from stringent import parse_regex, ParsableModel
from pydantic import BaseModel

class ConfigEntry(BaseModel):
    key: str
    value: str
    comment: str

class ConfigRecord(ParsableModel):
    entry: ConfigEntry = parse_regex(
        r'# (?P<comment>.*)\n(?P<key>\w+)=(?P<value>.*)'
    )
```

**Note:** For complex multi-line patterns, you may need to pass regex flags. However, the current implementation uses `re.compile()` which accepts flags as a second parameter. You may need to modify the pattern or use `re.compile()` directly if you need flags.

### Optional Groups

Handle optional parts in regex:

```python
class FlexibleLog(BaseModel):
    timestamp: str
    level: str
    message: str
    user: str | None = None

class LogRecord(ParsableModel):
    log: FlexibleLog = parse_regex(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}) \[(?P<level>\w+)\] '
        r'(?:User: (?P<user>\w+) )?(?P<message>.*)'
    )

# Works with or without user
log1 = LogRecord(log="2024-01-15 [INFO] User: alice Operation completed")
log2 = LogRecord(log="2024-01-15 [ERROR] Connection failed")
```

### Complex Text Extraction

Extract data from unstructured text:

```python
class InvoiceLine(BaseModel):
    quantity: str
    item: str
    price: str
    total: str

class InvoiceRecord(ParsableModel):
    line: InvoiceLine = parse_regex(
        r'(?P<quantity>\d+)x\s+(?P<item>[^(]+)\s+\(@\$(?P<price>[\d.]+)\)\s+Total: \$(?P<total>[\d.]+)'
    )

invoice_line = "3x Widget A (@$10.00) Total: $30.00"
record = InvoiceRecord(line=invoice_line)
```

## Performance Considerations

- Regex patterns are compiled once when the `RegexParsePattern` is created
- Named group extraction is efficient
- For very high-performance scenarios, consider pre-compiling patterns

## Best Practices

1. **Use named groups** - Always use `(?P<name>...)` syntax for field mapping

2. **Test patterns** - Test your regex patterns with various inputs before using in production

3. **Chain with fallbacks** - Combine regex with simpler patterns for flexibility

4. **Handle errors** - Wrap regex parsing in try/except blocks for production code

5. **Document patterns** - Complex regex patterns can be hard to read - add comments explaining the pattern

6. **Consider alternatives** - For simple patterns, format strings (`parse()`) are often more readable

## Limitations

- Regex patterns must contain named groups
- Multi-line patterns may require special handling
- Very complex regex patterns can be slow - consider simpler alternatives when possible

## See Also

- **[Basic Usage](basic-usage.md)** - Format string patterns and pattern chaining
- **[JSON Parsing](json-parsing.md)** - JSON parsing guide
- **[API Reference](api-reference.md)** - Complete API documentation


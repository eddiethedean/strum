"""Doctest-based verification for documentation examples."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test_examples import execute_code, extract_code_blocks  # noqa: E402


def convert_to_doctest_format(code: str) -> str:
    """
    Convert a code block to doctest format.

    This is a simplified conversion - for full doctest support,
    we'd need more sophisticated parsing.
    """
    lines = code.split("\n")
    doctest_lines = []

    for line in lines:
        # Skip empty lines at start
        if not doctest_lines and not line.strip():
            continue

        # Add >>> prompt for executable lines
        if line.strip() and not line.startswith("#") and not line.startswith(" " * 4):
            # This is a rough heuristic - in practice, we'd need AST parsing
            doctest_lines.append(f">>> {line}")
        elif line.strip():
            doctest_lines.append(line)
        else:
            doctest_lines.append(line)

    return "\n".join(doctest_lines)


def run_examples_as_doctest(file_path: Path) -> tuple[int, int]:
    """
    Test examples in a markdown file using doctest-like approach.

    Returns:
        (passed_count, failed_count)
    """
    content = file_path.read_text()
    code_blocks = extract_code_blocks(content)

    passed = 0
    failed = 0

    # Create a shared namespace for examples in the same file
    namespace = {
        "__name__": "__main__",
        "__file__": str(file_path),
    }

    # Add common imports
    try:
        from typing import Literal, Union

        from pydantic import BaseModel, EmailStr, ValidationError

        from stringent import ParsableModel, parse, parse_json

        namespace.update(
            {
                "BaseModel": BaseModel,
                "EmailStr": EmailStr,
                "ValidationError": ValidationError,
                "Literal": Literal,
                "Union": Union,
                "parse": parse,
                "parse_json": parse_json,
                "ParsableModel": ParsableModel,
            }
        )
    except ImportError:
        # If imports fail, skip doctest verification
        return 0, len(code_blocks)

    for block in code_blocks:
        try:
            _stdout, _stderr, exception = execute_code(block["code"], namespace)
            if exception is None:
                passed += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return passed, failed


def run_all_docs_tests():
    """Test all documentation files."""
    base_dir = Path(__file__).parent.parent

    files_to_test = [
        base_dir / "README.md",
        base_dir / "docs" / "getting-started.md",
        base_dir / "docs" / "basic-usage.md",
        base_dir / "docs" / "advanced-patterns.md",
        base_dir / "docs" / "api-reference.md",
        base_dir / "docs" / "index.md",
    ]

    total_passed = 0
    total_failed = 0

    for file_path in files_to_test:
        if file_path.exists():
            passed, failed = run_examples_as_doctest(file_path)
            total_passed += passed
            total_failed += failed
            print(f"{file_path.name}: {passed} passed, {failed} failed")

    print(f"\nTotal: {total_passed} passed, {total_failed} failed")
    return total_failed == 0


class TestDocsDoctest:
    """Pytest-compatible tests for doctest verification."""

    def test_readme_examples(self):
        """Verify README examples can be executed."""
        readme_path = Path(__file__).parent.parent / "README.md"
        _passed, failed = run_examples_as_doctest(readme_path)
        assert failed == 0, f"{failed} examples failed in README.md"

    def test_getting_started_examples(self):
        """Verify getting-started examples can be executed."""
        doc_path = Path(__file__).parent.parent / "docs" / "getting-started.md"
        _passed, failed = run_examples_as_doctest(doc_path)
        assert failed == 0, f"{failed} examples failed in getting-started.md"

    def test_basic_usage_examples(self):
        """Verify basic-usage examples can be executed."""
        doc_path = Path(__file__).parent.parent / "docs" / "basic-usage.md"
        _passed, failed = run_examples_as_doctest(doc_path)
        assert failed == 0, f"{failed} examples failed in basic-usage.md"

    def test_advanced_patterns_examples(self):
        """Verify advanced-patterns examples can be executed."""
        doc_path = Path(__file__).parent.parent / "docs" / "advanced-patterns.md"
        _passed, failed = run_examples_as_doctest(doc_path)
        assert failed == 0, f"{failed} examples failed in advanced-patterns.md"

    def test_api_reference_examples(self):
        """Verify api-reference examples can be executed."""
        doc_path = Path(__file__).parent.parent / "docs" / "api-reference.md"
        _passed, failed = run_examples_as_doctest(doc_path)
        assert failed == 0, f"{failed} examples failed in api-reference.md"

    def test_index_examples(self):
        """Verify index examples can be executed."""
        doc_path = Path(__file__).parent.parent / "docs" / "index.md"
        _passed, failed = run_examples_as_doctest(doc_path)
        assert failed == 0, f"{failed} examples failed in index.md"


if __name__ == "__main__":
    # Allow running directly
    success = run_all_docs_tests()
    sys.exit(0 if success else 1)

"""Extract and test Python code examples from markdown files."""

import io
import re
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def extract_code_blocks(markdown_content: str) -> list[dict[str, str]]:
    """
    Extract all Python code blocks from markdown content.

    Returns a list of dicts with:
    - 'code': the code content
    - 'start_line': line number where code block starts
    - 'end_line': line number where code block ends
    """
    code_blocks = []
    pattern = r"```python\n(.*?)```"

    for match in re.finditer(pattern, markdown_content, re.DOTALL):
        code = match.group(1).strip()
        # Calculate approximate line numbers
        start_pos = match.start()
        start_line = markdown_content[:start_pos].count("\n") + 1
        end_line = markdown_content[: match.end()].count("\n") + 1

        code_blocks.append(
            {
                "code": code,
                "start_line": start_line,
                "end_line": end_line,
            }
        )

    return code_blocks


def extract_expected_output(markdown_content: str, code_end_pos: int) -> str | None:
    """
    Extract expected output that follows a code block.
    Looks for output blocks or comment-style outputs.
    """
    # Look for output block after code
    remaining = markdown_content[code_end_pos:]

    # Check for markdown output block
    output_pattern = r"```\n(.*?)```"
    match = re.search(output_pattern, remaining, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Check for "Output:" or "**Output:**" followed by code block
    output_header_pattern = r"(?:\*\*)?Output(?:\*\*)?:\s*\n```\n(.*?)```"
    match = re.search(output_header_pattern, remaining, re.DOTALL)
    if match:
        return match.group(1).strip()

    return None


def execute_code(code: str, namespace: dict | None = None) -> tuple[str, str, Exception | None]:
    """
    Execute Python code and capture stdout, stderr, and any exceptions.

    Returns:
        (stdout, stderr, exception)
    """
    if namespace is None:
        namespace = {}

    # Set up namespace with common imports
    namespace.setdefault("__builtins__", __builtins__)

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    exception = None

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, namespace)
    except Exception as e:
        exception = e
        # Capture traceback to stderr
        stderr_capture.write(traceback.format_exc())

    stdout = stdout_capture.getvalue()
    stderr = stderr_capture.getvalue()

    return stdout, stderr, exception


def normalize_output(output: str) -> str:
    """Normalize output for comparison (strip trailing whitespace, etc.)."""
    lines = output.split("\n")
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in lines]
    # Remove trailing empty lines
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def run_code_block_test(
    code: str, file_path: Path, line_number: int, namespace: dict | None = None
) -> tuple[dict, dict]:
    """
    Test a single code block.

    Args:
        code: The code to execute
        file_path: Path to the file containing the example
        line_number: Line number of the example
        namespace: Optional shared namespace (for examples that depend on previous ones)

    Returns:
        (result_dict, updated_namespace)
    """
    # Use provided namespace or create a fresh one
    if namespace is None:
        namespace = {
            "__name__": "__main__",
            "__file__": str(file_path),
        }
    else:
        # Create a copy to avoid modifying the original
        namespace = namespace.copy()

    # Add common imports that examples might use
    try:
        from typing import Literal, Union

        from pydantic import BaseModel, EmailStr, ValidationError

        from strum import ParsableModel, parse, parse_json

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
    except ImportError as e:
        return {
            "success": False,
            "error": f"Import error: {e}",
            "stdout": "",
            "stderr": str(e),
            "exception": e,
            "line_number": line_number,
        }, namespace

    stdout, stderr, exception = execute_code(code, namespace)

    result = {
        "success": exception is None,
        "stdout": normalize_output(stdout),
        "stderr": normalize_output(stderr),
        "exception": exception,
        "line_number": line_number,
    }

    return result, namespace


def run_markdown_file_tests(file_path: Path, shared_namespace: bool = True) -> list[dict]:
    """
    Test all Python code blocks in a markdown file.

    Args:
        file_path: Path to the markdown file
        shared_namespace: If True, examples share a namespace (for dependencies)

    Returns a list of test results.
    """
    content = file_path.read_text()
    code_blocks = extract_code_blocks(content)

    results = []
    namespace = None  # Will be created on first use

    for i, block in enumerate(code_blocks):
        if shared_namespace:
            result, namespace = run_code_block_test(
                block["code"], file_path, block["start_line"], namespace
            )
        else:
            result, _ = run_code_block_test(block["code"], file_path, block["start_line"], None)

        result["block_index"] = i
        result["code"] = block["code"]
        results.append(result)

    return results


def main():
    """Main entry point for testing examples."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_examples.py <markdown_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    results = run_markdown_file_tests(file_path)

    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed

    print(f"\n{'=' * 60}")
    print(f"Testing examples in: {file_path}")
    print(f"{'=' * 60}")
    print(f"Total examples: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"{'=' * 60}\n")

    # Print details for failed tests
    for result in results:
        if not result["success"]:
            print(f"FAILED (line {result['line_number']}):")
            print(f"Code:\n{result['code'][:200]}...")
            if result["exception"]:
                print(f"Exception: {result['exception']}")
            if result["stderr"]:
                print(f"Stderr:\n{result['stderr']}")
            print()

    # Print outputs for all tests
    print(f"\n{'=' * 60}")
    print("Captured Outputs:")
    print(f"{'=' * 60}\n")

    for i, result in enumerate(results):
        print(f"Example {i + 1} (line {result['line_number']}):")
        if result["stdout"]:
            print("STDOUT:")
            print(result["stdout"])
        if result["stderr"]:
            print("STDERR:")
            print(result["stderr"])
        if result["success"]:
            print("STATUS: PASSED")
        else:
            print(f"STATUS: FAILED - {result['exception']}")
        print("-" * 60)
        print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

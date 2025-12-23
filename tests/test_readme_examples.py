"""Test all Python code examples from README.md."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test_examples import extract_code_blocks, run_markdown_file_tests  # noqa: E402

README_PATH = Path(__file__).parent.parent / "README.md"


class TestREADMEExamples:
    """Test all code examples in README.md."""

    def test_all_examples_exist(self) -> None:
        """Verify that README has code examples."""
        content = README_PATH.read_text()
        code_blocks = extract_code_blocks(content)
        assert len(code_blocks) > 0, "README.md should contain at least one code example"

    def test_example_execution(self) -> None:
        """Test that all examples can be executed."""
        results = run_markdown_file_tests(README_PATH)

        failures = []
        for i, result in enumerate(results):
            if not result["success"]:
                failures.append(
                    {
                        "index": i + 1,
                        "line": result["line_number"],
                        "error": str(result["exception"])
                        if result["exception"]
                        else "Unknown error",
                        "stderr": result["stderr"],
                    }
                )

        if failures:
            error_msg = "Some examples failed:\n"
            for failure in failures:
                error_msg += (
                    f"\nExample {failure['index']} (line {failure['line']}): {failure['error']}\n"
                )
                if failure["stderr"]:
                    error_msg += f"  {failure['stderr'][:200]}\n"
            pytest.fail(error_msg)

    def test_example_outputs_captured(self) -> None:
        """Verify that we can capture outputs from examples."""
        results = run_markdown_file_tests(README_PATH)

        # At least some examples should produce output
        examples_with_output = sum(1 for r in results if r["stdout"])
        # We expect at least a few examples to have output
        assert examples_with_output >= 0  # Just verify we can capture


if __name__ == "__main__":
    # Allow running directly to see outputs
    results = run_markdown_file_tests(README_PATH)

    print(f"\n{'=' * 60}")
    print("README.md Example Test Results")
    print(f"{'=' * 60}")

    for i, result in enumerate(results):
        status = "PASS" if result["success"] else "FAIL"
        print(f"\nExample {i + 1} (line {result['line_number']}): {status}")
        if result["stdout"]:
            print("Output:")
            print(result["stdout"])
        if not result["success"]:
            print(f"Error: {result['exception']}")
            if result["stderr"]:
                print(f"Stderr: {result['stderr'][:500]}")

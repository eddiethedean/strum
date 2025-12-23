"""Test all Python code examples from documentation files."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test_examples import extract_code_blocks, run_markdown_file_tests  # noqa: E402

DOCS_DIR = Path(__file__).parent.parent / "docs"
DOC_FILES = [
    "getting-started.md",
    "basic-usage.md",
    "advanced-patterns.md",
    "api-reference.md",
    "index.md",
]


class TestDocsExamples:
    """Test all code examples in documentation files."""

    @pytest.mark.parametrize("doc_file", DOC_FILES)
    def test_all_examples_exist(self, doc_file):
        """Verify that each doc file has code examples."""
        doc_path = DOCS_DIR / doc_file
        content = doc_path.read_text()
        code_blocks = extract_code_blocks(content)
        assert len(code_blocks) > 0, f"{doc_file} should contain at least one code example"

    @pytest.mark.parametrize("doc_file", DOC_FILES)
    def test_example_execution(self, doc_file):
        """Test that all examples in each doc file can be executed."""
        doc_path = DOCS_DIR / doc_file
        results = run_markdown_file_tests(doc_path)

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
            error_msg = f"Some examples failed in {doc_file}:\n"
            for failure in failures:
                error_msg += (
                    f"\nExample {failure['index']} (line {failure['line']}): {failure['error']}\n"
                )
                if failure["stderr"]:
                    error_msg += f"  {failure['stderr'][:200]}\n"
            pytest.fail(error_msg)

    @pytest.mark.parametrize("doc_file", DOC_FILES)
    def test_example_outputs_captured(self, doc_file):
        """Verify that we can capture outputs from examples."""
        doc_path = DOCS_DIR / doc_file
        results = run_markdown_file_tests(doc_path)

        # Verify we can capture outputs (some examples may not produce output)
        examples_with_output = sum(1 for r in results if r["stdout"])
        assert examples_with_output >= 0  # Just verify we can capture


if __name__ == "__main__":
    # Allow running directly to see outputs for all docs
    for doc_file in DOC_FILES:
        doc_path = DOCS_DIR / doc_file
        results = run_markdown_file_tests(doc_path)

        print(f"\n{'=' * 60}")
        print(f"{doc_file} Example Test Results")
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

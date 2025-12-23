"""Capture all example outputs in a structured format for documentation updates."""

import json
import sys
from pathlib import Path

from test_examples import extract_code_blocks, run_markdown_file_tests


def capture_outputs(file_path: Path) -> dict:
    """Capture all outputs from a markdown file."""
    results = run_markdown_file_tests(file_path)
    code_blocks = extract_code_blocks(file_path.read_text())

    outputs = []
    for i, (result, block) in enumerate(zip(results, code_blocks, strict=True)):
        code_str = block["code"]
        output_info = {
            "index": i + 1,
            "line": result["line_number"],
            "code": code_str[:100] + "..." if len(code_str) > 100 else code_str,
            "stdout": result["stdout"],
            "has_output": bool(result["stdout"]),
            "success": result["success"],
        }
        outputs.append(output_info)

    return {
        "file": str(file_path),
        "outputs": outputs,
    }


def main() -> None:
    """Capture outputs for all documentation files."""
    base_dir = Path(__file__).parent.parent

    files_to_test = [
        base_dir / "README.md",
        base_dir / "docs" / "getting-started.md",
        base_dir / "docs" / "basic-usage.md",
        base_dir / "docs" / "advanced-patterns.md",
        base_dir / "docs" / "api-reference.md",
        base_dir / "docs" / "index.md",
    ]

    all_outputs = {}
    for file_path in files_to_test:
        if file_path.exists():
            print(f"Capturing outputs from {file_path.name}...", file=sys.stderr)
            all_outputs[file_path.name] = capture_outputs(file_path)

    # Print JSON for easy parsing
    print(json.dumps(all_outputs, indent=2))

    # Also print human-readable summary
    print("\n" + "=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for filename, data in all_outputs.items():
        total = len(data["outputs"])
        with_output = sum(1 for o in data["outputs"] if o["has_output"])
        print(f"{filename}: {total} examples, {with_output} with output", file=sys.stderr)


if __name__ == "__main__":
    main()

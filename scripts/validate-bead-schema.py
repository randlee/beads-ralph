#!/usr/bin/env python3
"""CLI tool to validate beads-ralph bead JSON against pydantic schema."""

import sys
from pathlib import Path

from pydantic import ValidationError

from bead_schema import Bead

# Ensure stdout/stderr use UTF-8 encoding for cross-platform compatibility
# This fixes Windows console encoding issues with Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


def format_validation_errors(exc: ValidationError) -> str:
    """Format pydantic validation errors nicely with field paths."""
    lines = ["Validation errors:"]
    for error in exc.errors():
        # Get field path
        field_path = ".".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        message = error["msg"]

        # Format error line
        lines.append(f"  {field_path}: {message} (type={error_type})")

    return "\n".join(lines)


def validate_bead_from_file(file_path: str) -> bool:
    """
    Validate bead JSON from file.

    Args:
        file_path: Path to JSON file

    Returns:
        True if valid, False if invalid
    """
    try:
        with open(file_path, "r") as f:
            json_content = f.read()

        # Parse using pydantic
        Bead.model_validate_json(json_content)
        print("✓ Valid bead")
        return True

    except ValidationError as e:
        print(format_validation_errors(e), file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def validate_bead_from_stdin() -> bool:
    """
    Validate bead JSON from stdin.

    Returns:
        True if valid, False if invalid
    """
    try:
        json_content = sys.stdin.read()

        # Parse using pydantic
        Bead.model_validate_json(json_content)
        print("✓ Valid bead")
        return True

    except ValidationError as e:
        print(format_validation_errors(e), file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # File input
        file_path = sys.argv[1]
        is_valid = validate_bead_from_file(file_path)
    else:
        # Stdin input
        is_valid = validate_bead_from_stdin()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()

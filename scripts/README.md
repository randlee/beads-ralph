# Bead Schema Validation

Python tools for validating bead JSON files against the beads-ralph schema.

## Overview

This directory contains the schema validation system for beads-ralph:

- **`bead_schema.py`** - Pydantic v2 models defining the complete bead schema
- **`validate-bead-schema.py`** - CLI tool for validating bead JSON files
- **`requirements.txt`** - Python dependencies
- **`tests/`** - Comprehensive test suite with >90% coverage

## Installation

### Requirements

- Python 3.9 or higher
- pip package manager

### Setup

```bash
# Install dependencies
cd scripts
pip install -r requirements.txt
```

## Usage

### Validating Bead Files

**Basic validation:**
```bash
python3 validate-bead-schema.py examples/example-work-bead.json
```

**Validate from stdin:**
```bash
cat examples/example-work-bead.json | python3 validate-bead-schema.py
```

**Exit codes:**
- `0` - Validation successful
- `1` - Validation failed (with error details)

### Example Output

**Valid bead:**
```
$ python3 validate-bead-schema.py examples/example-work-bead.json
✓ Valid bead
```

**Invalid bead:**
```
$ python3 validate-bead-schema.py invalid-bead.json
✗ Validation failed:

metadata.phase
  String should match pattern '^[0-9]+[a-z]*$'
```

## Running Tests

### Full Test Suite

```bash
cd scripts
pytest tests/ -v
```

### With Coverage Report

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

**Expected Coverage**: >90% (95% on bead_schema.py, 89% overall)

## CI/CD Integration

Tests run automatically on every PR via GitHub Actions:
- **Platforms**: Ubuntu (Linux), macOS, Windows
- **Python versions**: 3.9, 3.10, 3.11, 3.12
- **Coverage threshold**: 90% (PRs fail if below)
- **Trigger**: All PRs to `develop` branch

See [`.github/workflows/python-tests.yml`](../.github/workflows/python-tests.yml) for workflow configuration.

## Examples

See [`examples/`](../examples/) directory for complete bead examples:
- `example-work-bead.json` - Work bead with all required fields
- `example-merge-bead.json` - Merge bead demonstrating parallel sprint integration

## Resources

- [Schema Specification](../docs/schema.md)
- [Implementation Plan](../pm/2026-02-08-implementation-plan.md)
- [Architecture Documentation](../docs/architecture.md)

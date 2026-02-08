# beads-ralph Schema Validation

Python-based schema validation for beads-ralph using Pydantic v2.

## Overview

This directory contains:

- `bead_schema.py` - Pydantic models for beads-ralph schema
- `validate-bead-schema.py` - CLI tool to validate bead JSON files
- `requirements.txt` - Python dependencies
- `tests/` - Unit tests with >90% coverage

## Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Validate from file

```bash
PYTHONPATH=scripts python3 scripts/validate-bead-schema.py path/to/bead.json
```

### Validate from stdin

```bash
cat bead.json | PYTHONPATH=scripts python3 scripts/validate-bead-schema.py
```

### Exit codes

- `0` - Valid bead
- `1` - Invalid bead (validation errors printed to stderr)

## Testing

Run all tests with coverage:

```bash
source .venv/bin/activate
PYTHONPATH=scripts pytest scripts/tests/ -v --cov=scripts --cov-report=term-missing
```

## Schema Coverage

The validator enforces all rules from `docs/schema.md`:

### Core Bead Fields
- `title` - Non-empty string
- `status` - One of: open, in_progress, closed, blocked
- `priority` - Integer 0-4
- `issue_type` - One of: beads-ralph-work, beads-ralph-merge
- `assignee` - Must be "beads-ralph-scrum-master"

### Metadata Fields
- `phase` - Pattern: `^[0-9]+[a-z]*$` (e.g., "1", "3a", "3ab")
- `sprint` - Pattern: `^[0-9]+[a-z]*\.[0-9]+[a-z]*$` (e.g., "1.2", "3a.2b")
- `dev_model` - One of: sonnet, opus, haiku
- `dev_prompts` - Non-empty array of strings
- `qa_agents` - Non-empty array of QAAgent objects

### QA Agent Validation
- Each QA agent must have: `agent_path`, `model`, `prompt`, `output_schema`
- `output_schema` must define `status` field with enum ["pass", "fail", "stop"]
- `output_schema` must define `message` field
- `model` must be one of: sonnet, opus, haiku

### Execution Tracking
- `DevExecution` - Validates attempt numbers, status, model
- `QAExecution` - Validates QA status, attempt numbers
- `ScrumResult` - Validates final result structure

## Examples

### Valid Bead

```json
{
  "id": "bd-a1b2c3",
  "title": "Implement user authentication API",
  "description": "Create auth endpoints",
  "status": "open",
  "priority": 1,
  "issue_type": "beads-ralph-work",
  "assignee": "beads-ralph-scrum-master",
  "metadata": {
    "worktree_path": "/path/to/worktree",
    "branch": "main/1-2-auth",
    "source_branch": "main",
    "phase": "1",
    "sprint": "1.2",
    "plan_file": "plans/feature.md",
    "plan_section": "## Phase 1",
    "plan_sprint_id": "1.2",
    "dev_agent_path": ".claude/agents/backend-dev",
    "dev_model": "sonnet",
    "dev_prompts": ["Implement auth API"],
    "qa_agents": [
      {
        "agent_path": ".claude/agents/qa-unit-tests",
        "model": "haiku",
        "prompt": "Run pytest",
        "output_schema": {
          "type": "object",
          "properties": {
            "status": {"enum": ["pass", "fail", "stop"]},
            "message": {"type": "string"}
          },
          "required": ["status", "message"]
        }
      }
    ],
    "max_retry_attempts": 3,
    "attempt_count": 0
  },
  "created_at": "2026-02-07T10:00:00",
  "updated_at": "2026-02-07T10:00:00"
}
```

### Validation Error Output

```
Validation errors:
  title: Value error, title must be non-empty (type=value_error)
  metadata.phase: Value error, phase must match pattern ^[0-9]+[a-z]*$, got: 1.2 (type=value_error)
  metadata.sprint: Value error, sprint must match pattern ^[0-9]+[a-z]*\.[0-9]+[a-z]*$, got: 1 (type=value_error)
  metadata.dev_prompts: Value error, dev_prompts must be non-empty array (type=value_error)
```

## Integration with beads-ralph

This validator will be used by:

- **beads-architect** - Validate generated beads before storage
- **scrum-master** - Validate bead updates after dev/QA execution
- **CI/CD pipeline** - Validate all bead files in repository
- **Developer tools** - Pre-flight checks before creating beads

## Design Philosophy

- **Strict validation** - Using Pydantic's strict mode to prevent type coercion
- **Clear error messages** - Field paths and error types for easy debugging
- **Comprehensive coverage** - All schema rules enforced, >90% test coverage
- **Easy integration** - Simple CLI interface, JSON input/output

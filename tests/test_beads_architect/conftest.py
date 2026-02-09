#!/usr/bin/env python3
"""Shared pytest fixtures for beads-architect tests."""

from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    """Return path to repository root."""
    # tests/test_beads_architect/conftest.py -> go up 3 levels
    # Use absolute() instead of resolve() to avoid following git worktree symlinks
    return Path(__file__).parent.parent.parent.absolute()


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent.absolute() / "fixtures"


@pytest.fixture
def validator_script():
    """Return path to bead validation script."""
    # Calculate from this file: tests/test_beads_architect/conftest.py
    repo_root = Path(__file__).parent.parent.parent.absolute()
    return repo_root / "scripts" / "validate-bead-schema.py"


@pytest.fixture
def examples_dir():
    """Return path to examples directory."""
    repo_root = Path(__file__).parent.parent.parent.absolute()
    return repo_root / "examples"


@pytest.fixture
def sample_sprint_metadata():
    """Provide sample sprint metadata for testing."""
    return {
        "sprint_id": "1.1",
        "title": "Initial Setup",
        "worktree": "../test-worktrees/feature/1-1-setup",
        "branch": "feature/1-1-setup",
        "source_branch": "develop",
        "dev_agents": [
            {"name": "python-backend-dev", "model": "sonnet"}
        ],
        "qa_agents": [
            {
                "name": "qa-python-tests",
                "model": "haiku",
                "prompt": "Run pytest with >90% coverage"
            }
        ],
        "tasks": [
            "Create initial project structure",
            "Set up configuration files",
            "Initialize git repository"
        ],
        "acceptance_criteria": [
            "Project structure follows standard conventions",
            "All configuration files are valid",
            "Git repository is properly initialized"
        ]
    }


@pytest.fixture
def qa_output_schema():
    """Provide valid QA agent output schema."""
    return {
        "type": "object",
        "properties": {
            "status": {
                "enum": ["pass", "fail", "stop"],
                "description": "Validation result"
            },
            "message": {
                "type": "string",
                "description": "Human-readable result message"
            }
        },
        "required": ["status", "message"]
    }

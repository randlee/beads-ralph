#!/usr/bin/env python3
"""Unit tests for CLI validator."""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


def get_valid_bead_json():
    """Return valid bead JSON for testing."""
    return {
        "id": "bd-a1b2c3",
        "title": "Implement user authentication API",
        "description": "Create authentication endpoints",
        "status": "open",
        "priority": 1,
        "issue_type": "beads-ralph-work",
        "assignee": "beads-ralph-scrum-master",
        "dependencies": ["bd-xyz123"],
        "labels": ["phase-01", "sprint-1-2", "backend"],
        "metadata": {
            "worktree_path": "/Users/dev/projects/my-app-worktrees/main/1-2-auth-api",
            "branch": "main/1-2-auth-api",
            "source_branch": "main",
            "phase": "1",
            "sprint": "1.2",
            "plan_file": "plans/feature-auth.md",
            "plan_section": "## Phase 1 > ### Sprint 1.2: User Authentication",
            "plan_sprint_id": "1.2",
            "dev_agent_path": ".claude/agents/backend-dev",
            "dev_model": "sonnet",
            "dev_prompts": [
                "Implement user authentication API endpoints.",
                "Follow existing patterns in services/auth/.",
            ],
            "qa_agents": [
                {
                    "agent_path": ".claude/agents/qa-unit-tests",
                    "model": "haiku",
                    "prompt": "Run pytest with coverage.",
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "status": {"enum": ["pass", "fail", "stop"]},
                            "message": {"type": "string"},
                            "coverage_percent": {"type": "number"},
                        },
                        "required": ["status", "message"],
                    },
                }
            ],
            "max_retry_attempts": 3,
            "attempt_count": 0,
            "scrum_master_session_id": None,
            "dev_agent_session_id": None,
            "dev_agent_executions": [],
            "qa_agent_executions": [],
            "pr_url": None,
            "pr_number": None,
            "scrum_result": None,
        },
        "created_at": "2026-02-07T10:00:00",
        "updated_at": "2026-02-07T10:00:00",
        "closed_at": None,
        "comments": [],
        "external_ref": None,
        "owner": None,
    }


def get_merge_bead_json():
    """Return valid merge bead JSON for testing."""
    return {
        "id": "bd-m1m2m3",
        "title": "Merge sprint 1.2 branches",
        "description": "Integrate branches from parallel sprints",
        "status": "open",
        "priority": 1,
        "issue_type": "beads-ralph-merge",
        "assignee": "beads-ralph-scrum-master",
        "dependencies": ["bd-a1b2c3", "bd-d4e5f6"],
        "labels": ["phase-01", "sprint-1-3", "merge"],
        "metadata": {
            "worktree_path": "/Users/dev/projects/my-app-worktrees/main/1-3-merge",
            "branch": "main/1-3-merge",
            "source_branch": "main",
            "phase": "1",
            "sprint": "1.3",
            "plan_file": "plans/feature-auth.md",
            "plan_section": "## Phase 1 > ### Sprint 1.3: Integration",
            "plan_sprint_id": "1.3",
            "branches_to_merge": [
                "main/1-2a-auth-api",
                "main/1-2b-user-profile",
            ],
            "dev_agent_path": ".claude/agents/merge-specialist",
            "dev_model": "sonnet",
            "dev_prompts": [
                "Merge branches carefully",
                "Resolve any merge conflicts",
            ],
            "qa_agents": [
                {
                    "agent_path": ".claude/agents/qa-integration-tests",
                    "model": "sonnet",
                    "prompt": "Run full integration test suite.",
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "status": {"enum": ["pass", "fail", "stop"]},
                            "message": {"type": "string"},
                        },
                        "required": ["status", "message"],
                    },
                }
            ],
            "max_retry_attempts": 3,
            "attempt_count": 0,
            "scrum_master_session_id": None,
            "dev_agent_session_id": None,
            "dev_agent_executions": [],
            "qa_agent_executions": [],
            "pr_url": None,
            "pr_number": None,
            "scrum_result": None,
        },
        "created_at": "2026-02-07T10:30:00",
        "updated_at": "2026-02-07T10:30:00",
        "closed_at": None,
        "comments": [],
        "external_ref": None,
        "owner": None,
    }


class TestValidatorFileInput:
    """Tests for validator with file input."""

    def test_valid_bead_file(self):
        """Test validator accepts valid bead JSON file."""
        bead_json = get_valid_bead_json()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "✓ Valid bead" in result.stdout
        finally:
            Path(temp_path).unlink()

    def test_valid_merge_bead_file(self):
        """Test validator accepts valid merge bead JSON file."""
        bead_json = get_merge_bead_json()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "✓ Valid bead" in result.stdout
        finally:
            Path(temp_path).unlink()

    def test_invalid_bead_missing_title(self):
        """Test validator rejects bead with missing title."""
        bead_json = get_valid_bead_json()
        bead_json["title"] = "   "  # Empty title

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Validation errors:" in result.stderr
            assert "title" in result.stderr
        finally:
            Path(temp_path).unlink()

    def test_invalid_bead_wrong_phase_pattern(self):
        """Test validator rejects bead with invalid phase pattern."""
        bead_json = get_valid_bead_json()
        bead_json["metadata"]["phase"] = "1.2"  # Invalid (contains dot)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Validation errors:" in result.stderr
            assert "phase must match pattern" in result.stderr
        finally:
            Path(temp_path).unlink()

    def test_invalid_bead_wrong_sprint_pattern(self):
        """Test validator rejects bead with invalid sprint pattern."""
        bead_json = get_valid_bead_json()
        bead_json["metadata"]["sprint"] = "1"  # Invalid (missing dot)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Validation errors:" in result.stderr
            assert "sprint must match pattern" in result.stderr
        finally:
            Path(temp_path).unlink()

    def test_invalid_bead_wrong_assignee(self):
        """Test validator rejects bead with wrong assignee."""
        bead_json = get_valid_bead_json()
        bead_json["assignee"] = "wrong-assignee"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Validation errors:" in result.stderr
            assert "assignee" in result.stderr
        finally:
            Path(temp_path).unlink()

    def test_invalid_bead_empty_dev_prompts(self):
        """Test validator rejects bead with empty dev_prompts."""
        bead_json = get_valid_bead_json()
        bead_json["metadata"]["dev_prompts"] = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Validation errors:" in result.stderr
            assert "dev_prompts must be non-empty" in result.stderr
        finally:
            Path(temp_path).unlink()

    def test_invalid_bead_missing_qa_output_schema_status(self):
        """Test validator rejects bead with QA agent missing status in output_schema."""
        bead_json = get_valid_bead_json()
        bead_json["metadata"]["qa_agents"][0]["output_schema"] = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bead_json, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python3", "scripts/validate-bead-schema.py", temp_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Validation errors:" in result.stderr
            assert "'status' property" in result.stderr
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test validator handles file not found error."""
        result = subprocess.run(
            ["python3", "scripts/validate-bead-schema.py", "/nonexistent/file.json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Error:" in result.stderr


class TestValidatorStdinInput:
    """Tests for validator with stdin input."""

    def test_valid_bead_stdin(self):
        """Test validator accepts valid bead JSON from stdin."""
        bead_json = get_valid_bead_json()
        json_str = json.dumps(bead_json)

        result = subprocess.run(
            ["python3", "scripts/validate-bead-schema.py"],
            input=json_str,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "✓ Valid bead" in result.stdout

    def test_invalid_bead_stdin(self):
        """Test validator rejects invalid bead JSON from stdin."""
        bead_json = get_valid_bead_json()
        bead_json["status"] = "invalid"  # Invalid status

        json_str = json.dumps(bead_json)

        result = subprocess.run(
            ["python3", "scripts/validate-bead-schema.py"],
            input=json_str,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Validation errors:" in result.stderr
        assert "status" in result.stderr


class TestValidatorErrorMessages:
    """Tests for validator error message formatting."""

    def test_error_message_includes_field_path(self):
        """Test error messages include field path."""
        bead_json = get_valid_bead_json()
        bead_json["metadata"]["dev_model"] = "invalid-model"

        json_str = json.dumps(bead_json)

        result = subprocess.run(
            ["python3", "scripts/validate-bead-schema.py"],
            input=json_str,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "metadata.dev_model" in result.stderr

    def test_multiple_validation_errors(self):
        """Test multiple validation errors are all reported."""
        bead_json = get_valid_bead_json()
        bead_json["title"] = "   "  # Invalid
        bead_json["status"] = "invalid"  # Invalid
        bead_json["priority"] = 10  # Invalid

        json_str = json.dumps(bead_json)

        result = subprocess.run(
            ["python3", "scripts/validate-bead-schema.py"],
            input=json_str,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        # All errors should be reported
        assert "title" in result.stderr
        assert "status" in result.stderr
        assert "priority" in result.stderr

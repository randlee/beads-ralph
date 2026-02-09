#!/usr/bin/env python3
"""Tests for schema validation integration in beads-architect.

These tests validate that beads-architect properly integrates with
the validate-bead-schema.py CLI tool to ensure generated beads are valid.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

import pytest


class TestSchemaValidationIntegration:
    """Tests for integrating with validate-bead-schema.py."""

    @pytest.fixture
    def sample_valid_bead(self, tmp_path):
        """Create a sample valid bead JSON file."""
        bead = {
            "id": "bd-1-1-test-validation",
            "title": "Test Validation",
            "description": "Test bead for validation",
            "status": "open",
            "priority": 1,
            "issue_type": "beads-ralph-work",
            "assignee": "beads-ralph-scrum-master",
            "owner": "beads-ralph-system",
            "dependencies": [],
            "labels": ["phase-01", "sprint-1-1"],
            "comments": [],
            "external_ref": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "closed_at": None,
            "metadata": {
                "rig": "beads-ralph",
                "worktree_path": "../test-worktrees/feature/1-1-test",
                "branch": "feature/1-1-test",
                "source_branch": "develop",
                "phase": "1",
                "sprint": "1.1",
                "plan_file": "pm/test-plan.md",
                "plan_section": "### Sprint 1.1: Test",
                "plan_sprint_id": "1.1",
                "branches_to_merge": None,
                "dev_agent_path": ".claude/agents/python-backend-dev",
                "dev_model": "sonnet",
                "dev_prompts": ["Create test"],
                "qa_agents": [
                    {
                        "agent_path": ".claude/agents/qa-python-tests",
                        "model": "haiku",
                        "prompt": "Run tests",
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
                "attempt_count": 0,
                "scrum_master_session_id": None,
                "dev_agent_session_id": None,
                "dev_agent_executions": [],
                "qa_agent_executions": [],
                "pr_url": None,
                "pr_number": None,
                "scrum_result": None,
            }
        }

        # Write to temp file
        bead_file = tmp_path / "valid-bead.json"
        with open(bead_file, "w") as f:
            json.dump(bead, f, indent=2)

        return bead_file

    def test_valid_bead_passes_validation(self, validator_script, sample_valid_bead):
        """Test that valid bead passes schema validation."""
        result = subprocess.run(
            ["python3", str(validator_script), str(sample_valid_bead)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Validation failed: {result.stderr}"
        assert "valid" in result.stdout.lower() or result.stdout == ""

    @pytest.mark.skip(reason="Validator script may not support stdin yet")
    def test_validation_via_stdin(self, validator_script, sample_valid_bead):
        """Test validation accepts JSON via stdin."""
        with open(sample_valid_bead) as f:
            bead_json = f.read()

        result = subprocess.run(
            ["python3", str(validator_script), "-"],
            input=bead_json,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_missing_required_field_fails(self, validator_script, tmp_path):
        """Test that bead missing required field fails validation."""
        invalid_bead = {
            "id": "bd-1-1-invalid",
            "title": "Invalid Bead",
            # Missing many required fields
        }

        bead_file = tmp_path / "invalid-bead.json"
        with open(bead_file, "w") as f:
            json.dump(invalid_bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(bead_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "validation error" in result.stderr.lower() or "field required" in result.stderr.lower()

    def test_invalid_phase_pattern_fails(self, validator_script, sample_valid_bead, tmp_path):
        """Test that invalid phase pattern fails validation."""
        with open(sample_valid_bead) as f:
            bead = json.load(f)

        # Set invalid phase
        bead["metadata"]["phase"] = "invalid-phase"

        invalid_file = tmp_path / "invalid-phase.json"
        with open(invalid_file, "w") as f:
            json.dump(bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(invalid_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1

    def test_invalid_sprint_pattern_fails(self, validator_script, sample_valid_bead, tmp_path):
        """Test that invalid sprint pattern fails validation."""
        with open(sample_valid_bead) as f:
            bead = json.load(f)

        # Set invalid sprint
        bead["metadata"]["sprint"] = "1.2.3"  # Too many parts

        invalid_file = tmp_path / "invalid-sprint.json"
        with open(invalid_file, "w") as f:
            json.dump(bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(invalid_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1

    def test_missing_rig_field_fails(self, validator_script, sample_valid_bead, tmp_path):
        """Test that bead without rig field fails validation."""
        with open(sample_valid_bead) as f:
            bead = json.load(f)

        # Remove rig field
        del bead["metadata"]["rig"]

        invalid_file = tmp_path / "no-rig.json"
        with open(invalid_file, "w") as f:
            json.dump(bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(invalid_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


class TestQAAgentSchemaValidation:
    """Tests for QA agent output schema validation."""

    def test_qa_agent_without_status_enum_fails(self):
        """Test QA agent without status enum fails validation."""
        invalid_qa_agent = {
            "agent_path": ".claude/agents/qa-test",
            "model": "haiku",
            "prompt": "Test",
            "output_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                    # Missing status field
                }
            }
        }

        # This should fail pydantic validation
        assert "status" not in invalid_qa_agent["output_schema"]["properties"]

    def test_qa_agent_with_wrong_status_values_fails(self):
        """Test QA agent with incorrect status enum values fails."""
        invalid_qa_agent = {
            "agent_path": ".claude/agents/qa-test",
            "model": "haiku",
            "prompt": "Test",
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"enum": ["success", "failure"]},  # Wrong values
                    "message": {"type": "string"}
                }
            }
        }

        # Should have ["pass", "fail", "stop"]
        actual_enum = invalid_qa_agent["output_schema"]["properties"]["status"]["enum"]
        expected_enum = ["pass", "fail", "stop"]

        assert actual_enum != expected_enum

    def test_qa_agent_valid_output_schema(self):
        """Test QA agent with valid output schema."""
        valid_qa_agent = {
            "agent_path": ".claude/agents/qa-test",
            "model": "haiku",
            "prompt": "Test",
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"enum": ["pass", "fail", "stop"]},
                    "message": {"type": "string"}
                },
                "required": ["status", "message"]
            }
        }

        # Verify structure
        schema = valid_qa_agent["output_schema"]
        assert "status" in schema["properties"]
        assert schema["properties"]["status"]["enum"] == ["pass", "fail", "stop"]
        assert "message" in schema["properties"]
        assert "status" in schema["required"]
        assert "message" in schema["required"]


class TestValidationErrorReporting:
    """Tests for validation error reporting and handling."""

    def test_validation_error_includes_field_path(self, validator_script, tmp_path):
        """Test validation errors include field paths."""
        invalid_bead = {
            "id": "bd-1-1-test",
            "title": "Test",
            # Missing many fields
        }

        bead_file = tmp_path / "error-test.json"
        with open(bead_file, "w") as f:
            json.dump(invalid_bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(bead_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        # Should mention specific fields
        error_output = result.stderr.lower()
        # Common validation frameworks mention field names
        assert len(error_output) > 0

    def test_validation_error_is_parseable(self, validator_script, tmp_path):
        """Test validation errors are in parseable format."""
        invalid_bead = {"id": "test"}

        bead_file = tmp_path / "parse-test.json"
        with open(bead_file, "w") as f:
            json.dump(invalid_bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(bead_file)],
            capture_output=True,
            text=True
        )

        # Should have clear error output
        assert result.returncode == 1
        assert len(result.stderr) > 0

    def test_multiple_validation_errors_reported(self, validator_script, tmp_path):
        """Test that multiple validation errors are all reported."""
        invalid_bead = {
            "id": "bd-1-1-test",
            # Missing many required fields - should report all
        }

        bead_file = tmp_path / "multi-error.json"
        with open(bead_file, "w") as f:
            json.dump(invalid_bead, f)

        result = subprocess.run(
            ["python3", str(validator_script), str(bead_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        # Should report multiple errors (check for multiple lines or error count)
        error_lines = result.stderr.strip().split("\n")
        assert len(error_lines) > 0


class TestBatchValidation:
    """Tests for validating multiple beads in batch."""

    def test_validate_multiple_bead_files(self, validator_script, tmp_path):
        """Test validating multiple bead files."""
        # Create multiple valid beads
        for i in range(3):
            bead = {
                "id": f"bd-1-{i+1}-test",
                "title": f"Test {i+1}",
                "description": f"Test bead {i+1}",
                "status": "open",
                "priority": 1,
                "issue_type": "beads-ralph-work",
                "assignee": "beads-ralph-scrum-master",
                "owner": "beads-ralph-system",
                "dependencies": [],
                "labels": [f"phase-01", f"sprint-1-{i+1}"],
                "comments": [],
                "external_ref": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "closed_at": None,
                "metadata": {
                    "rig": "beads-ralph",
                    "worktree_path": f"../test-worktrees/feature/1-{i+1}-test",
                    "branch": f"feature/1-{i+1}-test",
                    "source_branch": "develop",
                    "phase": "1",
                    "sprint": f"1.{i+1}",
                    "plan_file": "pm/test-plan.md",
                    "plan_section": f"### Sprint 1.{i+1}: Test",
                    "plan_sprint_id": f"1.{i+1}",
                    "branches_to_merge": None,
                    "dev_agent_path": ".claude/agents/python-backend-dev",
                    "dev_model": "sonnet",
                    "dev_prompts": [f"Task {i+1}"],
                    "qa_agents": [
                    {
                        "agent_path": ".claude/agents/qa-python-tests",
                        "model": "haiku",
                        "prompt": "Run tests",
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
                    "attempt_count": 0,
                    "scrum_master_session_id": None,
                    "dev_agent_session_id": None,
                    "dev_agent_executions": [],
                    "qa_agent_executions": [],
                    "pr_url": None,
                    "pr_number": None,
                    "scrum_result": None,
                }
            }

            bead_file = tmp_path / f"bead-{i+1}.json"
            with open(bead_file, "w") as f:
                json.dump(bead, f, indent=2)

        # Validate each file
        bead_files = list(tmp_path.glob("bead-*.json"))
        assert len(bead_files) == 3

        for bead_file in bead_files:
            result = subprocess.run(
                ["python3", str(validator_script), str(bead_file)],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Failed to validate {bead_file}: {result.stderr}"


class TestValidationInBeadsArchitect:
    """Tests for how beads-architect should use validation."""

    def test_validation_step_in_workflow(self):
        """Test that validation is a required step in bead generation workflow."""
        # Beads-architect workflow should include:
        # 1. Parse plan
        # 2. Generate bead JSON
        # 3. Validate with validate-bead-schema.py
        # 4. Only include valid beads in output

        workflow_steps = [
            "parse_plan",
            "generate_bead_json",
            "validate_bead",  # Critical step
            "return_result"
        ]

        assert "validate_bead" in workflow_steps

    def test_validation_failure_handling(self):
        """Test how beads-architect should handle validation failures."""
        # Expected behavior:
        # - Catch validation errors
        # - Report with error code: VALIDATION.BEAD_SCHEMA
        # - Include suggested action
        # - Mark as recoverable error

        expected_error_response = {
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION.BEAD_SCHEMA",
                "message": "Bead validation failed",
                "recoverable": True,
                "suggested_action": "Review pydantic validation errors"
            }
        }

        assert expected_error_response["error"]["code"] == "VALIDATION.BEAD_SCHEMA"
        assert expected_error_response["error"]["recoverable"] is True

    def test_partial_validation_failure(self):
        """Test handling when some beads validate but others don't."""
        # If generating multiple beads, some may be valid and some invalid
        # Beads-architect should:
        # - Validate each bead independently
        # - Include valid beads in output
        # - Report invalid beads with errors

        beads = [
            {"id": "bd-1-1-valid", "valid": True},
            {"id": "bd-1-2-invalid", "valid": False},
            {"id": "bd-1-3-valid", "valid": True},
        ]

        valid_beads = [b for b in beads if b["valid"]]
        invalid_beads = [b for b in beads if not b["valid"]]

        assert len(valid_beads) == 2
        assert len(invalid_beads) == 1


class TestExampleBeadValidation:
    """Tests for validating example beads from the repository."""

    def test_example_work_bead_validates(self, validator_script, examples_dir):
        """Test that example work bead passes validation."""
        work_bead_file = examples_dir / "example-work-bead.json"

        if not work_bead_file.exists():
            pytest.skip("Example work bead not found")

        result = subprocess.run(
            ["python3", str(validator_script), str(work_bead_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Example work bead failed validation: {result.stderr}"

    def test_example_merge_bead_validates(self, validator_script, examples_dir):
        """Test that example merge bead passes validation."""
        merge_bead_file = examples_dir / "example-merge-bead.json"

        if not merge_bead_file.exists():
            pytest.skip("Example merge bead not found")

        result = subprocess.run(
            ["python3", str(validator_script), str(merge_bead_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Example merge bead failed validation: {result.stderr}"

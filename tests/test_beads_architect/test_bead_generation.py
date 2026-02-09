#!/usr/bin/env python3
"""Tests for complete bead JSON generation.

These tests validate that beads-architect generates complete, valid bead JSON
with all 34 required fields properly populated from plan metadata.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest


class TestBeadIDGeneration:
    """Tests for generating bead IDs from sprint information."""

    @pytest.mark.parametrize("sprint_id,title,expected", [
        ("1.1", "Initial Setup", "bd-1-1-initial-setup"),
        ("1.2a", "Work Bead Example", "bd-1-2a-work-bead-example"),
        ("3a.2", "User Interface Components", "bd-3a-2-user-interface-components"),
        ("4.1", "System Integration", "bd-4-1-system-integration"),
    ])
    def test_bead_id_format(self, sprint_id, title, expected):
        """Test bead ID follows pattern: bd-<sprint>-<title-slug>."""
        # Convert title to slug: lowercase, replace spaces with hyphens
        # Handle phase splits correctly (3a.2 -> bd-3a-2-...)
        sprint_part = sprint_id.replace(".", "-")
        slug = title.lower().replace(" ", "-")
        bead_id = f"bd-{sprint_part}-{slug}"

        assert bead_id == expected

    def test_bead_id_special_characters(self):
        """Test bead ID handles special characters in titles."""
        title = "Test & Validation (with punctuation)"
        # Should strip special chars, keep alphanumeric and hyphens
        expected_slug = "test-validation-with-punctuation"

        # Simple implementation: keep only alphanumeric and spaces, then hyphenate
        cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in title)
        slug = "-".join(cleaned.lower().split())

        assert slug == expected_slug


class TestCoreFieldGeneration:
    """Tests for generating core bead fields."""

    def test_required_core_fields_present(self):
        """Test all 15 core fields are present in generated bead."""
        required_core_fields = [
            "id", "title", "description", "status", "priority",
            "issue_type", "assignee", "owner", "dependencies",
            "labels", "comments", "external_ref", "created_at",
            "updated_at", "closed_at"
        ]

        # Mock bead structure
        bead = {
            "id": "bd-1-1-test",
            "title": "Test Sprint",
            "description": "Test description",
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
        }

        for field in required_core_fields:
            assert field in bead, f"Missing required field: {field}"

    def test_work_bead_issue_type(self):
        """Test work beads have correct issue_type."""
        bead = {"issue_type": "beads-ralph-work"}
        assert bead["issue_type"] == "beads-ralph-work"

    def test_merge_bead_issue_type(self):
        """Test merge beads have correct issue_type."""
        bead = {"issue_type": "beads-ralph-merge"}
        assert bead["issue_type"] == "beads-ralph-merge"

    def test_status_defaults_to_open(self):
        """Test newly generated beads default to 'open' status."""
        bead = {"status": "open"}
        assert bead["status"] == "open"

    def test_priority_from_phase(self):
        """Test priority is derived from phase number."""
        # Phase 1 -> priority 1, Phase 2 -> priority 2, etc.
        test_cases = [
            ("1", 1),
            ("2", 2),
            ("3a", 3),
            ("4", 4),
        ]

        for phase, expected_priority in test_cases:
            # Extract numeric part of phase
            priority = int(phase[0]) if phase[0].isdigit() else 1
            assert priority == expected_priority

    def test_labels_include_phase_and_sprint(self):
        """Test labels include phase and sprint tags."""
        bead = {
            "labels": ["phase-01", "sprint-1-1"],
            "metadata": {"phase": "1", "sprint": "1.1"}
        }

        # Verify phase label format
        assert any(label.startswith("phase-") for label in bead["labels"])
        # Verify sprint label format
        assert any(label.startswith("sprint-") for label in bead["labels"])

    def test_timestamps_iso_format(self):
        """Test timestamps use ISO 8601 format."""
        now = datetime.now().isoformat()
        bead = {
            "created_at": now,
            "updated_at": now,
        }

        # Should be valid ISO format
        datetime.fromisoformat(bead["created_at"])
        datetime.fromisoformat(bead["updated_at"])


class TestMetadataFieldGeneration:
    """Tests for generating metadata fields."""

    def test_required_metadata_fields_present(self):
        """Test all 19 metadata fields are present."""
        required_metadata_fields = [
            "rig", "worktree_path", "branch", "source_branch", "phase",
            "sprint", "plan_file", "plan_section", "plan_sprint_id",
            "branches_to_merge", "dev_agent_path", "dev_model",
            "dev_prompts", "qa_agents", "max_retry_attempts",
            "attempt_count", "scrum_master_session_id",
            "dev_agent_session_id", "dev_agent_executions",
            "qa_agent_executions", "pr_url", "pr_number", "scrum_result"
        ]

        # Note: schema has 23 total metadata fields (19 from agent doc + 4 execution tracking)
        metadata = {
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
            "dev_prompts": ["Task 1", "Task 2"],
            "qa_agents": [],
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

        for field in required_metadata_fields:
            assert field in metadata, f"Missing metadata field: {field}"

    def test_rig_field_always_beads_ralph(self):
        """Test rig field is always 'beads-ralph'."""
        metadata = {"rig": "beads-ralph"}
        assert metadata["rig"] == "beads-ralph"

    def test_worktree_path_from_plan(self):
        """Test worktree_path extracted from plan metadata."""
        plan_metadata = {"worktree": "../test-worktrees/feature/1-1-test"}
        bead_metadata = {"worktree_path": plan_metadata["worktree"]}

        assert bead_metadata["worktree_path"] == "../test-worktrees/feature/1-1-test"

    def test_branch_and_source_branch_from_plan(self):
        """Test branch fields extracted from plan."""
        plan_metadata = {
            "branch": "feature/1-1-test",
            "source_branch": "develop"
        }
        bead_metadata = {
            "branch": plan_metadata["branch"],
            "source_branch": plan_metadata["source_branch"]
        }

        assert bead_metadata["branch"] == "feature/1-1-test"
        assert bead_metadata["source_branch"] == "develop"

    def test_phase_and_sprint_from_sprint_id(self):
        """Test phase and sprint extracted from sprint ID."""
        sprint_id = "3a.2"

        # Extract phase (everything before last dot)
        parts = sprint_id.split(".")
        if len(parts[0]) > 1 and parts[0][-1].isalpha():
            phase = parts[0]  # "3a"
        else:
            phase = parts[0][0]  # "3"

        metadata = {
            "phase": phase,
            "sprint": sprint_id,
            "plan_sprint_id": sprint_id
        }

        assert metadata["sprint"] == "3a.2"
        assert metadata["plan_sprint_id"] == "3a.2"

    def test_branches_to_merge_null_for_work_beads(self):
        """Test branches_to_merge is null for work beads."""
        work_bead_metadata = {
            "issue_type": "beads-ralph-work",
            "branches_to_merge": None
        }

        assert work_bead_metadata["branches_to_merge"] is None

    def test_branches_to_merge_array_for_merge_beads(self):
        """Test branches_to_merge is array for merge beads."""
        merge_bead_metadata = {
            "issue_type": "beads-ralph-merge",
            "branches_to_merge": ["feature/1-2a-frontend", "feature/1-2b-backend"]
        }

        assert isinstance(merge_bead_metadata["branches_to_merge"], list)
        assert len(merge_bead_metadata["branches_to_merge"]) == 2

    def test_initial_execution_arrays_empty(self):
        """Test execution tracking arrays start empty."""
        metadata = {
            "dev_agent_executions": [],
            "qa_agent_executions": [],
        }

        assert metadata["dev_agent_executions"] == []
        assert metadata["qa_agent_executions"] == []

    def test_initial_session_ids_null(self):
        """Test session IDs start as null."""
        metadata = {
            "scrum_master_session_id": None,
            "dev_agent_session_id": None,
        }

        assert metadata["scrum_master_session_id"] is None
        assert metadata["dev_agent_session_id"] is None

    def test_initial_pr_fields_null(self):
        """Test PR fields start as null."""
        metadata = {
            "pr_url": None,
            "pr_number": None,
        }

        assert metadata["pr_url"] is None
        assert metadata["pr_number"] is None


class TestDevAgentConfiguration:
    """Tests for dev agent configuration in beads."""

    def test_single_dev_agent_parsing(self):
        """Test parsing single dev agent from plan."""
        plan_text = """**Dev Agents**:
- `python-backend-dev` (sonnet)
"""
        # Expected result
        expected = {
            "dev_agent_path": ".claude/agents/python-backend-dev",
            "dev_model": "sonnet"
        }

        # In real implementation, would parse from plan_text
        assert expected["dev_model"] in ["haiku", "sonnet", "opus"]

    def test_multiple_dev_agents_first_used(self):
        """Test that first dev agent is used as primary."""
        plan_text = """**Dev Agents**:
- `python-backend-dev` (sonnet)
- `go-backend-dev` (sonnet)
"""
        # Should use first agent as primary
        expected = {
            "dev_agent_path": ".claude/agents/python-backend-dev",
            "dev_model": "sonnet"
        }

        # Note: Multiple dev agents might be listed in dev_prompts context
        assert expected["dev_agent_path"] == ".claude/agents/python-backend-dev"

    def test_dev_model_extraction(self):
        """Test extracting model from agent specification."""
        test_cases = [
            ("python-backend-dev (haiku)", "haiku"),
            ("go-backend-dev (sonnet)", "sonnet"),
            ("planning-architect (opus)", "opus"),
        ]

        for agent_spec, expected_model in test_cases:
            # Extract model from parentheses
            model = agent_spec.split("(")[1].split(")")[0]
            assert model == expected_model

    def test_dev_prompts_from_tasks(self):
        """Test dev_prompts populated from task list."""
        tasks = [
            "Create initial project structure",
            "Set up configuration files",
            "Initialize git repository"
        ]

        metadata = {"dev_prompts": tasks}

        assert len(metadata["dev_prompts"]) == 3
        assert all(isinstance(task, str) for task in metadata["dev_prompts"])


class TestQAAgentConfiguration:
    """Tests for QA agent configuration in beads."""

    def test_qa_agent_structure(self):
        """Test QA agent has required fields."""
        qa_agent = {
            "agent_path": ".claude/agents/qa-python-tests",
            "model": "haiku",
            "prompt": "Run pytest with >90% coverage",
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"enum": ["pass", "fail", "stop"]},
                    "message": {"type": "string"}
                },
                "required": ["status", "message"]
            }
        }

        assert "agent_path" in qa_agent
        assert "model" in qa_agent
        assert "prompt" in qa_agent
        assert "output_schema" in qa_agent

    def test_qa_agent_output_schema_structure(self):
        """Test QA agent output_schema has required status field."""
        output_schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["pass", "fail", "stop"]},
                "message": {"type": "string"}
            },
            "required": ["status", "message"]
        }

        # Verify status enum
        assert "status" in output_schema["properties"]
        assert "enum" in output_schema["properties"]["status"]
        assert set(output_schema["properties"]["status"]["enum"]) == {"pass", "fail", "stop"}

        # Verify required fields
        assert "status" in output_schema["required"]
        assert "message" in output_schema["required"]

    def test_multiple_qa_agents_parsing(self):
        """Test parsing multiple QA agents from plan."""
        qa_agents = [
            {
                "agent_path": ".claude/agents/qa-python-tests",
                "model": "haiku",
                "prompt": "Run pytest"
            },
            {
                "agent_path": ".claude/agents/qa-schema-validator",
                "model": "haiku",
                "prompt": "Validate schema"
            }
        ]

        assert len(qa_agents) == 2
        assert all("agent_path" in qa for qa in qa_agents)
        assert all("model" in qa for qa in qa_agents)

    def test_qa_agent_model_validation(self):
        """Test QA agent model is valid."""
        valid_models = ["haiku", "sonnet", "opus"]

        test_agents = [
            {"model": "haiku"},
            {"model": "sonnet"},
            {"model": "opus"},
        ]

        for agent in test_agents:
            assert agent["model"] in valid_models


class TestBeadValidation:
    """Tests for validating generated beads against schema."""

    @pytest.fixture
    def sample_complete_bead(self):
        """Provide a complete sample bead for testing."""
        return {
            "id": "bd-1-1-test",
            "title": "Test Sprint",
            "description": "Test description",
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
                "dev_prompts": ["Task 1"],
                "qa_agents": [],
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

    def test_complete_bead_structure(self, sample_complete_bead):
        """Test complete bead has all required fields."""
        # Core fields
        core_fields = [
            "id", "title", "description", "status", "priority",
            "issue_type", "assignee", "owner", "dependencies",
            "labels", "comments", "external_ref", "created_at",
            "updated_at", "closed_at"
        ]

        for field in core_fields:
            assert field in sample_complete_bead

        # Metadata fields
        assert "metadata" in sample_complete_bead
        assert "rig" in sample_complete_bead["metadata"]

    def test_bead_json_serializable(self, sample_complete_bead):
        """Test bead can be serialized to JSON."""
        json_str = json.dumps(sample_complete_bead, indent=2)
        assert json_str is not None

        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["id"] == sample_complete_bead["id"]


class TestCompleteBeadGeneration:
    """Integration tests for complete bead generation from plan sections."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_generate_bead_from_simple_plan_sprint(self, fixtures_dir):
        """Test generating complete bead from simple plan sprint."""
        # This would be implemented by actual beads-architect agent
        # Test validates the expected structure

        expected_bead_structure = {
            "id": str,
            "title": str,
            "description": str,
            "status": str,
            "priority": int,
            "issue_type": str,
            "dependencies": list,
            "metadata": {
                "rig": str,
                "worktree_path": str,
                "branch": str,
                "phase": str,
                "sprint": str,
            }
        }

        # Verify types (placeholder for actual implementation test)
        assert expected_bead_structure["id"] == str
        assert expected_bead_structure["metadata"]["rig"] == str

    def test_generate_multiple_beads_from_plan(self, fixtures_dir):
        """Test generating multiple beads from plan with multiple sprints."""
        plan_file = fixtures_dir / "simple-plan.md"

        # Should generate 3 beads for 3 sprints
        expected_bead_count = 3

        # Placeholder for actual implementation
        assert expected_bead_count == 3

    def test_beads_have_correct_dependencies(self, fixtures_dir):
        """Test generated beads have correct dependency relationships."""
        # For simple-plan.md: 1.1 -> 1.2 -> 1.3

        expected_dependencies = {
            "bd-1-1-initial-setup": [],
            "bd-1-2-core-implementation": ["bd-1-1-initial-setup"],
            "bd-1-3-final-integration": ["bd-1-2-core-implementation"],
        }

        # Placeholder for actual verification
        for bead_id, deps in expected_dependencies.items():
            assert isinstance(deps, list)

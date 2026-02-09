#!/usr/bin/env python3
"""Unit tests for pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from bead_schema import (
    Bead,
    BeadMetadata,
    DevExecution,
    QAAgent,
    QAExecution,
    QAResult,
    ScrumResult,
)


class TestQAAgent:
    """Tests for QAAgent model."""

    def test_valid_qa_agent(self):
        """Test valid QA agent configuration."""
        qa = QAAgent(
            agent_path=".claude/agents/qa-unit-tests",
            model="haiku",
            prompt="Run pytest with coverage",
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"enum": ["pass", "fail", "stop"]},
                    "message": {"type": "string"},
                },
            },
        )
        assert qa.agent_path == ".claude/agents/qa-unit-tests"
        assert qa.model == "haiku"

    def test_invalid_model(self):
        """Test invalid model raises error."""
        with pytest.raises(ValidationError) as exc_info:
            QAAgent(
                agent_path=".claude/agents/qa-unit-tests",
                model="gpt-4",  # Invalid
                prompt="Test",
                output_schema={
                    "type": "object",
                    "properties": {
                        "status": {"enum": ["pass", "fail", "stop"]},
                        "message": {"type": "string"},
                    },
                },
            )
        assert "model must be one of" in str(exc_info.value)

    def test_missing_status_in_output_schema(self):
        """Test output_schema without status field raises error."""
        with pytest.raises(ValidationError) as exc_info:
            QAAgent(
                agent_path=".claude/agents/qa-unit-tests",
                model="haiku",
                prompt="Test",
                output_schema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                    },
                },
            )
        assert "must have 'status' property" in str(exc_info.value)

    def test_missing_message_in_output_schema(self):
        """Test output_schema without message field raises error."""
        with pytest.raises(ValidationError) as exc_info:
            QAAgent(
                agent_path=".claude/agents/qa-unit-tests",
                model="haiku",
                prompt="Test",
                output_schema={
                    "type": "object",
                    "properties": {
                        "status": {"enum": ["pass", "fail", "stop"]},
                    },
                },
            )
        assert "must have 'message' property" in str(exc_info.value)

    def test_invalid_status_enum(self):
        """Test invalid status enum values raise error."""
        with pytest.raises(ValidationError) as exc_info:
            QAAgent(
                agent_path=".claude/agents/qa-unit-tests",
                model="haiku",
                prompt="Test",
                output_schema={
                    "type": "object",
                    "properties": {
                        "status": {"enum": ["pass", "fail", "invalid"]},
                        "message": {"type": "string"},
                    },
                },
            )
        assert "status enum must only contain" in str(exc_info.value)


class TestDevExecution:
    """Tests for DevExecution model."""

    def test_valid_dev_execution(self):
        """Test valid dev execution."""
        dev = DevExecution(
            attempt=1,
            session_id="claude-dev-abc123",
            agent_path=".claude/agents/backend-dev",
            model="sonnet",
            started_at=datetime(2026, 2, 7, 10, 0, 0),
            completed_at=datetime(2026, 2, 7, 10, 15, 0),
            status="completed",
        )
        assert dev.attempt == 1
        assert dev.status == "completed"

    def test_invalid_attempt(self):
        """Test invalid attempt number raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DevExecution(
                attempt=0,  # Invalid
                session_id="claude-dev-abc123",
                agent_path=".claude/agents/backend-dev",
                model="sonnet",
                started_at=datetime(2026, 2, 7, 10, 0, 0),
                completed_at=datetime(2026, 2, 7, 10, 15, 0),
                status="completed",
            )
        assert "attempt must be >= 1" in str(exc_info.value)

    def test_invalid_status(self):
        """Test invalid status raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DevExecution(
                attempt=1,
                session_id="claude-dev-abc123",
                agent_path=".claude/agents/backend-dev",
                model="sonnet",
                started_at=datetime(2026, 2, 7, 10, 0, 0),
                completed_at=datetime(2026, 2, 7, 10, 15, 0),
                status="invalid",  # Invalid
            )
        assert "status must be one of" in str(exc_info.value)


class TestQAExecution:
    """Tests for QAExecution model."""

    def test_valid_qa_execution(self):
        """Test valid QA execution."""
        qa = QAExecution(
            attempt=1,
            session_id="claude-qa-abc123",
            agent_path=".claude/agents/qa-unit-tests",
            model="haiku",
            started_at=datetime(2026, 2, 7, 10, 16, 0),
            completed_at=datetime(2026, 2, 7, 10, 18, 0),
            status="pass",
            message="All tests passed",
            details={"total": 42, "passed": 42},
        )
        assert qa.status == "pass"
        assert qa.message == "All tests passed"

    def test_invalid_qa_status(self):
        """Test invalid QA status raises error."""
        with pytest.raises(ValidationError) as exc_info:
            QAExecution(
                attempt=1,
                session_id="claude-qa-abc123",
                agent_path=".claude/agents/qa-unit-tests",
                model="haiku",
                started_at=datetime(2026, 2, 7, 10, 16, 0),
                completed_at=datetime(2026, 2, 7, 10, 18, 0),
                status="invalid",  # Invalid
                message="Test",
            )
        assert "status must be one of" in str(exc_info.value)


class TestBeadMetadata:
    """Tests for BeadMetadata model."""

    def get_valid_qa_agent(self):
        """Helper to create valid QA agent."""
        return QAAgent(
            agent_path=".claude/agents/qa-unit-tests",
            model="haiku",
            prompt="Run pytest",
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"enum": ["pass", "fail", "stop"]},
                    "message": {"type": "string"},
                },
            },
        )

    def test_valid_metadata(self):
        """Test valid metadata."""
        metadata = BeadMetadata(
            rig="beads-ralph",
            worktree_path="/path/to/worktree",
            branch="main/1-2-auth",
            source_branch="main",
            phase="1",
            sprint="1.2",
            plan_file="plans/feature.md",
            plan_section="## Phase 1",
            plan_sprint_id="1.2",
            dev_agent_path=".claude/agents/backend-dev",
            dev_model="sonnet",
            dev_prompts=["Implement auth API"],
            qa_agents=[self.get_valid_qa_agent()],
        )
        assert metadata.phase == "1"
        assert metadata.sprint == "1.2"

    def test_invalid_phase_pattern(self):
        """Test invalid phase pattern raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BeadMetadata(
                rig="beads-ralph",
                worktree_path="/path/to/worktree",
                branch="main/1-2-auth",
                source_branch="main",
                phase="1.2",  # Invalid (contains dot)
                sprint="1.2",
                plan_file="plans/feature.md",
                plan_section="## Phase 1",
                plan_sprint_id="1.2",
                dev_agent_path=".claude/agents/backend-dev",
                dev_model="sonnet",
                dev_prompts=["Test"],
                qa_agents=[self.get_valid_qa_agent()],
            )
        assert "phase must match pattern" in str(exc_info.value)

    def test_invalid_sprint_pattern(self):
        """Test invalid sprint pattern raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BeadMetadata(
                rig="beads-ralph",
                worktree_path="/path/to/worktree",
                branch="main/1-2-auth",
                source_branch="main",
                phase="1",
                sprint="1",  # Invalid (missing dot and number)
                plan_file="plans/feature.md",
                plan_section="## Phase 1",
                plan_sprint_id="1.2",
                dev_agent_path=".claude/agents/backend-dev",
                dev_model="sonnet",
                dev_prompts=["Test"],
                qa_agents=[self.get_valid_qa_agent()],
            )
        assert "sprint must match pattern" in str(exc_info.value)

    def test_valid_phase_patterns(self):
        """Test all valid phase patterns."""
        valid_phases = ["1", "2", "3a", "3b", "12", "3ab"]
        for phase in valid_phases:
            metadata = BeadMetadata(
                rig="beads-ralph",
                worktree_path="/path/to/worktree",
                branch="main/branch",
                source_branch="main",
                phase=phase,
                sprint="1.1",
                plan_file="plans/feature.md",
                plan_section="## Phase",
                plan_sprint_id="1.1",
                dev_agent_path=".claude/agents/dev",
                dev_model="sonnet",
                dev_prompts=["Test"],
                qa_agents=[self.get_valid_qa_agent()],
            )
            assert metadata.phase == phase

    def test_valid_sprint_patterns(self):
        """Test all valid sprint patterns."""
        valid_sprints = ["1.1", "3a.2", "3b.2a", "3b.2b", "12.5c"]
        for sprint in valid_sprints:
            metadata = BeadMetadata(
                rig="beads-ralph",
                worktree_path="/path/to/worktree",
                branch="main/branch",
                source_branch="main",
                phase="1",
                sprint=sprint,
                plan_file="plans/feature.md",
                plan_section="## Phase",
                plan_sprint_id=sprint,
                dev_agent_path=".claude/agents/dev",
                dev_model="sonnet",
                dev_prompts=["Test"],
                qa_agents=[self.get_valid_qa_agent()],
            )
            assert metadata.sprint == sprint

    def test_empty_dev_prompts(self):
        """Test empty dev_prompts raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BeadMetadata(
                rig="beads-ralph",
                worktree_path="/path/to/worktree",
                branch="main/branch",
                source_branch="main",
                phase="1",
                sprint="1.1",
                plan_file="plans/feature.md",
                plan_section="## Phase",
                plan_sprint_id="1.1",
                dev_agent_path=".claude/agents/dev",
                dev_model="sonnet",
                dev_prompts=[],  # Empty
                qa_agents=[self.get_valid_qa_agent()],
            )
        assert "dev_prompts must be non-empty array" in str(exc_info.value)

    def test_empty_qa_agents(self):
        """Test empty qa_agents raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BeadMetadata(
                rig="beads-ralph",
                worktree_path="/path/to/worktree",
                branch="main/branch",
                source_branch="main",
                phase="1",
                sprint="1.1",
                plan_file="plans/feature.md",
                plan_section="## Phase",
                plan_sprint_id="1.1",
                dev_agent_path=".claude/agents/dev",
                dev_model="sonnet",
                dev_prompts=["Test"],
                qa_agents=[],  # Empty
            )
        assert "qa_agents must be non-empty array" in str(exc_info.value)


class TestBead:
    """Tests for complete Bead model."""

    def get_valid_metadata(self):
        """Helper to create valid metadata."""
        return BeadMetadata(
            rig="beads-ralph",
            worktree_path="/path/to/worktree",
            branch="main/1-2-auth",
            source_branch="main",
            phase="1",
            sprint="1.2",
            plan_file="plans/feature.md",
            plan_section="## Phase 1",
            plan_sprint_id="1.2",
            dev_agent_path=".claude/agents/backend-dev",
            dev_model="sonnet",
            dev_prompts=["Implement auth API"],
            qa_agents=[
                QAAgent(
                    agent_path=".claude/agents/qa-unit-tests",
                    model="haiku",
                    prompt="Run pytest",
                    output_schema={
                        "type": "object",
                        "properties": {
                            "status": {"enum": ["pass", "fail", "stop"]},
                            "message": {"type": "string"},
                        },
                    },
                )
            ],
        )

    def test_valid_bead(self):
        """Test valid bead."""
        bead = Bead(
            id="bd-a1b2c3",
            title="Implement user authentication",
            description="Create auth endpoints",
            status="open",
            priority=1,
            issue_type="beads-ralph-work",
            assignee="beads-ralph-scrum-master",
            metadata=self.get_valid_metadata(),
            created_at=datetime(2026, 2, 7, 10, 0, 0),
            updated_at=datetime(2026, 2, 7, 10, 0, 0),
        )
        assert bead.id == "bd-a1b2c3"
        assert bead.title == "Implement user authentication"

    def test_empty_title(self):
        """Test empty title raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Bead(
                id="bd-a1b2c3",
                title="   ",  # Empty
                description="Test",
                status="open",
                priority=1,
                issue_type="beads-ralph-work",
                assignee="beads-ralph-scrum-master",
                metadata=self.get_valid_metadata(),
                created_at=datetime(2026, 2, 7, 10, 0, 0),
                updated_at=datetime(2026, 2, 7, 10, 0, 0),
            )
        assert "title must be non-empty" in str(exc_info.value)

    def test_invalid_status(self):
        """Test invalid status raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Bead(
                id="bd-a1b2c3",
                title="Test",
                description="Test",
                status="invalid",  # Invalid
                priority=1,
                issue_type="beads-ralph-work",
                assignee="beads-ralph-scrum-master",
                metadata=self.get_valid_metadata(),
                created_at=datetime(2026, 2, 7, 10, 0, 0),
                updated_at=datetime(2026, 2, 7, 10, 0, 0),
            )
        assert "status must be one of" in str(exc_info.value)

    def test_invalid_priority(self):
        """Test invalid priority raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Bead(
                id="bd-a1b2c3",
                title="Test",
                description="Test",
                status="open",
                priority=5,  # Invalid (out of range)
                issue_type="beads-ralph-work",
                assignee="beads-ralph-scrum-master",
                metadata=self.get_valid_metadata(),
                created_at=datetime(2026, 2, 7, 10, 0, 0),
                updated_at=datetime(2026, 2, 7, 10, 0, 0),
            )
        assert "priority must be between 0 and 4" in str(exc_info.value)

    def test_invalid_issue_type(self):
        """Test invalid issue_type raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Bead(
                id="bd-a1b2c3",
                title="Test",
                description="Test",
                status="open",
                priority=1,
                issue_type="invalid",  # Invalid
                assignee="beads-ralph-scrum-master",
                metadata=self.get_valid_metadata(),
                created_at=datetime(2026, 2, 7, 10, 0, 0),
                updated_at=datetime(2026, 2, 7, 10, 0, 0),
            )
        assert "issue_type must be one of" in str(exc_info.value)

    def test_invalid_assignee(self):
        """Test invalid assignee raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Bead(
                id="bd-a1b2c3",
                title="Test",
                description="Test",
                status="open",
                priority=1,
                issue_type="beads-ralph-work",
                assignee="wrong-assignee",  # Invalid
                metadata=self.get_valid_metadata(),
                created_at=datetime(2026, 2, 7, 10, 0, 0),
                updated_at=datetime(2026, 2, 7, 10, 0, 0),
            )
        assert "assignee must be 'beads-ralph-scrum-master'" in str(exc_info.value)


class TestScrumResult:
    """Tests for ScrumResult model."""

    def test_valid_scrum_result(self):
        """Test valid scrum result."""
        result = ScrumResult(
            bead_id="bd-a1b2c3",
            success=True,
            pr_url="https://github.com/user/repo/pull/42",
            pr_number=42,
            bead_updated=True,
            attempt_count=1,
            qa_results=[
                QAResult(
                    agent_path=".claude/agents/qa-unit-tests",
                    status="pass",
                    message="Tests passed",
                )
            ],
            fatal=False,
        )
        assert result.success is True
        assert result.pr_number == 42

    def test_invalid_attempt_count(self):
        """Test invalid attempt_count raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ScrumResult(
                bead_id="bd-a1b2c3",
                success=True,
                bead_updated=True,
                attempt_count=-1,  # Invalid
                fatal=False,
            )
        assert "attempt_count must be >= 0" in str(exc_info.value)

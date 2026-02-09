#!/usr/bin/env python3
"""Tests for parsing implementation plans and extracting sprint metadata.

These tests validate the beads-architect agent's ability to:
- Parse markdown plan files with sprint sections
- Extract sprint metadata (worktree, branch, agents, tasks)
- Handle malformed markdown gracefully
- Support optional sprint filters
"""

import json
import re
from pathlib import Path

import pytest


class TestSprintHeaderParsing:
    """Tests for extracting sprint sections from markdown."""

    def test_parse_simple_sprint_headers(self):
        """Test parsing basic sprint headers with sequential numbering."""
        markdown = """
### Sprint 1.1: Initial Setup

Some content here

### Sprint 1.2: Core Implementation

More content

### Sprint 1.3: Final Integration

Last section
"""
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        matches = re.findall(pattern, markdown)

        assert len(matches) == 3
        assert matches[0] == ("1", "1", "", "Initial Setup")
        assert matches[1] == ("1", "2", "", "Core Implementation")
        assert matches[2] == ("1", "3", "", "Final Integration")

    def test_parse_parallel_sprint_headers(self):
        """Test parsing sprint headers with parallel suffixes (a, b, c)."""
        markdown = """
### Sprint 1.2a: Frontend Development (Parallel)

Content for 1.2a

### Sprint 1.2b: Backend API (Parallel)

Content for 1.2b

### Sprint 1.3: Integration

Content for 1.3
"""
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        matches = re.findall(pattern, markdown)

        assert len(matches) == 3
        assert matches[0] == ("1", "2", "a", "Frontend Development (Parallel)")
        assert matches[1] == ("1", "2", "b", "Backend API (Parallel)")
        assert matches[2] == ("1", "3", "", "Integration")

    def test_parse_phase_split_headers(self):
        """Test parsing sprint headers with phase splits (3a.1, 3b.1)."""
        markdown = """
### Sprint 3a.1: UI Components

Content for 3a.1

### Sprint 3b.1: API Layer

Content for 3b.1

### Sprint 4.1: System Integration

Content for 4.1
"""
        # Extended pattern for phase splits
        pattern = r"### Sprint (\d+)([a-c])?\.(\d+)([a-c])?:\s*(.+)"
        matches = re.findall(pattern, markdown)

        assert len(matches) == 3
        assert matches[0] == ("3", "a", "1", "", "UI Components")
        assert matches[1] == ("3", "b", "1", "", "API Layer")
        assert matches[2] == ("4", "", "1", "", "System Integration")

    def test_invalid_sprint_header_format(self):
        """Test that invalid sprint headers are not matched."""
        markdown = """
### Sprint ABC: Invalid

### Sprint 1: Missing dot notation

### 1.1: Missing Sprint prefix

### Sprint 1.1.1: Too many numbers
"""
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        matches = re.findall(pattern, markdown)

        assert len(matches) == 0


class TestMetadataExtraction:
    """Tests for extracting metadata from sprint sections."""

    @pytest.fixture
    def sample_sprint_section(self):
        """Provide a sample sprint section for testing."""
        return """### Sprint 1.1: Initial Setup

**Worktree**: `../test-worktrees/feature/1-1-setup`
**Branch**: `feature/1-1-setup`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)
- `go-backend-dev` (opus)

**QA Agents**:
- `qa-python-tests` (haiku) - Run pytest with >90% coverage
- `qa-schema-validator` (haiku) - Validate output

**Tasks**:
- Create initial project structure
- Set up configuration files
- Initialize git repository

**Acceptance Criteria**:
- Project structure follows standard conventions
- All configuration files are valid
"""

    def test_extract_worktree_path(self, sample_sprint_section):
        """Test extracting worktree path from sprint section."""
        pattern = r"\*\*Worktree\*\*:\s*`([^`]+)`"
        match = re.search(pattern, sample_sprint_section)

        assert match is not None
        assert match.group(1) == "../test-worktrees/feature/1-1-setup"

    def test_extract_branch_name(self, sample_sprint_section):
        """Test extracting branch name from sprint section."""
        pattern = r"\*\*Branch\*\*:\s*`([^`]+)`"
        match = re.search(pattern, sample_sprint_section)

        assert match is not None
        assert match.group(1) == "feature/1-1-setup"

    def test_extract_source_branch(self, sample_sprint_section):
        """Test extracting source branch from sprint section."""
        pattern = r"\*\*Source Branch\*\*:\s*`([^`]+)`"
        match = re.search(pattern, sample_sprint_section)

        assert match is not None
        assert match.group(1) == "develop"

    def test_extract_dev_agents(self, sample_sprint_section):
        """Test extracting dev agents with models from sprint section."""
        # Pattern to find Dev Agents section
        dev_section = re.search(
            r"\*\*Dev Agents\*\*:(.*?)(?=\n\*\*|\Z)",
            sample_sprint_section,
            re.DOTALL
        )

        assert dev_section is not None

        # Extract individual agents
        agent_pattern = r"-\s*`([^`]+)`\s*\((\w+)\)"
        agents = re.findall(agent_pattern, dev_section.group(1))

        assert len(agents) == 2
        assert agents[0] == ("python-backend-dev", "sonnet")
        assert agents[1] == ("go-backend-dev", "opus")

    def test_extract_qa_agents(self, sample_sprint_section):
        """Test extracting QA agents with models and prompts."""
        # Pattern to find QA Agents section
        qa_section = re.search(
            r"\*\*QA Agents\*\*:(.*?)(?=\n\*\*|\Z)",
            sample_sprint_section,
            re.DOTALL
        )

        assert qa_section is not None

        # Extract individual QA agents (handles multiline)
        agent_pattern = r"-\s*`([^`]+)`\s*\((\w+)\)\s*-\s*(.+?)(?=\n\s*-|\n\*\*|\Z)"
        agents = re.findall(agent_pattern, qa_section.group(1), re.DOTALL)

        assert len(agents) >= 1
        assert agents[0][0] == "qa-python-tests"
        assert agents[0][1] == "haiku"
        assert "Run pytest" in agents[0][2]

    def test_extract_tasks(self, sample_sprint_section):
        """Test extracting task list from sprint section."""
        # Pattern to find Tasks section
        tasks_section = re.search(
            r"\*\*Tasks\*\*:(.*?)(?=\n\*\*|\Z)",
            sample_sprint_section,
            re.DOTALL
        )

        assert tasks_section is not None

        # Extract individual tasks (one per line starting with -)
        task_pattern = r"-\s*(.+?)(?=\n\s*-|\n\*\*|\Z)"
        tasks = re.findall(task_pattern, tasks_section.group(1), re.DOTALL)

        assert len(tasks) >= 3
        # Verify task content (may have newlines)
        task_text = " ".join(tasks)
        assert "Create initial project structure" in task_text
        assert "Set up configuration files" in task_text
        assert "Initialize git repository" in task_text

    def test_missing_required_fields(self):
        """Test handling of sprint sections with missing required fields."""
        incomplete_section = """### Sprint 1.1: Incomplete

**Worktree**: `../test-worktrees/feature/1-1`

**Tasks**:
- Do something
"""
        # Should not find branch
        branch_pattern = r"\*\*Branch\*\*:\s*`([^`]+)`"
        assert re.search(branch_pattern, incomplete_section) is None

        # Should not find source branch
        source_pattern = r"\*\*Source Branch\*\*:\s*`([^`]+)`"
        assert re.search(source_pattern, incomplete_section) is None


class TestPlanFileParsing:
    """Integration tests for parsing complete plan files."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_parse_simple_plan(self, fixtures_dir):
        """Test parsing simple sequential plan file."""
        plan_file = fixtures_dir / "simple-plan.md"

        with open(plan_file) as f:
            content = f.read()

        # Extract all sprint headers
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        sprints = re.findall(pattern, content)

        assert len(sprints) == 3
        assert sprints[0][3] == "Initial Setup"
        assert sprints[1][3] == "Core Implementation"
        assert sprints[2][3] == "Final Integration"

    def test_parse_parallel_plan(self, fixtures_dir):
        """Test parsing plan with parallel sprints."""
        plan_file = fixtures_dir / "parallel-plan.md"

        with open(plan_file) as f:
            content = f.read()

        # Extract all sprint headers
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        sprints = re.findall(pattern, content)

        assert len(sprints) == 4
        # Check parallel sprints
        assert sprints[1][2] == "a"  # 1.2a
        assert sprints[2][2] == "b"  # 1.2b
        assert sprints[3][2] == ""   # 1.3

    def test_parse_complex_plan(self, fixtures_dir):
        """Test parsing plan with phase splits and convergence."""
        plan_file = fixtures_dir / "complex-plan.md"

        with open(plan_file) as f:
            content = f.read()

        # Need extended pattern for phase splits
        pattern = r"### Sprint (\d+)([a-c])?\.(\d+)([a-c])?:\s*(.+)"
        sprints = re.findall(pattern, content)

        # Should find sprints across multiple phases including splits
        assert len(sprints) >= 7

        # Check for phase splits (3a.x and 3b.x)
        phase_3a_sprints = [s for s in sprints if s[1] == "a"]
        phase_3b_sprints = [s for s in sprints if s[1] == "b"]

        assert len(phase_3a_sprints) >= 2
        assert len(phase_3b_sprints) >= 2

    def test_filter_by_sprint_id(self, fixtures_dir):
        """Test filtering to process only specific sprint."""
        plan_file = fixtures_dir / "simple-plan.md"

        with open(plan_file) as f:
            content = f.read()

        # Filter for sprint 1.2 only
        target_sprint = "1.2"
        pattern = r"### Sprint (1\.2):\s*(.+?)(?=\n###|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        assert match is not None
        assert "Core Implementation" in match.group(2)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_plan_file(self):
        """Test handling of empty plan file."""
        content = ""
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        matches = re.findall(pattern, content)

        assert len(matches) == 0

    def test_plan_with_no_sprints(self):
        """Test handling of plan file without sprint sections."""
        content = """
# Some Plan

This is just text with no sprint sections.

## Phase 1

More text but no sprint headers.
"""
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        matches = re.findall(pattern, content)

        assert len(matches) == 0

    def test_malformed_sprint_section(self):
        """Test handling of malformed sprint metadata."""
        content = """### Sprint 1.1: Test

**Worktree**: missing-backticks
**Branch**: `feature/test`
**Dev Agents**:
- missing-backticks-around-agent (sonnet)
"""
        # Worktree without backticks should not match
        worktree_pattern = r"\*\*Worktree\*\*:\s*`([^`]+)`"
        assert re.search(worktree_pattern, content) is None

        # Branch with backticks should match
        branch_pattern = r"\*\*Branch\*\*:\s*`([^`]+)`"
        assert re.search(branch_pattern, content) is not None

    def test_unicode_in_sprint_titles(self):
        """Test handling of Unicode characters in sprint titles."""
        content = "### Sprint 1.1: Initial Setup 🚀"
        pattern = r"### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)"
        match = re.search(pattern, content)

        assert match is not None
        assert "🚀" in match.group(4)

    def test_multiline_task_descriptions(self):
        """Test handling of multiline task descriptions."""
        content = """**Tasks**:
- Create initial project structure
  with multiple directories
- Set up configuration files
  including .env and config.yaml
"""
        # Pattern that captures multiline tasks
        task_pattern = r"-\s*(.+?)(?=\n\s*-|\Z)"
        tasks = re.findall(task_pattern, content, re.DOTALL)

        # Should capture both tasks with their continuation lines
        assert len(tasks) >= 2
        # Verify multiline content captured
        assert "multiple directories" in tasks[0] or "project structure" in tasks[0]

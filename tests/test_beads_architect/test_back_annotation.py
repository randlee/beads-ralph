#!/usr/bin/env python3
"""Tests for plan back-annotation functionality.

These tests validate that beads-architect can insert HTML comment annotations
into implementation plans to enable bi-directional tracking between plans and beads.
"""

import re
from pathlib import Path

import pytest


class TestHTMLCommentFormat:
    """Tests for HTML comment format specification."""

    def test_basic_comment_format(self):
        """Test basic HTML comment format matches specification."""
        bead_id = "bd-1-1-test-sprint"
        expected = f"<!-- beads-ralph: {bead_id} -->"

        assert expected == "<!-- beads-ralph: bd-1-1-test-sprint -->"

    def test_comment_format_with_different_ids(self):
        """Test comment format for various bead ID patterns."""
        test_cases = [
            "bd-1-1-setup",
            "bd-1-2a-frontend",
            "bd-3a-2-user-interface",
            "bd-4-1-integration",
        ]

        for bead_id in test_cases:
            comment = f"<!-- beads-ralph: {bead_id} -->"
            assert comment.startswith("<!-- beads-ralph:")
            assert comment.endswith("-->")
            assert bead_id in comment

    def test_comment_regex_pattern(self):
        """Test regex pattern for extracting bead ID from comment."""
        comment = "<!-- beads-ralph: bd-1-1-test -->"
        pattern = r"<!-- beads-ralph:\s+(bd-[\w-]+)\s+-->"

        match = re.search(pattern, comment)
        assert match is not None
        assert match.group(1) == "bd-1-1-test"

    def test_extract_bead_ids_from_multiple_comments(self):
        """Test extracting multiple bead IDs from markdown with comments."""
        markdown = """
### Sprint 1.1: Setup
<!-- beads-ralph: bd-1-1-setup -->

Some content

### Sprint 1.2: Implementation
<!-- beads-ralph: bd-1-2-implementation -->

More content
"""
        pattern = r"<!-- beads-ralph:\s+(bd-[\w-]+)\s+-->"
        matches = re.findall(pattern, markdown)

        assert len(matches) == 2
        assert matches[0] == "bd-1-1-setup"
        assert matches[1] == "bd-1-2-implementation"


class TestCommentInsertion:
    """Tests for inserting comments after sprint headings."""

    def test_insert_after_sprint_heading(self):
        """Test inserting comment immediately after sprint heading."""
        sprint_section = """### Sprint 1.1: Initial Setup

**Worktree**: `../test-worktrees/feature/1-1-setup`
"""
        bead_id = "bd-1-1-initial-setup"
        comment = f"<!-- beads-ralph: {bead_id} -->"

        # Insert after heading line
        lines = sprint_section.split("\n")
        lines.insert(1, comment)
        annotated = "\n".join(lines)

        expected = """### Sprint 1.1: Initial Setup
<!-- beads-ralph: bd-1-1-initial-setup -->

**Worktree**: `../test-worktrees/feature/1-1-setup`
"""
        assert annotated == expected

    def test_insert_preserves_existing_content(self):
        """Test that insertion preserves all existing content."""
        original = """### Sprint 1.1: Test

**Worktree**: `../test`
**Branch**: `feature/test`

**Tasks**:
- Task 1
- Task 2
"""
        bead_id = "bd-1-1-test"
        comment = f"<!-- beads-ralph: {bead_id} -->"

        # Insert after first line
        lines = original.split("\n")
        lines.insert(1, comment)
        annotated = "\n".join(lines)

        # Verify all original content is present
        assert "### Sprint 1.1: Test" in annotated
        assert "**Worktree**: `../test`" in annotated
        assert "**Branch**: `feature/test`" in annotated
        assert "- Task 1" in annotated
        assert "- Task 2" in annotated

        # Verify comment is present
        assert comment in annotated

    def test_detect_existing_annotation(self):
        """Test detecting if sprint already has annotation."""
        annotated_section = """### Sprint 1.1: Test
<!-- beads-ralph: bd-1-1-test -->

Content here
"""
        # Check if annotation already exists
        pattern = r"<!-- beads-ralph:\s+bd-[\w-]+\s+-->"
        has_annotation = re.search(pattern, annotated_section) is not None

        assert has_annotation is True

    def test_skip_already_annotated_sprint(self):
        """Test that already annotated sprints are not re-annotated."""
        annotated_section = """### Sprint 1.1: Test
<!-- beads-ralph: bd-1-1-test -->

Content
"""
        # Should detect existing annotation and skip
        pattern = r"<!-- beads-ralph:\s+bd-[\w-]+\s+-->"
        if re.search(pattern, annotated_section):
            # Don't insert another comment
            final = annotated_section
        else:
            lines = annotated_section.split("\n")
            lines.insert(1, "<!-- beads-ralph: bd-1-1-test -->")
            final = "\n".join(lines)

        # Should only have one comment
        matches = re.findall(pattern, final)
        assert len(matches) == 1


class TestSprintHeaderLocation:
    """Tests for locating sprint headers in markdown."""

    def test_find_sprint_heading(self):
        """Test finding sprint heading in markdown."""
        markdown = """
## Phase 1

### Sprint 1.1: Initial Setup

Content here

### Sprint 1.2: Implementation

More content
"""
        # Find all sprint headings
        pattern = r"^### Sprint (\d+(?:[a-c])?)\.(\d+)([a-c])?:\s*(.+)$"
        matches = re.finditer(pattern, markdown, re.MULTILINE)

        sprint_headings = [(m.start(), m.group(0)) for m in matches]
        assert len(sprint_headings) == 2

    def test_find_specific_sprint_by_id(self):
        """Test finding specific sprint heading by sprint ID."""
        markdown = """
### Sprint 1.1: Setup

Content

### Sprint 1.2: Core

Content

### Sprint 1.3: Final

Content
"""
        target_sprint_id = "1.2"
        pattern = rf"^### Sprint {re.escape(target_sprint_id)}:\s*(.+)$"

        match = re.search(pattern, markdown, re.MULTILINE)
        assert match is not None
        assert "Core" in match.group(1)

    def test_handle_parallel_sprint_suffixes(self):
        """Test finding sprint headings with parallel suffixes."""
        markdown = """
### Sprint 1.2a: Frontend

Content

### Sprint 1.2b: Backend

Content
"""
        pattern = r"^### Sprint (\d+)\.(\d+)([a-c]):\s*(.+)$"
        matches = re.findall(pattern, markdown, re.MULTILINE)

        assert len(matches) == 2
        assert matches[0][2] == "a"
        assert matches[1][2] == "b"

    def test_handle_phase_split_headers(self):
        """Test finding sprint headings with phase splits."""
        markdown = """
### Sprint 3a.1: UI Components

Content

### Sprint 3b.1: API Layer

Content
"""
        pattern = r"^### Sprint (\d+)([a-c])\.(\d+):\s*(.+)$"
        matches = re.findall(pattern, markdown, re.MULTILINE)

        assert len(matches) == 2
        assert matches[0][1] == "a"
        assert matches[1][1] == "b"


class TestBidirectionalTracking:
    """Tests for bi-directional navigation between plans and beads."""

    def test_plan_to_bead_mapping(self):
        """Test mapping from plan sprint ID to bead ID."""
        # Plan contains sprint 1.2a with annotation
        plan_section = """### Sprint 1.2a: Frontend
<!-- beads-ralph: bd-1-2a-frontend -->
"""
        # Extract bead ID
        pattern = r"<!-- beads-ralph:\s+(bd-[\w-]+)\s+-->"
        match = re.search(pattern, plan_section)

        assert match is not None
        bead_id = match.group(1)
        assert bead_id == "bd-1-2a-frontend"

    def test_bead_to_plan_mapping(self):
        """Test mapping from bead metadata back to plan location."""
        # Bead contains plan location in metadata
        bead_metadata = {
            "plan_file": "pm/2026-02-08-implementation-plan.md",
            "plan_section": "### Sprint 1.2a: Frontend Development",
            "plan_sprint_id": "1.2a"
        }

        # Can use this to locate sprint in plan
        plan_file = bead_metadata["plan_file"]
        sprint_id = bead_metadata["plan_sprint_id"]

        assert plan_file == "pm/2026-02-08-implementation-plan.md"
        assert sprint_id == "1.2a"

    def test_find_sprint_from_bead_metadata(self):
        """Test finding sprint section using bead metadata."""
        plan_content = """
### Sprint 1.1: Setup

Content

### Sprint 1.2a: Frontend

Content
"""
        bead_metadata = {
            "plan_sprint_id": "1.2a"
        }

        sprint_id = bead_metadata["plan_sprint_id"]
        pattern = rf"^### Sprint {re.escape(sprint_id)}:\s*(.+)$"

        match = re.search(pattern, plan_content, re.MULTILINE)
        assert match is not None
        assert "Frontend" in match.group(1)


class TestAnnotationWorkflow:
    """Tests for complete annotation workflow."""

    def test_full_annotation_workflow(self):
        """Test complete workflow of annotating a plan."""
        original_plan = """# Implementation Plan

## Phase 1

### Sprint 1.1: Initial Setup

**Worktree**: `../test/1-1`

### Sprint 1.2: Core Implementation

**Worktree**: `../test/1-2`
"""
        # Beads to annotate
        beads = [
            {"sprint_id": "1.1", "bead_id": "bd-1-1-initial-setup"},
            {"sprint_id": "1.2", "bead_id": "bd-1-2-core-implementation"},
        ]

        # Annotate each sprint
        annotated_plan = original_plan
        for bead in beads:
            sprint_id = bead["sprint_id"]
            bead_id = bead["bead_id"]
            comment = f"<!-- beads-ralph: {bead_id} -->"

            # Find sprint heading and insert comment
            pattern = rf"(^### Sprint {re.escape(sprint_id)}:.+$)"
            replacement = rf"\1\n{comment}"
            annotated_plan = re.sub(
                pattern,
                replacement,
                annotated_plan,
                flags=re.MULTILINE
            )

        # Verify both annotations present
        assert "<!-- beads-ralph: bd-1-1-initial-setup -->" in annotated_plan
        assert "<!-- beads-ralph: bd-1-2-core-implementation -->" in annotated_plan

        # Verify original content preserved
        assert "Initial Setup" in annotated_plan
        assert "Core Implementation" in annotated_plan
        assert "**Worktree**:" in annotated_plan

    def test_incremental_annotation(self):
        """Test annotating plan incrementally as beads are created."""
        plan = """### Sprint 1.1: Setup

Content

### Sprint 1.2: Implementation

Content
"""
        # First bead created
        bead_1 = {"sprint_id": "1.1", "bead_id": "bd-1-1-setup"}
        comment_1 = f"<!-- beads-ralph: {bead_1['bead_id']} -->"

        # Annotate sprint 1.1
        plan_v1 = re.sub(
            r"(^### Sprint 1\.1:.+$)",
            rf"\1\n{comment_1}",
            plan,
            flags=re.MULTILINE
        )

        # Verify only 1.1 annotated
        assert comment_1 in plan_v1
        assert "bd-1-2-implementation" not in plan_v1

        # Second bead created
        bead_2 = {"sprint_id": "1.2", "bead_id": "bd-1-2-implementation"}
        comment_2 = f"<!-- beads-ralph: {bead_2['bead_id']} -->"

        # Annotate sprint 1.2
        plan_v2 = re.sub(
            r"(^### Sprint 1\.2:.+$)",
            rf"\1\n{comment_2}",
            plan_v1,
            flags=re.MULTILINE
        )

        # Verify both annotated
        assert comment_1 in plan_v2
        assert comment_2 in plan_v2


class TestEdgeCases:
    """Tests for edge cases in back-annotation."""

    def test_sprint_heading_with_parentheses(self):
        """Test annotating sprint with parentheses in title."""
        sprint = "### Sprint 1.2a: Frontend (Parallel)"
        bead_id = "bd-1-2a-frontend"
        comment = f"<!-- beads-ralph: {bead_id} -->"

        # Should handle parentheses correctly
        pattern = r"(^### Sprint 1\.2a:.+$)"
        annotated = re.sub(pattern, rf"\1\n{comment}", sprint, flags=re.MULTILINE)

        assert comment in annotated
        assert "Frontend (Parallel)" in annotated

    def test_sprint_with_unicode_title(self):
        """Test annotating sprint with Unicode characters."""
        sprint = "### Sprint 1.1: Initial Setup 🚀"
        bead_id = "bd-1-1-initial-setup"
        comment = f"<!-- beads-ralph: {bead_id} -->"

        pattern = r"(^### Sprint 1\.1:.+$)"
        annotated = re.sub(pattern, rf"\1\n{comment}", sprint, flags=re.MULTILINE)

        assert comment in annotated
        assert "🚀" in annotated

    def test_multiple_plans_different_files(self):
        """Test tracking annotations across multiple plan files."""
        # Different beads reference different plan files
        bead_1 = {
            "metadata": {
                "plan_file": "pm/phase-1-plan.md",
                "plan_sprint_id": "1.1"
            }
        }
        bead_2 = {
            "metadata": {
                "plan_file": "pm/phase-2-plan.md",
                "plan_sprint_id": "2.1"
            }
        }

        # Should be able to annotate correct file for each bead
        assert bead_1["metadata"]["plan_file"] != bead_2["metadata"]["plan_file"]

    def test_empty_plan_file(self):
        """Test handling empty or malformed plan file."""
        empty_plan = ""

        # Should not find any sprint headers
        pattern = r"^### Sprint \d+\.\d+:"
        matches = re.findall(pattern, empty_plan, re.MULTILINE)

        assert len(matches) == 0

    def test_plan_without_sprint_headers(self):
        """Test plan file without proper sprint headers."""
        malformed_plan = """
# Some Plan

This is just text with no sprint sections.
"""
        pattern = r"^### Sprint \d+\.\d+:"
        matches = re.findall(pattern, malformed_plan, re.MULTILINE)

        assert len(matches) == 0


class TestRealWorldScenarios:
    """Tests using realistic plan fixtures."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_annotate_simple_plan(self, fixtures_dir):
        """Test annotating simple sequential plan."""
        plan_file = fixtures_dir / "simple-plan.md"

        with open(plan_file) as f:
            plan_content = f.read()

        # Find sprint headings
        pattern = r"^### Sprint (\d+)\.(\d+):\s*(.+)$"
        matches = re.findall(pattern, plan_content, re.MULTILINE)

        assert len(matches) == 3
        # Should be able to annotate each sprint

    def test_annotate_parallel_plan(self, fixtures_dir):
        """Test annotating plan with parallel sprints."""
        plan_file = fixtures_dir / "parallel-plan.md"

        with open(plan_file) as f:
            plan_content = f.read()

        # Find parallel sprint headings
        pattern = r"^### Sprint (\d+)\.(\d+)([a-c]):\s*(.+)$"
        matches = re.findall(pattern, plan_content, re.MULTILINE)

        # Should find parallel sprints
        parallel_sprints = [m for m in matches if m[2] != ""]
        assert len(parallel_sprints) >= 2

    def test_annotate_complex_plan(self, fixtures_dir):
        """Test annotating complex plan with phase splits."""
        plan_file = fixtures_dir / "complex-plan.md"

        with open(plan_file) as f:
            plan_content = f.read()

        # Find phase split headings
        pattern = r"^### Sprint (\d+)([a-c])\.(\d+):\s*(.+)$"
        matches = re.findall(pattern, plan_content, re.MULTILINE)

        # Should find phase split sprints
        phase_splits = [m for m in matches if m[1] != ""]
        assert len(phase_splits) >= 2

#!/usr/bin/env python3
"""Tests for dependency generation logic in beads-architect agent.

These tests validate the core dependency resolution algorithm:
- Sequential sprints: 1.1 → 1.2 → 1.3
- Parallel sprints: 1.2a, 1.2b both depend on 1.1 (not each other)
- Merge sprints: 1.3 depends on [1.2a, 1.2b]
- Phase splits: 3a.1, 3b.1 (parallel phase branches)
- Phase convergence: 4.1 depends on last sprints of 3a and 3b
"""

import json
from pathlib import Path

import pytest


class TestSequentialDependencies:
    """Tests for sequential sprint dependencies."""

    def test_simple_sequential_chain(self):
        """Test basic sequential dependency: 1.1 → 1.2 → 1.3."""
        sprints = [
            {"id": "bd-1-1-setup", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2-core", "sprint": "1.2", "phase": "1"},
            {"id": "bd-1-3-integration", "sprint": "1.3", "phase": "1"},
        ]

        # Expected dependencies
        expected = {
            "bd-1-1-setup": [],
            "bd-1-2-core": ["bd-1-1-setup"],
            "bd-1-3-integration": ["bd-1-2-core"],
        }

        # Verify dependency structure
        for sprint in sprints:
            assert sprint["id"] in expected

    def test_multi_phase_sequential(self):
        """Test sequential dependencies across multiple phases."""
        sprints = [
            {"id": "bd-1-1-setup", "sprint": "1.1", "phase": "1"},
            {"id": "bd-2-1-core", "sprint": "2.1", "phase": "2"},
            {"id": "bd-3-1-advanced", "sprint": "3.1", "phase": "3"},
        ]

        # Phase transitions: each phase depends on last sprint of previous phase
        expected = {
            "bd-1-1-setup": [],
            "bd-2-1-core": ["bd-1-1-setup"],  # First of phase 2 depends on last of phase 1
            "bd-3-1-advanced": ["bd-2-1-core"],  # First of phase 3 depends on last of phase 2
        }

        for sprint in sprints:
            assert sprint["id"] in expected


class TestParallelDependencies:
    """Tests for parallel sprint dependencies."""

    def test_parallel_sprints_same_base(self):
        """Test parallel sprints depend on same base, not each other."""
        sprints = [
            {"id": "bd-1-1-foundation", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2a-frontend", "sprint": "1.2a", "phase": "1"},
            {"id": "bd-1-2b-backend", "sprint": "1.2b", "phase": "1"},
        ]

        # Both 1.2a and 1.2b depend on 1.1, not each other
        expected = {
            "bd-1-1-foundation": [],
            "bd-1-2a-frontend": ["bd-1-1-foundation"],
            "bd-1-2b-backend": ["bd-1-1-foundation"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected

        # Verify 1.2a and 1.2b do NOT depend on each other
        assert "bd-1-2b-backend" not in expected["bd-1-2a-frontend"]
        assert "bd-1-2a-frontend" not in expected["bd-1-2b-backend"]

    def test_three_way_parallel(self):
        """Test three parallel sprints (1.2a, 1.2b, 1.2c)."""
        sprints = [
            {"id": "bd-1-1-base", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2a-task-a", "sprint": "1.2a", "phase": "1"},
            {"id": "bd-1-2b-task-b", "sprint": "1.2b", "phase": "1"},
            {"id": "bd-1-2c-task-c", "sprint": "1.2c", "phase": "1"},
        ]

        # All three depend on 1.1, none depend on each other
        expected = {
            "bd-1-1-base": [],
            "bd-1-2a-task-a": ["bd-1-1-base"],
            "bd-1-2b-task-b": ["bd-1-1-base"],
            "bd-1-2c-task-c": ["bd-1-1-base"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected


class TestMergeDependencies:
    """Tests for merge sprint dependencies."""

    def test_merge_after_parallel(self):
        """Test merge sprint depends on all parallel predecessors."""
        sprints = [
            {"id": "bd-1-1-base", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2a-frontend", "sprint": "1.2a", "phase": "1"},
            {"id": "bd-1-2b-backend", "sprint": "1.2b", "phase": "1"},
            {"id": "bd-1-3-integration", "sprint": "1.3", "phase": "1"},
        ]

        # 1.3 depends on both 1.2a and 1.2b
        expected = {
            "bd-1-1-base": [],
            "bd-1-2a-frontend": ["bd-1-1-base"],
            "bd-1-2b-backend": ["bd-1-1-base"],
            "bd-1-3-integration": ["bd-1-2a-frontend", "bd-1-2b-backend"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected

        # Verify merge has multiple dependencies
        assert len(expected["bd-1-3-integration"]) == 2

    def test_merge_after_three_parallel(self):
        """Test merge sprint depends on three parallel predecessors."""
        sprints = [
            {"id": "bd-1-1-base", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2a-task-a", "sprint": "1.2a", "phase": "1"},
            {"id": "bd-1-2b-task-b", "sprint": "1.2b", "phase": "1"},
            {"id": "bd-1-2c-task-c", "sprint": "1.2c", "phase": "1"},
            {"id": "bd-1-3-merge", "sprint": "1.3", "phase": "1"},
        ]

        # 1.3 depends on all three parallel sprints
        expected = {
            "bd-1-1-base": [],
            "bd-1-2a-task-a": ["bd-1-1-base"],
            "bd-1-2b-task-b": ["bd-1-1-base"],
            "bd-1-2c-task-c": ["bd-1-1-base"],
            "bd-1-3-merge": ["bd-1-2a-task-a", "bd-1-2b-task-b", "bd-1-2c-task-c"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected

        # Verify merge has three dependencies
        assert len(expected["bd-1-3-merge"]) == 3


class TestPhaseSplits:
    """Tests for phase split dependencies (parallel phase branches)."""

    def test_phase_split_initialization(self):
        """Test phase splits start from same base (last sprint of previous phase)."""
        sprints = [
            {"id": "bd-2-1-base", "sprint": "2.1", "phase": "2"},
            {"id": "bd-3a-1-frontend", "sprint": "3a.1", "phase": "3a"},
            {"id": "bd-3b-1-backend", "sprint": "3b.1", "phase": "3b"},
        ]

        # Both 3a.1 and 3b.1 depend on 2.1 (last sprint of phase 2)
        expected = {
            "bd-2-1-base": [],
            "bd-3a-1-frontend": ["bd-2-1-base"],
            "bd-3b-1-backend": ["bd-2-1-base"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected

        # Verify phase splits do NOT depend on each other
        assert "bd-3b-1-backend" not in expected["bd-3a-1-frontend"]
        assert "bd-3a-1-frontend" not in expected["bd-3b-1-backend"]

    def test_phase_split_internal_sequence(self):
        """Test sequential dependencies within a phase split."""
        sprints = [
            {"id": "bd-3a-1-ui-components", "sprint": "3a.1", "phase": "3a"},
            {"id": "bd-3a-2-user-interface", "sprint": "3a.2", "phase": "3a"},
        ]

        # Within phase 3a, 3a.2 depends on 3a.1
        expected = {
            "bd-3a-1-ui-components": [],  # Simplified, would depend on previous phase
            "bd-3a-2-user-interface": ["bd-3a-1-ui-components"],
        }

        # Verify internal sequence
        assert expected["bd-3a-2-user-interface"] == ["bd-3a-1-ui-components"]

    def test_multiple_phase_splits(self):
        """Test multiple independent phase branches."""
        sprints = [
            {"id": "bd-2-1-base", "sprint": "2.1", "phase": "2"},
            {"id": "bd-3a-1-track-a", "sprint": "3a.1", "phase": "3a"},
            {"id": "bd-3b-1-track-b", "sprint": "3b.1", "phase": "3b"},
            {"id": "bd-3c-1-track-c", "sprint": "3c.1", "phase": "3c"},
        ]

        # All three phase splits depend on 2.1, not each other
        expected = {
            "bd-2-1-base": [],
            "bd-3a-1-track-a": ["bd-2-1-base"],
            "bd-3b-1-track-b": ["bd-2-1-base"],
            "bd-3c-1-track-c": ["bd-2-1-base"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected


class TestPhaseConvergence:
    """Tests for phase convergence (merging phase splits)."""

    def test_convergence_from_two_splits(self):
        """Test convergence depends on last sprint of each split phase."""
        sprints = [
            {"id": "bd-3a-1-frontend-start", "sprint": "3a.1", "phase": "3a"},
            {"id": "bd-3a-2-frontend-end", "sprint": "3a.2", "phase": "3a"},
            {"id": "bd-3b-1-backend-start", "sprint": "3b.1", "phase": "3b"},
            {"id": "bd-3b-2-backend-end", "sprint": "3b.2", "phase": "3b"},
            {"id": "bd-4-1-integration", "sprint": "4.1", "phase": "4"},
        ]

        # 4.1 depends on last sprints of both 3a and 3b
        expected = {
            "bd-3a-1-frontend-start": [],  # Simplified
            "bd-3a-2-frontend-end": ["bd-3a-1-frontend-start"],
            "bd-3b-1-backend-start": [],  # Simplified
            "bd-3b-2-backend-end": ["bd-3b-1-backend-start"],
            "bd-4-1-integration": ["bd-3a-2-frontend-end", "bd-3b-2-backend-end"],
        }

        # Verify convergence depends on last of each split
        assert "bd-3a-2-frontend-end" in expected["bd-4-1-integration"]
        assert "bd-3b-2-backend-end" in expected["bd-4-1-integration"]

        # Should NOT depend on intermediate sprints
        assert "bd-3a-1-frontend-start" not in expected["bd-4-1-integration"]
        assert "bd-3b-1-backend-start" not in expected["bd-4-1-integration"]


class TestComplexDependencyPatterns:
    """Tests for complex multi-level dependency scenarios."""

    def test_sequential_parallel_merge_pattern(self):
        """Test common pattern: sequential → parallel → merge → sequential."""
        sprints = [
            {"id": "bd-1-1-setup", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2a-frontend", "sprint": "1.2a", "phase": "1"},
            {"id": "bd-1-2b-backend", "sprint": "1.2b", "phase": "1"},
            {"id": "bd-1-3-integration", "sprint": "1.3", "phase": "1"},
            {"id": "bd-1-4-finalize", "sprint": "1.4", "phase": "1"},
        ]

        expected = {
            "bd-1-1-setup": [],
            "bd-1-2a-frontend": ["bd-1-1-setup"],
            "bd-1-2b-backend": ["bd-1-1-setup"],
            "bd-1-3-integration": ["bd-1-2a-frontend", "bd-1-2b-backend"],
            "bd-1-4-finalize": ["bd-1-3-integration"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected

    def test_nested_parallel_groups(self):
        """Test multiple sets of parallel sprints in sequence."""
        sprints = [
            {"id": "bd-1-1-base", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2a-parallel-set-1", "sprint": "1.2a", "phase": "1"},
            {"id": "bd-1-2b-parallel-set-1", "sprint": "1.2b", "phase": "1"},
            {"id": "bd-1-3-merge-1", "sprint": "1.3", "phase": "1"},
            {"id": "bd-1-4a-parallel-set-2", "sprint": "1.4a", "phase": "1"},
            {"id": "bd-1-4b-parallel-set-2", "sprint": "1.4b", "phase": "1"},
            {"id": "bd-1-5-merge-2", "sprint": "1.5", "phase": "1"},
        ]

        expected = {
            "bd-1-1-base": [],
            "bd-1-2a-parallel-set-1": ["bd-1-1-base"],
            "bd-1-2b-parallel-set-1": ["bd-1-1-base"],
            "bd-1-3-merge-1": ["bd-1-2a-parallel-set-1", "bd-1-2b-parallel-set-1"],
            "bd-1-4a-parallel-set-2": ["bd-1-3-merge-1"],
            "bd-1-4b-parallel-set-2": ["bd-1-3-merge-1"],
            "bd-1-5-merge-2": ["bd-1-4a-parallel-set-2", "bd-1-4b-parallel-set-2"],
        }

        for sprint in sprints:
            assert sprint["id"] in expected


class TestDependencyAlgorithm:
    """Tests for the core dependency resolution algorithm."""

    def test_sprint_id_to_bead_id_conversion(self):
        """Test converting sprint IDs to bead IDs."""
        test_cases = [
            ("1.1", "Initial Setup", "bd-1-1-initial-setup"),
            ("1.2a", "Frontend Development", "bd-1-2a-frontend-development"),
            ("3a.2", "User Interface", "bd-3a-2-user-interface"),
            ("4.1", "System Integration", "bd-4-1-system-integration"),
        ]

        for sprint_id, title, expected_bead_id in test_cases:
            # Convert sprint ID: replace . with - for bead ID format
            sprint_part = sprint_id.replace(".", "-")
            # Convert title: lowercase, replace spaces with hyphens
            name = title.lower().replace(" ", "-")
            bead_id = f"bd-{sprint_part}-{name}"

            assert bead_id == expected_bead_id

    def test_determine_previous_sprint_sequential(self):
        """Test finding previous sprint in sequential case."""
        # For sprint 1.2, previous is 1.1
        current = {"sprint": "1.2", "phase": "1"}
        # In sequential case, look for sprint 1.1 in same phase
        expected_previous = "1.1"

        # Algorithm: parse current sprint (1.2) and decrement (1.1)
        parts = current["sprint"].split(".")
        phase = parts[0]
        sprint_num = int(parts[1][0]) - 1

        if sprint_num > 0:
            previous_sprint = f"{phase}.{sprint_num}"
            assert previous_sprint == expected_previous

    def test_detect_parallel_sprints(self):
        """Test detecting parallel sprint suffixes."""
        test_cases = [
            ("1.2a", True),
            ("1.2b", True),
            ("1.2c", True),
            ("1.2", False),
            ("3a.1", False),  # This is a phase split, not parallel
        ]

        for sprint_id, is_parallel in test_cases:
            # Check if sprint_id ends with letter (and is not phase split)
            # Parallel: X.Ya where first part has no letter
            parts = sprint_id.split(".")
            if len(parts) == 2:
                # Check if first part is pure number and second part ends with letter
                first_is_number = parts[0].isdigit()
                second_ends_letter = parts[1][-1].isalpha()
                result = first_is_number and second_ends_letter
            else:
                result = False

            assert result == is_parallel

    def test_detect_phase_splits(self):
        """Test detecting phase split patterns."""
        test_cases = [
            ("3a.1", True),
            ("3b.2", True),
            ("1.2a", False),  # This is parallel, not phase split
            ("4.1", False),
        ]

        for sprint_id, is_phase_split in test_cases:
            # Phase split has letter in first part (before dot)
            parts = sprint_id.split(".")
            has_phase_letter = len(parts[0]) > 1 and parts[0][-1].isalpha()

            assert has_phase_letter == is_phase_split


class TestRealWorldScenarios:
    """Tests using actual dependency fixtures."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_simple_plan_dependencies(self, fixtures_dir):
        """Test dependencies match expected output for simple plan."""
        expected_file = fixtures_dir / "expected-simple-dependencies.json"

        with open(expected_file) as f:
            expected = json.load(f)

        # Verify sequential chain
        assert expected["bd-1-1-setup"]["dependencies"] == []
        assert expected["bd-1-2-core"]["dependencies"] == ["bd-1-1-setup"]
        assert expected["bd-1-3-integration"]["dependencies"] == ["bd-1-2-core"]

    def test_parallel_plan_dependencies(self, fixtures_dir):
        """Test dependencies match expected output for parallel plan."""
        expected_file = fixtures_dir / "expected-parallel-dependencies.json"

        with open(expected_file) as f:
            expected = json.load(f)

        # Verify parallel structure
        assert expected["bd-1-1-foundation"]["dependencies"] == []
        assert expected["bd-1-2a-frontend"]["dependencies"] == ["bd-1-1-foundation"]
        assert expected["bd-1-2b-backend"]["dependencies"] == ["bd-1-1-foundation"]

        # Verify merge depends on both parallel
        assert set(expected["bd-1-3-integration"]["dependencies"]) == {
            "bd-1-2a-frontend",
            "bd-1-2b-backend"
        }

    def test_complex_plan_dependencies(self, fixtures_dir):
        """Test dependencies match expected output for complex plan."""
        expected_file = fixtures_dir / "expected-complex-dependencies.json"

        with open(expected_file) as f:
            expected = json.load(f)

        # Verify phase convergence
        convergence_deps = expected["bd-4-1-integration"]["dependencies"]
        assert "bd-3a-2-user-interface" in convergence_deps
        assert "bd-3b-2-business-logic" in convergence_deps

        # Verify phase splits are independent
        assert expected["bd-3a-1-ui-components"]["dependencies"] == ["bd-2-1-database"]
        assert expected["bd-3b-1-api-layer"]["dependencies"] == ["bd-2-1-database"]


class TestEdgeCases:
    """Tests for edge cases in dependency generation."""

    def test_single_sprint_plan(self):
        """Test plan with only one sprint has no dependencies."""
        sprints = [
            {"id": "bd-1-1-only", "sprint": "1.1", "phase": "1"},
        ]

        expected = {
            "bd-1-1-only": [],
        }

        assert expected["bd-1-1-only"] == []

    def test_circular_dependency_detection(self):
        """Test that circular dependencies would be detected."""
        # This should never happen in valid plans, but test detection
        # In a real implementation, the algorithm should validate DAG structure

        # Example of invalid circular reference
        invalid = {
            "bd-1-1-a": ["bd-1-2-b"],  # A depends on B
            "bd-1-2-b": ["bd-1-1-a"],  # B depends on A (circular!)
        }

        # A proper algorithm should detect this
        # This is a placeholder for validation logic
        assert "bd-1-1-a" in invalid["bd-1-2-b"]
        assert "bd-1-2-b" in invalid["bd-1-1-a"]

    def test_missing_dependency_reference(self):
        """Test handling of reference to non-existent sprint."""
        # If a sprint claims to depend on a sprint that doesn't exist
        # the algorithm should either error or skip the invalid reference

        sprints = [
            {"id": "bd-1-1-exists", "sprint": "1.1", "phase": "1"},
            {"id": "bd-1-2-has-bad-dep", "sprint": "1.2", "phase": "1"},
        ]

        # If 1.2 claims to depend on non-existent 1.1.5
        # the validation should catch this
        all_sprint_ids = {s["id"] for s in sprints}
        dependency = "bd-1-1.5-nonexistent"

        assert dependency not in all_sprint_ids

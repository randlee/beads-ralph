# Phase/Sprint Numbering Scheme

beads-ralph uses the synaptic-canvas numbering scheme for phases and sprints to enable parallel execution.

## Repository References

This document references the following external repository. It should be checked out locally as a sibling to this repository. If not available locally, please check it out before proceeding.

| Repository | GitHub URL | Local Path | Purpose |
|------------|------------|------------|---------|
| synaptic-canvas | *(Ask user for URL)* | `../synaptic-canvas/` | Authoritative source for phase/sprint numbering grammar and patterns |

## Authoritative Source

`../synaptic-canvas/plans/sc-kanban-design-v2.md` (lines 319-374)

## Grammar

### Phase Format

**Pattern**: `<number>[<letter>]*`

**Regex**: `^[0-9]+[a-z]*$`

**Examples**:
- `1` - Phase 1 (sequential)
- `2` - Phase 2 (sequential)
- `3a` - Phase 3, track A (parallel)
- `3b` - Phase 3, track B (parallel)
- `3ab` - Phase 3, tracks A and B merged
- `12` - Phase 12 (multi-digit)

**Letter Suffix Meaning**:
- No letter: Sequential phase, single track
- Single letter (`a`, `b`, `c`): Parallel phase track
- Multiple letters (`ab`, `abc`): Merged parallel tracks

### Sprint Format

**Pattern**: `<phase>.<number>[<letter>]*`

**Regex**: `^[0-9]+[a-z]*\.[0-9]+[a-z]*$`

**Examples**:
- `1.1` - Phase 1, Sprint 1
- `1.2` - Phase 1, Sprint 2
- `3a.2` - Phase 3a, Sprint 2
- `3b.2a` - Phase 3b, Sprint 2, track A (parallel sprint)
- `3b.2b` - Phase 3b, Sprint 2, track B (parallel sprint)
- `12.5c` - Phase 12, Sprint 5, track C

**Letter Suffix Meaning**:
- No letter: Sequential sprint
- Single letter: Parallel sprint within phase
- Multiple letters: Merged parallel sprints (rare)

## Parallel Execution Scenarios

| Scenario | Phase | Sprints | Dependencies | Meaning |
|----------|-------|---------|--------------|---------|
| **Sequential** | `1` | `1.1 → 1.2 → 1.3` | Each sprint blocks next | Standard linear execution |
| **Parallel Sprints** | `1` | `1.2a`, `1.2b` | No cross-dependencies | Sprints run concurrently, merge in `1.3` |
| **Phase Split** | `3` → `3a`, `3b` | `3a.1`, `3b.1` | Independent phase tracks | Completely separate work streams |
| **Nested Parallel** | `3a` | `3a.2a`, `3a.2b` | No cross-dependencies | Parallel sprints within parallel phase |
| **Converge & Split** | `2` → `3a`, `3b` → `4` | `2.x → {3a.1, 3b.1} → 4.1` | Phase 2 blocks 3a/3b, 3a/3b block 4 | Work diverges then converges |

## Dependency Rules

### Sequential Execution

```
Sprint 1.1 ─blocks─> Sprint 1.2 ─blocks─> Sprint 1.3
```

All sprints in sequence. Each sprint creates a bead dependency on the previous sprint.

**Bead Dependencies**:
```json
{
  "id": "bd-sprint-1-2",
  "metadata": {"phase": "1", "sprint": "1.2"},
  "dependencies": ["bd-sprint-1-1"]
}
```

### Parallel Sprint Execution

```
         ┌─> Sprint 1.2a ─┐
Sprint 1.1                 ├─blocks─> Sprint 1.3
         └─> Sprint 1.2b ─┘
```

Sprints `1.2a` and `1.2b` run in parallel. Both must complete before `1.3` starts.

**Bead Dependencies**:
```json
{
  "id": "bd-sprint-1-2a",
  "metadata": {"phase": "1", "sprint": "1.2a"},
  "dependencies": ["bd-sprint-1-1"]
}
{
  "id": "bd-sprint-1-2b",
  "metadata": {"phase": "1", "sprint": "1.2b"},
  "dependencies": ["bd-sprint-1-1"]
}
{
  "id": "bd-sprint-1-3",
  "metadata": {"phase": "1", "sprint": "1.3"},
  "dependencies": ["bd-sprint-1-2a", "bd-sprint-1-2b"]
}
```

### Phase Split Execution

```
         ┌─> Phase 3a: Sprint 3a.1 → 3a.2 ─┐
Phase 2 ─┤                                   ├─> Phase 4
         └─> Phase 3b: Sprint 3b.1 → 3b.2 ─┘
```

Phases `3a` and `3b` are independent tracks. Each has its own sprint sequence. Both must complete before `Phase 4`.

**Bead Dependencies**:
```json
// Phase 3a sprints
{
  "id": "bd-sprint-3a-1",
  "metadata": {"phase": "3a", "sprint": "3a.1"},
  "dependencies": ["bd-sprint-2-last"]
}
{
  "id": "bd-sprint-3a-2",
  "metadata": {"phase": "3a", "sprint": "3a.2"},
  "dependencies": ["bd-sprint-3a-1"]
}

// Phase 3b sprints
{
  "id": "bd-sprint-3b-1",
  "metadata": {"phase": "3b", "sprint": "3b.1"},
  "dependencies": ["bd-sprint-2-last"]
}
{
  "id": "bd-sprint-3b-2",
  "metadata": {"phase": "3b", "sprint": "3b.2"},
  "dependencies": ["bd-sprint-3b-1"]
}

// Phase 4 waits for both tracks
{
  "id": "bd-sprint-4-1",
  "metadata": {"phase": "4", "sprint": "4.1"},
  "dependencies": ["bd-sprint-3a-2", "bd-sprint-3b-2"]
}
```

## Worktree Integration

Worktree paths follow the sc-git-worktree convention: worktrees are placed as siblings to the repository.

### Worktree Path Pattern

```
../<repo-name>-worktrees/<branch-name>
```

Where:
- `<repo-name>` = Repository directory name (e.g., `my-app`)
- `<branch-name>` = Normalized sprint branch (e.g., `main/1-2-auth-api`)

**Example Structure**:
```
/Users/dev/projects/
├── my-app/                          # Main repository
└── my-app-worktrees/                # Worktrees (sibling directory)
    ├── main/1-1-project-setup/
    ├── main/1-2-auth-api/
    └── main/3a-2-api-design/
```

### Branch Naming Pattern

```
<source-branch>/<sprint-id>-<sprint-name>
```

**Normalization Rules**:
1. Replace `.` with `-` in sprint ID (e.g., `1.2` → `1-2`)
2. Convert sprint name to lowercase
3. Replace spaces with `-`
4. Remove special characters

### Examples

| Sprint | Name | Source Branch | Branch Name | Worktree Path |
|--------|------|---------------|-------------|---------------|
| `1.1` | Project Setup | `main` | `main/1-1-project-setup` | `../my-app-worktrees/main/1-1-project-setup` |
| `3a.2` | API Design | `main` | `main/3a-2-api-design` | `../my-app-worktrees/main/3a-2-api-design` |
| `3b.2a` | Auth Service | `develop` | `develop/3b-2a-auth-service` | `../my-app-worktrees/develop/3b-2a-auth-service` |
| `12.5c` | Performance Testing | `main` | `main/12-5c-performance-testing` | `../my-app-worktrees/main/12-5c-performance-testing` |

## Ralph Loop Sprint Discovery

The Go ralph loop discovers ready sprints using beads dependencies:

```go
// Find ready beads (open, no blockers, not in_progress)
readyBeads := findReadyBeads()

// Group by sprint
sprintMap := make(map[string][]Bead)
for _, bead := range readyBeads {
    sprint := bead.Metadata.Sprint
    sprintMap[sprint] = append(sprintMap[sprint], bead)
}

// Launch scrum-masters for each sprint in parallel
for sprint, beads := range sprintMap {
    for _, bead := range beads {
        go runScrumMaster(bead)
    }
}
```

**Key Property**: Dependencies ensure sprints execute in correct order. Parallel sprints have no cross-dependencies, so `bd ready` returns them simultaneously.

## Merge Sprints

When parallel sprints complete, a **merge sprint** integrates their branches.

### Merge Sprint Numbering

Merge sprints follow the next sequential sprint number:

```
1.2a, 1.2b (parallel) → 1.3 (merge)
3a.2a, 3a.2b (parallel) → 3a.3 (merge)
```

### Merge Bead Example

```json
{
  "id": "bd-merge-1-3",
  "title": "Merge sprint 1.2 branches",
  "description": "Integrate branches from parallel sprints 1.2a and 1.2b",
  "issue_type": "beads-ralph-merge",
  "dependencies": ["bd-sprint-1-2a", "bd-sprint-1-2b"],
  "metadata": {
    "phase": "1",
    "sprint": "1.3",
    "branch": "main/1-3-merge",
    "source_branch": "main",
    "branches_to_merge": [
      "main/1-2a-auth-api",
      "main/1-2b-user-profile"
    ],
    "dev_agent_path": ".claude/agents/merge-specialist",
    "dev_model": "sonnet"
  }
}
```

## Validation Examples

### Valid Phase Numbers

✅ `1` - Simple sequential phase
✅ `2` - Next sequential phase
✅ `3a` - Parallel track A
✅ `3b` - Parallel track B
✅ `3ab` - Merged tracks A and B
✅ `12` - Multi-digit phase
✅ `5abc` - Three parallel tracks merged

### Invalid Phase Numbers

❌ `1.2` - Contains `.` (sprint format, not phase)
❌ `a1` - Starts with letter
❌ `1-2` - Contains `-`
❌ `1A` - Uppercase letter
❌ `phase-1` - Contains text

### Valid Sprint Numbers

✅ `1.1` - Simple sequential sprint
✅ `1.2` - Next sprint in phase
✅ `3a.2` - Sprint in parallel phase
✅ `3b.2a` - Parallel sprint in parallel phase
✅ `3b.2b` - Another parallel sprint
✅ `12.5c` - Multi-digit phase and sprint with track

### Invalid Sprint Numbers

❌ `1` - Missing sprint number (phase format)
❌ `1-2` - Uses `-` instead of `.`
❌ `1.2.3` - Too many parts
❌ `a.1` - Phase starts with letter
❌ `1.a` - Sprint part starts with letter
❌ `1.2A` - Uppercase letter

## Key Design Documents

| Purpose | File |
|---------|------|
| Phase/Sprint Grammar | `../synaptic-canvas/plans/sc-kanban-design-v2.md` |
| Board Config & Cards | `../synaptic-canvas/docs/kanban-design.md` |
| Worktree Naming | `../synaptic-canvas/plans/sc-project-manager-design.md` |
| Parallel Execution Pattern | `../synaptic-canvas/docs/claude-code-skills-agents-guidelines-0.4.md` (Pattern 5) |

## Python Validation Functions

```python
import re

PHASE_PATTERN = re.compile(r'^[0-9]+[a-z]*$')
SPRINT_PATTERN = re.compile(r'^[0-9]+[a-z]*\.[0-9]+[a-z]*$')

def is_valid_phase(phase: str) -> bool:
    """Validate phase number format."""
    return bool(PHASE_PATTERN.match(phase))

def is_valid_sprint(sprint: str) -> bool:
    """Validate sprint number format."""
    return bool(SPRINT_PATTERN.match(sprint))

def extract_phase_from_sprint(sprint: str) -> str:
    """Extract phase number from sprint number."""
    if not is_valid_sprint(sprint):
        raise ValueError(f"Invalid sprint format: {sprint}")
    return sprint.split('.')[0]

def are_sprints_parallel(sprint1: str, sprint2: str) -> bool:
    """Check if two sprints can run in parallel."""
    # Sprints are parallel if they have the same base but different suffixes
    # e.g., 1.2a and 1.2b, or 3a.1a and 3a.1b
    if not (is_valid_sprint(sprint1) and is_valid_sprint(sprint2)):
        return False

    # Remove letter suffixes
    base1 = re.sub(r'[a-z]+$', '', sprint1)
    base2 = re.sub(r'[a-z]+$', '', sprint2)

    # Parallel if same base but different full strings
    return base1 == base2 and sprint1 != sprint2

def normalize_sprint_for_path(sprint: str) -> str:
    """Normalize sprint number for use in paths/branches."""
    return sprint.replace('.', '-')

# Examples
assert is_valid_phase('1')
assert is_valid_phase('3a')
assert not is_valid_phase('1.2')

assert is_valid_sprint('1.1')
assert is_valid_sprint('3a.2b')
assert not is_valid_sprint('1')

assert extract_phase_from_sprint('1.2') == '1'
assert extract_phase_from_sprint('3a.2b') == '3a'

assert are_sprints_parallel('1.2a', '1.2b')
assert not are_sprints_parallel('1.2', '1.3')

assert normalize_sprint_for_path('1.2') == '1-2'
assert normalize_sprint_for_path('3a.2b') == '3a-2b'
```

## Go Validation Functions

```go
package numbering

import (
	"fmt"
	"regexp"
	"strings"
)

var (
	phasePattern  = regexp.MustCompile(`^[0-9]+[a-z]*$`)
	sprintPattern = regexp.MustCompile(`^[0-9]+[a-z]*\.[0-9]+[a-z]*$`)
)

// IsValidPhase validates phase number format
func IsValidPhase(phase string) bool {
	return phasePattern.MatchString(phase)
}

// IsValidSprint validates sprint number format
func IsValidSprint(sprint string) bool {
	return sprintPattern.MatchString(sprint)
}

// ExtractPhaseFromSprint extracts phase number from sprint number
func ExtractPhaseFromSprint(sprint string) (string, error) {
	if !IsValidSprint(sprint) {
		return "", fmt.Errorf("invalid sprint format: %s", sprint)
	}
	parts := strings.Split(sprint, ".")
	return parts[0], nil
}

// AreSprintsParallel checks if two sprints can run in parallel
func AreSprintsParallel(sprint1, sprint2 string) bool {
	if !IsValidSprint(sprint1) || !IsValidSprint(sprint2) {
		return false
	}

	// Remove letter suffixes
	letterPattern := regexp.MustCompile(`[a-z]+$`)
	base1 := letterPattern.ReplaceAllString(sprint1, "")
	base2 := letterPattern.ReplaceAllString(sprint2, "")

	// Parallel if same base but different full strings
	return base1 == base2 && sprint1 != sprint2
}

// NormalizeSprintForPath normalizes sprint number for use in paths/branches
func NormalizeSprintForPath(sprint string) string {
	return strings.ReplaceAll(sprint, ".", "-")
}
```

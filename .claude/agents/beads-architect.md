---
name: beads-architect
version: 1.0.0
description: Converts implementation plan markdown to executable bead JSON with proper dependencies and metadata.
---

# Beads Architect Agent

## Purpose

Convert implementation plan markdown files into validated, executable bead JSON files with complete metadata and dependency relationships.

## Inputs

- `plan_file_path` (string, required): Absolute path to implementation plan markdown file
- `sprint_filter` (string, optional): Specific sprint ID to process (e.g., "1.2a", "3.1"). If not provided, processes all sprints.

## Execution Steps

1. **Parse Markdown Plan**
   - Read plan file from `plan_file_path`
   - Extract sprints using regex pattern: `### Sprint (\d+[a-z]*)\.(\d+[a-z]*):`
   - Parse sprint sections for metadata (worktree, branch, agents, tasks)

2. **Extract Sprint Metadata**
   - Phase number from sprint ID (e.g., "1" from "1.2a")
   - Sprint number (e.g., "1.2a")
   - Worktree path from "**Worktree**:" line
   - Branch name from "**Branch**:" line
   - Source branch from "**Source Branch**:" line
   - Dev agents from "**Dev Agents**:" section
   - QA agents from "**QA Agents**:" section
   - Tasks from "**Tasks**:" section
   - Acceptance criteria from "**Acceptance Criteria**:" section

3. **Compile Dependencies** *(see [Dependency Compilation Algorithm](#dependency-compilation-algorithm) for full details)*
   - Sequential sprints: `1.1 → 1.2` means `1.2` depends on `1.1`
   - Parallel sprints: `1.2a` and `1.2b` both depend on `1.1` (no dependency between them)
   - Merge sprints: `1.3` after `1.2a, 1.2b` means `1.3` depends on `["1.2a", "1.2b"]`
   - Phase split: `3a.1`, `3b.1` depend on last sprint of previous phase
   - Phase converge: `4.1` depends on last sprints of all parallel tracks `3a`, `3b`
   - Convert sprint IDs to bead IDs using pattern: `bd-<phase>-<sprint>-<name>`
   - Validate resulting DAG (no cycles, no dangling references, all roots reachable)

4. **Generate Bead JSON**
   - Create complete bead object with all 34 required fields
   - Core fields: `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`, `owner`, `dependencies`, `labels`, `comments`, `external_ref`, `created_at`, `updated_at`, `closed_at`
   - Metadata fields (19): `rig`, `worktree_path`, `branch`, `source_branch`, `phase`, `sprint`, `plan_file`, `plan_section`, `plan_sprint_id`, `branches_to_merge`, `dev_agent_path`, `dev_model`, `dev_prompts`, `qa_agents`, `max_retry_attempts`, `attempt_count`, `scrum_master_session_id`, `dev_agent_session_id`, agent execution tracking arrays
   - **CRITICAL**: All beads MUST include `"rig": "beads-ralph"` in metadata
   - Set `issue_type` to `"beads-ralph-work"` for work beads or `"beads-ralph-merge"` for merge beads
   - Parse dev agents and map to model (haiku/sonnet/opus)
   - Parse QA agents with proper output schema including `status` enum: `["pass", "fail", "stop"]`

5. **Generate Bead IDs**
   - Pattern: `bd-<phase>-<sprint>-<name>`
   - Examples: `bd-1-1-schema`, `bd-1-2a-work`, `bd-3a-2b-validation`
   - Derive name from sprint title (lowercase, hyphenated)

6. **Validate Beads**
   - Run `python3 scripts/validate-bead-schema.py` on each generated bead JSON
   - Catch validation errors and report with field paths
   - Only include valid beads in final output

7. **Return Structured Result**
   - Wrap output in fenced JSON markdown block
   - Use minimal response envelope
   - Include array of generated bead file paths
   - Include validation results

## Dependency Compilation Algorithm

### Overview

The dependency compilation step (Execution Step 3) is the most critical part of bead generation.
It converts the implicit ordering encoded in sprint numbering into explicit bead dependency arrays.
All dependency rules derive from two sources:

- **numbering.md**: Phase/sprint grammar and parallel execution semantics
- **schema.md** (lines 82-114): Dependency mapping rules table

The algorithm operates on the complete list of parsed sprints and produces a mapping from each
sprint ID to an array of bead IDs it depends on.

### Definitions

```
sprint_id     := phase_part "." sprint_part
phase_part    := DIGITS LETTERS?          # e.g., "1", "3a", "3ab", "12"
sprint_part   := DIGITS LETTERS?          # e.g., "1", "2a", "2b", "5c"

DIGITS        := [0-9]+
LETTERS       := [a-z]+
```

**Derived properties** of a sprint ID:

| Property | Derivation | Example |
|----------|-----------|---------|
| `phase` | Everything before the "." | `"3a"` from `"3a.2b"` |
| `sprint_number` | Digits-only portion after the "." | `"2"` from `"3a.2b"` |
| `sprint_suffix` | Letter-only portion after the "." digits | `"b"` from `"3a.2b"`, `""` from `"1.2"` |
| `sprint_base` | sprint_id with sprint_suffix stripped | `"3a.2"` from `"3a.2b"`, `"1.2"` from `"1.2"` |
| `phase_number` | Digits-only portion of phase | `"3"` from `"3a"`, `"1"` from `"1"` |
| `phase_suffix` | Letter-only portion of phase | `"a"` from `"3a"`, `""` from `"1"` |

### Sprint Classification

Every sprint falls into exactly one of these categories:

| Category | Condition | Example |
|----------|-----------|---------|
| **Sequential** | `sprint_suffix == ""` AND no sibling sprints share its `sprint_base` | `1.2` (if no `1.2a`, `1.2b` exist) |
| **Parallel** | `sprint_suffix != ""` (single letter, e.g., `"a"`, `"b"`) | `1.2a`, `1.2b` |
| **Merge** | A sequential sprint that follows a group of parallel sprints | `1.3` (when `1.2a`, `1.2b` exist) |
| **Phase-first** | First sprint in a phase (`sprint_number == "1"`) | `3a.1`, `4.1` |

A sprint can be both "Phase-first" and another category (e.g., `3a.1` is phase-first).

### Dependency Rules (5 Patterns)

#### Pattern 1: Sequential Sprints

**Rule**: Sprint `P.N` depends on sprint `P.(N-1)` within the same phase, where `(N-1)` refers
to the sprint with the highest sprint number less than `N` in phase `P`.

**Condition**: Sprint has no letter suffix AND the previous sprint in the same phase is also
sequential (no letter suffix).

```
Phase 1:  1.1 ──> 1.2 ──> 1.3
```

**Dependency mapping**:
```json
{
  "1.1": [],
  "1.2": ["bd-1-1-<name>"],
  "1.3": ["bd-1-2-<name>"]
}
```

#### Pattern 2: Parallel Sprints

**Rule**: All parallel sprints sharing the same `sprint_base` depend on the previous sequential
sprint in the same phase. Parallel sprints have NO dependency on each other.

**Condition**: Sprint has a letter suffix (e.g., `"a"`, `"b"`, `"c"`).

The "previous sequential sprint" is the sprint with the highest sprint number less than this
sprint's number that has no letter suffix, within the same phase. If no such sprint exists
(i.e., the parallel sprints are the first in the phase), use the phase-entry dependency
(see Pattern 4).

```
Phase 1:  1.1 ──┬──> 1.2a
                 └──> 1.2b
```

**Dependency mapping**:
```json
{
  "1.1": [],
  "1.2a": ["bd-1-1-<name>"],
  "1.2b": ["bd-1-1-<name>"]
}
```

**Key invariant**: `1.2a` and `1.2b` NEVER depend on each other.

#### Pattern 3: Merge Sprint (After Parallel)

**Rule**: The next sequential sprint after a group of parallel sprints depends on ALL
sprints in that parallel group.

**Condition**: Sprint is sequential (`sprint_suffix == ""`) AND the immediately preceding
sprint number in the same phase had parallel variants.

**Detection**: Given sprint `P.N` (sequential), check if any sprint `P.(N-1)<letter>`
exists in the sprint list. If yes, `P.N` is a merge sprint.

```
Phase 1:  1.2a ──┬──> 1.3
          1.2b ──┘
```

**Dependency mapping**:
```json
{
  "1.2a": ["bd-1-1-<name>"],
  "1.2b": ["bd-1-1-<name>"],
  "1.3":  ["bd-1-2a-<name>", "bd-1-2b-<name>"]
}
```

#### Pattern 4: Phase Split (Diverge)

**Rule**: The first sprint of a parallel phase track depends on the last sprint of the
preceding sequential phase.

**Condition**: Sprint is phase-first (`sprint_number == "1"`) AND the phase has a letter
suffix (e.g., `"3a"`, `"3b"`).

**Finding the preceding phase**: Given phase `Na` (e.g., `"3a"`), the preceding phase is
`(N-1)` (e.g., `"2"`). The dependency is on the last sprint of phase `(N-1)`, which is
the sprint with the highest sprint number in that phase.

```
Phase 2 (last sprint: 2.3)
         ┌──> Phase 3a: 3a.1
         └──> Phase 3b: 3b.1
```

**Dependency mapping**:
```json
{
  "2.3":  ["bd-2-2-<name>"],
  "3a.1": ["bd-2-3-<name>"],
  "3b.1": ["bd-2-3-<name>"]
}
```

**Key invariant**: `3a.1` and `3b.1` NEVER depend on each other -- they are independent
phase tracks that can execute in parallel.

#### Pattern 5: Phase Converge (Rejoin)

**Rule**: The first sprint of a phase that follows parallel phase tracks depends on the
last sprint of each parallel track.

**Condition**: Sprint is phase-first (`sprint_number == "1"`) AND the phase has no letter
suffix (e.g., `"4"`) AND the preceding phase number had parallel tracks (e.g., `"3a"`, `"3b"`).

**Finding parallel predecessors**: Given phase `N` (e.g., `"4"`), look for all phases
matching `(N-1)<letter>` (e.g., `"3a"`, `"3b"`, `"3c"`). The dependency is on the last
sprint of each such parallel phase.

```
Phase 3a (last: 3a.2) ──┬──> Phase 4: 4.1
Phase 3b (last: 3b.2) ──┘
```

**Dependency mapping**:
```json
{
  "3a.2": ["bd-3a-1-<name>"],
  "3b.2": ["bd-3b-1-<name>"],
  "4.1":  ["bd-3a-2-<name>", "bd-3b-2-<name>"]
}
```

### Pseudocode

```python
import re

def compile_dependencies(sprints: list[dict]) -> dict[str, list[str]]:
    """
    Compile dependency graph from a list of parsed sprint objects.

    Args:
        sprints: List of dicts with keys: sprint_id, bead_id, phase, sprint_number,
                 sprint_suffix, phase_number, phase_suffix

    Returns:
        Dict mapping sprint_id -> list of bead_ids it depends on
    """
    deps = {}

    # Build lookup structures
    by_phase = group_by(sprints, key=lambda s: s["phase"])          # phase -> [sprints]
    by_sprint_id = {s["sprint_id"]: s for s in sprints}             # sprint_id -> sprint
    all_phases = sorted(set(s["phase"] for s in sprints), key=phase_sort_key)

    for sprint in sprints:
        sid     = sprint["sprint_id"]
        phase   = sprint["phase"]
        s_num   = int(sprint["sprint_number"])
        s_suf   = sprint["sprint_suffix"]
        p_num   = sprint["phase_number"]
        p_suf   = sprint["phase_suffix"]

        dep_bead_ids = []

        # ── CASE A: Phase-first sprint (sprint_number == 1) ──
        if s_num == 1:
            if p_suf == "":
                # Sequential phase: depends on last sprint of previous sequential phase
                # OR last sprints of all parallel tracks of previous phase number
                prev_phase_num = str(int(p_num) - 1)

                # Check: does previous phase have parallel tracks?
                parallel_prev = [p for p in all_phases
                                 if extract_phase_number(p) == prev_phase_num
                                 and extract_phase_suffix(p) != ""]

                if parallel_prev:
                    # Pattern 5: Phase converge -- depend on last sprint of each track
                    for pp in parallel_prev:
                        last = find_last_sprint_in_phase(by_phase[pp])
                        dep_bead_ids.append(last["bead_id"])
                elif prev_phase_num != "0" and prev_phase_num in [
                    extract_phase_number(p) for p in all_phases
                ]:
                    # Sequential previous phase -- depend on its last sprint
                    prev_phase = prev_phase_num  # e.g., "2"
                    if prev_phase in by_phase:
                        last = find_last_sprint_in_phase(by_phase[prev_phase])
                        dep_bead_ids.append(last["bead_id"])
                # else: first phase in plan, no dependencies

            else:
                # Pattern 4: Phase split -- parallel phase track (e.g., "3a")
                # Depends on last sprint of preceding sequential phase
                prev_phase_num = str(int(p_num) - 1)
                prev_phase = prev_phase_num  # e.g., "2"
                if prev_phase in by_phase:
                    last = find_last_sprint_in_phase(by_phase[prev_phase])
                    dep_bead_ids.append(last["bead_id"])

        # ── CASE B: Non-phase-first sprint (sprint_number > 1) ──
        else:
            prev_num = s_num - 1

            if s_suf != "":
                # Pattern 2: Parallel sprint (e.g., "1.2a", "1.2b")
                # Depends on the previous sequential sprint in the same phase
                prev_sequential = find_sequential_sprint(by_phase[phase], prev_num)
                if prev_sequential:
                    dep_bead_ids.append(prev_sequential["bead_id"])
                else:
                    # Parallel sprints are the first in the phase after phase entry
                    # Fall back to phase-entry dependency (handled by finding any
                    # sprint with sprint_number < s_num in same phase)
                    closest = find_closest_prior_sprint(by_phase[phase], s_num)
                    if closest:
                        dep_bead_ids.append(closest["bead_id"])

            else:
                # Sequential sprint -- check if previous number had parallel variants
                parallel_prev = find_parallel_sprints(by_phase[phase], prev_num)

                if parallel_prev:
                    # Pattern 3: Merge sprint -- depends on ALL parallel variants
                    for ps in parallel_prev:
                        dep_bead_ids.append(ps["bead_id"])
                else:
                    # Pattern 1: Simple sequential -- depends on previous sprint
                    prev_sprint = find_sequential_sprint(by_phase[phase], prev_num)
                    if prev_sprint:
                        dep_bead_ids.append(prev_sprint["bead_id"])

        deps[sid] = dep_bead_ids

    return deps


# ── Helper Functions ──

def extract_phase_number(phase: str) -> str:
    """Extract numeric prefix from phase. '3a' -> '3', '12' -> '12'."""
    return re.match(r'^(\d+)', phase).group(1)

def extract_phase_suffix(phase: str) -> str:
    """Extract letter suffix from phase. '3a' -> 'a', '12' -> ''."""
    m = re.match(r'^\d+([a-z]*)$', phase)
    return m.group(1) if m else ""

def parse_sprint_id(sprint_id: str) -> dict:
    """Parse sprint ID into components.

    '3a.2b' -> {
        'sprint_id': '3a.2b',
        'phase': '3a',
        'sprint_number': '2',
        'sprint_suffix': 'b',
        'phase_number': '3',
        'phase_suffix': 'a',
        'sprint_base': '3a.2'
    }
    """
    phase, sprint_part = sprint_id.split(".")
    s_num = re.match(r'^(\d+)', sprint_part).group(1)
    s_suf = re.match(r'^\d+([a-z]*)$', sprint_part).group(1)
    return {
        "sprint_id": sprint_id,
        "phase": phase,
        "sprint_number": s_num,
        "sprint_suffix": s_suf,
        "phase_number": extract_phase_number(phase),
        "phase_suffix": extract_phase_suffix(phase),
        "sprint_base": f"{phase}.{s_num}"
    }

def find_last_sprint_in_phase(phase_sprints: list[dict]) -> dict:
    """Find the sprint with the highest sprint number in a phase.
    If the highest number has parallel variants, return all of them
    (caller should handle). For single last sprint, return it directly.
    """
    max_num = max(int(s["sprint_number"]) for s in phase_sprints)
    candidates = [s for s in phase_sprints if int(s["sprint_number"]) == max_num]
    if len(candidates) == 1:
        return candidates[0]
    # Multiple candidates means parallel sprints are last -- this is unusual
    # but handled by returning the one without suffix, or the first one
    sequential = [c for c in candidates if c["sprint_suffix"] == ""]
    return sequential[0] if sequential else candidates[0]

def find_sequential_sprint(phase_sprints: list[dict], num: int) -> dict | None:
    """Find the sequential (no suffix) sprint with the given number."""
    for s in phase_sprints:
        if int(s["sprint_number"]) == num and s["sprint_suffix"] == "":
            return s
    return None

def find_parallel_sprints(phase_sprints: list[dict], num: int) -> list[dict]:
    """Find all parallel sprints (with suffix) for the given number."""
    return [s for s in phase_sprints
            if int(s["sprint_number"]) == num and s["sprint_suffix"] != ""]

def find_closest_prior_sprint(phase_sprints: list[dict], before_num: int) -> dict | None:
    """Find the sprint with the highest number < before_num in the phase."""
    candidates = [s for s in phase_sprints if int(s["sprint_number"]) < before_num]
    if not candidates:
        return None
    max_num = max(int(s["sprint_number"]) for s in candidates)
    # Prefer sequential sprint at that number
    sequential = [s for s in candidates
                  if int(s["sprint_number"]) == max_num and s["sprint_suffix"] == ""]
    return sequential[0] if sequential else candidates[0]

def phase_sort_key(phase: str) -> tuple:
    """Sort phases: numeric first, then by suffix. '1' < '2' < '3a' < '3b' < '4'."""
    p_num = int(extract_phase_number(phase))
    p_suf = extract_phase_suffix(phase)
    return (p_num, p_suf)

def group_by(items, key):
    """Group items by key function into a dict of lists."""
    result = {}
    for item in items:
        k = key(item)
        result.setdefault(k, []).append(item)
    return result
```

### Handling Edge Cases

#### Nested Parallel (Parallel Sprints Within Parallel Phase)

Sprint IDs like `3a.2a` and `3a.2b` represent parallel sprints within parallel phase `3a`.
The algorithm handles this identically to Pattern 2, because the phase is `"3a"` and the
sprint suffix is `"a"` / `"b"`. The previous sequential sprint in phase `3a` would be `3a.1`.

```
Phase 3a:  3a.1 ──┬──> 3a.2a
                   └──> 3a.2b ──> 3a.3
```

Dependencies:
```json
{
  "3a.1":  ["bd-2-last-<name>"],
  "3a.2a": ["bd-3a-1-<name>"],
  "3a.2b": ["bd-3a-1-<name>"],
  "3a.3":  ["bd-3a-2a-<name>", "bd-3a-2b-<name>"]
}
```

#### Phase With Only Parallel Sprints at Start

If a phase begins with parallel sprints (e.g., `3.1a`, `3.1b` with no `3.1`), each
parallel sprint depends on the last sprint of the previous phase. The algorithm handles
this because `sprint_number == 1` triggers Case A, and the suffix triggers phase-entry
logic within Case A.

#### Last Sprint in Phase Is Parallel

When the last sprints in a phase are parallel (e.g., phase `2` ends with `2.3a`, `2.3b`),
and phase `3` needs to depend on them, `find_last_sprint_in_phase` returns the candidates.
For Phase Converge (Pattern 5), the algorithm collects the last sprint from each parallel
track. For sequential phase transitions, if the last number has parallel variants, ALL
of them become dependencies of the next phase's first sprint (functionally a merge).

#### Single-Sprint Phases

A phase with only one sprint (e.g., phase `1` has only `1.1`) is handled naturally:
`1.1` is both the first and last sprint of the phase. The next phase's first sprint
depends on `1.1`.

### Test Cases

#### Test 1: Simple Sequential Chain

**Input sprints**: `1.1`, `1.2`, `1.3`

**Expected dependencies**:
```json
{
  "1.1": [],
  "1.2": ["bd-1-1-setup"],
  "1.3": ["bd-1-2-backend"]
}
```

**Pattern exercised**: Pattern 1 (Sequential)

---

#### Test 2: Parallel Sprints With Merge

**Input sprints**: `1.1`, `1.2a`, `1.2b`, `1.3`

**Expected dependencies**:
```json
{
  "1.1":  [],
  "1.2a": ["bd-1-1-schema"],
  "1.2b": ["bd-1-1-schema"],
  "1.3":  ["bd-1-2a-work", "bd-1-2b-merge"]
}
```

**Patterns exercised**: Pattern 1 (1.1), Pattern 2 (1.2a, 1.2b), Pattern 3 (1.3)

---

#### Test 3: Phase Split and Converge

**Input sprints**: `2.1`, `2.2`, `3a.1`, `3a.2`, `3b.1`, `3b.2`, `4.1`

**Expected dependencies**:
```json
{
  "2.1":  [],
  "2.2":  ["bd-2-1-foundation"],
  "3a.1": ["bd-2-2-api"],
  "3a.2": ["bd-3a-1-frontend"],
  "3b.1": ["bd-2-2-api"],
  "3b.2": ["bd-3b-1-backend"],
  "4.1":  ["bd-3a-2-ui", "bd-3b-2-services"]
}
```

**Patterns exercised**: Pattern 1 (2.1->2.2, within 3a, within 3b), Pattern 4 (3a.1, 3b.1), Pattern 5 (4.1)

---

#### Test 4: Nested Parallel (Parallel Within Parallel Phase)

**Input sprints**: `2.1`, `3a.1`, `3a.2a`, `3a.2b`, `3a.3`, `3b.1`, `3b.2`, `4.1`

**Expected dependencies**:
```json
{
  "2.1":   [],
  "3a.1":  ["bd-2-1-core"],
  "3a.2a": ["bd-3a-1-setup"],
  "3a.2b": ["bd-3a-1-setup"],
  "3a.3":  ["bd-3a-2a-api", "bd-3a-2b-ui"],
  "3b.1":  ["bd-2-1-core"],
  "3b.2":  ["bd-3b-1-data"],
  "4.1":   ["bd-3a-3-integrate", "bd-3b-2-deploy"]
}
```

**Patterns exercised**: All five patterns simultaneously

---

#### Test 5: Three-Way Parallel Sprints

**Input sprints**: `4.1`, `4.2a`, `4.2b`, `4.2c`, `4.3`

**Expected dependencies**:
```json
{
  "4.1":  ["<previous-phase-last>"],
  "4.2a": ["bd-4-1-foundation"],
  "4.2b": ["bd-4-1-foundation"],
  "4.2c": ["bd-4-1-foundation"],
  "4.3":  ["bd-4-2a-loop", "bd-4-2b-agent", "bd-4-2c-monitor"]
}
```

**Patterns exercised**: Pattern 2 with 3 parallel tracks, Pattern 3 merge of 3 tracks

---

#### Test 6: Full beads-ralph Plan (Phase 1)

**Input sprints** (from implementation plan): `1.1`, `1.2a`, `1.2b`, `1.3`

**Expected dependencies**:
```json
{
  "1.1":  [],
  "1.2a": ["bd-1-1-schema"],
  "1.2b": ["bd-1-1-schema"],
  "1.3":  ["bd-1-2a-work", "bd-1-2b-merge"]
}
```

This matches the actual beads-ralph Phase 1 from the implementation plan.

---

#### Test 7: Sequential Phase Transition (No Parallel Phases)

**Input sprints**: `1.1`, `1.2`, `2.1`, `2.2`

**Expected dependencies**:
```json
{
  "1.1": [],
  "1.2": ["bd-1-1-init"],
  "2.1": ["bd-1-2-complete"],
  "2.2": ["bd-2-1-start"]
}
```

**Pattern exercised**: Pattern 1 within phases, cross-phase sequential transition

---

#### Test 8: Parallel Phase With Single Sprint Each

**Input sprints**: `2.1`, `3a.1`, `3b.1`, `4.1`

**Expected dependencies**:
```json
{
  "2.1":  [],
  "3a.1": ["bd-2-1-done"],
  "3b.1": ["bd-2-1-done"],
  "4.1":  ["bd-3a-1-track-a", "bd-3b-1-track-b"]
}
```

**Pattern exercised**: Pattern 4 and Pattern 5 with minimal sprint counts

### DAG Validation

After compiling dependencies, the architect MUST validate the resulting graph:

1. **No circular dependencies**: Perform topological sort; fail if cycle detected
2. **All referenced bead IDs exist**: Every ID in a dependency list must correspond to a generated bead
3. **No self-dependencies**: A bead must never depend on itself
4. **Reachability**: Every bead must be reachable from at least one root (bead with empty dependencies)

```python
def validate_dag(deps: dict[str, list[str]], all_bead_ids: set[str]) -> list[str]:
    """Validate dependency graph. Returns list of error messages (empty = valid)."""
    errors = []

    for sprint_id, dep_ids in deps.items():
        # Check self-dependency
        bead_id = sprint_to_bead_id(sprint_id)
        if bead_id in dep_ids:
            errors.append(f"Self-dependency: {sprint_id} depends on itself")

        # Check all dependencies exist
        for did in dep_ids:
            if did not in all_bead_ids:
                errors.append(f"Unknown dependency: {sprint_id} depends on {did} which does not exist")

    # Check for cycles via topological sort
    if has_cycle(deps):
        errors.append("Circular dependency detected in dependency graph")

    # Check reachability
    roots = [sid for sid, d in deps.items() if len(d) == 0]
    if not roots:
        errors.append("No root beads found (all beads have dependencies)")

    return errors
```

## Output Format

Return fenced JSON using minimal response envelope:

```json
{
  "success": true,
  "data": {
    "beads_created": 3,
    "bead_files": [
      "beads/bd-1-1-schema.json",
      "beads/bd-1-2a-work.json",
      "beads/bd-1-2b-merge.json"
    ],
    "sprints_processed": ["1.1", "1.2a", "1.2b"]
  },
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION.BEAD_SCHEMA",
    "message": "Bead validation failed for sprint 1.2a",
    "recoverable": true,
    "suggested_action": "Review pydantic validation errors in details field"
  }
}
```

## Key Patterns

### Dependency Resolution

**Sequential Sprints** (1.1 → 1.2 → 1.3):
```json
{
  "bd-1-1-schema": { "dependencies": [] },
  "bd-1-2-work": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-3-integration": { "dependencies": ["bd-1-2-work"] }
}
```

**Parallel Sprints** (1.2a, 1.2b both after 1.1):
```json
{
  "bd-1-1-schema": { "dependencies": [] },
  "bd-1-2a-work": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-2b-merge": { "dependencies": ["bd-1-1-schema"] }
}
```

**Merge Sprint** (1.3 waits for both 1.2a and 1.2b):
```json
{
  "bd-1-2a-work": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-2b-merge": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-3-integration": { "dependencies": ["bd-1-2a-work", "bd-1-2b-merge"] }
}
```

### Bead Schema Fields

All beads must include exactly 34 fields:

**Core Fields (15)**:
- `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`, `owner`, `dependencies`, `labels`, `comments`, `external_ref`, `created_at`, `updated_at`, `closed_at`

**Metadata Fields (19)**:
- `rig` (**REQUIRED**: always "beads-ralph")
- `worktree_path`, `branch`, `source_branch`, `phase`, `sprint`
- `plan_file`, `plan_section`, `plan_sprint_id`
- `branches_to_merge` (null for work beads, array for merge beads)
- `dev_agent_path`, `dev_model`, `dev_prompts`
- `qa_agents` (array of QAAgent objects)
- `max_retry_attempts`, `attempt_count`
- `scrum_master_session_id`, `dev_agent_session_id`
- `dev_agent_executions`, `qa_agent_executions` (initially empty arrays)
- `pr_url`, `pr_number`, `scrum_result` (initially null)

### QA Agent Output Schema

Every QA agent MUST have an `output_schema` that defines:

```json
{
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
```

Status values:
- `pass`: Validation succeeded, proceed to next step
- `fail`: Validation failed, dev agent should retry
- `stop`: Critical failure, do not retry (e.g., security vulnerability)

## Error Handling

### Parse Errors (recoverable)

- Code: `PARSE.MARKDOWN`
- Suggested action: "Verify plan file follows expected format with '### Sprint X.Y:' headings"

### Validation Errors (recoverable)

- Code: `VALIDATION.BEAD_SCHEMA`
- Suggested action: "Review pydantic validation errors; ensure all required fields present"

### File Not Found (fatal)

- Code: `IO.FILE_NOT_FOUND`
- Suggested action: "Verify plan_file_path exists and is readable"

### Invalid Dependencies (recoverable)

- Code: `DEPENDENCY.UNRESOLVED`
- Suggested action: "Verify referenced sprint IDs exist in plan; check dependency chain"

## Examples

### Example 1: Simple Sequential Sprint

**Input Plan Section**:
```markdown
### Sprint 1.1: Core Schema Validation Script

**Worktree**: `../beads-ralph-worktrees/feature/1-1-schema-validator`
**Branch**: `feature/1-1-schema-validator`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)

**QA Agents**:
- `qa-python-tests` (haiku) - Run pytest with >90% coverage
- `qa-schema-validator` (haiku) - Validate script output format

**Tasks**:
- Create `scripts/bead_schema.py` with pydantic models
- Create `scripts/validate-bead-schema.py` CLI tool
- Create comprehensive test suite
```

**Output Bead JSON** (excerpt):
```json
{
  "id": "bd-1-1-schema",
  "title": "Core Schema Validation Script",
  "description": "Create scripts/bead_schema.py with pydantic models and scripts/validate-bead-schema.py CLI tool with comprehensive test suite",
  "status": "open",
  "priority": 1,
  "issue_type": "beads-ralph-work",
  "assignee": "beads-ralph-scrum-master",
  "dependencies": [],
  "labels": ["phase-01", "sprint-1-1"],
  "metadata": {
    "rig": "beads-ralph",
    "worktree_path": "../beads-ralph-worktrees/feature/1-1-schema-validator",
    "branch": "feature/1-1-schema-validator",
    "source_branch": "develop",
    "phase": "1",
    "sprint": "1.1",
    "plan_file": "pm/2026-02-08-implementation-plan.md",
    "plan_section": "### Sprint 1.1: Core Schema Validation Script",
    "plan_sprint_id": "1.1",
    "dev_agent_path": ".claude/agents/python-backend-dev",
    "dev_model": "sonnet",
    "dev_prompts": [
      "Create scripts/bead_schema.py with pydantic models",
      "Create scripts/validate-bead-schema.py CLI tool",
      "Create comprehensive test suite"
    ],
    "qa_agents": [
      {
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
    ]
  }
}
```

### Example 2: Parallel Sprints

**Input Plan Sections**:
```markdown
### Sprint 1.2a: Example Work Bead (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/1-2a-work-bead`
**Branch**: `feature/1-2a-work-bead`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)

---

### Sprint 1.2b: Example Merge Bead (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/1-2b-merge-bead`
**Branch**: `feature/1-2b-merge-bead`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)
```

**Output Dependencies**:
```json
{
  "bd-1-2a-work": {
    "dependencies": ["bd-1-1-schema"]
  },
  "bd-1-2b-merge": {
    "dependencies": ["bd-1-1-schema"]
  }
}
```

Note: Both parallel sprints depend on the previous sequential sprint (1.1), but have no dependency on each other.

### Example 3: Merge Sprint

**Input Plan Section**:
```markdown
### Sprint 1.3: Integration & Documentation

**Worktree**: `../beads-ralph-worktrees/feature/1-3-schema-integration`
**Branch**: `feature/1-3-schema-integration`
**Source Branch**: `develop` (after 1.2a and 1.2b merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)
- `python-backend-dev` (sonnet) - CI/CD setup

**Tasks**:
- Merge any conflicts from 1.2a and 1.2b
- Create `scripts/README.md` documenting validator usage
```

**Output Bead JSON** (excerpt):
```json
{
  "id": "bd-1-3-integration",
  "title": "Integration & Documentation",
  "status": "open",
  "issue_type": "beads-ralph-work",
  "dependencies": ["bd-1-2a-work", "bd-1-2b-merge"],
  "metadata": {
    "rig": "beads-ralph",
    "sprint": "1.3",
    "phase": "1",
    "plan_sprint_id": "1.3"
  }
}
```

Note: Sprint 1.3 depends on BOTH parallel sprints 1.2a and 1.2b completing.

## Constraints

- Read-only access to plan files (never modify plan markdown)
- Must generate valid bead JSON per `scripts/bead_schema.py` pydantic models
- All beads MUST include `"rig": "beads-ralph"` in metadata
- Dependencies must form a valid DAG (no circular dependencies)
- Sprint IDs must match regex patterns from schema.md
- Bead IDs must be unique across all generated beads
- QA agent output schemas must include `status` enum: `["pass", "fail", "stop"]`

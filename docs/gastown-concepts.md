# Gastown Architectural Concepts: Deep Dive

**Research Date**: 2026-02-08
**Gastown Version**: v0.5.0-329-g7cf6e82d
**Source Agent**: a5acc68 (gastown-concepts-researcher, opus model)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051
**Purpose**: Comprehensive analysis of gastown's key concepts for potential integration into beads-ralph
**Methodology**: Direct source code analysis with file paths and line numbers

---

**Agent Resurrection**: Use claude-history tool with agent ID `a5acc68` to:
- Ask questions about gastown concept analysis
- Clarify source code references
- Request deeper investigation of specific concepts

---

## Overview

Gastown's beads system introduces 7 core architectural concepts that provide sophisticated workflow orchestration. This document analyzes each concept from source code, evaluates relevance to beads-ralph MVP, and identifies integration opportunities.

**Key Terminology Note**: In gastown (and beads), "rig" is a synonym for "repository". This terminology is used consistently throughout the codebase.

---

## 1. Rig (Repository Identity)

### What It Is
A Rig is gastown's term for a repository. It represents a repo-specific context with its own worktrees, branches, and bead namespace. Rigs are identified by a unique prefix and maintain their own state tracking.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/internal/beads/beads_rig.go`**

```go
// RigFields (lines 11-15)
type RigFields struct {
    Prefix      string `json:"prefix"`       // Unique identifier (e.g., "gt" for gastown)
    WorktreeDir string `json:"worktree_dir"` // Base path for worktrees
    Remote      string `json:"remote"`       // Git remote URL
}
```

Key functions:
- `CreateRigBead()` (line 78) -- creates the initial rig registration bead
- Actor tracking via `BD_ACTOR` env var (line 91-95)
- GitLab MR URL construction from remote (line 139-172)

**File: `/Users/randlee/Documents/github/gastown/internal/beads/beads_rig_state.go`**

```go
// RigState (lines 18-22)
type RigState struct {
    Path          string `json:"path"`           // Filesystem path to repo
    DefaultBranch string `json:"default_branch"` // e.g., "main"
    SyncStatus    string `json:"sync_status"`    // "synced"|"behind"|"ahead"
}
```

- `NewRigState()` (line 28) -- validates path exists and is git repo
- `RigStateFromPath()` (line 58) -- extracts current branch, checks git status
- `findDefaultBranch()` (line 91) -- reads from `git symbolic-ref refs/remotes/origin/HEAD`

### Relevance to beads-ralph
**MVP Value: LOW.** Ralph operates on a single repository (beads-ralph itself), so the multi-rig coordination isn't needed for MVP. However, the `RigState` pattern is useful for validating repo state before sprint execution.

**Potential future use**: If ralph expands to orchestrate work across multiple repos, the rig concept provides a clean namespace and state management pattern.

---

## 2. Molecule (Composite Workflow with DAG)

### What It Is
A Molecule is a composite workflow where multiple beads (atoms) are bonded together with dependency relationships. Molecules support DAG-based execution with tier computation (parallel execution levels), cycle detection, and ready/blocked status propagation.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/internal/beads/molecule.go`**

```go
// MoleculeStep (lines 12-21)
type MoleculeStep struct {
    Ref          string        `json:"ref"`           // Unique step identifier
    Title        string        `json:"title"`
    Needs        []string      `json:"needs"`         // Dependencies (step refs)
    Tier         string        `json:"tier,omitempty"` // Agent model (haiku/sonnet/opus)
    Type         string        `json:"type,omitempty"` // "task"|"wait"
    Instructions string        `json:"instructions,omitempty"`
    // ... additional fields
}
```

Key functions:
- `ParseMoleculeSteps()` (line 67) -- extracts steps from formula TOML
- `InstantiateMolecule()` (line 267) -- creates root bead + child beads (atoms) with bonds
- `detectCycles()` (line 513) -- validates DAG is acyclic using DFS
- Metadata propagation: `parent.Metadata["beads_meta"]` (line 312) includes step info for each atom

**File: `/Users/randlee/Documents/github/gastown/internal/cmd/molecule_dag.go`**

```go
// DAGNode (lines 16-25)
type DAGNode struct {
    ID          string
    Title       string
    Needs       []string  // Dependencies
    Tier        int       // Execution tier (0 = no deps, 1+ = after deps)
    Status      string    // "ready"|"blocked"|"in_progress"|"done"
    IsCritical  bool      // On critical path (longest chain)
}

// DAGInfo (lines 28-36)
type DAGInfo struct {
    Nodes           []*DAGNode
    TotalTiers      int
    CriticalPath    []string
    ParallelGroups  map[int][]string  // tier -> node IDs
}
```

Key functions:
- `computeTiers()` (line 213) -- Kahn's algorithm for topological sort, assigns execution tiers
- `findCriticalPath()` (line 265) -- longest path through DAG for scheduling priority
- `computeReadyBlockedStatus()` (line 323) -- propagates status based on dependencies
- `printDAG()` (line 104) -- ASCII visualization with tree structure

### Relevance to beads-ralph
**MVP Value: HIGH.** This is directly applicable to ralph's sprint execution model:
- A sprint with dev-QA-retry loop IS a molecule workflow
- Dependencies between sprints (1.2a, 1.2b → 1.3) map to molecule bonds
- Tier computation enables parallel execution of independent sprints
- Ready/blocked status helps orchestrator decide what to schedule next
- The DAG validation prevents circular dependencies in the plan

**Key adaptation**: Ralph's unit of work is a sprint (entire dev-QA cycle), not individual steps within a sprint. The molecule pattern should model sprint-level dependencies, not the internal dev-QA loop.

---

## 3. Convoy (Batch Work / Phase Tracking)

### What It Is
A Convoy is a collection of related work items (issues/beads) that move through the workflow as a batch. Convoys auto-close when all tracked items complete, detect stranded work (ready items with no workers), and provide batch-level progress reporting.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/internal/cmd/convoy.go`**

Key types (extracted from function signatures):
- `ConvoyFields` -- includes `tracks` relation (list of issue IDs in the convoy)
- `ConvoyStatus` -- aggregated status (all closed? any stranded?)

Key functions:
- `findStrandedConvoys()` (line 42) -- scans for convoys with ready work but no workers
- `isReadyIssue()` (line 79) -- checks if issue is open + not blocked by dependencies
- `checkAndCloseCompletedConvoys()` (line 125) -- auto-closes convoy when all tracked issues are done
- Three-observer pattern (line 163-182): event-driven (real-time), witness (hourly check), patrol (daily sweep)

**File: `/Users/randlee/Documents/github/gastown/internal/cmd/event.go`**
- Event bus with observers (line 46-73): `EventPatrol`, `EventWitness`, `EventHandler`
- Convoy completion detection triggered on issue close events

### Relevance to beads-ralph
**MVP Value: MEDIUM.** Convoys provide phase-level organization:
- A phase (e.g., Phase 1) could be a convoy tracking all its sprints (1.1, 1.2a, 1.2b, 1.3)
- Auto-close when all sprints complete triggers phase transition
- Stranded detection (ready work with no workers) maps to ralph's orchestrator detecting idle agents
- The three-observer pattern (event, witness, patrol) provides redundancy for detecting completion
- Cross-rig tracking is not needed for MVP (single repo), but the `tracks` relation pattern is useful

---

## 4. Formula (Work Generator / Template)

### What It Is
A Formula is a TOML-format workflow template that generates molecules. Formulas define steps with dependencies, variable placeholders, and execution metadata. They follow a three-tier resolution hierarchy: project -> town -> system.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/.beads/formulas/shiny.formula.toml`**
```toml
# Canonical "shiny" workflow: design -> implement -> review -> test -> submit
name = "shiny"
description = "Standard feature workflow"
type = "workflow"

[vars]
feature = { required = true, description = "Feature name" }
assignee = { required = false, description = "Default assignee" }

[[steps]]
ref = "design"
title = "Design {{feature}}"
instructions = "Create design document for {{feature}}."

[[steps]]
ref = "implement"
title = "Implement {{feature}}"
instructions = "Implement based on the design."
needs = ["design"]

[[steps]]
ref = "review"
title = "Review {{feature}}"
needs = ["implement"]
# ... etc
```

**File: `/Users/randlee/Documents/github/gastown/.beads/formulas/mol-polecat-work.formula.toml`**
- Full polecat work lifecycle (10 steps): load-context -> branch-setup -> preflight-tests -> implement -> self-review -> run-tests -> commit-changes -> cleanup-workspace -> prepare-for-review -> submit-and-exit
- Self-cleaning model: last step pushes, creates MR, nukes sandbox, exits

**File: `/Users/randlee/Documents/github/gastown/.beads/formulas/mol-convoy-feed.formula.toml`**
- Convoy feeding pattern: load-convoy -> check-capacity -> dispatch-work -> report-results -> return-to-kennel
- Single-pass design: dispatch and exit, retry on next patrol cycle

**File: `/Users/randlee/Documents/github/gastown/internal/cmd/formula.go`**
- Formula management: list, show, run, create
- Three-tier search (resolution order):
  1. Project: `.beads/formulas/` in the rig
  2. Town: `~/gt/.beads/formulas/` (user-level)
  3. System: embedded in the binary
- `executeConvoyFormula()` -- creates convoy + leg beads + synthesis bead, dispatches via `gt sling`
- Formula types: `task`, `workflow`, `patrol`, `convoy`

**File: `/Users/randlee/Documents/github/gastown/docs/formula-resolution.md`**
- Extended format planned with semver, author, registry URI, capabilities
- Mol Mall integration for remote formula sharing

### Relevance to beads-ralph
**MVP Value: MEDIUM-HIGH.** Formulas could template ralph's sprint execution patterns:
- The `mol-polecat-work.formula.toml` maps closely to ralph's dev-QA cycle: setup-worktree -> implement -> test -> review -> submit
- Variable substitution (`{{feature}}`) maps to sprint-specific values (branch name, phase, sprint ID)
- Three-tier resolution provides a clean way to override default workflows per-project
- TOML format is simpler than ralph's current plan markdown for defining execution steps
- The `convoy-feed` pattern maps to ralph's orchestrator dispatching work to agents

---

## 5. Wisp (Ephemeral Bead with TTL)

### What It Is
A Wisp is an ephemeral bead (issue) that is not synced to the persistent git JSONL store. Wisps are used for operational workflows, patrol cycles, and temporary coordination that shouldn't accumulate as permanent records. They have garbage collection with a configurable threshold.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/internal/beads/beads.go`**
- `CreateOptions` has `Ephemeral bool` field for creating wisps
- The `Issue` struct includes `Ephemeral bool` in its JSON representation

**File: `/Users/randlee/Documents/github/gastown/internal/doctor/wisp_check.go`**

```go
// WispGCCheck (lines 18-22)
type WispGCCheck struct {
    FixableCheck
    threshold     time.Duration           // 1 hour default
    abandonedRigs map[string]int          // rig -> count of abandoned wisps
}
```

- `NewWispGCCheck()` (line 25) -- creates with 1-hour threshold
- `countAbandonedWisps()` (line 92) -- scans `issues.jsonl` for `Wisp: true` + not closed + older than threshold
- `Fix()` (line 132) -- runs `bd mol wisp gc` per rig with abandoned wisps
- GC criteria (line 123): `issue.Wisp && issue.Status != "closed" && !issue.UpdatedAt.IsZero() && issue.UpdatedAt.Before(cutoff)`

**File: `/Users/randlee/Documents/github/gastown/internal/cmd/gate.go`**
- Wake messages are sent as wisps (line 158): `Wisp: true` -- auto-cleanup after reading

**File: `/Users/randlee/Documents/github/gastown/docs/concepts/molecules.md`**
- Wisp vs Molecule decision criteria: Is audit trail needed? Is this a repeating cycle? Is there a discrete deliverable?

### Relevance to beads-ralph
**MVP Value: LOW-MEDIUM.** Wisps could be useful for:
- Failed QA retry attempts (don't pollute the permanent record)
- Temporary orchestrator coordination beads
- Agent heartbeat/status beads that auto-expire
- However, for MVP, ralph can simply close/archive failed attempts rather than implementing a separate ephemeral system

---

## 6. Slot (Resource Lock / Merge Queue)

### What It Is
A Slot is a mutex/lock mechanism implemented as a bead for serialized conflict resolution. The primary use case is a merge queue where only one agent at a time can merge to a target branch, preventing merge conflicts.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/internal/beads/beads_merge_slot.go`**

```go
// MergeSlotStatus (lines 11-17)
type MergeSlotStatus struct {
    ID        string   `json:"id"`
    Available bool     `json:"available"`
    Holder    string   `json:"holder,omitempty"`
    Waiters   []string `json:"waiters,omitempty"`
    Error     string   `json:"error,omitempty"`
}
```

Key functions:
- `MergeSlotCreate()` (line 22) -- creates the slot bead via `bd merge-slot create --json`
- `MergeSlotCheck()` (line 41) -- checks availability, returns holder and waiters
- `MergeSlotAcquire()` (line 63) -- acquires exclusive access; `--wait` flag adds requester to waiter queue if held
- `MergeSlotRelease()` (line 92) -- releases with holder verification (only the holder can release)
- `MergeSlotEnsureExists()` (line 120) -- idempotent create-if-not-exists

### Relevance to beads-ralph
**MVP Value: HIGH.** This is directly applicable to ralph's merge queue challenge:
- Multiple agents working in parallel worktrees will need to merge to `develop`
- Without serialization, merge conflicts are likely when agents finish simultaneously
- The acquire/release pattern with waiters queue provides exactly the coordination needed
- Holder verification prevents accidental releases
- The `--wait` flag means agents can queue up rather than spin-polling
- beads-ralph's orchestrator could manage the slot, granting merge access to one agent at a time

---

## 7. Gate (Synchronization Barrier)

### What It Is
A Gate is an async coordination primitive. It represents a condition that must be satisfied before waiting agents can proceed. Gates support multiple types (timer, GitHub Actions run, human approval, mail notification) and maintain a list of waiters who are notified when the gate closes.

### Source Code Structure

**File: `/Users/randlee/Documents/github/gastown/internal/cmd/gate.go`**

Gate types (from help text, line 28): `timer`, `gh:run`, `human`, `mail`

```go
// GateWakeResult (lines 76-82)
type GateWakeResult struct {
    GateID      string   `json:"gate_id"`
    CloseReason string   `json:"close_reason"`
    Waiters     []string `json:"waiters"`
    Notified    []string `json:"notified"`
    Failed      []string `json:"failed,omitempty"`
}
```

- Gate info structure (lines 94-99): `ID`, `Status`, `CloseReason`, `Waiters`
- `runGateWake()` (line 84) -- sends wake mail to all waiters after gate closes
- Wake messages sent as wisps (line 158) with high priority
- Mail routing via town's mail system (line 136): `mail.NewRouter(townRoot)`
- Gate commands in `bd` CLI: create, show, list, close, approve, eval
- `bd gate eval` -- evaluates and closes elapsed gates (used by Deacon patrol)

### Relevance to beads-ralph
**MVP Value: MEDIUM.** Gates could coordinate ralph's parallel execution:
- A `gh:run` gate could wait for CI/CD pipeline completion before proceeding
- A `human` gate could pause execution pending human review of a PR
- Sprint dependencies could be modeled as gates: Sprint 1.2 waits on gate that closes when 1.1 completes
- The waiter notification pattern avoids polling (agents park and get woken)
- However, for MVP, ralph's orchestrator can manage dependencies directly through its Go loop without the full gate abstraction

---

## Cross-Cutting Patterns

### GUPP Principle
"If it's on your hook, you must run it" -- from `/Users/randlee/Documents/github/github-research/gastown/architecture.md`. Agents are assigned work via a hook mechanism and are expected to execute autonomously. This aligns with ralph's dev/QA agent model.

### Two-Level Beads Architecture
From `/Users/randlee/Documents/github/gastown/internal/beads/beads.go`:
- Town-level beads (`hq-*`) -- cross-project coordination (convoys, slots)
- Rig-level beads (`<prefix>-*`) -- project-specific work items

Ralph operates at a single level (one repo), but could adopt the prefix pattern for namespacing phases/sprints.

### Mail System for Agent Communication
From `/Users/randlee/Documents/github/gastown/internal/cmd/gate.go` and convoy lifecycle:
- Agents communicate via a file-based mail system
- Messages have types (notification, request, response) and priorities
- Wisp flag on messages enables auto-cleanup

Ralph's agent-teams feature provides inter-agent communication, but a structured mail/notification pattern could improve coordination.

### Provenance Tracking
From `/Users/randlee/Documents/github/gastown/internal/beads/beads_rig.go` (line 91):
- `BD_ACTOR` env var tracks who created/modified beads
- `instantiated_from` and `template_step` metadata in molecule steps (molecule.go lines 312, 405)

Ralph should track which agent created/modified each bead for audit trail.

---

## Summary: Priority Ranking for beads-ralph MVP

| Concept | MVP Priority | Rationale |
|---------|-------------|-----------|
| **Molecule** | HIGH | Sprint execution IS a molecule workflow. DAG deps, tiers, ready/blocked status all directly applicable. |
| **Slot** | HIGH | Merge queue serialization is critical for parallel worktree agents. Acquire/release with waiters solves this cleanly. |
| **Formula** | MEDIUM-HIGH | TOML templates could standardize sprint execution patterns. The polecat-work formula maps to dev-QA cycle. |
| **Convoy** | MEDIUM | Phase-level batch tracking with auto-close. Stranded detection useful for idle agent management. |
| **Gate** | MEDIUM | CI/CD wait, human review pause, sprint dependencies. Useful but orchestrator can handle most cases in MVP. |
| **Wisp** | LOW-MEDIUM | Ephemeral beads for retries and temp coordination. Nice-to-have; can use close/archive for MVP. |
| **Rig** | LOW | Single-repo operation for MVP. Only the State pattern is useful. |

---

## Key Source Files Referenced

| File | Lines | Concept | Key Structures/Functions |
|------|-------|---------|--------------------------|
| `/Users/randlee/Documents/github/gastown/internal/beads/molecule.go` | 12-21, 67, 267, 513 | Molecule | MoleculeStep, ParseMoleculeSteps, InstantiateMolecule, detectCycles |
| `/Users/randlee/Documents/github/gastown/internal/cmd/molecule_dag.go` | 16-36, 213, 265, 323 | Molecule DAG | DAGNode, DAGInfo, computeTiers, findCriticalPath |
| `/Users/randlee/Documents/github/gastown/internal/beads/beads_merge_slot.go` | 11-17, 22, 41, 63, 92, 120 | Slot | MergeSlotStatus, Create, Check, Acquire, Release |
| `/Users/randlee/Documents/github/gastown/.beads/formulas/mol-polecat-work.formula.toml` | Full file | Formula | 10-step polecat workflow |
| `/Users/randlee/Documents/github/gastown/.beads/formulas/shiny.formula.toml` | Full file | Formula | Standard feature workflow |
| `/Users/randlee/Documents/github/gastown/internal/cmd/formula.go` | Various | Formula | Three-tier resolution, executeConvoyFormula |
| `/Users/randlee/Documents/github/gastown/internal/cmd/convoy.go` | 42, 79, 125, 163-182 | Convoy | findStrandedConvoys, checkAndCloseCompletedConvoys |
| `/Users/randlee/Documents/github/gastown/internal/cmd/gate.go` | 28, 76-82, 84, 158 | Gate | GateWakeResult, runGateWake, wisp messages |
| `/Users/randlee/Documents/github/gastown/internal/doctor/wisp_check.go` | 18-22, 25, 92, 132 | Wisp | WispGCCheck, countAbandonedWisps, Fix |
| `/Users/randlee/Documents/github/gastown/internal/beads/beads_rig.go` | 11-15, 78, 91-95 | Rig | RigFields, CreateRigBead, BD_ACTOR |
| `/Users/randlee/Documents/github/gastown/internal/beads/beads_rig_state.go` | 18-22, 28, 58, 91 | Rig State | RigState, NewRigState, findDefaultBranch |

---

**Document Version**: 1.0
**Last Updated**: 2026-02-08
**Next Steps**: Review integration proposals in `gastown-integration-proposal.md`

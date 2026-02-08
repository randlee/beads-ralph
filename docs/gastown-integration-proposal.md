# Gastown Integration Proposals for beads-ralph

**Research Date**: 2026-02-08
**Gastown Version**: v0.5.0-329-g7cf6e82d
**Source Agent**: a5acc68 (gastown-concepts-researcher, opus model)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051
**Status**: Ready for implementation planning

---

**Agent Resurrection**: Use claude-history tool with agent ID `a5acc68` to:
- Discuss specific integration proposals
- Clarify implementation details
- Explore alternative integration approaches

---

## Executive Summary

After comprehensive source code analysis of gastown, 7 key concepts were evaluated for integration into beads-ralph MVP. **Priority rankings** based on immediate value and implementation complexity:

| Priority | Concept | Value Proposition | Complexity |
|----------|---------|-------------------|------------|
| **HIGH** | Merge Slot | Worktree serialization for parallel agents | Low |
| **HIGH** | Molecule | Sprint as DAG with tier computation | Medium |
| **MEDIUM-HIGH** | Formula | TOML templates for sprint execution | Medium |
| **MEDIUM** | Convoy | Phase-level batch tracking | Low |
| **MEDIUM** | Gate | CI/CD and review wait coordination | Medium |
| **MEDIUM** | Agent Provenance | BD_ACTOR pattern for audit trail | Low |
| **LOW-MEDIUM** | Wisp | Ephemeral beads for failed retries | Low |

---

## Proposal 1: Merge Slot for Worktree Serialization (HIGH PRIORITY)

### Problem
Multiple parallel sprints may attempt to merge to the same target branch simultaneously, causing git conflicts and race conditions.

### Gastown Solution
**Source**: `/Users/randlee/Documents/github/gastown/internal/beads/beads_merge_slot.go`

Slots implement an acquire/release mutex pattern:
- Only one bead can hold a slot at a time
- Waiting beads queue up with waiter list
- Automatic release on merge completion or failure

### How Merge Slot Works (Detailed Explanation)

**Scenario**: 10 parallel worktrees finish simultaneously and want to merge to integration branch.

**Without Merge Slot**:
```
Agent 1: git merge feature/1-1 → CONFLICT
Agent 2: git merge feature/1-2 → CONFLICT
Agent 3: git merge feature/1-3 → CONFLICT
... chaos ensues ...
```

**With Merge Slot**:
```
1. Agent 1 calls MergeSlotAcquire("slot-integration")
   → Slot available: granted to Agent 1
   → Slot.holder = "bd-sprint-1-1"
   → Slot.waiters = []

2. Agent 2 calls MergeSlotAcquire("slot-integration", --wait)
   → Slot held by Agent 1: added to queue
   → Slot.holder = "bd-sprint-1-1"
   → Slot.waiters = ["bd-sprint-1-2"]

3. Agent 3-10 call MergeSlotAcquire("slot-integration", --wait)
   → All added to waiters queue in order
   → Slot.waiters = ["bd-sprint-1-2", "bd-sprint-1-3", ..., "bd-sprint-1-10"]

4. Agent 1 completes merge, calls MergeSlotRelease()
   → Verifies holder (only holder can release)
   → Slot.holder = null
   → Notifies first waiter (Agent 2): "slot available"

5. Agent 2 auto-acquires when notified
   → Slot.holder = "bd-sprint-1-2"
   → Slot.waiters = ["bd-sprint-1-3", ..., "bd-sprint-1-10"]

6. Process repeats until all 10 agents have merged serially
```

**Key Implementation Details**:
- **Holder Verification**: Only the agent that acquired the slot can release it (prevents accidental releases)
- **Waiter Queue**: FIFO ordering ensures fairness
- **Auto-wake**: When slot releases, first waiter is notified (no polling needed)
- **Timeout Protection**: If holder crashes, slot auto-releases after timeout (e.g., 5 minutes)

### Proposal for beads-ralph

**Implementation**:
1. Create `issue_type: "beads-ralph-merge-slot"`
2. One slot per target branch (e.g., `slot-<integration-branch>`, `slot-main`)
3. Scrum-master acquires slot before merge sprint execution
4. Release slot after PR merge or failure

**Metadata Schema Addition**:
```yaml
metadata:
  slot_id: "slot-<integration-branch>"  # Generic for any branch (develop, integration, main)
  holder: "bd-sprint-1-3"               # Current merge bead holding the slot
  waiters: ["bd-sprint-2-3", "bd-sprint-3-3"]  # Queue of waiting merge beads
  acquired_at: "2026-02-08T14:00:00Z"   # Timestamp for timeout detection
  timeout_seconds: 300                  # Auto-release after 5 minutes if holder doesn't release
```

**Integration Branch Flexibility**:
- Supports git-flow: `slot-develop`, `slot-main`
- Supports integration worktree: `slot-integration-branch-name`
- Supports custom workflows: any branch name can have a slot

**Benefits**:
- Prevents concurrent merge conflicts
- Serializes PR queue naturally
- Low complexity, high value
- Works with any branch naming convention
- Handles large-scale parallelism (10+ worktrees)

**Recommendation**: **Implement in Phase 2** (after MVP demonstrates basic merge workflow)

---

## Proposal 2: Sprint as Molecule with DAG Dependencies (HIGH PRIORITY)

### Problem
Current plan uses flat dependency lists. Complex sprints with internal sub-tasks need structured coordination.

### Gastown Solution
**Source**: `/Users/randlee/Documents/github/gastown/internal/beads/molecule.go`

Molecules are composite workflows with:
- Root bead (molecule ID)
- Child beads (bonded atoms)
- DAG-based dependency resolution (Kahn's algorithm)
- Tier computation for parallel execution
- Ready/blocked status propagation

### Proposal for beads-ralph

**Use Case**: Multi-agent sprints like Sprint 2.3 (architect + writer working together)

**Implementation**:
1. Create molecule bead as sprint container
2. Each agent gets a child bead (atom) within molecule
3. Dependencies define execution order
4. Scrum-master launches agents in tier order

**Example**: Sprint 2.3 as Molecule
```yaml
# Molecule root
id: mol-sprint-2-3
issue_type: beads-ralph-molecule
title: "Sprint 2.3: Beads Architect Integration"

metadata:
  mol_type: molecule
  atoms: ["bd-architect-work", "bd-writer-work"]
  dependencies:
    bd-architect-work: []  # Tier 0 (runs first)
    bd-writer-work: ["bd-architect-work"]  # Tier 1 (waits for architect)

# Atom 1
id: bd-architect-work
issue_type: beads-ralph-work
metadata:
  molecule_id: mol-sprint-2-3
  dev_agent_path: ".claude/agents/planning-architect.md"

# Atom 2
id: bd-writer-work
issue_type: beads-ralph-work
metadata:
  molecule_id: mol-sprint-2-3
  dev_agent_path: ".claude/agents/markdown-doc-writer.md"
  depends_on: ["bd-architect-work"]
```

**Benefits**:
- Natural agent-team representation
- Structured parallel + sequential work
- Clear dependency visualization
- Shared QA after all atoms complete

**Recommendation**: **Implement in Phase 3** (after agent-teams are validated)

---

## Proposal 3: Formula Templates for Sprint Execution (MEDIUM-HIGH PRIORITY)

### Problem
Sprints have repetitive structure. Manual bead creation is tedious and error-prone.

### Gastown Solution
**Source**: `.beads/formulas/*.formula.toml`

Formulas are TOML templates with:
- Variable substitution (`{{var}}`)
- Multi-step workflows
- Predefined dev/QA agent configurations

**Example Formula**:
```toml
[formula]
name = "standard-sprint"
description = "Standard beads-ralph sprint with dev-QA loop"

[variables]
phase = {type = "string", description = "Phase number"}
sprint = {type = "string", description = "Sprint number"}
sprint_name = {type = "string", description = "Human-readable name"}
dev_agent = {type = "string", description = "Dev agent path"}

[steps]
[steps.create_bead]
title = "Sprint {{phase}}.{{sprint}}: {{sprint_name}}"
worktree_path = "../beads-ralph-worktrees/feature/{{phase}}-{{sprint}}-{{slug}}"
branch_name = "feature/{{phase}}-{{sprint}}-{{slug}}"
dev_agent_path = "{{dev_agent}}"
```

### Proposal for beads-ralph

**Use Case**: Beads-architect agent generates beads from plan markdown using formulas

**Implementation**:
1. Create `.beads-ralph/formulas/` directory
2. Define formula templates for:
   - `standard-sprint.formula.toml`
   - `parallel-sprint.formula.toml`
   - `merge-sprint.formula.toml`
3. Beads-architect agent:
   - Parses plan markdown
   - Selects appropriate formula
   - Substitutes variables
   - Creates bead JSON

**Benefits**:
- DRY principle for sprint creation
- Standardized structure
- Easy to modify patterns

**Recommendation**: **Implement in Phase 2** (Sprint 2.1-2.3, during beads-architect development)

---

## Proposal 4: Convoy-Style Phase Tracking (MEDIUM PRIORITY)

### Problem
Need visibility into phase-level progress. Hard to answer "How is Phase 1 going?"

### Gastown Solution
**Source**: `/Users/randlee/Documents/github/gastown/internal/cmd/convoy.go`

Convoys are batch trackers:
- One convoy bead per batch
- Auto-closes when all members complete
- Detects stranded work (incomplete after most finish)

### Proposal for beads-ralph

**Use Case**: Phase-level progress tracking

**Implementation**:
```yaml
id: convoy-phase-1
issue_type: beads-ralph-convoy
title: "Phase 1: Schema & Validation"
metadata:
  convoy_members: ["bd-1-1", "bd-1-2a", "bd-1-2b", "bd-1-3"]
  convoy_status: "3/4 complete"
  stranded: []  # Empty = all progressing normally
```

**Benefits**:
- Phase completion visibility
- Stranded work detection
- Batch operations (e.g., "close Phase 1")

**Recommendation**: **Implement in Phase 4** (nice-to-have for reporting)

---

## Proposal 5: Gate for CI/CD and Review Waits (MEDIUM PRIORITY)

### Problem
Merge sprints must wait for parallel sprints to complete. Currently handled via dependencies, but lacks async coordination.

### Gastown Solution
**Source**: `/Users/randlee/Documents/github/gastown/internal/cmd/gate.go`

Gates are synchronization barriers:
- Define required beads
- Waiting beads block until gate opens
- Notification mechanism when ready

### Proposal for beads-ralph

**Use Case 1**: Merge sprint coordination
```yaml
id: gate-before-1-3
issue_type: beads-ralph-gate
metadata:
  required: ["bd-1-2a", "bd-1-2b"]
  waiting: ["bd-1-3"]
  status: "open"  # Opens when bd-1-2a and bd-1-2b both closed
```

**Use Case 2**: CI/CD wait
```yaml
id: gate-ci-checks-pass
metadata:
  required: ["ci-check-tests", "ci-check-lint", "ci-check-security"]
  waiting: ["bd-merge-to-main"]
```

**Benefits**:
- Explicit sync points
- Async coordination
- Notification on gate open

**Recommendation**: **Implement in Phase 5** (after basic parallel execution works)

---

## Proposal 6: Agent Provenance Tracking (MEDIUM PRIORITY)

### Problem
Need audit trail showing which agent did what work, with ability to resurrect agents for follow-up.

### Gastown Solution
**Source**: Throughout gastown codebase, `BD_ACTOR` environment variable

Pattern:
```bash
export BD_ACTOR="agent:polecat-main"
bd update bd-abc123 --status closed
# Bead automatically records actor in metadata
```

### beads-ralph Requirement
**CRITICAL**: Every agent that executes work in the ralph loop MUST have its agent_id tracked.

**Purpose**:
- Enable agent resurrection via claude-history tool
- Question agents about their work after execution
- Complete tasks that were not finished in initial run
- Full audit trail of who did what

### Proposal for beads-ralph

**Implementation**:
1. Track both `agent_id` (unique instance) and `agent_name` (role/type)
2. Record in dev_executions and qa_executions arrays
3. Enable claude-history tool integration for agent resurrection

**Schema (Already Added)**:
```yaml
execution_tracking:
  dev_executions:
    - agent_id: "a5acc68"           # Unique instance ID (for resurrection)
      agent_name: "python-backend-dev"  # Role/type name
      attempt: 1
      started_at: "2026-02-08T14:00:00Z"
      completed_at: "2026-02-08T14:45:00Z"
      status: "success"
      commit_hash: "abc123def456"

  qa_executions:
    - agent_id: "a177a45"           # Unique instance ID (for resurrection)
      agent_name: "qa-python-tests"     # Role/type name
      attempt: 1
      started_at: "2026-02-08T14:45:00Z"
      completed_at: "2026-02-08T14:50:00Z"
      status: "pass"
      feedback: null
```

**Benefits**:
- Complete audit trail with agent instance tracking
- Agent resurrection capability via claude-history tool
- Actor accountability
- Debugging support
- Follow-up task completion

**Recommendation**: **Implement in Phase 1** (REQUIRED field, already added to schema)

---

## Proposal 7: Wisp for Failed Retry Cleanup (LOW-MEDIUM PRIORITY)

### Problem
Failed QA attempts create temporary work. Need automatic cleanup to avoid bead clutter.

### Gastown Solution
**Source**: `/Users/randlee/Documents/github/gastown/internal/doctor/wisp_check.go`

Wisps are ephemeral beads:
- `wisp_type` field (e.g., "experiment", "temp")
- TTL-based auto-close
- Garbage collection by doctor process

### Proposal for beads-ralph

**Use Case**: Mark retry attempt beads as wisps with 7-day TTL

**Implementation**:
```yaml
id: bd-retry-attempt-2
issue_type: beads-ralph-work
metadata:
  wisp_type: "retry_attempt"
  ttl: "7d"
  original_bead: "bd-1-1"
  attempt: 2
```

**Benefits**:
- Automatic cleanup
- Audit trail preserved for 7 days
- Reduced bead clutter

**Recommendation**: **Implement post-MVP** (nice-to-have, not critical)

---

## Implementation Roadmap

### Phase 1 (Current - Schema Validation)
- [x] **Agent Provenance**: agent_id tracking REQUIRED in schema (already added)

### Phase 2 (Post-MVP, Priority Integrations)
- [ ] **Merge Slot**: Prevent concurrent merge conflicts
- [ ] **Formula Templates**: Beads-architect uses formulas to generate beads

### Phase 3 (Agent-Team Support)
- [ ] **Molecule**: Multi-agent sprints as composite workflows
- [ ] **DAG Dependencies**: Tier-based execution order

### Phase 4 (Batch Operations)
- [ ] **Convoy**: Phase-level progress tracking

### Phase 5 (Advanced Coordination)
- [ ] **Gate**: Explicit synchronization barriers for merge/CI waits

### Post-MVP (Nice-to-Have)
- [ ] **Wisp**: Ephemeral beads for cleanup

---

## Schema Updates Required

### Add to `metadata` field:
```yaml
# For all beads
rig: "beads-ralph"  # ALREADY ADDED
provenance: []  # Actor tracking

# For molecule beads
mol_type: "molecule|atom"
molecule_id: "mol-sprint-X-Y"
atoms: ["bd-1", "bd-2"]

# For merge beads
slot_id: "slot-develop"

# For convoy beads
convoy_id: "convoy-phase-X"
convoy_members: ["bd-1", "bd-2"]

# For gate beads
required: ["bd-1", "bd-2"]
waiting: ["bd-3"]

# For wisp beads
wisp_type: "retry_attempt|experiment"
ttl: "7d"
```

---

## Conclusion

**High-value, low-complexity wins for immediate implementation:**
1. Merge Slot (prevents conflicts)
2. Agent Provenance (audit trail)
3. Formula Templates (DRY sprint creation)

**Defer to later phases:**
- Molecule (wait for agent-team validation)
- Convoy (nice reporting feature, not critical)
- Gate (overkill for MVP, dependencies work fine)
- Wisp (cleanup can be manual for now)

**Recommendation**: Incorporate Merge Slot, Agent Provenance, and Formula Templates into implementation plan Phase 2.

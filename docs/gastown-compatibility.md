# Gastown Compatibility Design

**Version**: 1.0.0
**Last Updated**: 2026-02-09
**Status**: Design Document

---

## Overview

This document defines how beads-ralph aligns with gastown's agent orchestration patterns to enable cross-system compatibility and potential integration.

**Goal**: AgentSpec should be portable between beads-ralph and gastown, allowing beads-ralph agents to run as gastown polecats/witnesses, and vice versa.

---

## Core Concepts

### Role vs Agent Distinction

**Role** (gastown): System-level orchestration function
- Defines lifecycle (ephemeral vs persistent)
- Defines spawn mechanism (tmux session pattern)
- Defines cleanup behavior
- Defines health monitoring

**Agent** (beads-ralph): Behavior implementation
- Defines instructions/prompt (markdown file)
- Defines tool usage patterns
- Defines communication style
- Defines domain expertise

**Key Insight**: Role determines HOW an agent runs in the system, Agent determines WHAT it does.

---

## Role Mapping

### beads-ralph Functions → gastown Roles

| beads-ralph Function | gastown Role | Lifecycle | Agent File | Rationale |
|---------------------|--------------|-----------|------------|-----------|
| **Scrum-master** | `polecat` | Ephemeral | `beads-ralph-scrum-master.md` | Orchestrates one sprint, self-terminates when PR created |
| **Dev agent** | `polecat` | Ephemeral | `backend-dev.md`, `frontend-dev.md`, etc. | Executes work for one bead, exits when done |
| **QA agent** | `polecat` | Ephemeral | `qa-go-tests.md`, `qa-security-scan.md`, etc. | Validates work for one bead, returns pass/fail/stop |
| **Merge specialist** | `polecat` | Ephemeral | `merge-specialist.md` | Resolves conflicts for one merge bead, exits when done |
| **Scribe** | `witness` | Persistent | `beads-scribe.md` | Monitors beads, maintains record-keeping (plan annotation, GitHub sync) |
| **Ralph loop** | `mayor` | Persistent | `ralph-coordinator.md` | Coordinates all sprints, dispatches work to scrum-masters |

**Pattern**:
- **Single-task workers** → polecat (ephemeral)
- **Monitoring/coordination** → witness (persistent)
- **Top-level orchestration** → mayor (persistent)

---

## AgentSpec (Portable Schema)

### Type Definition

```go
type AgentSpec struct {
    // Role: System integration pattern (gastown compatibility)
    Role   string `json:"role" yaml:"role"`  // "polecat", "witness", "mayor"

    // Agent: Behavior implementation (prompt file)
    Agent  string `json:"agent" yaml:"agent"` // ".claude/agents/scrum-master.md"

    // Model selection (follows 4-level resolution priority)
    Model  string `json:"model,omitempty" yaml:"model,omitempty"` // "opus", "sonnet", "haiku"

    // Execution configuration (use system defaults if empty)
    Executable string   `json:"executable,omitempty" yaml:"executable,omitempty"` // "claude"
    Options    []string `json:"options,omitempty" yaml:"options,omitempty"`       // CLI flags

    // Context & resurrection
    Context string `json:"context,omitempty" yaml:"context,omitempty"`   // Human-readable context
    AgentID string `json:"agent_id,omitempty" yaml:"agent_id,omitempty"` // For session resume

    // Environment variables
    Env map[string]string `json:"env,omitempty" yaml:"env,omitempty"` // Additional env vars
}
```

**Design Principles**:
- **Minimal required fields**: Only `role` and `agent` are required
- **System defaults**: Executable, options, model use system defaults if omitted
- **YAML and JSON serializable**: Works in config files and APIs
- **Resolution priority**: Bead → Agent frontmatter → System config → Hardcoded default

---

## Model Resolution Priority

Both beads-ralph and gastown follow same priority:

```
1. AgentSpec.Model (explicit override)          ← In bead/work item metadata
   ↓ if empty
2. Agent YAML frontmatter (recommended_model)   ← In agent .md file
   ↓ if empty
3. System config (default_model)                ← In beads-ralph.yaml or gastown settings
   ↓ if empty
4. Hardcoded: "sonnet"                          ← Universal fallback
```

**Example**:
```yaml
# Agent frontmatter: .claude/agents/backend-dev.md
---
name: backend-dev
recommended_model: sonnet  # Used if bead doesn't specify
---
```

```json
// Bead metadata (runtime override)
{
  "dev_agents": [{
    "agent": ".claude/agents/backend-dev.md",
    "model": "opus"  // ← WINS (complex sprint needs opus)
  }]
}
```

---

## Command Building (Unified)

Both systems can use same logic to build agent launch command:

```go
func BuildAgentCommand(spec AgentSpec, systemDefaults Config) []string {
    // 1. Resolve executable
    executable := spec.Executable
    if executable == "" {
        executable = systemDefaults.DefaultExecutable // "claude"
    }

    // 2. Resolve model
    model := resolveModel(spec, systemDefaults) // 4-level priority

    // 3. Resolve options
    options := spec.Options
    if len(options) == 0 {
        options = systemDefaults.DefaultOptions
    }

    // 4. Build command
    cmd := []string{executable}

    // Add model flag
    if model != "" {
        cmd = append(cmd, "--model", model)
    }

    // Add options
    cmd = append(cmd, options...)

    // Add agent flag
    cmd = append(cmd, "--agent", spec.Agent)

    return cmd
}
```

**Result**: `["claude", "--model", "sonnet", "--dangerously-skip-permissions", "--agent", ".claude/agents/scrum-master.md"]`

---

## JSON Output Requirement (beads-ralph Deviation)

### Requirement

**All polecats in beads-ralph MUST return fenced JSON output** with structured results.

**Enforcement Methods**:

#### Option A: JSON Output Flag (Recommended)
Use Claude's `--output-format json` flag to enforce JSON response:

```bash
claude --model sonnet \
       --dangerously-skip-permissions \
       --output-format json \
       --agent .claude/agents/beads-ralph-scrum-master.md
```

**Pros**:
- ✅ Claude enforces JSON format automatically
- ✅ No resurrection logic needed
- ✅ Cleaner implementation

**Cons**:
- ⚠️ Requires Claude Code support for `--output-format json` flag

#### Option B: Resurrection on Invalid Output
If agent doesn't return fenced JSON, resurrect and retry:

```go
func runScrumMaster(ctx context.Context, bead Bead, config Config) ScrumResult {
    output := executeAgent(ctx, bead, config)

    // Try to parse JSON output
    result, err := parseJSONOutput(output)
    if err != nil {
        // No valid JSON - resurrect agent and retry
        log.Warnf("Agent %s didn't return JSON, resurrecting with JSON requirement", bead.ID)

        output = resurrectAgentWithJSONRequirement(ctx, bead, config)
        result, err = parseJSONOutput(output)

        if err != nil {
            return ScrumResult{
                Success: false,
                Fatal:   true,
                Error:   "Agent failed to return valid JSON after resurrection",
            }
        }
    }

    return result
}
```

**Pros**:
- ✅ Works even if `--output-format json` isn't available
- ✅ Self-correcting

**Cons**:
- ❌ More complex
- ❌ Wastes resources on failed attempts

**Recommendation**: Use **Option A** (`--output-format json`) if available, fallback to **Option B** if needed.

### Expected JSON Schema (ScrumResult)

```json
{
  "bead_id": "bd-abc123",
  "success": true,
  "pr_url": "https://github.com/user/repo/pull/42",
  "pr_number": 42,
  "bead_updated": true,
  "attempt_count": 2,
  "qa_results": [
    {
      "agent_path": ".claude/agents/qa-unit-tests.md",
      "status": "pass",
      "message": "All tests passed. Coverage: 85%",
      "details": {"total": 42, "passed": 42, "coverage_percent": 85}
    }
  ],
  "error": null,
  "fatal": false
}
```

**Note**: gastown polecats typically don't return structured JSON (they work via molecules and mail). This is a **beads-ralph-specific deviation** to enable programmatic result processing.

---

## State Tracking Comparison

### gastown: AgentFields (Full State Tracking)

```go
type AgentFields struct {
    RoleType          string  // polecat, witness, mayor
    Rig               string  // Repository name
    AgentState        string  // spawning, working, done, stuck
    HookBead          string  // Currently assigned work
    CleanupStatus     string  // Git state: clean, has_uncommitted, etc.
    ActiveMR          string  // Active merge request
    NotificationLevel string  // Communication preferences
}
```

**Storage**: Agent bead (special issue type in beads database)
**Mutability**: Changes during agent lifecycle
**Use case**: Long-lived agents, crash recovery, health monitoring

### beads-ralph: Minimal Tracking (MVP)

**In-memory tracking** (during execution):
```go
type RunningAgent struct {
    SessionID  string    // Process/tmux ID
    BeadID     string    // Which bead it's working on
    StartTime  time.Time // For timeout detection
    AgentSpec  AgentSpec // Launch config
}
```

**Persistent tracking** (after completion):
- Stored in bead metadata as `scrum_result`
- Includes: PR URL, attempt count, QA results, timestamps

**Rationale**: beads-ralph MVP uses ephemeral agents that self-report results. No need for persistent agent beads in Phase 4-6.

**Post-MVP**: Can adopt gastown's AgentFields if needed for:
- Long-lived agents (persistent Ralph coordinator, witnesses)
- Distributed execution (multiple Ralph instances)
- Advanced observability (agent health dashboards)

---

## Integration Examples

### beads-ralph Bead → gastown Polecat

**beads-ralph bead metadata**:
```json
{
  "id": "bd-sprint-4-2b",
  "title": "Sprint 4.2b: Configuration System",
  "team_name": "sprint-4-2-parallel",
  "scrum_master_agent": {
    "role": "polecat",
    "agent": ".claude/agents/beads-ralph-scrum-master.md",
    "model": "sonnet",
    "context": "Sprint 4.2b - YAML config system"
  }
}
```

**gastown execution**:
```bash
# Spawn polecat in gastown
gt sling bd-sprint-4-2b beads-ralph \
  --agent=".claude/agents/beads-ralph-scrum-master.md" \
  --model="sonnet"

# Creates:
# - Tmux session: gt-beads-ralph-polecat-ConfigWorker
# - Worktree: ~/gt/beads-ralph/polecats/ConfigWorker/
# - Agent bead: gt-beads-ralph-polecat-ConfigWorker
# - Environment: GT_ROLE=polecat, GT_RIG=beads-ralph
```

### gastown Agent → beads-ralph Ralph Loop

**gastown agent** (adapted for beads-ralph):
```yaml
---
name: polecat-generic
role: polecat
recommended_model: sonnet
---

# Polecat Generic Worker

You are a polecat (ephemeral worker) executing work for a bead.

## CRITICAL: JSON Output

You MUST return fenced JSON with results:

\`\`\`json
{
  "success": true,
  "pr_url": "...",
  "error": null
}
\`\`\`

## Lifecycle

1. Read hooked work via `bd show <bead-id>`
2. Execute work according to bead description
3. Create PR via `gh pr create`
4. Return JSON results
5. Self-terminate (ephemeral)
```

**beads-ralph execution**:
```go
// Ralph loop launches gastown-style polecat
spec := AgentSpec{
    Role:  "polecat",
    Agent: ".claude/agents/polecat-generic.md",
    Model: "sonnet",
}

result := runScrumMaster(ctx, bead, spec, config)
```

---

## Cross-System Agent Directory

### Portable Agents (Work in Both Systems)

| Agent File | Role | beads-ralph Use | gastown Use |
|-----------|------|-----------------|-------------|
| `merge-specialist.md` | polecat | Merge conflict resolution | Merge bead execution |
| `qa-unit-tests.md` | polecat | QA validation (returns JSON) | Work validation (uses molecules) |
| `backend-dev.md` | polecat | Dev work (returns via commit) | Work execution (molecule-based) |

### System-Specific Agents

| Agent File | System | Role | Notes |
|-----------|--------|------|-------|
| `beads-ralph-scrum-master.md` | beads-ralph | polecat | Orchestrates dev/QA loop, requires JSON output |
| `polecat.md` | gastown | polecat | Generic worker, molecule-based, no JSON output |
| `beads-scribe.md` | beads-ralph | witness | Monitors beads, plan annotation, GitHub sync |
| `witness.md` | gastown | witness | Monitors polecats, health checks, nudging |
| `ralph-coordinator.md` | beads-ralph | mayor | Coordinates sprints (future: replace Go Ralph loop) |
| `mayor.md` | gastown | mayor | Coordinates work dispatch, convoy orchestration |

---

## Configuration Examples

### beads-ralph Config (`beads-ralph.yaml`)

```yaml
agents:
  default_model: sonnet
  default_executable: claude
  default_options:
    - "--dangerously-skip-permissions"
    - "--output-format"
    - "json"

  # Role-based model selection (gastown-style)
  role_models:
    polecat: sonnet   # Worker agents
    witness: haiku    # Monitoring agents
    mayor: opus       # Coordination agents
```

### gastown Config (`settings/config.json`)

```json
{
  "default_agent": "claude",
  "role_agents": {
    "polecat": "claude-sonnet",
    "witness": "claude-haiku",
    "mayor": "claude-opus"
  },
  "agents": {
    "claude-sonnet": {
      "command": "claude",
      "args": ["--dangerously-skip-permissions"],
      "provider": "claude"
    }
  }
}
```

---

## Key Differences (beads-ralph vs gastown)

| Aspect | beads-ralph | gastown |
|--------|-------------|---------|
| **Output Format** | Fenced JSON required (`--output-format json`) | Molecule-based, mail communication |
| **State Tracking** | Minimal (in-memory + bead metadata) | Full AgentFields (agent beads) |
| **Work Discovery** | Go Ralph loop reads `bd ready` | Agents discover via `gt prime --hook` |
| **Orchestration** | Go loop + scrum-master agents | Mayor + molecules + mail |
| **Lifecycle** | Managed by Ralph loop (external) | Self-managed (GUPP principle) |
| **Agent Sessions** | Subprocess per bead (ephemeral) | Tmux sessions (persistent capable) |

---

## Future Integration Possibilities

### Phase 1: Shared AgentSpec (MVP Target)
- ✅ Use common AgentSpec type in both systems
- ✅ Portable agent files (same .md works in both)
- ✅ Shared model resolution logic

### Phase 2: Hybrid Execution
- Run beads-ralph sprints as gastown polecats
- Use gastown's tmux session management
- Benefit from gastown's crash recovery

### Phase 3: Unified Orchestration
- Ralph loop becomes gastown Mayor
- Scrum-master becomes gastown Polecat
- Scribe becomes gastown Witness
- Full gastown integration (GUPP, molecules, mail)

---

## References

**Gastown Research**:
- `/Users/randlee/Documents/github/github-research/gastown/architecture.md` - GUPP, hook mechanism, role hierarchy
- `/Users/randlee/Documents/github/github-research/gastown/agents.md` - Agent roles, configuration, prompt templates
- `/Users/randlee/Documents/github/gastown/internal/config/loader.go` - Agent configuration resolution
- `/Users/randlee/Documents/github/gastown/internal/polecat/session_manager.go` - Polecat spawn logic

**beads-ralph Docs**:
- `docs/architecture.md` - Ralph loop design, team_name grouping
- `docs/schema.md` - Bead metadata, agent specifications
- `pm/2026-02-08-implementation-plan.md` - Sprint breakdown, agent usage

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-09
**Maintained By**: beads-ralph development team

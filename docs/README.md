# beads-ralph

Autonomous multi-agent development system using beads for task coordination.

## Repository References

This document references the following external repositories. These should be checked out locally as siblings to this repository. If not available locally, please check them out before proceeding.

| Repository | GitHub URL | Local Path | Purpose |
|------------|------------|------------|---------|
| beads | https://github.com/steveyegge/beads | `../beads/` | Git-backed issue tracker for task coordination |
| synaptic-canvas | *(Ask user for URL)* | `../synaptic-canvas/` | Phase/sprint numbering scheme reference |

## Overview

beads-ralph is a Go-based autonomous execution system that orchestrates parallel Claude Code agents to execute software development plans. Inspired by earlier autonomous coding concepts, it provides:

- **Complete plans as input** (no iterative spec refinement)
- **Parallel execution** via isolated git worktrees
- **Built-in QA validation** with automatic retry loops
- **100% autonomous** operation (no human intervention)

## Architecture

```
Plan (markdown) → Planning Skill → Beads → Go Ralph Loop → Scrum-Masters → PRs
```

### Components (Steampunk Theme)

1. **Chronicler Skill** (`.claude/skills/beads-chronicler/SKILL.md`)
   - Chronicles plan into beads database
   - Delegates to mason (direct beads) or smelter (formulas)
   - Creates convoy tracking containers
   - Orchestrates plan annotation

2. **Mason Agent** (`.claude/agents/beads-mason.md`)
   - Builds beads from plan blueprints
   - Inserts validated beads via `bd create --json`
   - Compiles dependency chains
   - Handles plan back-annotation (optional)

3. **Alchemist Agent** (`.claude/agents/beads-alchemist.md`)
   - Designs reusable formula templates
   - Creates `.beads/formulas/*.formula.json`
   - Defines variables and constraints
   - Validates with dry-run pours

4. **Smelter Agent** (`.claude/agents/beads-smelter.md`)
   - Pours formulas into database
   - Supports: pour, wisp (ephemeral), dry-run
   - Uses `bd mol pour` / `bd mol wisp`
   - Creates molecules and beads from templates

5. **Scribe Agent** (`.claude/agents/beads-scribe-requirements.txt`)
   - Maintains record-keeping (double-ledger)
   - Annotates plan on bead creation
   - Updates plan on bead completion
   - Extensible backends (GitHub, Azure, Jira)

6. **Alchemy Skill** (`.claude/skills/beads-alchemy/SKILL.md`)
   - Formula design and testing workflow
   - Delegates to alchemist (design) + smelter (test)
   - Dry-run and wisp validation

7. **Go Ralph Loop** (`src/` - Phase 4)
   - Finds ready beads per sprint
   - Launches parallel scrum-master Claude sessions
   - Monitors completion and advances sprints
   - Handles failures and rollback

8. **Scrum-Master Agent** (`.claude/agents/beads-ralph-scrum-master.md` - Phase 5)
   - Creates/verifies worktrees
   - Launches dev agents
   - Runs QA validation loops
   - Creates PRs and updates beads

## Documentation

### Core Architecture

- **[Agent Architecture](./agent-architecture.md)** ⭐ - Extensible agent templates, design patterns, registries
- [System Architecture](./architecture.md) - System architecture and data flow
- [Schema Design](./schema.md) - Extended bead schema (34 fields)
- [Design Summary](./DESIGN-SUMMARY.md) - High-level implementation roadmap

### Operational Guides

- [Phase/Sprint Numbering](./numbering.md) - Numbering scheme and parallel execution
- [Corner Cases](./corner-cases.md) - Failure scenarios and mitigations

### Integration

- [Gastown Integration Proposal](./gastown-integration-proposal.md) - Integration with gastown system
- [Gastown Concepts](./gastown-concepts.md) - Understanding gastown architecture

### Quick Start

- [README](./README.md) - This document (overview and navigation)

## Key Features

- **Parallel Sprint Execution** - Multiple agents work simultaneously in isolated worktrees
- **Atomic Work Claiming** - Race-free bead claiming via `bd claim`
- **Built-in QA Loops** - Dev agents retry based on QA feedback (max N attempts)
- **Merge Sprints** - Dedicated sprints for branch integration
- **Complete Audit Trail** - Full git history for rollback and review
- **PR-Based Review** - Output is series of unmerged PRs for human review

## Directory Structure (Implementation Repo)

```
beads-ralph/
├── .claude/
│   ├── agents/
│   │   ├── beads-ralph-scrum-master.md
│   │   ├── beads-mason.md
│   │   └── plan-review.md
│   └── skills/
│       └── beads-ralph-planner/
│           └── SKILL.md
├── docs/
│   ├── architecture.md
│   ├── schema.md
│   └── design.md
├── src/
│   └── (go application)
└── scripts/
    ├── bead_schema.py              # Pydantic v2 models for schema validation
    └── validate-bead-schema.py     # CLI tool using pydantic models
```

## Workflow Example

```bash
# 1. User creates implementation plan
vim pm/implementation-plan.md

# 2. Chronicle plan into beads database
/beads-chronicler pm/implementation-plan.md

# This creates:
# - Beads for each sprint
# - Convoy tracking containers
# - Plan annotations with bead IDs

# 3. Verify beads created
bd list --json

# 4. Start autonomous execution (Phase 4+)
beads-ralph run --config beads-ralph.yaml

# 5. Monitor progress
beads-ralph status
bd show <bead-id> --json

# 6. Review PRs when complete
gh pr list
```

## Status

**Current Phase**: Phase 2 Complete - Beads Architect System
- ✅ Phase 1: Schema & Validation (4/4 sprints)
- ✅ Phase 2: Beads Architect Agents (4/4 sprints)
- 🔄 Phase 3: Planning System (upcoming)
- ⏳ Phase 4: Go Ralph Loop
- ⏳ Phase 5: Scrum-Master Agent
- ⏳ Phase 6: Example Agents & MVP Test

**Architecture**: Extensible agent templates with steampunk theme
- **Core Principle**: Agent roles are carefully defined, implementations are extensible
- **Theme**: Mason (builder), Alchemist (designer), Smelter (executor), Scribe (record-keeper), Chronicler (orchestrator)
- **Pattern**: Template-based with backend adapters (GitHub, Azure, Jira, etc.)

**Next Steps**: Planning system integration, scribe agent implementation

---

**Related Projects**:
- [beads](https://github.com/steveyegge/beads) - Git-backed issue tracker
- [synaptic-canvas](../synaptic-canvas/) - Phase/sprint numbering scheme

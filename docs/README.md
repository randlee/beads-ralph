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

### Components

1. **Planning Skill** (`.claude/skills/beads-ralph-planner/SKILL.md`)
   - Works with user to refine plan
   - Delegates to beads-mason agent to create beads
   - Validates schema before execution

2. **Beads Architect** (`.claude/agents/beads-mason.md`)
   - Converts finalized plan into beads with extended schema
   - Creates merge beads for integration sprints
   - Sets up dependency chains for sprint sequencing

3. **Plan Review Agent** (`.claude/agents/plan-review.md`)
   - Validates plan structure and completeness
   - Checks for parallel execution opportunities
   - Verifies phase/sprint numbering

4. **Go Ralph Loop** (`src/`)
   - Finds ready beads per sprint
   - Launches parallel scrum-master Claude sessions
   - Monitors completion and advances sprints
   - Handles failures and rollback

5. **Scrum-Master Agent** (`.claude/agents/beads-ralph-scrum-master.md`)
   - Creates/verifies worktrees
   - Launches dev agents
   - Runs QA validation loops
   - Creates PRs and updates beads

## Documentation

- [Schema Design](./schema.md) - Extended bead schema for beads-ralph
- [Architecture](./architecture.md) - System architecture and data flow
- [Phase/Sprint Numbering](./numbering.md) - Numbering scheme and parallel execution
- [Worktree Strategy](./worktree-strategy.md) - Git worktree management
- [Corner Cases](./corner-cases.md) - Failure scenarios and mitigations

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
# 1. User creates plan
vim plan.md

# 2. Run planning skill
/beads-ralph-planner plan.md

# 3. Review and refine plan with architect
# (iterative process until schema validation passes)

# 4. Start autonomous execution
beads-ralph run --config beads-ralph.yaml

# 5. Monitor progress
beads-ralph status

# 6. Review PRs when complete
gh pr list
```

## Status

**Current Phase**: Design and documentation
**Next Steps**: Schema design, Go implementation, agent/skill definitions

---

**Related Projects**:
- [beads](https://github.com/steveyegge/beads) - Git-backed issue tracker
- [synaptic-canvas](../synaptic-canvas/) - Phase/sprint numbering scheme

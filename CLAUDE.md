# Claude Instructions for beads-ralph

## ⚠️ CRITICAL: Branch Management Rules

**NEVER switch the main repository branch on disk from `develop`.**

- Main repo at `/Users/randlee/Documents/github/beads-ralph/` MUST remain on `develop` at all times
- **ALWAYS use `sc-git-worktree` skill** to create worktrees for all development work
- Do NOT use `git checkout` or `git switch` in the main repository
- All sprint work happens in worktrees at `../beads-ralph-worktrees/<branch-name>`

**Why**: Switching branches in the main repo breaks worktree references and destabilizes the development environment.

---

## Project Overview

**beads-ralph** is an autonomous multi-agent development orchestration system that:
- Converts complete plans into executable beads (work items)
- Executes work autonomously in parallel using isolated git worktrees
- Coordinates multiple Claude Code agents via Go orchestration loop
- Implements built-in QA validation with dev/QA retry loops
- Outputs unmerged PRs for human review with complete audit trail

**Goal**: Build beads-ralph MVP using the system itself (dogfooding).

---

## Implementation Plan

**Current Plan**: [`pm/2026-02-08-implementation-plan.md`](./pm/2026-02-08-implementation-plan.md)

- 6 phases, 26 sprints
- Aggressive parallelization with worktree isolation
- CI/CD integration (Python tests in Phase 1, Go tests in Phase 4)
- Target: MVP capable of building post-MVP features

**Current Status**: Ready to begin Phase 1, Sprint 1.1 (Schema Validation Script)

---

## Key Documentation

**For reference only - read when information is needed:**

- [`docs/README.md`](./docs/README.md) - System overview and quick reference
- [`docs/schema.md`](./docs/schema.md) - Extended bead schema with validation rules
- [`docs/numbering.md`](./docs/numbering.md) - Phase/sprint numbering scheme
- [`docs/architecture.md`](./docs/architecture.md) - System architecture and data flow
- [`docs/corner-cases.md`](./docs/corner-cases.md) - Failure scenarios and mitigations
- [`docs/DESIGN-SUMMARY.md`](./docs/DESIGN-SUMMARY.md) - High-level implementation roadmap

---

## Workflow

### Sprint Execution Pattern (Dev-QA Loop)

Every sprint follows this pattern:

1. **Create worktree** using `sc-git-worktree` skill
2. **Dev work** by assigned dev agent(s)
3. **QA validation** by assigned QA agent(s)
4. **Retry loop** if QA fails (max attempts configurable)
5. **Commit/Push/PR** to `develop` branch
6. **Agent-teams review** documenting what worked/didn't

### Integration Branch

- All PRs target `develop` branch
- Merge to `main` after review/approval
- Post-merge CI runs as safety net

---

## Agent Model Selection

- **Haiku** - Exploration, test execution, simple validation
- **Sonnet** - Implementation work, documentation writing
- **Opus** - Critical planning, architecture decisions, complex review

---

## Environment

**Task List**: `beads-ralph` (configured in `.env`)
**Agent Teams**: Enabled (experimental feature)

---

## Next Action

Begin **Sprint 1.1: Core Schema Validation Script**
- Create Python validator for bead schema
- Implement phase/sprint pattern validation
- Add comprehensive unit tests
- Set foundation for Phase 2 (beads-architect agent)

# beads-ralph Implementation Plan

**Created**: 2026-02-08
**Target**: MVP (Minimum Viable Product)
**Integration Branch**: `develop`
**Strategy**: Aggressive parallelization with dev-QA loop per sprint

---

## Plan Overview

This plan implements beads-ralph MVP using the system itself (dogfooding). Each sprint follows the dev-QA loop pattern with mandatory PR creation to `develop` branch.

### Phase Summary

| Phase | Focus | Sprints | Parallelization |
|-------|-------|---------|-----------------|
| **1** | Schema & Validation | 1.1, 1.2a/b, 1.3 | High |
| **2** | Beads Architect Agent | 2.1, 2.2a/b, 2.3 | Medium |
| **3** | Planning System | 3.1a/b, 3.2 | High |
| **4** | Go Ralph Loop | 4.1, 4.2a/b/c, 4.3 | High |
| **5** | Scrum-Master Agent | 5.1, 5.2, 5.3 | Sequential |
| **6** | Example Agents & MVP Test | 6.1a/b/c, 6.2, 6.3 | High |

### Key Agents

| Agent Name | Role | Model | Usage |
|------------|------|-------|-------|
| `beads-schema-expert` | Schema validation, design review | opus | Design review, QA across all phases |
| `python-backend-dev` | Python implementation | sonnet | Schema validation scripts |
| `go-backend-dev` | Go implementation | sonnet | Ralph loop implementation |
| `markdown-doc-writer` | Agent definitions, docs | sonnet | Agent/skill markdown files |
| `beads-explore-agent` | Repository exploration | haiku | Exploring beads/synaptic-canvas repos |
| `planning-architect` | Critical planning decisions | opus | Architecture decisions, dependency design |
| `qa-python-tests` | Python test execution | haiku | Run pytest, check coverage |
| `qa-go-tests` | Go test execution | haiku | Run go test, check coverage |
| `qa-schema-validator` | Schema compliance checks | haiku | Validate bead JSON against schema |
| `qa-code-review` | Architecture/code review | opus | Design patterns, code quality |

---

## Phase 1: Schema & Validation

**Goal**: Establish bead schema validation foundation and example beads.

### Sprint 1.1: Core Schema Validation Script

**Worktree**: `../beads-ralph-worktrees/feature/1-1-schema-validator`
**Branch**: `feature/1-1-schema-validator`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)

**QA Agents**:
- `qa-python-tests` (haiku) - Run pytest with >90% coverage
- `qa-schema-validator` (haiku) - Validate script output format
- `beads-schema-expert` (opus) - Review validation logic against schema.md

**Status**: ✅ **COMPLETED** (PR #4 merged)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051 (for agent resurrection via claude-history)

**Tasks**:
- [x] Create `scripts/bead_schema.py` with pydantic models
  - `BeadMetadata` base model with all metadata fields from schema.md
  - Nested models: `QAAgent`, `DevExecution`, `QAExecution`, `ScrumResult`
  - Complete `Bead` model combining core bead fields + metadata
  - Field validators using `@field_validator` decorator for phase/sprint patterns
  - Path validation for agent/skill paths
  - Model Config with strict validation (pydantic v2)
- [x] Create `scripts/validate-bead-schema.py` CLI tool
  - Accept JSON from file path or stdin
  - Parse using `Bead.model_validate_json()`
  - Catch `ValidationError` and format with field paths
  - Exit code 0 for valid, 1 for invalid
- [x] Create `scripts/requirements.txt` with pydantic>=2.0, pytest, pytest-cov
- [x] Create comprehensive test suite:
  - `scripts/tests/test_bead_schema.py` - Unit tests for pydantic models
  - `scripts/tests/test_validator.py` - Integration tests for CLI validator
  - Test valid beads from schema.md examples
  - Test invalid beads (missing fields, bad patterns)
  - Achieve >90% coverage (95% bead_schema.py, 89% overall)

**Acceptance Criteria**:
- Pydantic models cover all fields from schema.md (lines 41-238)
- Field validators enforce phase/sprint regex patterns
- Validator accepts valid bead JSON from schema.md examples (lines 240-324, 326-396)
- Validator rejects invalid JSON with pydantic validation errors
- Unit tests achieve >90% coverage
- All validation rules from schema.md implemented via pydantic

**Agent-Teams Review**:
- Document: Did team coordination improve efficiency?
- Note: Which agents collaborated, what worked, what didn't
- Lessons: Any coordination issues to address

---

### Sprint 1.2a: Example Work Bead (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/1-2a-work-bead`
**Branch**: `feature/1-2a-work-bead`
**Source Branch**: `develop` (after 1.1 merged)

**Dev Agents**:
- `python-backend-dev` (sonnet)

**QA Agents**:
- `qa-schema-validator` (haiku) - Validate against schema
- `beads-schema-expert` (opus) - Review completeness and accuracy

**Status**: ✅ **COMPLETED** (PR #8 - targets develop)
**Session ID**: [current session]

**Tasks**:
- [x] Create `examples/example-work-bead.json`
- [x] Include all required fields from schema.md (34 fields total)
- [x] Use realistic values for backend development sprint
- [x] Populate dev/QA agent configurations with proper output schemas
- [x] Validate with `validate-bead-schema.py`

**Acceptance Criteria**:
- Example passes schema validation ✅
- All metadata fields populated realistically ✅
- JSON is well-formatted and documented ✅
- Matches work bead example from schema.md (lines 240-324) ✅

**Agent-Teams Review**:
- Single agent work (automated by main session)
- No team coordination needed for straightforward JSON creation

---

### Sprint 1.2b: Example Merge Bead (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/1-2b-merge-bead`
**Branch**: `feature/1-2b-merge-bead`
**Source Branch**: `develop` (after 1.1 merged)

**Dev Agents**:
- `python-backend-dev` (sonnet)

**QA Agents**:
- `qa-schema-validator` (haiku) - Validate against schema
- `beads-schema-expert` (opus) - Review merge-specific fields

**Status**: ✅ **COMPLETED** (PR #9 - targets develop)
**Session ID**: [current session]

**Tasks**:
- [x] Create `examples/example-merge-bead.json`
- [x] Include all required fields including `branches_to_merge`
- [x] Set `issue_type` to `beads-ralph-merge`
- [x] Use realistic merge scenario (parallel sprints)
- [x] Validate with `validate-bead-schema.py`

**Acceptance Criteria**:
- Example passes schema validation ✅
- Merge-specific fields properly configured ✅
- Demonstrates parallel sprint merge scenario ✅
- Matches merge bead example from schema.md (lines 326-396) ✅

**Agent-Teams Review**:
- Single agent work (automated by main session)
- Parallel execution with 1.2a demonstrated worktree isolation

---

### Sprint 1.3: Integration & Documentation

**Worktree**: `../beads-ralph-worktrees/feature/1-3-schema-integration`
**Branch**: `feature/1-3-schema-integration`
**Source Branch**: `develop` (after 1.2a and 1.2b merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `qa-schema-validator` (haiku) - Test all examples
- `beads-schema-expert` (opus) - Final schema review
- `qa-code-review` (opus) - Review documentation completeness

**Tasks**:
- [ ] Merge any conflicts from 1.2a and 1.2b
- [ ] Create `scripts/README.md` documenting validator usage
- [ ] Add validation examples to documentation
- [ ] Run validator against all example beads
- [ ] Update root README.md with validation instructions

**Acceptance Criteria**:
- All example beads validate successfully
- Documentation is clear and complete
- No merge conflicts remaining
- Validator is ready for use in Phase 2

**Agent-Teams Review**:
- Document: Merge process experience
- Note: Any conflicts, how resolved
- Lessons: Merge strategy effectiveness

---

## Phase 2: Beads Architect Agent

**Goal**: Create agent that converts plans into beads with proper dependencies.

### Sprint 2.1: Beads Architect Agent Core

**Worktree**: `../beads-ralph-worktrees/feature/2-1-architect-core`
**Branch**: `feature/2-1-architect-core`
**Source Branch**: `develop`

**Dev Agents**:
- `markdown-doc-writer` (sonnet)
- `beads-explore-agent` (haiku) - Explore ../beads repo for API reference

**QA Agents**:
- `beads-schema-expert` (opus) - Review agent prompt accuracy
- `qa-code-review` (opus) - Review agent design and completeness

**Tasks**:
- [ ] Create `.claude/agents/beads-architect.md`
- [ ] Define agent role: convert plan markdown to bead JSON
- [ ] Add instructions for parsing phase/sprint numbers
- [ ] Add instructions for extracting dev/QA agent requirements
- [ ] Add instructions for determining worktree paths
- [ ] Add instructions for setting up branch names
- [ ] Include schema validation requirement
- [ ] Add examples of input plan → output bead mappings

**Acceptance Criteria**:
- Agent definition is complete and clear
- Instructions cover all schema fields
- Examples demonstrate core functionality
- Agent references validate-bead-schema.py for validation

**Agent-Teams Review**:
- Document: Coordination between doc-writer and explore agent
- Note: Was repo exploration helpful? Efficient?
- Lessons: Team composition for research + writing tasks

---

### Sprint 2.2a: Dependency Compilation Logic (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/2-2a-dependency-logic`
**Branch**: `feature/2-2a-dependency-logic`
**Source Branch**: `develop` (after 2.1 merged)

**Dev Agents**:
- `planning-architect` (opus)

**QA Agents**:
- `beads-schema-expert` (opus) - Verify dependency rules match schema.md
- `qa-code-review` (opus) - Review logic completeness

**Tasks**:
- [ ] Add to beads-architect.md: dependency compilation rules
- [ ] Sequential sprints: `1.1 → 1.2` maps to `1.2 depends on [1.1]`
- [ ] Parallel sprints: `1.2a`, `1.2b` both depend on `1.1`, not each other
- [ ] Merge sprints: `1.3` depends on `[1.2a, 1.2b]`
- [ ] Phase split: `3a.1`, `3b.1` depend on last sprint of phase 2
- [ ] Phase converge: `4.1` depends on last sprints of `3a` and `3b`
- [ ] Add algorithm/pseudocode for dependency generation
- [ ] Include test cases for each scenario

**Acceptance Criteria**:
- All dependency patterns from numbering.md covered
- Algorithm is clear and unambiguous
- Test cases validate each scenario
- Matches dependency rules from schema.md (lines 82-114)

**Agent-Teams Review**:
- Note: Single opus agent for critical logic
- Consider: Would team have helped?

---

### Sprint 2.2b: Plan Back-Annotation Design (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/2-2b-back-annotation`
**Branch**: `feature/2-2b-back-annotation`
**Source Branch**: `develop` (after 2.1 merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `beads-schema-expert` (opus) - Verify bi-directional tracking design
- `qa-code-review` (opus) - Review implementation approach

**Tasks**:
- [ ] Add to beads-architect.md: plan back-annotation instructions
- [ ] Define HTML comment format: `<!-- beads-ralph: bd-abc123 -->`
- [ ] Add instructions for inserting after sprint headings
- [ ] Define mapping: sprint ID → bead ID
- [ ] Add regex pattern for finding sprint headings
- [ ] Document plan → bead and bead → plan navigation use cases
- [ ] Include examples from schema.md (lines 398-490)

**Acceptance Criteria**:
- Back-annotation format matches schema.md
- Algorithm for finding sprint headings is clear
- Use cases demonstrate bi-directional tracking value
- Agent can parse and update plan files

**Agent-Teams Review**:
- Note: Single agent work or team experience

---

### Sprint 2.3: Beads Architect Integration & Testing

**Worktree**: `../beads-ralph-worktrees/feature/2-3-architect-integration`
**Branch**: `feature/2-3-architect-integration`
**Source Branch**: `develop` (after 2.2a and 2.2b merged)

**Dev Agents**:
- `planning-architect` (opus)
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `qa-schema-validator` (haiku) - Validate generated beads
- `beads-schema-expert` (opus) - Full agent review
- `qa-code-review` (opus) - Completeness check

**Tasks**:
- [ ] Merge 2.2a and 2.2b into beads-architect.md
- [ ] Add complete workflow: plan input → bead JSON output
- [ ] Include validation step using validate-bead-schema.py
- [ ] Add error handling instructions (malformed plan, missing fields)
- [ ] Create `examples/test-plan.md` (simple 2-3 sprint plan)
- [ ] Test: Run beads-architect agent against test-plan.md
- [ ] Verify: Generated beads pass validation
- [ ] Verify: Dependencies are correct

**Acceptance Criteria**:
- Beads-architect agent is complete and functional
- Test plan converts to valid beads
- Dependencies match expected pattern
- Agent handles errors gracefully
- Documentation is clear for future use

**Agent-Teams Review**:
- Document: Multi-agent coordination (architect + writer)
- Note: Division of labor effectiveness
- Lessons: Testing approach with agent teams

---

## Phase 3: Planning System

**Goal**: Complete the planning workflow (skill + review agent).

### Sprint 3.1a: Planning Skill Definition (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/3-1a-planning-skill`
**Branch**: `feature/3-1a-planning-skill`
**Source Branch**: `develop`

**Dev Agents**:
- `markdown-doc-writer` (sonnet)
- `beads-explore-agent` (haiku) - Research Claude Code skill format

**QA Agents**:
- `beads-schema-expert` (opus) - Verify skill integrates with beads-architect
- `qa-code-review` (opus) - Review skill design

**Tasks**:
- [ ] Create `.claude/skills/beads-ralph-planner/SKILL.md`
- [ ] Define skill invocation: `/beads-ralph-planner <plan-file>`
- [ ] Add instructions: work with user to refine plan structure
- [ ] Add instructions: validate phase/sprint organization
- [ ] Add instructions: check for parallel execution opportunities
- [ ] Add instructions: delegate to beads-architect for bead creation
- [ ] Add instructions: run plan-review agent for validation
- [ ] Include workflow diagram in comments

**Acceptance Criteria**:
- Skill follows Claude Code skill format
- Workflow is clear: refine → architect → review → create
- Integration points with beads-architect specified
- User interaction patterns defined

**Agent-Teams Review**:
- Document: Coordination between writer and explorer
- Note: Research phase effectiveness
- Lessons: Skill format understanding

---

### Sprint 3.1b: Plan Review Agent (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/3-1b-plan-review`
**Branch**: `feature/3-1b-plan-review`
**Source Branch**: `develop`

**Dev Agents**:
- `planning-architect` (opus)

**QA Agents**:
- `beads-schema-expert` (opus) - Review validation coverage
- `qa-code-review` (opus) - Review agent completeness

**Tasks**:
- [ ] Create `.claude/agents/plan-review.md`
- [ ] Define role: validate bead schema and dependencies
- [ ] Add validation: all required fields present
- [ ] Add validation: phase/sprint pattern regex
- [ ] Add validation: dependency graph (no cycles)
- [ ] Add validation: file paths exist (agents, skills)
- [ ] Add validation: worktree paths (no conflicts)
- [ ] Add validation: branch names (git-safe)
- [ ] Define output: validation report with errors/warnings

**Acceptance Criteria**:
- Agent covers all validations from schema.md (lines 647-784)
- Cycle detection algorithm is clear
- Error messages are actionable
- Agent integrates with planning skill workflow

**Agent-Teams Review**:
- Note: Single opus agent for validation logic
- Consider: Team value for complex validation rules

---

### Sprint 3.2: Planning System Integration

**Worktree**: `../beads-ralph-worktrees/feature/3-2-planning-integration`
**Branch**: `feature/3-2-planning-integration`
**Source Branch**: `develop` (after 3.1a and 3.1b merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `beads-schema-expert` (opus) - Full planning system review
- `qa-code-review` (opus) - Integration check

**Tasks**:
- [ ] Update beads-ralph-planner skill to call plan-review agent
- [ ] Add error handling for validation failures
- [ ] Add user feedback loop for plan refinement
- [ ] Create `examples/planning-workflow.md` documenting full flow
- [ ] Test: Run skill on test-plan.md
- [ ] Verify: Validation catches errors
- [ ] Verify: Workflow completes successfully

**Acceptance Criteria**:
- Planning skill integrates with architect and review agents
- Validation failures provide clear feedback
- User can iterate on plan until validation passes
- Complete workflow is documented

**Agent-Teams Review**:
- Document: Integration testing experience
- Note: Agent coordination challenges
- Lessons: Testing complex workflows

---

## Phase 4: Go Ralph Loop

**Goal**: Implement Go orchestration loop for autonomous execution.

### Sprint 4.1: Go Project Setup & Core Loop Structure

**Worktree**: `../beads-ralph-worktrees/feature/4-1-go-setup`
**Branch**: `feature/4-1-go-setup`
**Source Branch**: `develop`

**Dev Agents**:
- `go-backend-dev` (sonnet)

**QA Agents**:
- `qa-go-tests` (haiku) - Verify build and basic tests
- `qa-code-review` (opus) - Review architecture

**Tasks**:
- [ ] Create `src/go.mod` (module: github.com/randlee/beads-ralph)
- [ ] Create `src/main.go` with CLI entry point
- [ ] Create `src/ralph/loop.go` with main loop skeleton
- [ ] Define `Bead` struct matching schema metadata
- [ ] Define `ScrumResult` struct for scrum-master output
- [ ] Implement `findReadyBeads()` calling `bd ready --json`
- [ ] Implement `groupBySprint()` function
- [ ] Add basic logging setup
- [ ] Create `src/ralph/loop_test.go` with unit tests

**Acceptance Criteria**:
- Project compiles successfully
- Core loop structure matches architecture.md (lines 240-301)
- Unit tests pass
- Logging is functional

**Agent-Teams Review**:
- Note: Single go-backend-dev for initial setup
- Consider: Was this sufficient?

---

### Sprint 4.2a: Bead Claiming Logic (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/4-2a-claim-logic`
**Branch**: `feature/4-2a-claim-logic`
**Source Branch**: `develop` (after 4.1 merged)

**Dev Agents**:
- `go-backend-dev` (sonnet)

**QA Agents**:
- `qa-go-tests` (haiku) - Test claiming scenarios
- `beads-schema-expert` (opus) - Verify race-free claiming
- `qa-code-review` (opus) - Review concurrency safety

**Tasks**:
- [ ] Create `src/ralph/claim.go`
- [ ] Implement `claimBead(beadID)` calling `bd claim`
- [ ] Handle `ErrAlreadyClaimed` case
- [ ] Add retry logic with exponential backoff
- [ ] Create tests for race conditions
- [ ] Document atomic CAS behavior

**Acceptance Criteria**:
- Claiming is atomic (CAS via bd claim)
- Race conditions handled gracefully
- Already-claimed errors don't crash loop
- Tests verify concurrent claim attempts

**Agent-Teams Review**:
- Note: Single agent for concurrency-critical code
- Consider: Opus for review appropriate?

---

### Sprint 4.2b: Configuration System (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/4-2b-config-system`
**Branch**: `feature/4-2b-config-system`
**Source Branch**: `develop` (after 4.1 merged)

**Dev Agents**:
- `go-backend-dev` (sonnet)

**QA Agents**:
- `qa-go-tests` (haiku) - Test config loading
- `qa-code-review` (opus) - Review config design

**Tasks**:
- [ ] Create `src/config/config.go`
- [ ] Define `Config` struct matching architecture.md (lines 779-828)
- [ ] Implement YAML loading (using gopkg.in/yaml.v3)
- [ ] Add validation for required fields
- [ ] Add default values
- [ ] Create `beads-ralph.yaml.example` in repo root
- [ ] Create tests for config validation

**Acceptance Criteria**:
- Config loads from YAML successfully
- All fields from architecture.md represented
- Validation catches missing required fields
- Example config is well-documented

**Agent-Teams Review**:
- Note: Single agent work

---

### Sprint 4.2c: Scrum-Master Launcher (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/4-2c-scrum-launcher`
**Branch**: `feature/4-2c-scrum-launcher`
**Source Branch**: `develop` (after 4.1 merged)

**Dev Agents**:
- `go-backend-dev` (sonnet)

**QA Agents**:
- `qa-go-tests` (haiku) - Test launcher logic
- `qa-code-review` (opus) - Review subprocess management

**Tasks**:
- [ ] Create `src/ralph/scrum_master.go`
- [ ] Implement `runScrumMaster(bead, config)` function
- [ ] Build Claude Code command with --agent flag
- [ ] Implement prompt generation from bead metadata
- [ ] Add timeout handling (context.WithTimeout)
- [ ] Capture stdout/stderr
- [ ] Parse JSON output from scrum-master
- [ ] Return ScrumResult struct

**Acceptance Criteria**:
- Launches Claude Code with correct arguments
- Timeout kills runaway processes
- Captures and parses scrum-master JSON output
- Errors are properly propagated

**Agent-Teams Review**:
- Note: Single agent for subprocess logic

---

### Sprint 4.3: Result Processing & Loop Integration

**Worktree**: `../beads-ralph-worktrees/feature/4-3-result-processing`
**Branch**: `feature/4-3-result-processing`
**Source Branch**: `develop` (after 4.2a, 4.2b, 4.2c merged)

**Dev Agents**:
- `go-backend-dev` (sonnet)

**QA Agents**:
- `qa-go-tests` (haiku) - Integration tests (shared run for all 4.2 work)
- `beads-schema-expert` (opus) - Review bead update logic
- `qa-code-review` (opus) - Architecture review

**Tasks**:
- [ ] Merge 4.2a/b/c branches
- [ ] Create `src/ralph/results.go`
- [ ] Implement `processResults(results)` function
- [ ] Check for fatal errors (stop loop)
- [ ] Check for success (continue)
- [ ] Check for failures (log, continue)
- [ ] Implement result aggregation
- [ ] Add parallelism control (semaphore)
- [ ] Complete main loop integration
- [ ] Add end-to-end tests

**Acceptance Criteria**:
- All 4.2 branches merged cleanly
- Result processing matches architecture.md design
- Parallelism is controlled (max_parallel_sessions)
- Fatal errors stop the loop
- Tests verify full loop iteration

**Agent-Teams Review**:
- Document: Merge process for 3 parallel branches
- Note: Shared test run efficiency
- Lessons: Multi-branch integration strategy

---

## Phase 5: Scrum-Master Agent

**Goal**: Implement scrum-master agent that orchestrates dev/QA per bead.

### Sprint 5.1: Scrum-Master Agent Core

**Worktree**: `../beads-ralph-worktrees/feature/5-1-scrum-master-core`
**Branch**: `feature/5-1-scrum-master-core`
**Source Branch**: `develop`

**Dev Agents**:
- `markdown-doc-writer` (sonnet)
- `planning-architect` (opus) - Design orchestration logic

**QA Agents**:
- `beads-schema-expert` (opus) - Review bead interaction
- `qa-code-review` (opus) - Review agent workflow

**Tasks**:
- [ ] Create `.claude/agents/beads-ralph-scrum-master.md`
- [ ] Define role: orchestrate dev/QA for single bead
- [ ] Add instructions: read bead with `bd show --json`
- [ ] Add instructions: extract metadata (worktree, branch, agents, prompts)
- [ ] Add instructions: create worktree using sc-git-worktree skill
- [ ] Add instructions: verify branch exists
- [ ] Add instructions: cd into worktree
- [ ] Add workflow diagram showing dev → QA → retry → PR flow
- [ ] Define JSON output schema (ScrumResult)

**Acceptance Criteria**:
- Agent definition is complete
- Workflow matches architecture.md (lines 419-479)
- Bead reading and parsing is clear
- Worktree management is specified

**Agent-Teams Review**:
- Document: Writer + architect coordination
- Note: Was architect input valuable for orchestration design?
- Lessons: Team composition for complex agent definitions

---

### Sprint 5.2: Dev/QA Retry Loop

**Worktree**: `../beads-ralph-worktrees/feature/5-2-dev-qa-loop`
**Branch**: `feature/5-2-dev-qa-loop`
**Source Branch**: `develop` (after 5.1 merged)

**Dev Agents**:
- `planning-architect` (opus)

**QA Agents**:
- `beads-schema-expert` (opus) - Review retry logic
- `qa-code-review` (opus) - Review error handling

**Tasks**:
- [ ] Add to scrum-master agent: dev/QA retry loop algorithm
- [ ] Add instructions: launch dev agent from metadata.dev_agent_path
- [ ] Add instructions: pass dev_prompts from metadata
- [ ] Add instructions: wait for dev agent completion
- [ ] Add instructions: launch QA agents in background (Task tool)
- [ ] Add instructions: collect QA results
- [ ] Add instructions: check for `stop` status (fatal, exit)
- [ ] Add instructions: check for `fail` status (retry with feedback)
- [ ] Add instructions: check for `pass` status (proceed to PR)
- [ ] Add instructions: max retry limit (max_retry_attempts)
- [ ] Include pseudocode from architecture.md (lines 481-505)

**Acceptance Criteria**:
- Retry loop matches architecture.md design
- QA status values handled correctly (pass/fail/stop)
- Feedback passed to dev agent on retry
- Max attempts enforced

**Agent-Teams Review**:
- Note: Single opus for critical retry logic
- Consider: Testing approach for retry scenarios

---

### Sprint 5.3: PR Creation & Bead Updates

**Worktree**: `../beads-ralph-worktrees/feature/5-3-pr-bead-updates`
**Branch**: `feature/5-3-pr-bead-updates`
**Source Branch**: `develop` (after 5.2 merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `beads-schema-expert` (opus) - Review bead update logic
- `qa-code-review` (opus) - Review PR creation flow

**Tasks**:
- [ ] Add to scrum-master agent: PR creation instructions
- [ ] Add instructions: use `gh pr create` with title/body
- [ ] Add instructions: capture PR URL and number
- [ ] Add instructions: update bead with `bd update`
- [ ] Add instructions: set status to `closed`
- [ ] Add instructions: update metadata with PR info
- [ ] Add instructions: update metadata with scrum_result
- [ ] Add instructions: update metadata with agent execution history
- [ ] Add instructions: return JSON result
- [ ] Include JSON output example from architecture.md (lines 509-534)

**Acceptance Criteria**:
- PR creation uses gh CLI correctly
- Bead updates include all execution tracking
- JSON output matches ScrumResult schema
- Agent handles PR creation failures

**Agent-Teams Review**:
- Note: Integration of all scrum-master pieces
- Lessons: Agent complexity management

---

## Phase 6: Example Agents & MVP Testing

**Goal**: Create example dev/QA agents and run end-to-end MVP test.

### Sprint 6.1a: Example Dev Agents (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/6-1a-dev-agents`
**Branch**: `feature/6-1a-dev-agents`
**Source Branch**: `develop`

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `qa-code-review` (opus) - Review agent definitions

**Tasks**:
- [ ] Create `.claude/agents/backend-dev.md` (Python/Go backend work)
- [ ] Create `.claude/agents/frontend-dev.md` (TypeScript/React frontend work)
- [ ] Create `.claude/agents/merge-specialist.md` (Merge conflict resolution)
- [ ] Each agent: Define role and responsibilities
- [ ] Each agent: Add instructions for working in worktrees
- [ ] Each agent: Add instructions for following project conventions
- [ ] Each agent: Add instructions for committing changes

**Acceptance Criteria**:
- Three example dev agents defined
- Each agent has clear role and instructions
- Agents reference worktree context
- Agents are ready for use by scrum-master

**Agent-Teams Review**:
- Note: Single writer for consistency

---

### Sprint 6.1b: Example QA Agents (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/6-1b-qa-agents`
**Branch**: `feature/6-1b-qa-agents`
**Source Branch**: `develop`

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `beads-schema-expert` (opus) - Review QA output schemas
- `qa-code-review` (opus) - Review QA agent design

**Tasks**:
- [ ] Create `.claude/agents/qa-unit-tests.md`
- [ ] Create `.claude/agents/qa-security-scan.md`
- [ ] Create `.claude/agents/qa-lint.md`
- [ ] Each agent: Define structured JSON input schema
- [ ] Each agent: Define structured JSON output schema
- [ ] Each agent: Add instructions for status values (pass/fail/stop)
- [ ] Each agent: Add examples from architecture.md (lines 622-663)

**Acceptance Criteria**:
- Three example QA agents defined
- Input/output schemas are clear
- Status semantics match architecture.md
- Agents return structured JSON

**Agent-Teams Review**:
- Document: Schema design coordination
- Note: beads-schema-expert input value

---

### Sprint 6.1c: MVP Test Plan (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/6-1c-mvp-test-plan`
**Branch**: `feature/6-1c-mvp-test-plan`
**Source Branch**: `develop`

**Dev Agents**:
- `planning-architect` (opus)

**QA Agents**:
- `beads-schema-expert` (opus) - Review test plan structure
- `qa-code-review` (opus) - Review test coverage

**Tasks**:
- [ ] Create `examples/mvp-test-plan.md`
- [ ] Design simple 3-phase plan:
  - Phase 1: Setup (1 sprint)
  - Phase 2: Parallel work (2.1a backend, 2.1b frontend)
  - Phase 3: Integration (3.1 merge sprint)
- [ ] Each sprint: Clear description and tasks
- [ ] Each sprint: Specify dev/QA agents to use
- [ ] Each sprint: Simple, achievable goals
- [ ] Add dummy project files that sprints will modify

**Acceptance Criteria**:
- Test plan demonstrates parallel execution
- Test plan includes merge sprint
- Test plan is achievable for MVP test
- Plan follows phase/sprint numbering rules

**Agent-Teams Review**:
- Note: Opus planning for critical test design

---

### Sprint 6.2: End-to-End MVP Test

**Worktree**: `../beads-ralph-worktrees/feature/6-2-mvp-e2e-test`
**Branch**: `feature/6-2-mvp-e2e-test`
**Source Branch**: `develop` (after 6.1a, 6.1b, 6.1c merged)

**Dev Agents**:
- `planning-architect` (opus) - Orchestrate test execution
- `go-backend-dev` (sonnet) - Fix any Go issues found

**QA Agents**:
- `qa-go-tests` (haiku) - Shared test run for merged work
- `beads-schema-expert` (opus) - Validate generated beads
- `qa-code-review` (opus) - Full system review

**Tasks**:
- [ ] Merge 6.1a/b/c branches
- [ ] Run beads-ralph-planner skill on mvp-test-plan.md
- [ ] Verify: Beads created successfully
- [ ] Verify: Dependencies are correct
- [ ] Verify: Plan is back-annotated
- [ ] Run `beads-ralph run` (Go loop)
- [ ] Monitor: Check logs for errors
- [ ] Verify: Scrum-masters launched
- [ ] Verify: Dev agents executed
- [ ] Verify: QA agents validated
- [ ] Verify: PRs created
- [ ] Document: Any failures or issues

**Acceptance Criteria**:
- Planning system converts test plan to beads
- Ralph loop executes without fatal errors
- All sprints complete (success or graceful failure)
- PRs are created and reviewable
- Complete audit trail in git history

**Agent-Teams Review**:
- Document: Full system testing experience
- Note: Agent coordination at scale
- Lessons: What broke, what worked well
- Critical: Document any gaps for iteration

---

### Sprint 6.3: MVP Documentation & Cleanup

**Worktree**: `../beads-ralph-worktrees/feature/6-3-mvp-documentation`
**Branch**: `feature/6-3-mvp-documentation`
**Source Branch**: `develop` (after 6.2 merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)

**QA Agents**:
- `qa-code-review` (opus) - Review documentation completeness

**Tasks**:
- [ ] Update README.md with MVP status
- [ ] Create `docs/getting-started.md` with installation and usage
- [ ] Create `docs/troubleshooting.md` with common issues
- [ ] Document test results from 6.2
- [ ] Add known limitations section
- [ ] Add "next steps" section (post-MVP features)
- [ ] Update architecture.md with any implementation changes

**Acceptance Criteria**:
- Documentation is clear and complete
- Users can install and run beads-ralph
- Troubleshooting covers observed issues
- Known limitations are documented
- MVP is ready for dogfooding post-MVP features

**Agent-Teams Review**:
- Document: Final documentation phase
- Note: Lessons learned across all phases
- Summary: Agent-teams effectiveness overall
- Recommendations: Improvements for post-MVP work

---

## Success Metrics

### MVP Success Criteria
- [ ] Planning system converts plans to valid beads
- [ ] Ralph loop executes beads autonomously
- [ ] Parallel sprints execute concurrently
- [ ] Dev/QA retry loops function correctly
- [ ] PRs are created with complete audit trail
- [ ] System can dogfood post-MVP features

### Key Deliverables
- [ ] Schema validation script (`scripts/validate-bead-schema.py`)
- [ ] Beads architect agent (`.claude/agents/beads-architect.md`)
- [ ] Planning skill (`.claude/skills/beads-ralph-planner/SKILL.md`)
- [ ] Plan review agent (`.claude/agents/plan-review.md`)
- [ ] Go ralph loop (`src/`)
- [ ] Scrum-master agent (`.claude/agents/beads-ralph-scrum-master.md`)
- [ ] Example dev/QA agents (`.claude/agents/`)
- [ ] Working MVP demonstrated with test plan

---

## Post-MVP Backlog

Features to build using beads-ralph itself:
- Human escalation beads for fatal errors
- Smart merge conflict resolution
- Incremental QA (only affected tests)
- Cost tracking per sprint/phase
- Dynamic agent selection based on code analysis
- Multi-machine distributed execution
- Web dashboard for monitoring
- Advanced failure recovery strategies
- Cross-sprint integration testing
- Automated rollback on failure

---

## Notes for Execution

### Worktree Management
- All worktrees created with `sc-git-worktree` skill
- Worktree path pattern: `../beads-ralph-worktrees/<branch-name>`
- Each worktree isolated (no cross-contamination)

### Dev-QA Pattern
- Every sprint: Dev agent(s) → QA agent(s) → Commit/Push/PR
- Multiple dev agents on same worktree → Shared QA test run
- Architecture/code review → Multiple QA agents per scrum-master discretion

### Agent-Teams Usage
- Use teams when coordination benefits efficiency
- Document experience after each sprint
- Note what worked, what didn't, lessons learned
- Quick note if teams not used in a sprint

### Integration Strategy
- All PRs target `develop` branch
- Merge sprints required after parallel work
- Review PRs before merging to prevent breakage
- Maintain clean git history for audit trail

### Model Selection
- **Haiku**: Exploration, test execution, simple validation
- **Sonnet**: Implementation work, documentation writing
- **Opus**: Critical planning, architecture decisions, complex review

---

## Completion Log

### ✅ Sprint 1.1: Core Schema Validation Script
**Status**: Completed 2026-02-08
**PR**: #4 (merged to develop)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051
**Outcome**:
- Created pydantic v2 models with strict validation
- CLI validator with 95% coverage on core module
- All QA gates passed (pytest, schema validation, design review)

### ✅ Schema Registry (Post-Sprint 1.1)
**Status**: Completed 2026-02-08
**PR**: #5 (merged to develop)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051
**Outcome**:
- Centralized version tracking for beads/gastown/ralph schemas
- Documented 43 base SQL columns, extension mechanisms
- Identified 8 discrepancies between docs and source code
- Established "rig = repository" terminology

### 🔄 Gastown Integration Research (Post-Sprint 1.1)
**Status**: In Review 2026-02-08
**PR**: #6 (pending review)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051
**Outcome**:
- Comprehensive analysis of 7 gastown concepts with source references
- 7 prioritized integration proposals (Merge Slot, Molecule/DAG, Formula, etc.)
- Added CRITICAL REQUIREMENT: agent_id tracking for agent resurrection
- Updated schema with agent_id fields in dev/QA execution structures

### ✅ Sprint 1.2a: Example Work Bead
**Status**: Completed 2026-02-08
**PR**: #8 (targets develop, pending review)
**Session ID**: [current session]
**Outcome**:
- Created `examples/example-work-bead.json` with all 34 required fields
- Demonstrates work bead pattern (`issue_type: "beads-ralph-work"`)
- Realistic backend development context with dev/QA agent configurations
- Passes validate-bead-schema.py validation
- Parallel execution with Sprint 1.2b

### ✅ Sprint 1.2b: Example Merge Bead
**Status**: Completed 2026-02-08
**PR**: #9 (targets develop, pending review)
**Session ID**: [current session]
**Outcome**:
- Created `examples/example-merge-bead.json` with merge-specific fields
- Demonstrates merge bead pattern (`issue_type: "beads-ralph-merge"`)
- Includes `branches_to_merge` field for parallel sprint integration
- Passes validate-bead-schema.py validation
- Parallel execution with Sprint 1.2a

---

**Plan Status**: Phase 1 in progress
**Next Action**: Sprint 1.3 (Integration & Documentation - merge 1.2a/b)
**Estimated MVP Completion**: 6 phases, ~24 sprints, highly parallelized
**Progress**: 3/26 sprints complete (Sprint 1.1 ✅, 1.2a ✅, 1.2b ✅)

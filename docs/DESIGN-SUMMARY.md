# beads-ralph Design Summary

Comprehensive design documentation for autonomous multi-agent development system.

## Documentation Created

| Document | Purpose | Status |
|----------|---------|--------|
| [README.md](./README.md) | System overview and quick reference | ✅ Complete |
| [schema.md](./schema.md) | Extended bead schema with validation | ✅ Complete |
| [numbering.md](./numbering.md) | Phase/sprint numbering reference | ✅ Complete |
| [corner-cases.md](./corner-cases.md) | Failure scenarios and mitigations | ✅ Complete |
| [architecture.md](./architecture.md) | System architecture and data flow | ✅ Complete |

## Design Decisions

### 1. Schema Strategy

**Decision**: Store all beads-ralph fields in `Metadata` JSON field

**Rationale**:
- No modifications to beads core schema required
- Backward compatible with standard beads
- Flexible for future extensions
- Can query using beads' existing JSON query capabilities

**Key Fields**:
- **Worktree**: `worktree_path`, `branch`, `source_branch`
- **Execution**: `phase`, `sprint`, `dev_agent_path`, `dev_model`, `dev_prompts`
- **Plan Tracking**: `plan_file`, `plan_section`, `plan_sprint_id` (bi-directional)
- **Agent Tracking**: `scrum_master_session_id`, `dev_agent_session_id`, `dev_agent_executions[]`, `qa_agent_executions[]`
- **Validation**: `qa_agents[]`, `max_retry_attempts`, `attempt_count`
- **Results**: `pr_url`, `pr_number`, `scrum_result`

**Bi-directional Tracking**: Plan files are back-annotated with bead IDs using HTML comments (`<!-- beads-ralph: bd-abc123 -->`), enabling easy navigation between plan and implementation.

**Agent Resurrection**: All agent session IDs are preserved, allowing future questions or debugging of specific work items.

### 2. Numbering Scheme & Dependency Mapping

**Decision**: Adopt synaptic-canvas phase/sprint numbering and compile to bead dependencies

**Format**:
- Phase: `<number>[<letter>]*` (e.g., `1`, `3a`, `3ab`)
- Sprint: `<phase>.<number>[<letter>]*` (e.g., `1.1`, `3a.2b`)

**Benefits**:
- Natural parallel execution support (letter suffixes)
- Clear hierarchical structure
- Regex-validatable
- Human-readable

**Dependency Compilation Rules**:
- Sequential `1.1 → 1.2`: `1.2` depends on `1.1`
- Parallel `1.2a`, `1.2b`: No dependency between them, both depend on `1.1`
- Merge `1.3` after `1.2a`, `1.2b`: `1.3` depends on [`1.2a`, `1.2b`]
- Phase split `2 → 3a`, `3b`: `3a.1` and `3b.1` both depend on last sprint of phase `2`
- Phase converge `3a`, `3b → 4`: `4.1` depends on last sprints of both `3a` and `3b`

**Key Insight**: Phase/sprint numbering is a human-friendly encoding that gets compiled into beads dependencies at planning time. Ralph loop is agnostic to numbering—it only sees the dependency graph via `bd ready`.

### 3. Orchestration Model

**Decision**: Go executable launching parallel Claude sessions (scrum-masters)

**Rationale**:
- Go provides concurrency primitives (goroutines, channels)
- Direct control over parallelism limits
- Better error handling than pure bash
- Cross-platform support
- Easy integration with beads CLI

**Architecture**:
```
Go Ralph Loop
  ├─> Scrum-Master 1 (Claude session)
  │     ├─> Dev Agent (Claude sub-session)
  │     └─> QA Agents (Claude sub-sessions)
  ├─> Scrum-Master 2 (Claude session)
  │     ├─> Dev Agent
  │     └─> QA Agents
  └─> Scrum-Master N (Claude session)
        ├─> Dev Agent
        └─> QA Agents
```

### 4. QA Integration

**Decision**: Structured JSON input/output with pass/fail/stop status

**Benefits**:
- Automated retry loop (dev fixes based on QA feedback)
- Multiple QA agents per bead (tests, lint, security)
- Clear failure semantics (fail = retry, stop = fatal)
- Extensible (add new QA agents without code changes)

**QA Status Semantics**:
- `pass` - Continue to next step
- `fail` - Dev agent should fix and retry
- `stop` - Critical failure, do not retry (security, unrecoverable error)

### 5. Failure Handling

**Decision**: Multi-tier failure mitigation with rollback support

**Tiers**:
1. **Automatic Retry**: Dev/QA loop (max N attempts)
2. **Scrum-Master Retry**: PR creation, bead update failures
3. **Fatal Stop**: Security issues, max retries exceeded, infrastructure failure
4. **Manual Recovery**: Human intervention for fatal errors

**Rollback Strategy**:
- Complete git history preserved
- Worktrees isolated (easy to delete/recreate)
- PRs unmerged (easy to close)
- Beads track attempt history (comments)

### 6. Worktree Strategy

**Decision**: One worktree per sprint, persistent until all work complete, following sc-git-worktree convention

**Path Pattern**: `../<repo-name>-worktrees/<branch-name>`

**Example**:
- Repo: `/Users/dev/projects/my-app/`
- Worktrees: `/Users/dev/projects/my-app-worktrees/<branch-name>`
- Sprint 1.2 branch `main/1-2-auth-api` → `/Users/dev/projects/my-app-worktrees/main/1-2-auth-api`

**Benefits**:
- Complete isolation between sprints
- No cross-contamination
- Can inspect worktrees post-execution
- Easy cleanup (delete sibling directory)
- Consistent with sc-git-worktree skill/agents
- Worktrees as siblings to repo (clean separation)

**Tradeoffs**:
- Disk space usage (N worktrees × repo size)
- Worktree creation time
- Accepted for MVP (optimize later if needed)

### 7. Concurrency Control

**Decision**: Atomic bead claiming via `bd claim` (CAS)

**Rationale**:
- Prevents race conditions
- Database-level guarantee
- Works with multiple Go processes
- No distributed locking needed

**Implementation**: `UPDATE issues SET assignee='...' WHERE id='...' AND assignee=''`

### 8. Planning Process

**Decision**: Three-agent planning system with validation

**Agents**:
1. **beads-ralph-planner** (skill) - Works with user to refine plan
2. **beads-architect** (agent) - Converts plan to beads
3. **plan-review** (agent) - Validates schema and dependencies

**Benefits**:
- Separation of concerns
- Iterative refinement
- Validation before execution
- Prevents invalid configurations

## Key Design Patterns

### 1. Orchestrator Pattern

Scrum-master orchestrates dev and QA agents, making all state changes:

```
Scrum-Master (orchestrator)
  ├─> Spawns dev agent
  ├─> Collects dev result
  ├─> Spawns QA agents
  ├─> Collects QA results
  ├─> Decides: retry or proceed
  ├─> Creates PR
  └─> Updates bead
```

**Not**: Dev agent updating beads or launching QA directly

### 2. Retry Loop Pattern

Dev/QA retry loop with feedback:

```python
for attempt in range(1, max_attempts + 1):
    run_dev_agent()
    qa_results = run_qa_agents()

    if any_stop(qa_results):
        return FATAL

    if all_pass(qa_results):
        return SUCCESS

    feedback = collect_failures(qa_results)
    pass_feedback_to_dev(feedback)

return FATAL  # Max attempts reached
```

### 3. Structured Output Pattern

QA agents return structured JSON with defined schema:

```json
{
  "status": "pass|fail|stop",
  "message": "Human-readable summary",
  "details": {
    // Agent-specific fields
  }
}
```

Enables automated processing and feedback loops.

### 4. Dependency Graph Pattern

Sprints encoded as dependency chains:

```
Sprint 1.1 ──blocks──> Sprint 1.2a ──┐
                                      ├──> Sprint 1.3
Sprint 1.1 ──blocks──> Sprint 1.2b ──┘
```

`bd ready` respects dependencies, ensuring correct execution order.

### 5. Isolation Pattern

Each sprint works in isolated environment:

- **Git worktree** - Separate working directory
- **Branch** - Independent commit history
- **PR** - Isolated review
- **Bead** - Independent task tracking

No shared state between sprints.

## Schema Validation

### Required Validations

1. **Phase Pattern**: `^[0-9]+[a-z]*$`
2. **Sprint Pattern**: `^[0-9]+[a-z]*\.[0-9]+[a-z]*$`
3. **Required Fields**: All metadata fields present
4. **QA Agent Schema**: Each QA has valid output_schema
5. **File Existence**: Agent paths exist
6. **Dependency Graph**: No cycles
7. **Worktree Paths**: No conflicts

### Validation Tools

- **Pydantic Models**: `scripts/bead_schema.py` - Type-safe schema definitions using pydantic v2
- **Python Script**: `scripts/validate-bead-schema.py` - CLI tool using pydantic models
- **Plan Review Agent**: Validates during planning using pydantic models
- **Go Ralph Loop**: Pre-flight checks before execution

## Corner Cases Covered

Comprehensive analysis of 30+ failure scenarios across 7 categories:

1. **Scrum-Master Failures** (4 scenarios)
2. **Dev Agent Failures** (3 scenarios)
3. **QA Agent Failures** (4 scenarios)
4. **Infrastructure Failures** (6 scenarios)
5. **Concurrency Failures** (2 scenarios)
6. **Schema/Configuration Failures** (3 scenarios)
7. **Merge-Specific Failures** (2 scenarios)

Each scenario includes:
- Detection method
- Root causes
- Mitigation strategy
- Recovery procedure
- Implementation examples

## Implementation Roadmap

### Phase 1: Schema & Validation (Priority 1)

- [ ] Implement pydantic v2 models for bead schema
- [ ] Create schema validation CLI tool using pydantic
- [ ] Create example beads (work and merge types)
- [ ] Test phase/sprint numbering patterns
- [ ] Validate worktree path generation

**Deliverables**:
- `scripts/bead_schema.py` (pydantic models)
- `scripts/validate-bead-schema.py` (CLI using models)
- `examples/example-work-bead.json`
- `examples/example-merge-bead.json`

### Phase 2: Go Ralph Loop (Priority 2)

- [ ] Implement core loop (find ready, launch scrum-masters)
- [ ] Implement bead claiming logic
- [ ] Implement result processing
- [ ] Add configuration loading
- [ ] Add logging and error handling

**Deliverables**:
- `src/main.go`
- `src/ralph/loop.go`
- `src/ralph/scrum_master.go`
- `src/config/config.go`

### Phase 3: Agents & Skills (Priority 3)

- [ ] Define beads-ralph-scrum-master agent
- [ ] Define beads-ralph-planner skill
- [ ] Define beads-architect agent
- [ ] Define plan-review agent
- [ ] Define example dev agents (backend, frontend, merge)
- [ ] Define example QA agents (tests, security, lint)

**Deliverables**:
- `.claude/agents/beads-ralph-scrum-master.md`
- `.claude/skills/beads-ralph-planner/SKILL.md`
- `.claude/agents/beads-architect.md`
- `.claude/agents/plan-review.md`
- `.claude/agents/backend-dev.md` (example)
- `.claude/agents/qa-unit-tests.md` (example)

### Phase 4: Integration Testing (Priority 4)

- [ ] Create test plan (simple 2-sprint project)
- [ ] Run end-to-end test
- [ ] Validate PRs created correctly
- [ ] Test failure scenarios
- [ ] Test rollback procedures

**Deliverables**:
- `examples/test-plan.md`
- Test results documentation
- Failure scenario test cases

### Phase 5: Production Hardening (Priority 5)

- [ ] Add monitoring and metrics
- [ ] Implement status commands
- [ ] Add pre-flight disk space checks
- [ ] Implement rate limiting
- [ ] Add comprehensive logging
- [ ] Create user documentation

**Deliverables**:
- User guide
- Operator manual
- Troubleshooting guide

## Open Questions & Future Work

### MVP Scope

**In Scope**:
- ✅ Core ralph loop
- ✅ Parallel sprint execution
- ✅ Dev/QA retry loops
- ✅ PR creation
- ✅ Basic error handling

**Out of Scope (Post-MVP)**:
- ❌ Human escalation beads
- ❌ Automatic rollback on failure
- ❌ Multi-machine distribution
- ❌ Web dashboard
- ❌ Advanced merge strategies
- ❌ Cost optimization
- ❌ Dynamic agent selection

### Future Enhancements

1. **Escalation System**: Create escalation beads for human review on fatal errors
2. **Smart QA**: Only run affected tests (incremental testing)
3. **Merge Intelligence**: ML-based conflict resolution
4. **Cost Tracking**: Track API costs per sprint/phase
5. **Model Selection**: Choose model based on task complexity
6. **Distributed**: Multi-machine coordination via Dolt
7. **Dashboard**: Real-time monitoring web UI
8. **Learning**: Track patterns, auto-improve prompts
9. **Integration Tests**: Cross-sprint integration testing
10. **Approval Gates**: Human approval for high-risk changes

## Success Criteria

### MVP Success Metrics

1. **Correctness**: 90%+ of sprints complete without fatal errors
2. **Automation**: 100% autonomous execution (no manual intervention during run)
3. **Parallelism**: 5+ concurrent sprints executing successfully
4. **Recovery**: Graceful handling of QA failures (retry loops work)
5. **Audit**: Complete git history for all changes
6. **Review**: All PRs created and ready for human review

### Production Success Metrics

1. **Throughput**: 10+ sprints per hour
2. **Success Rate**: 95%+ sprints complete on first attempt
3. **Mean Time to PR**: <15 minutes per sprint
4. **Rollback Rate**: <5% of sprints require rollback
5. **Fatal Error Rate**: <2% of sprints hit fatal errors

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Claude API rate limits | High | High | Rate limiting, backoff, parallelism control |
| Disk space exhaustion | Medium | High | Pre-flight checks, cleanup automation |
| Merge conflicts | Medium | Medium | Merge specialist agent, human escalation |
| QA false positives | Medium | Medium | QA agent tuning, multi-agent validation |
| Network partitions | Low | High | Retry logic, local state preservation |
| Schema corruption | Low | High | Validation at planning phase, runtime checks |
| Dependency cycles | Low | High | Cycle detection, validation before creation |
| Security vulnerabilities | Low | Critical | Security QA agent with `stop` semantics |

## Next Steps

1. **Review Design**: User reviews all documentation
2. **Create Implementation Repo**: Set up actual beads-ralph repository
3. **Phase 1 Implementation**: Schema validation scripts
4. **Test with Simple Plan**: 2-3 sprint example
5. **Iterate**: Refine based on learnings

## Contact & Questions

This design documentation was created in the `github-research` repository as a reference for implementing beads-ralph. When ready to implement, create a new repository and copy these design documents as a starting point.

**Design Philosophy**:
- Start simple, evolve incrementally
- Validate early and often
- Fail fast with clear error messages
- Preserve audit trail for debugging
- Human review as final gate
- 100% autonomous between planning and review

---

**Status**: Design Complete ✅
**Next Phase**: Implementation Planning
**Created**: 2026-02-07

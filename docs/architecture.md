# beads-ralph Architecture

System architecture for autonomous multi-agent development with parallel execution.

## System Overview

beads-ralph is a Go-based orchestration system that coordinates multiple Claude Code agents working in parallel on isolated git worktrees. It combines:

- **beads** - Git-backed issue tracker for work coordination
- **Claude Code** - AI agents for development and QA
- **Git worktrees** - Isolated work environments
- **GitHub** - Pull request workflow for review

```
┌────────────────────────────────────────────────────────────────┐
│                         User Input                              │
│  • Root branch                                                  │
│  • Plan (markdown with phases/sprints)                          │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                   Planning Phase (Claude)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ beads-ralph-planner skill                                │  │
│  │  • Works with user to refine plan                        │  │
│  │  • Validates structure and completeness                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ beads-mason agent                                    │  │
│  │  • Converts plan to beads with extended schema           │  │
│  │  • Creates merge beads for integration                   │  │
│  │  • Sets up dependency chains for sprints                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ plan-review agent                                        │  │
│  │  • Validates bead schema                                 │  │
│  │  • Checks for dependency cycles                          │  │
│  │  • Verifies phase/sprint numbering                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                    Beads Database (SQLite)                      │
│  • Extended schema with worktree, branch, agents, QA           │
│  • Dependencies control sprint ordering                         │
│  • Labels for phase/sprint grouping                             │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                Go Ralph Loop (Orchestrator)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Find ready beads (bd ready)                           │  │
│  │ 2. Group by team_name (metadata.team_name)               │  │
│  │ 3. Launch parallel scrum-master sessions (one per team)  │  │
│  │ 4. Monitor completion                                    │  │
│  │ 5. Advance to next team                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Scrum-Master 1  │  │  Scrum-Master 2  │  │  Scrum-Master N  │
│  (Claude)        │  │  (Claude)        │  │  (Claude)        │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        ↓                     ↓                     ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Dev Agent       │  │  Dev Agent       │  │  Dev Agent       │
│  (Claude)        │  │  (Claude)        │  │  (Claude)        │
│  Worktree A      │  │  Worktree B      │  │  Worktree C      │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        ↓                     ↓                     ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  QA Agents       │  │  QA Agents       │  │  QA Agents       │
│  (Claude)        │  │  (Claude)        │  │  (Claude)        │
│  • Unit tests    │  │  • Unit tests    │  │  • Unit tests    │
│  • Security scan │  │  • Security scan │  │  • Security scan │
│  • Lint check    │  │  • Lint check    │  │  • Lint check    │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        ↓                     ↓                     ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  PR Created      │  │  PR Created      │  │  PR Created      │
│  Branch A        │  │  Branch B        │  │  Branch C        │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                    User Review Phase                            │
│  • Review PRs on GitHub                                         │
│  • Merge approved PRs                                           │
│  • Request changes if needed                                    │
│  • Complete git history for rollback                            │
└────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Planning System

#### 1.1 beads-ralph-planner Skill

**Type**: Claude Code Skill (`.claude/skills/beads-ralph-planner/SKILL.md`)

**Responsibilities**:
- Work with user to refine plan structure
- Validate phase/sprint organization
- Ensure plan is optimized for parallel execution
- Delegate to beads-mason for bead creation

**Input**:
```markdown
# plan.md

## Phase 1: Project Setup
### Sprint 1.1: Initialize Project
- Set up repository structure
- Configure CI/CD
- Add initial documentation

### Sprint 1.2: Setup Development Environment
- Create Docker dev environment
- Configure IDE settings
- Add development scripts

## Phase 2: Backend Development
### Sprint 2.1a: User API (parallel)
- Implement user CRUD endpoints
- Add authentication middleware

### Sprint 2.1b: Product API (parallel)
- Implement product CRUD endpoints
- Add search functionality

### Sprint 2.2: Integration (merge)
- Merge user and product APIs
- Integration tests
```

**Output**: Validated plan ready for bead creation

#### 1.2 beads-mason Agent

**Type**: Claude Code Agent (`.claude/agents/beads-mason.md`)

**Responsibilities**:
- Convert finalized plan into beads with extended schema
- Create work beads for each sprint
- Create merge beads for integration sprints
- Set up dependency chains
- Validate schema compliance

**Algorithm**:
```python
def create_beads(plan):
    beads = []
    prev_sprint_beads = {}

    for phase in plan.phases:
        for sprint in phase.sprints:
            bead = create_work_bead(sprint)

            # Add dependencies on previous sprint(s)
            if sprint.is_merge:
                # Merge sprint depends on all parallel sprints it merges
                bead.dependencies = get_parallel_sprint_beads(sprint)
            else:
                # Regular sprint depends on previous sequential sprint
                prev = get_previous_sprint(sprint)
                if prev in prev_sprint_beads:
                    bead.dependencies = [prev_sprint_beads[prev]]

            beads.append(bead)
            prev_sprint_beads[sprint.id] = bead.id

    return beads

def create_work_bead(sprint):
    return {
        "title": sprint.title,
        "description": sprint.description,
        "issue_type": "beads-ralph-merge" if sprint.is_merge else "beads-ralph-work",
        "assignee": "beads-ralph-scrum-master",
        "metadata": {
            "worktree_path": generate_worktree_path(sprint),
            "branch": generate_branch_name(sprint),
            "source_branch": sprint.source_branch,
            "phase": sprint.phase,
            "sprint": sprint.sprint,
            "team_name": generate_team_name(sprint),
            "scrum_master_agent": create_agent_spec(
                role="polecat",
                agent=".claude/agents/beads-ralph-scrum-master.md",
                model=select_model_for_scrum_master(sprint),
                context=f"Sprint {sprint.sprint} - {sprint.title}"
            ),
            "dev_agents": [
                create_agent_spec(
                    role="polecat",
                    agent=select_dev_agent(sprint),
                    model=select_model_for_dev(sprint),
                    context=sprint.description
                )
            ],
            "dev_prompts": extract_prompts(sprint),
            "qa_agents": select_qa_agent_specs(sprint),
            "max_retry_attempts": 3
        }
    }
```

**Output**: JSON array of bead definitions ready for creation

#### 1.3 plan-review Agent

**Type**: Claude Code Agent (`.claude/agents/plan-review.md`)

**Responsibilities**:
- Validate bead schema against specification using pydantic models
- Check for dependency cycles
- Verify phase/sprint numbering
- Validate worktree paths and branch names
- Check agent/skill file existence

**Validation Steps**:
1. Schema validation using pydantic models from `scripts/bead_schema.py`
2. Pattern validation (phase/sprint regex)
3. Dependency graph analysis (cycle detection)
4. File existence checks (agents, skills)
5. Worktree path validation (no conflicts)
6. Branch name validation (git-safe names)

**Technology Stack**:
- Python 3.12+ with pydantic v2 for schema validation
- Provides type safety and detailed validation errors

**Output**: Validation report with errors/warnings

---

### 2. Go Ralph Loop

**Type**: Go executable (`src/main.go`)

**Responsibilities**:
- Main orchestration loop
- Find ready beads per sprint
- Launch parallel scrum-master sessions
- Monitor completion
- Handle failures
- Advance sprints

#### 2.1 Core Loop Algorithm

```go
func ralphLoop(ctx context.Context, config Config) error {
    for {
        // 1. Find ready beads
        readyBeads, err := findReadyBeads(ctx, config)
        if err != nil {
            return fmt.Errorf("find ready beads: %w", err)
        }

        if len(readyBeads) == 0 {
            log.Info("No ready beads. All work complete or blocked.")
            break
        }

        // 2. Group by team
        teamGroups := groupByTeam(readyBeads)
        log.Infof("Found %d team(s) ready: %v", len(teamGroups), teamNames(teamGroups))

        // 3. Launch parallel scrum-masters (one Claude session per team)
        var wg sync.WaitGroup
        results := make(chan ScrumResult, len(teamGroups))
        semaphore := make(chan struct{}, config.MaxParallelSessions)

        for teamName, beads := range teamGroups {
            log.Infof("Starting team %s with %d bead(s)", teamName, len(beads))

            for _, bead := range beads {
                wg.Add(1)

                go func(b Bead) {
                    defer wg.Done()

                    // Acquire semaphore (limit parallelism)
                    semaphore <- struct{}{}
                    defer func() { <-semaphore }()

                    result := runScrumMaster(ctx, b, config)
                    results <- result
                }(bead)
            }
        }

        // 4. Wait for all scrum-masters to complete
        wg.Wait()
        close(results)

        // 5. Process results
        allSuccess, fatalError := processResults(results)

        if fatalError != nil {
            return fmt.Errorf("fatal error: %w", fatalError)
        }

        if !allSuccess {
            log.Warn("Some beads failed. Check status and retry.")
            // Continue to next iteration (may have other ready work)
        }
    }

    log.Info("Ralph loop completed successfully.")
    return nil
}
```

#### 2.2 Key Functions

**findReadyBeads**:
```go
func findReadyBeads(ctx context.Context, config Config) ([]Bead, error) {
    cmd := exec.CommandContext(ctx, "bd", "ready",
        "--assignee", "beads-ralph-scrum-master",
        "--json",
        "--limit", "100")

    output, err := cmd.Output()
    if err != nil {
        return nil, err
    }

    var beads []Bead
    if err := json.Unmarshal(output, &beads); err != nil {
        return nil, err
    }

    // Filter by issue type
    filtered := []Bead{}
    for _, bead := range beads {
        if bead.IssueType == "beads-ralph-work" || bead.IssueType == "beads-ralph-merge" {
            filtered = append(filtered, bead)
        }
    }

    return filtered, nil
}
```

**groupByTeam**:
```go
func groupByTeam(beads []Bead) map[string][]Bead {
    groups := make(map[string][]Bead)
    for _, bead := range beads {
        teamName := bead.Metadata.TeamName
        groups[teamName] = append(groups[teamName], bead)
    }
    return groups
}
```

**Note**: Beads are grouped by `metadata.team_name`, not by sprint number. This allows flexible team composition:
- **Scenario 1**: One team with multiple devs on different branches (all beads share same team_name)
- **Scenario 2**: Sequential dev→review→fix→qa workflow (all beads in one team_name)
- **Scenario 3**: Multiple isolated teams for parallel sprints (different team_name values)

**runScrumMaster**:
```go
func runScrumMaster(ctx context.Context, bead Bead, config Config) ScrumResult {
    // 1. Claim bead atomically
    if err := claimBead(ctx, bead.ID); err != nil {
        if err == ErrAlreadyClaimed {
            return ScrumResult{Skipped: true}
        }
        return ScrumResult{Success: false, Error: err.Error()}
    }

    // 2. Build scrum-master prompt
    prompt := buildScrumMasterPrompt(bead, config)

    // 3. Launch Claude Code session
    ctx, cancel := context.WithTimeout(ctx, config.ScrumMasterTimeout)
    defer cancel()

    cmd := exec.CommandContext(ctx, "claude",
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "--agent", ".claude/agents/beads-ralph-scrum-master",
        "-p", prompt)

    output, err := cmd.Output()
    if err != nil {
        return ScrumResult{
            BeadID:  bead.ID,
            Success: false,
            Error:   err.Error(),
        }
    }

    // 4. Parse result
    var result ScrumResult
    if err := parseJSONOutput(output, &result); err != nil {
        return ScrumResult{
            BeadID:  bead.ID,
            Success: false,
            Error:   fmt.Sprintf("parse error: %v", err),
        }
    }

    // 5. Verify PR created and bead updated
    if result.Success && (result.PR_URL == "" || !result.BeadUpdated) {
        return retryScrumMaster(ctx, bead, result, config)
    }

    return result
}
```

---

### 3. Scrum-Master Agent & Agent-Teams Integration

**Type**: Claude Code Agent (`.claude/agents/beads-ralph-scrum-master.md`)

**Responsibilities**:
- Read all beads for this team (from `team_name` grouping)
- Create/verify worktrees using sc-git-worktree skill
- **Use Claude Agent-Teams**: Coordinate multiple agents via TeamCreate
- Launch dev agents with prompts from beads
- Monitor dev agent completion
- Launch QA agents in background
- Implement dev/QA retry loop
- Create PRs using gh CLI
- Update bead statuses and metadata
- Return structured JSON result

**Agent-Teams Integration**:
- **One Claude session per team**: Ralph loop groups beads by `metadata.team_name`
- **Scrum-master orchestrates team**: Uses TeamCreate to coordinate dev/QA agents
- **Flexible team composition**: beads-mason decides team structure (architect's choice)
  - Example: 3 devs on 3 branches, one team (team_name: "sprint-2.1-ui")
  - Example: dev→review→fix→qa sequential, one team (team_name: "sprint-3.1-auth")

#### 3.1 Scrum-Master Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Read Bead & Extract Metadata                        │
│    • bd show <bead-id> --json                           │
│    • Parse metadata: worktree, branch, agents, prompts  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Create/Verify Worktree                               │
│    • /sc-git-worktree:sc-git-worktree create            │
│    • Verify branch exists                               │
│    • cd into worktree                                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Launch Dev Agent                                     │
│    • Use dev_agents[0] AgentSpec from metadata          │
│    • Build command using AgentSpec (role, agent, model) │
│    • Pass dev_prompts from metadata                     │
│    • Wait for completion                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Launch QA Agents (Background)                        │
│    • For each AgentSpec in metadata.qa_agents:          │
│      - Build command using AgentSpec                    │
│      - Launch as background task                        │
│      - Pass worktree, branch, changed files as input    │
│    • Collect all QA results                             │
└─────────────────────────────────────────────────────────┘
                         ↓
                    ┌────────┐
                    │QA Pass?│
                    └────────┘
                    ↙        ↘
              Yes ↙            ↘ No
                 ↓              ↓
    ┌────────────────────┐  ┌──────────────────────────┐
    │ 5a. Create PR      │  │ 5b. Dev/QA Retry Loop    │
    │ • gh pr create     │  │ • Pass QA failures to dev│
    │ • Capture PR URL   │  │ • Re-run dev agent       │
    └────────────────────┘  │ • Re-run QA agents       │
                            │ • Max N attempts         │
                            │ • If still fail: Fatal   │
                            └──────────────────────────┘
                                      ↓
                                (back to QA Pass?)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Update Bead                                          │
│    • bd update <bead-id> --status closed                │
│    • bd update <bead-id> --metadata '{...}'             │
│    • Add PR URL, PR number, scrum result                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 7. Return JSON Result                                   │
│    • Fenced JSON with:                                  │
│      - success, pr_url, pr_number                       │
│      - bead_updated, attempt_count                      │
│      - qa_results, error, fatal                         │
└─────────────────────────────────────────────────────────┘
```

#### 3.2 Dev/QA Retry Loop

```
attempt = 1

while attempt <= max_retry_attempts:
    run_dev_agent()

    qa_results = run_all_qa_agents()

    if any_qa_stopped():
        return FATAL

    if all_qa_passed():
        return SUCCESS

    # QA failed, pass feedback to dev
    feedback = collect_qa_failures(qa_results)
    update_dev_prompt_with_feedback(feedback)

    attempt += 1

# Max attempts reached
return FATAL
```

#### 3.3 Expected JSON Output

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
      "agent": ".claude/agents/qa-unit-tests.md",
      "status": "pass",
      "message": "All tests passed. Coverage: 85%",
      "details": {"total": 42, "passed": 42, "coverage_percent": 85}
    },
    {
      "agent": ".claude/agents/qa-security-scan.md",
      "status": "pass",
      "message": "No vulnerabilities found",
      "details": {"vulnerabilities": []}
    }
  ],
  "error": null,
  "fatal": false
}
```

---

### 4. Dev Agents

**Type**: Claude Code Agents (`.claude/agents/<agent-name>.md`)

**Examples**:
- `backend-dev.md` - Backend development (APIs, services)
- `frontend-dev.md` - Frontend development (UI, components)
- `merge-specialist.md` - Merge conflict resolution
- `test-writer.md` - Test creation and fixes

**Responsibilities**:
- Execute work according to prompts in bead
- Work within designated worktree
- Follow project conventions and patterns
- Create/modify code files
- Run builds/tests locally
- Commit changes to branch

**Key Characteristics**:
- Specialized per work type (backend, frontend, merge, etc.)
- Receive context from scrum-master (worktree, branch, prompts)
- Return when work is complete (no explicit JSON)
- May receive QA feedback and fix issues

**Example Prompt (from scrum-master)**:
```
You are a backend development agent working in beads-ralph sprint 2.1a.

Worktree: /path/to/worktrees/main/2-1a-user-api
Branch: main/2-1a-user-api

Your tasks:
1. Implement user CRUD endpoints in the backend service
2. Follow existing patterns in services/auth/
3. Use bcrypt for password hashing
4. Add integration tests for login and signup endpoints
5. Update API documentation in docs/api.md

When complete, ensure all changes are committed to the branch.
```

---

### 5. QA Agents

**Type**: Claude Code Agents (`.claude/agents/<qa-agent-name>.md`)

**Examples**:
- `qa-unit-tests.md` - Run unit tests, check coverage
- `qa-integration-tests.md` - Run integration tests
- `qa-security-scan.md` - Security scanning (bandit, gosec)
- `qa-lint.md` - Linting and formatting checks
- `qa-type-check.md` - Type checking (TypeScript, mypy)

**Responsibilities**:
- Receive structured input (worktree, branch, changed files)
- Run validation checks (tests, scans, lints)
- Return structured JSON output with status

**Input Schema** (passed by scrum-master):
```json
{
  "worktree_path": "/Users/dev/projects/my-app-worktrees/main/2-1a-user-api",
  "branch": "main/2-1a-user-api",
  "changed_files": ["services/auth/api.go", "services/auth/api_test.go"]
}
```

**Output Schema** (required):
```json
{
  "status": "pass|fail|stop",
  "message": "Human-readable summary",
  "details": {
    // Agent-specific details
  }
}
```

**Status Values**:
- `pass` - Validation succeeded, continue
- `fail` - Validation failed, dev should fix and retry
- `stop` - Critical failure, do not retry (e.g., security issue)

**Example QA Agent (Unit Tests)**:
```markdown
# QA: Unit Tests

You are a QA agent that runs unit tests and checks coverage.

## Input

You will receive JSON with:
- worktree_path: Path to worktree
- branch: Branch name
- changed_files: Array of changed file paths

## Task

1. cd into worktree_path
2. Run unit tests: pytest -v
3. Check coverage: pytest --cov --cov-report=json
4. Parse results

## Output

Return fenced JSON:

'''json
{
  "status": "pass|fail|stop",
  "message": "Summary of test results",
  "details": {
    "total_tests": 42,
    "passed": 42,
    "failed": 0,
    "coverage_percent": 85
  }
}
'''

Status rules:
- pass: All tests passed and coverage >= 80%
- fail: Any tests failed OR coverage < 80%
- stop: Test suite crashed or cannot run
```

---

## Data Flow

### Planning Phase Data Flow

```
User → beads-ralph-planner skill
       ↓
plan.md (validated)
       ↓
beads-mason agent
       ↓
beads_definitions.json
       ↓
plan-review agent (validation)
       ↓
bd create (create beads in database)
       ↓
Beads Database
```

### Execution Phase Data Flow

```
Beads Database
       ↓
bd ready (Go ralph loop)
       ↓
[Bead 1, Bead 2, ...Bead N] (grouped by sprint)
       ↓
Launch N parallel scrum-masters (Go goroutines)
       ├─────────────────┬─────────────────┐
       ↓                 ↓                 ↓
Scrum-Master 1    Scrum-Master 2    Scrum-Master N
       ↓                 ↓                 ↓
bd claim (atomic)  bd claim (atomic)  bd claim (atomic)
       ↓                 ↓                 ↓
Create worktree    Create worktree    Create worktree
       ↓                 ↓                 ↓
Launch dev agent   Launch dev agent   Launch dev agent
       ↓                 ↓                 ↓
Code changes       Code changes       Code changes
       ↓                 ↓                 ↓
Launch QA agents   Launch QA agents   Launch QA agents
       ↓                 ↓                 ↓
QA pass/fail       QA pass/fail       QA pass/fail
       ↓                 ↓                 ↓
Create PR          Create PR          Create PR
       ↓                 ↓                 ↓
bd update (status) bd update (status) bd update (status)
       ↓                 ↓                 ↓
Return result      Return result      Return result
       └─────────────────┴─────────────────┘
                         ↓
              Process results (Go)
                         ↓
              Next iteration of ralph loop
```

---

## Concurrency Model

### Parallelism Levels

1. **Sprint-Level Parallelism**: Multiple sprints with same base number run in parallel
   - Example: `1.2a` and `1.2b` run concurrently
   - Controlled by bead dependencies

2. **Bead-Level Parallelism**: Multiple beads within same sprint run in parallel
   - Example: Sprint `2.1` has 3 beads, all run concurrently
   - Limited by configuration: `max_parallel_sessions`

3. **QA-Level Parallelism**: Multiple QA agents run in parallel per bead
   - All QA agents for a bead launch simultaneously
   - Results collected and evaluated together

### Synchronization Points

1. **Sprint Boundaries**: Sprint `1.3` waits for `1.2a` and `1.2b` to complete
   - Enforced by bead dependencies
   - `bd ready` only returns beads with no open blockers

2. **Dev/QA Boundary**: QA agents wait for dev agent to complete
   - Sequential within scrum-master
   - Dev completes → QA launches

3. **Bead Claiming**: Atomic claim via `bd claim` (CAS operation)
   - Prevents two scrum-masters from working on same bead
   - Database-level synchronization

### Concurrency Safety

**Thread-Safe Operations**:
- `bd claim` - Atomic compare-and-swap
- `bd update` - Serialized via beads daemon (RPC)
- `bd ready` - Read-only, no locks needed

**Isolation Mechanisms**:
- **Git worktrees** - Separate working directories per bead
- **Beads daemon** - Single-writer architecture (Unix domain socket)
- **PR branches** - Independent branches per sprint

**No Shared State**:
- Each scrum-master operates independently
- No shared memory between scrum-masters
- Communication only via beads database

---

## Configuration

### beads-ralph.yaml

```yaml
# Ralph loop configuration
ralph:
  max_parallel_sessions: 10       # Max concurrent scrum-masters
  poll_interval: 5s                # Interval between ready bead checks

# Timeouts
timeouts:
  scrum_master: 30m                # Max time for scrum-master
  dev_agent: 20m                   # Max time for dev agent
  qa_agent: 10m                    # Max time per QA agent

# Retry configuration
retry:
  max_attempts: 3                  # Max dev/QA retry loop iterations
  pr_creation_retries: 2           # Max retries for PR creation

# Worktree configuration
worktrees:
  # Worktrees placed as sibling to repository: ../<repo-name>-worktrees/
  # Example: For repo "my-app" at /Users/dev/projects/my-app
  #          Worktrees go in /Users/dev/projects/my-app-worktrees/
  repo_name: "my-app"              # Repository name (auto-detected if not set)
  source_branch: "main"
  cleanup_on_complete: false       # Keep worktrees after completion

# Disk space checks
disk:
  min_free_gb: 10                  # Refuse to start if less than this
  check_before_start: true

# Network configuration
network:
  max_retries: 5
  retry_backoff: exponential
  timeout: 30s

# Claude API configuration
claude:
  max_parallel_sessions: 10        # Respect rate limits
  rate_limit_backoff: exponential
  max_retries: 5

# Logging
logging:
  level: info                      # debug, info, warn, error
  format: json                     # json, text
  file: "beads-ralph.log"
```

---

## Deployment Architecture

### Local Development

```
Developer Machine: /Users/dev/projects/
├── my-app/                          # Main repository
│   ├── .git/
│   ├── .beads/                      # Beads database
│   ├── src/
│   └── beads-ralph                  # Go executable
│
└── my-app-worktrees/                # Worktrees (sibling directory)
    ├── main/1-1-project-setup/      # Sprint 1.1 worktree
    ├── main/1-2-environment/        # Sprint 1.2 worktree
    └── main/2-1a-user-api/          # Sprint 2.1a worktree
```

**Key Convention**: Worktrees are placed in `../<repo-name>-worktrees/` following sc-git-worktree standard.

### CI/CD Integration (Future)

```
GitHub Actions Runner
├── Checkout repo
├── Install beads, Claude Code
├── Run beads-ralph
├── Collect PRs
├── Post status to GitHub
```

### Multi-Machine (Future)

```
Machine 1: Ralph loop + beads daemon
Machine 2-N: Remote scrum-masters
All machines: Shared beads via Dolt remotes
```

---

## Monitoring & Observability

### Metrics (Future)

- **Throughput**: Beads completed per hour
- **Latency**: Average time per bead
- **Success Rate**: % of beads completed successfully
- **Retry Rate**: % of beads requiring retries
- **QA Failure Rate**: % by QA agent type
- **Parallelism**: Average concurrent scrum-masters

### Logging

**Ralph Loop**:
```
[INFO] Starting ralph loop (max 10 parallel sessions)
[INFO] Found 3 sprint(s) ready: [1.2a, 1.2b, 1.3]
[INFO] Starting sprint 1.2a with 2 bead(s)
[INFO] Launching scrum-master for bead bd-abc123
```

**Scrum-Master**:
```
[INFO] [bd-abc123] Claimed bead: Implement user API
[INFO] [bd-abc123] Creating worktree: /worktrees/main/2-1a-user-api
[INFO] [bd-abc123] Launching dev agent: backend-dev
[INFO] [bd-abc123] Dev agent completed
[INFO] [bd-abc123] Launching 2 QA agent(s)
[INFO] [bd-abc123] QA passed on attempt 1
[INFO] [bd-abc123] Creating PR: main/2-1a-user-api
[INFO] [bd-abc123] PR created: #42
[INFO] [bd-abc123] Updated bead status: closed
[INFO] [bd-abc123] Scrum-master completed successfully
```

### Status Commands (Future)

```bash
# Show active sprints
beads-ralph status

# Show detailed bead status
beads-ralph status --bead bd-abc123

# Show QA failure summary
beads-ralph qa-report

# Show stuck beads
beads-ralph blocked
```

---

## Security Considerations

1. **Credential Management**: `--dangerously-skip-permissions` mode requires trusted environment
2. **Code Review**: All PRs reviewed by humans before merge
3. **QA Validation**: Security scans required for all changes
4. **Worktree Isolation**: Prevents cross-contamination between sprints
5. **Audit Trail**: Complete git history of all changes

---

## Performance Characteristics

### Expected Throughput

- **Sequential sprints**: 1 sprint per (dev time + QA time + PR time)
- **Parallel sprints**: N sprints per (max dev time + QA time + PR time)
- **Typical times**:
  - Dev agent: 5-15 minutes
  - QA agents: 2-5 minutes
  - PR creation: 30 seconds
  - Total per bead: 10-20 minutes

### Scalability

- **Local**: 10-20 parallel scrum-masters (CPU/memory limited)
- **Multi-machine** (future): 50-100 parallel scrum-masters
- **Bottlenecks**:
  - Claude API rate limits
  - Git operations (fetch/push)
  - Disk I/O (worktree creation)

---

## Future Enhancements

1. **Dynamic Agent Selection**: Choose agents based on code analysis
2. **Incremental QA**: Only run affected tests
3. **Smart Merge**: Automatic merge conflict resolution
4. **Cost Optimization**: Model selection based on complexity
5. **Distributed Execution**: Multi-machine coordination via Dolt
6. **Human Escalation**: Create escalation beads for review
7. **Learning System**: Track patterns, improve agent prompts
8. **Dashboard**: Real-time web UI for monitoring
9. **Rollback Automation**: Automatic rollback on failures
10. **Integration Testing**: Cross-sprint integration tests

# beads-ralph Schema Design

Extended bead schema for autonomous multi-agent development with parallel execution.

## Repository References

This document references the following external repositories. These should be checked out locally as siblings to this repository. If not available locally, please check them out before proceeding.

| Repository | GitHub URL | Local Path | Purpose |
|------------|------------|------------|---------|
| beads | https://github.com/steveyegge/beads | `../beads/` | Base schema and storage system |
| synaptic-canvas | *(Ask user for URL)* | `../synaptic-canvas/` | Source of phase/sprint numbering scheme |

## Schema Overview

beads-ralph extends the standard beads schema by adding fields to the `Metadata` JSON object. All custom fields are stored in `Metadata` to avoid modifying beads core schema.

## Core Bead Fields (Standard)

These fields are part of the base beads schema and used as-is:

| Field | Type | Usage |
|-------|------|-------|
| `ID` | string | Unique identifier (e.g., `bd-a1b2`) |
| `Title` | string | Work item title |
| `Description` | string | Detailed description |
| `Status` | string | `open`, `in_progress`, `closed`, `blocked` |
| `Priority` | int | 0-4 (0=critical, 4=minimal) |
| `IssueType` | string | `beads-ralph-work`, `beads-ralph-merge` |
| `Assignee` | string | `beads-ralph-scrum-master` |
| `Owner` | string | Creator/owner |
| `Dependencies[]` | array | Dependency relationships (controls sprint order) |
| `Labels[]` | array | Tags (e.g., `phase-01`, `sprint-1-2`) |
| `Comments[]` | array | Dev/QA interaction history |
| `Metadata` | JSON | **All beads-ralph custom fields** |
| `ExternalRef` | string | PR URL after creation |
| `CreatedAt` | timestamp | Creation time |
| `UpdatedAt` | timestamp | Last update time |
| `ClosedAt` | timestamp | Completion time |

## Extended Schema (Metadata JSON)

All beads-ralph-specific fields are stored in the `Metadata` JSON object:

### Work Identification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `worktree_path` | string | Yes | Absolute path to worktree on disk |
| `branch` | string | Yes | Branch name for this work |
| `source_branch` | string | Yes | Branch to create worktree from (e.g., "main") |
| `phase` | string | Yes | Phase number (e.g., "1", "3a", "3ab") |
| `sprint` | string | Yes | Sprint number (e.g., "1.1", "3a.2b") |

### Plan Tracking (Bi-directional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_file` | string | Yes | Path to original plan file (e.g., "plans/feature-x.md") |
| `plan_section` | string | Yes | Section identifier in plan (line numbers or heading anchor) |
| `plan_sprint_id` | string | Yes | Sprint ID as written in plan (for back-annotation) |

### Phase/Sprint Numbering

Following synaptic-canvas numbering scheme:

**Phase Pattern**: `^[0-9]+[a-z]*$`
- Examples: `1`, `2`, `3a`, `3b`, `12`, `3ab`
- Letter suffixes indicate parallel phase tracks

**Sprint Pattern**: `^[0-9]+[a-z]*\.[0-9]+[a-z]*$`
- Examples: `1.1`, `3a.2`, `3b.2a`, `3b.2b`
- Format: `<phase>.<sprint-number>[<letter>]*`
- Letter suffixes indicate parallel sprints within a phase

**Parallel Execution Rules**:
- Sequential: `1.1 → 1.2 → 1.3` (run in order)
- Parallel sprints: `1.2a`, `1.2b` (run concurrently)
- Phase split: `3a`, `3b` (independent tracks)
- Nested parallel: `3a.2a`, `3a.2b` (parallel within parallel phase)

**Mapping to Bead Dependencies**:

Phase/sprint numbering encodes execution semantics that must be converted to explicit bead dependencies:

| Sprint Pattern | Dependency Rule |
|----------------|-----------------|
| Sequential: `1.1 → 1.2` | `1.2` depends on `1.1` |
| Parallel: `1.2a`, `1.2b` | No dependency between them, both depend on `1.1` |
| Merge: `1.3` after `1.2a`, `1.2b` | `1.3` depends on [`1.2a`, `1.2b`] |
| Phase split: `2 → 3a`, `3b` | `3a.1` and `3b.1` both depend on last sprint of phase `2` |
| Phase converge: `3a`, `3b → 4` | `4.1` depends on last sprints of both `3a` and `3b` |

**Example (Parallel with Merge)**:
```
Plan:
  Sprint 1.1: Setup
  Sprint 1.2a: Backend (parallel)
  Sprint 1.2b: Frontend (parallel)
  Sprint 1.3: Integration (merge)

Generated Dependencies:
  1.1: []              # No blockers
  1.2a: ["1.1"]        # Waits for setup
  1.2b: ["1.1"]        # Waits for setup
  1.3: ["1.2a", "1.2b"] # Merge waits for BOTH

Execution:
  Iteration 1: bd ready → [bd-aaa]         (1.1)
  Iteration 2: bd ready → [bd-bbb, bd-ccc] (1.2a and 1.2b in parallel)
  Iteration 3: bd ready → [bd-ddd]         (1.3 after both)
```

The **beads-architect agent** is responsible for parsing phase/sprint numbers and generating correct dependency relationships when creating beads.

### Dev Agent Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dev_agent_path` | string | Yes | Path to dev agent (e.g., ".claude/agents/backend-dev") |
| `dev_model` | string | Yes | Model for dev agent ("sonnet", "opus", "haiku") |
| `dev_prompts` | string[] | Yes | Array of prompts for dev agent |

### QA Agent Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `qa_agents` | QAAgent[] | Yes | Array of QA agent specifications |

**QAAgent Object Schema**:

```json
{
  "agent_path": "string",      // Path to QA agent (e.g., ".claude/agents/qa-unit-tests")
  "model": "string",           // Model for QA agent ("sonnet", "opus", "haiku")
  "prompt": "string",          // Prompt for QA agent
  "input_schema": {            // JSON Schema for QA input (optional)
    "type": "object",
    "properties": {
      "worktree_path": {"type": "string"},
      "branch": {"type": "string"},
      "changed_files": {"type": "array", "items": {"type": "string"}}
    }
  },
  "output_schema": {           // JSON Schema for QA output (required)
    "type": "object",
    "properties": {
      "status": {"enum": ["pass", "fail", "stop"]},
      "message": {"type": "string"},
      "details": {"type": "object"}
    },
    "required": ["status", "message"]
  }
}
```

**QA Output Status Values**:
- `pass` - Validation succeeded, continue to next step
- `fail` - Validation failed, dev agent should fix and retry
- `stop` - Critical failure, do not retry (e.g., security vulnerability)

### Retry Logic

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `max_retry_attempts` | int | No | 3 | Maximum dev/QA retry loop iterations |
| `attempt_count` | int | No | 0 | Current retry attempt count |

### Agent Execution Tracking

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scrum_master_session_id` | string | No | Claude session ID of scrum-master (for resurrection) |
| `dev_agent_session_id` | string | No | Claude session ID of dev agent that did the work |
| `dev_agent_executions` | DevExecution[] | No | History of all dev agent execution attempts |
| `qa_agent_executions` | QAExecution[] | No | History of all QA agent executions |

**DevExecution Object Schema**:

```json
{
  "attempt": 1,                          // Attempt number (1, 2, 3...)
  "session_id": "string",                // Claude session ID
  "agent_path": ".claude/agents/backend-dev",
  "model": "sonnet",
  "started_at": "2026-02-07T10:00:00Z",
  "completed_at": "2026-02-07T10:15:00Z",
  "status": "completed|failed|timeout",
  "feedback_from_qa": "string"           // QA feedback if this was a retry
}
```

**QAExecution Object Schema**:

```json
{
  "attempt": 1,                          // Which dev attempt this validated
  "session_id": "string",                // Claude session ID
  "agent_path": ".claude/agents/qa-unit-tests",
  "model": "haiku",
  "started_at": "2026-02-07T10:16:00Z",
  "completed_at": "2026-02-07T10:18:00Z",
  "status": "pass|fail|stop",
  "message": "All tests passed. Coverage: 85%",
  "details": {}                          // Agent-specific result details
}
```

### Output Tracking

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pr_url` | string | No | GitHub PR URL (populated after creation) |
| `pr_number` | int | No | GitHub PR number |
| `scrum_result` | ScrumResult | No | Final result from scrum-master |

**ScrumResult Object Schema**:

```json
{
  "bead_id": "string",         // Bead ID being worked on
  "success": boolean,          // Overall success status
  "pr_url": "string",          // PR URL if created
  "pr_number": int,            // PR number if created
  "bead_updated": boolean,     // Whether bead status was updated
  "attempt_count": int,        // Final retry attempt count
  "qa_results": [              // Results from all QA agents
    {
      "agent_path": "string",
      "status": "pass|fail|stop",
      "message": "string",
      "details": {}
    }
  ],
  "error": "string",           // Error message if failed
  "fatal": boolean             // If true, stop ralph loop
}
```

## Complete Bead Example (Work Bead)

```json
{
  "id": "bd-a1b2c3",
  "title": "Implement user authentication API",
  "description": "Create authentication endpoints for user login and signup",
  "status": "open",
  "priority": 1,
  "issue_type": "beads-ralph-work",
  "assignee": "beads-ralph-scrum-master",
  "dependencies": ["bd-xyz123"],
  "labels": ["phase-01", "sprint-1-2", "backend"],
  "metadata": {
    "worktree_path": "/Users/dev/projects/my-app-worktrees/main/1-2-auth-api",
    "branch": "main/1-2-auth-api",
    "source_branch": "main",
    "phase": "1",
    "sprint": "1.2",
    "plan_file": "plans/feature-auth.md",
    "plan_section": "## Phase 1 > ### Sprint 1.2: User Authentication",
    "plan_sprint_id": "1.2",
    "dev_agent_path": ".claude/agents/backend-dev",
    "dev_model": "sonnet",
    "dev_prompts": [
      "Implement user authentication API endpoints in the backend service.",
      "Follow existing patterns in services/auth/. Use bcrypt for password hashing.",
      "Add integration tests for login and signup endpoints.",
      "Update API documentation in docs/api.md"
    ],
    "qa_agents": [
      {
        "agent_path": ".claude/agents/qa-unit-tests",
        "model": "haiku",
        "prompt": "Run pytest with coverage. Verify new endpoints have >80% coverage.",
        "output_schema": {
          "type": "object",
          "properties": {
            "status": {"enum": ["pass", "fail", "stop"]},
            "message": {"type": "string"},
            "coverage_percent": {"type": "number"}
          },
          "required": ["status", "message"]
        }
      },
      {
        "agent_path": ".claude/agents/qa-security-scan",
        "model": "sonnet",
        "prompt": "Run bandit security scanner. Check for SQL injection, hardcoded secrets, and password handling issues.",
        "output_schema": {
          "type": "object",
          "properties": {
            "status": {"enum": ["pass", "fail", "stop"]},
            "message": {"type": "string"},
            "vulnerabilities": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {"type": "string"},
                  "issue": {"type": "string"},
                  "file": {"type": "string"},
                  "line": {"type": "number"}
                }
              }
            }
          },
          "required": ["status", "message"]
        }
      }
    ],
    "max_retry_attempts": 3,
    "attempt_count": 0,
    "scrum_master_session_id": null,
    "dev_agent_session_id": null,
    "dev_agent_executions": [],
    "qa_agent_executions": [],
    "pr_url": null,
    "pr_number": null,
    "scrum_result": null
  },
  "created_at": "2026-02-07T10:00:00Z",
  "updated_at": "2026-02-07T10:00:00Z"
}
```

## Complete Bead Example (Merge Bead)

```json
{
  "id": "bd-m1m2m3",
  "title": "Merge sprint 1.2 branches",
  "description": "Integrate branches from parallel sprints 1.2a and 1.2b",
  "status": "open",
  "priority": 1,
  "issue_type": "beads-ralph-merge",
  "assignee": "beads-ralph-scrum-master",
  "dependencies": ["bd-a1b2c3", "bd-d4e5f6"],
  "labels": ["phase-01", "sprint-1-3", "merge"],
  "metadata": {
    "worktree_path": "/Users/dev/projects/my-app-worktrees/main/1-3-merge",
    "branch": "main/1-3-merge",
    "source_branch": "main",
    "phase": "1",
    "sprint": "1.3",
    "plan_file": "plans/feature-auth.md",
    "plan_section": "## Phase 1 > ### Sprint 1.3: Integration",
    "plan_sprint_id": "1.3",
    "branches_to_merge": [
      "main/1-2a-auth-api",
      "main/1-2b-user-profile"
    ],
    "dev_agent_path": ".claude/agents/merge-specialist",
    "dev_model": "sonnet",
    "dev_prompts": [
      "Merge branches main/1-2a-auth-api and main/1-2b-user-profile into main/1-3-merge",
      "Resolve any merge conflicts carefully, preserving functionality from both branches",
      "Run full test suite after merge to ensure integration is clean",
      "Update CHANGELOG.md with merged features"
    ],
    "qa_agents": [
      {
        "agent_path": ".claude/agents/qa-integration-tests",
        "model": "sonnet",
        "prompt": "Run full integration test suite. Verify auth and profile features work together.",
        "output_schema": {
          "type": "object",
          "properties": {
            "status": {"enum": ["pass", "fail", "stop"]},
            "message": {"type": "string"},
            "test_results": {
              "type": "object",
              "properties": {
                "total": {"type": "number"},
                "passed": {"type": "number"},
                "failed": {"type": "number"}
              }
            }
          },
          "required": ["status", "message"]
        }
      }
    ],
    "max_retry_attempts": 3,
    "attempt_count": 0,
    "scrum_master_session_id": null,
    "dev_agent_session_id": null,
    "dev_agent_executions": [],
    "qa_agent_executions": [],
    "pr_url": null,
    "pr_number": null,
    "scrum_result": null
  },
  "created_at": "2026-02-07T10:30:00Z",
  "updated_at": "2026-02-07T10:30:00Z"
}
```

## Plan Back-Annotation (Bi-directional Tracking)

After beads are created from a plan, the plan file should be annotated with bead IDs for bi-directional tracking.

### Annotation Format

Original plan section:
```markdown
### Sprint 1.2: User Authentication
- Implement user login endpoint
- Implement user signup endpoint
- Add password hashing with bcrypt
```

After bead creation:
```markdown
### Sprint 1.2: User Authentication
<!-- beads-ralph: bd-a1b2c3 -->
- Implement user login endpoint
- Implement user signup endpoint
- Add password hashing with bcrypt
```

### Annotation Algorithm

```python
def annotate_plan_with_bead_ids(plan_file: str, sprint_to_bead_id: dict):
    """
    Back-annotate plan file with bead IDs.

    Args:
        plan_file: Path to plan markdown file
        sprint_to_bead_id: Dict mapping sprint ID → bead ID
    """
    with open(plan_file, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    for i, line in enumerate(lines):
        updated_lines.append(line)

        # Check if this line is a sprint heading
        if line.startswith('### Sprint '):
            # Extract sprint ID (e.g., "1.2" from "### Sprint 1.2: User Auth")
            match = re.match(r'### Sprint ([0-9a-z.]+):', line)
            if match:
                sprint_id = match.group(1)
                if sprint_id in sprint_to_bead_id:
                    bead_id = sprint_to_bead_id[sprint_id]
                    # Add annotation comment
                    annotation = f'<!-- beads-ralph: {bead_id} -->\n'
                    updated_lines.append(annotation)

    with open(plan_file, 'w') as f:
        f.writelines(updated_lines)
```

### Use Cases for Bi-directional Tracking

**Plan → Bead**:
```bash
# Find bead for sprint 1.2 from plan
grep "Sprint 1.2" plans/feature-auth.md -A 1 | grep "beads-ralph:"
# Output: <!-- beads-ralph: bd-a1b2c3 -->

# Show bead details
bd show bd-a1b2c3
```

**Bead → Plan**:
```bash
# Find plan section from bead
bd show bd-a1b2c3 --json | jq -r '.metadata.plan_file, .metadata.plan_section'
# Output:
# plans/feature-auth.md
# ## Phase 1 > ### Sprint 1.2: User Authentication

# Open plan at specific section
code plans/feature-auth.md  # IDE will allow search for section heading
```

**Agent Resurrection**:
```bash
# Find agents that worked on a bead
bd show bd-a1b2c3 --json | jq -r '.metadata.dev_agent_session_id'
# Output: claude-session-abc123

# View agent session history (future feature)
claude history show claude-session-abc123

# Question agent about the work (future feature)
claude resume claude-session-abc123 -p "Why did you choose bcrypt over argon2?"
```

## Worktree Path Normalization

Worktree paths follow the sc-git-worktree convention: `../<repo-name>-worktrees/<branch-name>`

**Convention**:
- Worktrees are placed as siblings to the repository directory
- Pattern: `../<repo-name>-worktrees/<branch-name>`
- Where `<branch-name>` is the normalized sprint branch (e.g., `main/1-2-auth-api`)

**Example Structure**:
```
/Users/dev/projects/
├── my-app/                          # Main repository
│   ├── .git/
│   ├── src/
│   └── ...
└── my-app-worktrees/                # Worktrees directory (sibling)
    ├── main/1-1-project-setup/      # Sprint 1.1 worktree
    ├── main/1-2-auth-api/           # Sprint 1.2 worktree
    └── main/3a-2b-api-validation/   # Sprint 3a.2b worktree
```

**Path Generation**:
```python
repo_name = "my-app"
branch_name = "main/1-2-auth-api"
worktree_path = f"../{repo_name}-worktrees/{branch_name}"
# Result: ../my-app-worktrees/main/1-2-auth-api
```

**Absolute Path Examples**:
- Repo: `/Users/dev/projects/my-app`
- Sprint `1.1`, branch `main/1-1-project-setup`
  → `/Users/dev/projects/my-app-worktrees/main/1-1-project-setup`

- Sprint `3a.2b`, branch `main/3a-2b-api-validation`
  → `/Users/dev/projects/my-app-worktrees/main/3a-2b-api-validation`

- Sprint `2.1a`, branch `develop/2-1a-auth-service`
  → `/Users/dev/projects/my-app-worktrees/develop/2-1a-auth-service`

## Branch Naming Convention

Branch names follow the pattern: `<source-branch>/<sprint-id>-<sprint-name>`

**Normalization Rules**:
- Sprint ID: Replace `.` with `-`
- Sprint name: Lowercase, replace spaces with `-`, remove special characters

**Examples**:
- Sprint `1.1`, name "Project Setup", source "main"
  → `main/1-1-project-setup`

- Sprint `3a.2b`, name "API Validation", source "main"
  → `main/3a-2b-api-validation`

## Completed Bead Example (With Execution Tracking)

Example of a completed bead showing populated execution tracking fields:

```json
{
  "id": "bd-a1b2c3",
  "title": "Implement user authentication API",
  "status": "closed",
  "closed_at": "2026-02-07T10:45:00Z",
  "metadata": {
    "sprint": "1.2",
    "attempt_count": 2,
    "scrum_master_session_id": "claude-sm-session-xyz789",
    "dev_agent_session_id": "claude-dev-session-abc123",
    "dev_agent_executions": [
      {
        "attempt": 1,
        "session_id": "claude-dev-session-abc123",
        "agent_path": ".claude/agents/backend-dev",
        "model": "sonnet",
        "started_at": "2026-02-07T10:00:00Z",
        "completed_at": "2026-02-07T10:15:00Z",
        "status": "completed",
        "feedback_from_qa": null
      },
      {
        "attempt": 2,
        "session_id": "claude-dev-session-def456",
        "agent_path": ".claude/agents/backend-dev",
        "model": "sonnet",
        "started_at": "2026-02-07T10:25:00Z",
        "completed_at": "2026-02-07T10:35:00Z",
        "status": "completed",
        "feedback_from_qa": "QA failed: Unit tests failed for signup endpoint. Missing validation for duplicate emails."
      }
    ],
    "qa_agent_executions": [
      {
        "attempt": 1,
        "session_id": "claude-qa-session-ghi789",
        "agent_path": ".claude/agents/qa-unit-tests",
        "model": "haiku",
        "started_at": "2026-02-07T10:16:00Z",
        "completed_at": "2026-02-07T10:18:00Z",
        "status": "fail",
        "message": "Unit tests failed: test_signup_duplicate_email FAILED",
        "details": {"total": 42, "passed": 41, "failed": 1}
      },
      {
        "attempt": 2,
        "session_id": "claude-qa-session-jkl012",
        "agent_path": ".claude/agents/qa-unit-tests",
        "model": "haiku",
        "started_at": "2026-02-07T10:36:00Z",
        "completed_at": "2026-02-07T10:38:00Z",
        "status": "pass",
        "message": "All tests passed. Coverage: 87%",
        "details": {"total": 45, "passed": 45, "coverage_percent": 87}
      },
      {
        "attempt": 2,
        "session_id": "claude-qa-session-mno345",
        "agent_path": ".claude/agents/qa-security-scan",
        "model": "sonnet",
        "started_at": "2026-02-07T10:38:00Z",
        "completed_at": "2026-02-07T10:40:00Z",
        "status": "pass",
        "message": "No vulnerabilities found",
        "details": {"vulnerabilities": []}
      }
    ],
    "pr_url": "https://github.com/user/repo/pull/42",
    "pr_number": 42,
    "scrum_result": {
      "bead_id": "bd-a1b2c3",
      "success": true,
      "pr_url": "https://github.com/user/repo/pull/42",
      "pr_number": 42,
      "bead_updated": true,
      "attempt_count": 2,
      "qa_results": [
        {"agent_path": ".claude/agents/qa-unit-tests", "status": "pass"},
        {"agent_path": ".claude/agents/qa-security-scan", "status": "pass"}
      ],
      "error": null,
      "fatal": false
    }
  }
}
```

**Key Observations**:
- **Attempt 1 failed**: QA detected missing duplicate email validation
- **Attempt 2 succeeded**: Dev agent fixed the issue based on QA feedback
- **Session IDs preserved**: Can resurrect any agent to ask follow-up questions
- **Full audit trail**: Complete history of all dev and QA executions

## Schema Validation

### Required Fields Validation

All beads-ralph beads MUST have:

1. **Core Fields**:
   - `title` (non-empty)
   - `status` (valid enum)
   - `issue_type` (`beads-ralph-work` or `beads-ralph-merge`)
   - `assignee` (set to `beads-ralph-scrum-master`)

2. **Metadata Fields**:
   - `worktree_path` (valid absolute path)
   - `branch` (valid branch name)
   - `source_branch` (non-empty)
   - `phase` (matches phase pattern)
   - `sprint` (matches sprint pattern)
   - `plan_file` (path to plan file)
   - `plan_section` (section identifier in plan)
   - `plan_sprint_id` (sprint ID as in plan)
   - `dev_agent_path` (valid path to agent file)
   - `dev_model` (one of: "sonnet", "opus", "haiku")
   - `dev_prompts` (non-empty array)
   - `qa_agents` (non-empty array of valid QAAgent objects)

3. **QA Agent Validation**:
   - Each QA agent MUST have: `agent_path`, `model`, `prompt`, `output_schema`
   - `output_schema` MUST define `status` field with enum ["pass", "fail", "stop"]
   - `output_schema` MUST define `message` field

### Pattern Validation

**Phase Pattern**: `^[0-9]+[a-z]*$`
- Valid: `1`, `2`, `3a`, `3b`, `12`, `3ab`
- Invalid: `1.2`, `a1`, `1-2`, `1A`

**Sprint Pattern**: `^[0-9]+[a-z]*\.[0-9]+[a-z]*$`
- Valid: `1.1`, `3a.2`, `3b.2a`, `3b.2b`, `12.5c`
- Invalid: `1`, `1-2`, `1.2.3`, `a.1`

**Branch Pattern**: `^[a-zA-Z0-9/_-]+$`
- Valid: `main/1-2-auth`, `develop/3a-2b-api`
- Invalid: `main/1.2`, `feat/auth api` (contains space)

### Python Validation Script

```python
#!/usr/bin/env python3
import json
import re
import sys

PHASE_PATTERN = re.compile(r'^[0-9]+[a-z]*$')
SPRINT_PATTERN = re.compile(r'^[0-9]+[a-z]*\.[0-9]+[a-z]*$')
VALID_MODELS = ["sonnet", "opus", "haiku"]
VALID_STATUSES = ["pass", "fail", "stop"]

def validate_bead(bead):
    errors = []

    # Validate core fields
    if not bead.get('title'):
        errors.append("Missing or empty 'title'")
    if bead.get('issue_type') not in ['beads-ralph-work', 'beads-ralph-merge']:
        errors.append(f"Invalid issue_type: {bead.get('issue_type')}")
    if bead.get('assignee') != 'beads-ralph-scrum-master':
        errors.append(f"Invalid assignee: {bead.get('assignee')}")

    # Validate metadata
    metadata = bead.get('metadata', {})

    # Required fields
    required = ['worktree_path', 'branch', 'source_branch', 'phase', 'sprint',
                'dev_agent_path', 'dev_model', 'dev_prompts', 'qa_agents']
    for field in required:
        if field not in metadata:
            errors.append(f"Missing metadata.{field}")

    # Phase/sprint pattern validation
    if 'phase' in metadata and not PHASE_PATTERN.match(metadata['phase']):
        errors.append(f"Invalid phase format: {metadata['phase']}")
    if 'sprint' in metadata and not SPRINT_PATTERN.match(metadata['sprint']):
        errors.append(f"Invalid sprint format: {metadata['sprint']}")

    # Model validation
    if metadata.get('dev_model') not in VALID_MODELS:
        errors.append(f"Invalid dev_model: {metadata.get('dev_model')}")

    # Dev prompts validation
    dev_prompts = metadata.get('dev_prompts', [])
    if not isinstance(dev_prompts, list) or len(dev_prompts) == 0:
        errors.append("dev_prompts must be non-empty array")

    # QA agents validation
    qa_agents = metadata.get('qa_agents', [])
    if not isinstance(qa_agents, list) or len(qa_agents) == 0:
        errors.append("qa_agents must be non-empty array")
    else:
        for i, qa in enumerate(qa_agents):
            if not qa.get('agent_path'):
                errors.append(f"qa_agents[{i}]: missing agent_path")
            if qa.get('model') not in VALID_MODELS:
                errors.append(f"qa_agents[{i}]: invalid model")
            if not qa.get('prompt'):
                errors.append(f"qa_agents[{i}]: missing prompt")

            # Validate output schema
            output_schema = qa.get('output_schema', {})
            props = output_schema.get('properties', {})
            if 'status' not in props:
                errors.append(f"qa_agents[{i}]: output_schema missing 'status' property")
            else:
                status_enum = props['status'].get('enum', [])
                if not all(s in VALID_STATUSES for s in status_enum):
                    errors.append(f"qa_agents[{i}]: invalid status enum values")
            if 'message' not in props:
                errors.append(f"qa_agents[{i}]: output_schema missing 'message' property")

    return errors

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: validate-bead-schema.py <bead.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        bead = json.load(f)

    errors = validate_bead(bead)
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Bead schema is valid")
        sys.exit(0)
```

## Schema Evolution

Future schema extensions may include:

- `docker_image` - Containerized execution environment
- `resource_limits` - CPU/memory constraints
- `timeout_minutes` - Max execution time
- `notification_config` - Alert configuration
- `rollback_strategy` - Automated rollback rules
- `approval_required` - Manual approval gates
- `cost_estimate` - API cost prediction

Schema extensions should be added to `Metadata` to maintain backward compatibility.

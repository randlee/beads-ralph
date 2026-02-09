# Beads-Architect Agent Requirements

**Version**: 2.0.0
**Status**: Draft
**Last Updated**: 2026-02-08
**Review Status**: Reviewed by beads-research-expert (agentId: a8b5dc6)

---

## Executive Summary

The beads-architect agent converts implementation plan markdown into executable beads stored in the **Dolt database** via the **bd CLI**. It generates complete bead JSON with proper dependencies, validates schema compliance, and optionally annotates the plan with bead IDs.

**Critical Change from v1.2.0**: Agent must use `bd create --json` to insert beads into database, not write JSON files to filesystem.

---

## Functional Requirements

### FR-1: Parse Implementation Plan Markdown

**Description**: Extract sprint sections, metadata, and tasks from plan file.

**Inputs**:
- `plan_file_path` (string, required): Absolute path to markdown plan
- `sprint_filter` (string, optional): Specific sprint ID (e.g., "1.2a", "3.1")
- `annotate_plan` (boolean, optional): Insert bead ID back-annotations

**Parsing Rules**:
- Sprint heading regex: `^### Sprint (\d+[a-z]*)\.(\d+[a-z]*): (.+)$`
- Extract: phase_part, sprint_part, title
- Parse metadata sections: Worktree, Branch, Source Branch, Dev Agents, QA Agents, Tasks, Acceptance Criteria

### FR-2: Compile Sprint Dependencies

**Description**: Generate dependency graph as DAG following docs/numbering.md rules.

**Five Dependency Patterns**:
1. **Sequential**: Sprint with no suffix depends on previous sequential sprint in same phase
2. **Parallel**: Sprints with suffixes depend on previous sequential sprint; no inter-parallel dependencies
3. **Merge**: Next sequential sprint after parallel group depends on ALL parallel sprints
4. **Phase Split**: First sprint of parallel phase track depends on last sprint of previous phase
5. **Phase Converge**: First sprint after multiple parallel phase tracks depends on last sprint of each track

**DAG Validation**:
- No cycles (detect via DFS with gray/black sets)
- No dangling references (all dependency IDs exist)
- No self-dependencies
- All sprints reachable from graph root

### FR-3: Generate Bead IDs and Metadata

**Description**: Create unique bead IDs and populate all 34 required schema fields.

**Bead ID Pattern**: `bd-<phase>-<sprint>-<descriptive-name>`

**Examples**:
- `bd-1-1-schema` (phase 1, sprint 1)
- `bd-1-2a-work-bead` (phase 1, sprint 2a, parallel)
- `bd-3a-2b-validation` (phase 3a, sprint 2b)

**Required Fields** (34 total):

**Core Fields (15)**:
- `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`, `owner`
- `dependencies`, `labels`, `comments`, `external_ref`
- `created_at`, `updated_at`, `closed_at`

**Metadata Fields (19)**:
- `rig` (**REQUIRED**: always `"beads-ralph"`)
- `worktree_path`, `branch`, `source_branch`, `phase`, `sprint`
- `plan_file`, `plan_section`, `plan_sprint_id`
- `branches_to_merge` (null for work beads, array for merge beads)
- `dev_agent_path`, `dev_model`, `dev_prompts`
- `qa_agents` (array with required `output_schema`)
- `max_retry_attempts`, `attempt_count`
- `scrum_master_session_id`, `dev_agent_session_id`
- `dev_agent_executions`, `qa_agent_executions` (initially empty arrays)
- `pr_url`, `pr_number`, `scrum_result` (initially null)

**Issue Type**:
- `"beads-ralph-work"` for work sprints
- `"beads-ralph-merge"` for merge sprints

### FR-4: Insert Beads into Dolt Database (CRITICAL)

**Description**: Use `bd create --json` to insert beads into Dolt database.

**Required Behavior**:
```bash
# For each generated bead:
echo '<bead-json>' | bd create --json -

# Or using temp file:
echo '<bead-json>' > /tmp/bead.json
bd create --json /tmp/bead.json
```

**Output Parsing**:
- Parse `bd create --json` stdout for bead ID
- Capture any errors from stderr
- Validate insertion with `bd show <bead-id> --json`

**Pre-flight Checks**:
1. Verify bd CLI available: `bd --version`
2. Check database initialized: `bd info --json`
3. Validate daemon running: Check `daemon_running: true` in info output

**Error Handling**:
- `bd --version` fails → `DATABASE.CLI_NOT_FOUND`
- `bd info` shows no database → `DATABASE.NOT_INITIALIZED`
- `bd create` fails → `DATABASE.INSERT_FAILED`
- Duplicate ID constraint violation → `DEPENDENCY.DUPLICATE_ID`

**IMPORTANT**: Agent must NEVER write JSON files to filesystem. All beads must be inserted via bd CLI.

### FR-5: Validate Bead Schema

**Description**: Validate each bead before database insertion.

**Validation Steps**:
1. Generate bead JSON in memory
2. Validate using `python3 scripts/validate-bead-schema.py` (stdin or temp file)
3. If validation passes, insert via `bd create --json`
4. If validation fails, return error and skip insertion

**Schema Validation**:
- All 34 required fields present
- Field types match pydantic models in `scripts/bead_schema.py`
- Phase pattern: `^\d+[a-z]*$` (e.g., "1", "3a")
- Sprint pattern: `^\d+[a-z]*\.\d+[a-z]*$` (e.g., "1.2", "3a.2b")
- QA agent `output_schema` includes required `status` and `message` fields

### FR-6: Back-Annotate Plan (Optional)

**Description**: Insert bead ID annotations into plan markdown after sprint headings.

**Annotation Format**:
```markdown
### Sprint 1.2: User Authentication
<!-- beads-ralph: bd-1-2-user-auth -->
```

**Insertion Rules**:
- Detect sprint heading: `^### Sprint (\d+[a-z]*)\.(\d+[a-z]*): (.+)$`
- Insert annotation on next line
- Replace existing annotation if present
- Preserve all other content unchanged

**Update Algorithm**:
```text
for each line in plan:
  output line
  if line matches sprint heading:
    extract sprint_id
    bead_id = sprint_to_bead_map[sprint_id]
    annotation = "<!-- beads-ralph: " + bead_id + " -->"
    if next_line starts with "<!-- beads-ralph:":
      replace next_line with annotation
    else:
      insert annotation
```

### FR-7: Return Structured Result

**Description**: Return fenced JSON with database insertion results.

**Success Response**:
```json
{
  "success": true,
  "data": {
    "beads_created": 3,
    "bead_ids": [
      "bd-1-1-schema",
      "bd-1-2a-work",
      "bd-1-2b-merge"
    ],
    "sprints_processed": ["1.1", "1.2a", "1.2b"],
    "database_status": "inserted",
    "plan_annotated": true
  },
  "error": null
}
```

**Failure Response**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DATABASE.INSERT_FAILED",
    "message": "Failed to insert bead bd-1-2a-work into database",
    "recoverable": true,
    "suggested_action": "Check bd daemon is running with 'bd info --json'"
  }
}
```

---

## Non-Functional Requirements

### NFR-1: Database Integration (CRITICAL)

**Requirement**: Agent must use bd CLI for ALL database operations.

**Prohibited**:
- ❌ Writing JSON files to `beads/` directory
- ❌ Direct SQLite/Dolt file access
- ❌ Bypassing daemon RPC layer

**Required**:
- ✅ Use `bd create --json` for insertion
- ✅ Use `bd show --json` for verification
- ✅ Use `bd info --json` for pre-flight checks
- ✅ Parse JSON output from bd CLI commands

**Rationale**: Go ralph loop queries database using `bd ready --json`. Beads must be in database, not filesystem.

### NFR-2: Concurrency Safety

**Requirement**: Agent must support concurrent execution by multiple architect instances.

**Strategies**:
- Use unique bead IDs (include timestamp or random suffix if parallel architects)
- Rely on database uniqueness constraints for ID conflicts
- Handle `bd create` failures gracefully (duplicate ID → recoverable error)
- No shared file writes (database serializes via daemon)

**Dolt Benefits**:
- MySQL-compatible SQL server (no file-level locks)
- Daemon serializes writes
- 40+ concurrent bd processes supported

### NFR-3: Validation Before Insertion

**Requirement**: Validate schema compliance BEFORE inserting into database.

**Rationale**:
- Database may not catch all schema violations
- Python pydantic validator provides detailed error messages
- Prevents polluting database with invalid beads

**Process**:
1. Generate bead JSON
2. Validate with pydantic (scripts/validate-bead-schema.py)
3. If valid, insert with `bd create --json`
4. If invalid, return error WITHOUT database insertion

---

## Error Codes

### Database Errors (Fatal)

- `DATABASE.CLI_NOT_FOUND`: bd command not in PATH
- `DATABASE.NOT_INITIALIZED`: No .beads/ directory or database
- `DATABASE.INSERT_FAILED`: bd create command failed
- `DATABASE.DAEMON_NOT_RUNNING`: Daemon not running (from bd info)

### Validation Errors (Recoverable)

- `VALIDATION.BEAD_SCHEMA`: Pydantic validation failed
- `VALIDATION.MISSING_FIELD`: Required field missing
- `VALIDATION.INVALID_PATTERN`: Phase/sprint pattern mismatch

### Dependency Errors (Recoverable)

- `DEPENDENCY.UNRESOLVED`: Dangling dependency reference
- `DEPENDENCY.CYCLE_DETECTED`: Circular dependency in DAG
- `DEPENDENCY.DUPLICATE_ID`: Non-unique bead ID
- `DEPENDENCY.SELF_DEP`: Sprint depends on itself

### Parse Errors (Recoverable)

- `PARSE.MARKDOWN`: Malformed sprint heading
- `PARSE.MISSING_SECTION`: Required section missing (e.g., Dev Agents)

### IO Errors (Fatal)

- `IO.FILE_NOT_FOUND`: Plan file not found
- `IO.PERMISSION_DENIED`: Cannot read plan file

---

## Examples

### Example 1: Simple Sequential Sprint

**Plan Section**:
```markdown
### Sprint 1.1: Core Schema Validation Script

**Worktree**: `../beads-ralph-worktrees/feature/1-1-schema-validator`
**Branch**: `feature/1-1-schema-validator`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)

**QA Agents**:
- `qa-python-tests` (haiku) - Run pytest with >90% coverage

**Tasks**:
- Create scripts/bead_schema.py with pydantic models
- Create scripts/validate-bead-schema.py CLI tool
- Create comprehensive test suite
```

**Generated Bead JSON** (before insertion):
```json
{
  "id": "bd-1-1-schema",
  "title": "Core Schema Validation Script",
  "description": "Create scripts/bead_schema.py with pydantic models and scripts/validate-bead-schema.py CLI tool with comprehensive test suite",
  "status": "open",
  "priority": 1,
  "issue_type": "beads-ralph-work",
  "assignee": "beads-ralph-scrum-master",
  "owner": null,
  "dependencies": [],
  "labels": ["phase-01", "sprint-1-1"],
  "comments": [],
  "external_ref": null,
  "created_at": "2026-02-08T10:00:00Z",
  "updated_at": "2026-02-08T10:00:00Z",
  "closed_at": null,
  "metadata": {
    "rig": "beads-ralph",
    "worktree_path": "../beads-ralph-worktrees/feature/1-1-schema-validator",
    "branch": "feature/1-1-schema-validator",
    "source_branch": "develop",
    "phase": "1",
    "sprint": "1.1",
    "plan_file": "pm/2026-02-08-implementation-plan.md",
    "plan_section": "### Sprint 1.1: Core Schema Validation Script",
    "plan_sprint_id": "1.1",
    "branches_to_merge": null,
    "dev_agent_path": ".claude/agents/python-backend-dev",
    "dev_model": "sonnet",
    "dev_prompts": [
      "Create scripts/bead_schema.py with pydantic models",
      "Create scripts/validate-bead-schema.py CLI tool",
      "Create comprehensive test suite"
    ],
    "qa_agents": [
      {
        "agent_path": ".claude/agents/qa-python-tests",
        "model": "haiku",
        "prompt": "Run pytest with >90% coverage",
        "output_schema": {
          "type": "object",
          "properties": {
            "status": {"enum": ["pass", "fail", "stop"]},
            "message": {"type": "string"}
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
  }
}
```

**Database Insertion**:
```bash
# Validate first
echo '<bead-json>' | python3 scripts/validate-bead-schema.py
# Output: ✓ Valid bead (exit code 0)

# Insert into database
echo '<bead-json>' | bd create --json -
# Output: {"id": "bd-1-1-schema", "status": "created"}

# Verify insertion
bd show bd-1-1-schema --json
# Output: <full-bead-json>
```

**Agent Output**:
```json
{
  "success": true,
  "data": {
    "beads_created": 1,
    "bead_ids": ["bd-1-1-schema"],
    "sprints_processed": ["1.1"],
    "database_status": "inserted",
    "plan_annotated": false
  },
  "error": null
}
```

### Example 2: Parallel Sprints with Dependencies

**Plan Sections**:
```markdown
### Sprint 1.2a: Example Work Bead (Parallel)
...

### Sprint 1.2b: Example Merge Bead (Parallel)
...
```

**Dependency Resolution**:
- Both 1.2a and 1.2b depend on 1.1 (previous sequential sprint)
- No dependency between 1.2a and 1.2b (parallel execution)

**Generated Dependencies**:
```json
{
  "bd-1-2a-work": {
    "dependencies": ["bd-1-1-schema"]
  },
  "bd-1-2b-merge": {
    "dependencies": ["bd-1-1-schema"]
  }
}
```

**Database Insertion** (both beads):
```bash
# Insert first parallel bead
echo '<bead-1.2a-json>' | bd create --json -

# Insert second parallel bead
echo '<bead-1.2b-json>' | bd create --json -

# Verify both ready (dependency on 1.1 satisfied)
bd ready --json
# Output: [{"id": "bd-1-2a-work"}, {"id": "bd-1-2b-merge"}]
```

---

## Integration with Go Ralph Loop

### Ralph Loop Workflow

```
1. Ralph: bd ready --json  → Finds ready beads (dependencies satisfied, not claimed)
2. Ralph: bd update bd-1-2a --claim --json → Atomically claims bead
3. Ralph: Launches scrum-master agent with bead metadata
4. Scrum-master: bd show bd-1-2a --json → Reads full bead details
5. Scrum-master: Executes dev/QA loop in worktree
6. Scrum-master: bd update bd-1-2a --status closed --json → Marks complete
7. Scrum-master: bd update bd-1-2a --metadata '{"pr_url": "..."}' --json → Adds PR info
8. Ralph: bd ready --json → Finds next ready beads (dependencies unblocked)
```

### Critical Integration Points

1. **Beads must be in database** for `bd ready` to find them
2. **Dependencies must be bead IDs** for dependency resolution
3. **Metadata must include worktree/branch** for scrum-master to operate
4. **QA agents must have output_schema** for scrum-master to validate

---

## Testing Requirements

### Unit Tests (Minimum)

1. **Sequential sprints** (1.1, 1.2, 1.3) → linear dependencies
2. **Parallel sprints** (1.1, 1.2a, 1.2b, 1.3) → merge dependencies
3. **Phase split** (2.3, 3a.1, 3b.1) → parallel phase dependencies
4. **Phase converge** (3a.2, 3b.2, 4.1) → converge dependencies
5. **Duplicate ID** → DEPENDENCY.DUPLICATE_ID error
6. **Dangling reference** → DEPENDENCY.UNRESOLVED error
7. **Cycle detection** → DEPENDENCY.CYCLE_DETECTED error
8. **Missing required field** → VALIDATION.MISSING_FIELD error

### Integration Tests

1. **bd CLI availability** → Verify pre-flight checks
2. **Database insertion** → Verify bd create success
3. **Bead retrieval** → Verify bd show returns inserted bead
4. **Ready queue** → Verify bd ready finds inserted beads with satisfied deps

---

## Change Log

### v2.0.0 (Draft) - 2026-02-08

**BREAKING CHANGES**:
- ❌ **REMOVED**: JSON file writing to `beads/` directory
- ✅ **ADDED**: bd CLI integration (`bd create --json`)
- ✅ **ADDED**: Pre-flight checks (`bd --version`, `bd info`)
- ✅ **ADDED**: Database insertion validation (`bd show`)
- ✅ **CHANGED**: Output format (bead_ids instead of bead_files)

**Rationale**: Integration with Go ralph loop requires beads in Dolt database, not filesystem.

### v1.2.0 - 2026-02-08

- ✅ Executable dependency compilation pseudocode
- ✅ Back-annotation algorithm with regex/insertion logic
- ✅ Concrete metadata extraction guidance
- ✅ 3 examples + 6 test cases

**Issue**: Did not integrate with bd CLI or Dolt database.

### v1.0.0 - 2026-02-07

- Initial beads-architect specification
- Basic dependency compilation (5 rules, conceptual)
- Basic back-annotation (format only)

---

**Next Steps**:
1. Review these requirements with beads-research-expert
2. Update beads-architect.md agent specification to v2.0.0
3. Implement bd CLI integration in agent prompt
4. Test with implementation plan (pm/2026-02-08-implementation-plan.md)
5. Validate beads appear in database with `bd list --json`

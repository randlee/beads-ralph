---
name: beads-architect
version: 2.0.0
description: Converts implementation plans into validated beads inserted into the Dolt database (bd CLI) with full dependencies and optional plan back-annotations.
---

# Beads Architect Agent

## Purpose

Convert implementation plan markdown into fully validated beads inserted into the Dolt database via `bd create --json`, with correct dependencies and optional plan back-annotations. This agent MUST write to the database, not to files.

## Inputs

- `plan_file_path` (string, required): Absolute path to implementation plan markdown.
- `sprint_filter` (string, optional): Specific sprint ID to process (e.g., "1.2a", "3.1").
- `annotate_plan` (boolean, optional, default: false): Insert bead ID back-annotations into the plan.
- `mode` (string, optional, default: "direct"): "direct" for plan-to-beads insertion. "formula" only if explicitly requested.

## Execution Steps (7)

1. **Pre-flight Database Checks**
Run these first. Fail fast on errors.

Commands:
```bash
bd --version
bd info --json
```

Expected:
- `bd --version` succeeds or error `DATABASE.CLI_NOT_FOUND`.
- `bd info --json` returns `database_path`. If missing → `DATABASE.NOT_INITIALIZED`.

2. **Parse Markdown Plan**
Extract sprint sections using:
```
^### Sprint (\d+[a-z]*)\.(\d+[a-z]*): (.+)$
```

Capture:
- `phase_part`, `sprint_part`, `title`.

3. **Extract Sprint Metadata**
Parse each sprint block for:
- Worktree path from `**Worktree**:` line.
- Branch from `**Branch**:` line.
- Source branch from `**Source Branch**:` line.
- Dev agents from `**Dev Agents**:` section.
- QA agents from `**QA Agents**:` section.
- Tasks from `**Tasks**:` section.
- Acceptance criteria from `**Acceptance Criteria**:` section (optional).

4. **Compile Dependencies**
Apply the dependency algorithm below to produce a DAG. Validate:
- No cycles.
- No dangling refs.
- No self-deps.

5. **Generate Bead IDs, Core Fields, and Metadata**
Use deterministic bead IDs and populate all fields required by `scripts/bead_schema.py`:
- Core fields on the bead object.
- `metadata` object with all required beads-ralph fields.

6. **Validate and Insert into Database**
For each bead:
- Validate: `echo '<bead-json>' | python3 scripts/validate-bead-schema.py`.
- Insert: `echo '<bead-json>' | bd create --json -`.
- Optional verify: `bd show <bead-id> --json`.
- If any insert fails, return structured error and stop further inserts.

7. **Optional Plan Back-Annotation**
If `annotate_plan` is true, insert bead ID annotations after each sprint heading using the algorithm below.

Return fenced JSON with minimal response envelope and database status.

## Dependency Compilation Algorithm (Executable Guidance)

### Sprint Grammar

```
sprint_id     := phase_part "." sprint_part
phase_part    := DIGITS LETTERS?   # "1", "3a"
sprint_part   := DIGITS LETTERS?   # "1", "2a"
```

Derived fields:
- `phase`: full phase part (e.g., "3a").
- `phase_number`: digits-only from phase ("3").
- `phase_suffix`: letters-only from phase ("a" or "").
- `sprint_number`: digits-only from sprint ("2").
- `sprint_suffix`: letters-only from sprint ("a" or "").
- `sprint_base`: sprint with suffix stripped ("3a.2" from "3a.2b").

### Rules

1. Sequential: sprint with no suffix depends on previous sequential sprint in same phase.
2. Parallel: sprint with suffix depends on previous sequential sprint in same phase, no inter-parallel deps.
3. Merge: next sequential after parallel group depends on all sprints in that group.
4. Phase Split: first sprint of a parallel phase track depends on last sprint of previous phase.
5. Phase Converge: first sprint after multiple parallel phase tracks depends on last sprint of each track.

### Helper Functions (Pseudocode)

```text
parse_parts(sprint_id):
  phase, sprint = sprint_id.split(".")
  phase_number  = digits_only(phase)
  phase_suffix  = letters_only(phase)
  sprint_number = digits_only(sprint)
  sprint_suffix = letters_only(sprint)
  sprint_base   = phase + "." + sprint_number
  return {phase, phase_number, phase_suffix, sprint_number, sprint_suffix, sprint_base}

group_by_phase(sprints):
  return dict phase -> list of sprint_ids in that phase

phase_last_sprint(phase, sprints_in_phase):
  max_num = max(sprint_number)
  candidates = [s for s in sprints_in_phase if sprint_number(s) == max_num]
  return sequential_if_exists_else_any(candidates)

prev_sequential_sprint(phase, sprint_number, sprints_in_phase):
  candidates = [s for s in sprints_in_phase if sprint_number(s) < sprint_number and sprint_suffix(s) == ""]
  if empty -> null
  return max_by_sprint_number(candidates)

parallel_group(phase, sprint_number, sprints_in_phase):
  return [s for s in sprints_in_phase if sprint_number(s) == sprint_number and sprint_suffix(s) != ""]
```

### Main Algorithm (Pseudocode)

```text
compile_dependencies(sprints):
  deps = {sprint_id: [] for sprint_id in sprints}
  by_phase = group_by_phase(sprints)

  for each phase in by_phase:
    for each sprint in by_phase[phase]:
      parts = parse_parts(sprint)

      if parts.sprint_suffix != "":
        prev = prev_sequential_sprint(parts.phase, parts.sprint_number, by_phase[parts.phase])
        if prev is null:
          deps[sprint] = phase_entry_dependencies(parts.phase, by_phase, sprints)
        else:
          deps[sprint] = [prev]
        continue

      if has_parallel_group_before(parts.phase, parts.sprint_number, by_phase[parts.phase]):
        group = parallel_group(parts.phase, parts.sprint_number - 1, by_phase[parts.phase])
        deps[sprint] = group
        continue

      if parts.sprint_number == 1:
        deps[sprint] = phase_entry_dependencies(parts.phase, by_phase, sprints)
        continue

      prev = prev_sequential_sprint(parts.phase, parts.sprint_number, by_phase[parts.phase])
      if prev is not null:
        deps[sprint] = [prev]

  validate_dag(deps)
  return deps

phase_entry_dependencies(phase, by_phase, sprints):
  if phase has suffix:
    prev_phase_number = int(phase_number(phase)) - 1
    prev_phase = str(prev_phase_number)
    return [phase_last_sprint(prev_phase, by_phase[prev_phase])]
  else:
    parallel_tracks = [p for p in by_phase.keys()
                       if phase_number(p) == phase_number(phase)-1 and phase_suffix(p) != ""]
    if parallel_tracks not empty:
      return [phase_last_sprint(p, by_phase[p]) for p in parallel_tracks]
    return []
```

### DAG Validation (Required)

```text
validate_dag(deps):
  ensure no self-dependency
  ensure all referenced sprint_ids exist
  detect cycles via DFS (gray/black sets)
```

## Plan Back-Annotation (Optional)

### Format

```markdown
### Sprint 1.2: User Authentication
<!-- beads-ralph: bd-1-2-user-auth -->
```

### Insertion Algorithm (Pseudocode)

```text
annotate_plan(plan_text, sprint_to_bead):
  lines = plan_text.splitlines()
  out = []
  i = 0
  while i < len(lines):
    line = lines[i]
    out.append(line)
    if matches_sprint_heading(line):
      sprint_id = extract_sprint_id(line)
      bead_id = sprint_to_bead[sprint_id]
      annotation = "<!-- beads-ralph: " + bead_id + " -->"
      if i+1 < len(lines) and lines[i+1].strip().startswith("<!-- beads-ralph:"):
        out.append(annotation)
        i += 1
      else:
        out.append(annotation)
    i += 1
  return "\n".join(out) + "\n"
```

Errors:
- Missing sprint in map → `DEPENDENCY.UNRESOLVED`.
- Duplicate/conflicting annotation → `DEPENDENCY.DUPLICATE_ID`.
- No headings matched → `PARSE.MARKDOWN`.

## Bead ID Generation

Pattern: `bd-<phase>-<sprint>-<descriptive-name>`

Algorithm:
1. Normalize `phase_part` and `sprint_part` to lowercase.
2. Slugify title: lowercase, spaces to hyphen, remove punctuation, max 30 chars.
3. Construct ID and verify uniqueness across output set.

## Metadata Extraction (Concrete)

Dev prompts:
- Each bullet under `**Tasks**:` becomes one `dev_prompts` entry.

Dev agent:
- Parse `- \`agent-name\` (model)`.
- `dev_agent_path` = `.claude/agents/<agent-name>`.
- `dev_model` = `haiku|sonnet|opus`.

QA agents:
- Parse `- \`agent-name\` (model) - description`.
- `qa_agents[]` object includes `output_schema` with `status` and `message`.

Plan fields:
- `plan_section` = exact sprint heading line.
- `plan_sprint_id` = `phase_part + "." + sprint_part`.

Tracking fields:
- `dev_agent_executions` and `qa_agent_executions` start as empty arrays.
- `scrum_master_session_id`, `dev_agent_session_id`, `pr_url`, `pr_number`, `scrum_result` start as null.

## Bead Schema Fields (Matches scripts/bead_schema.py)

Core bead fields:
- `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`, `owner`, `dependencies`, `labels`, `comments`, `metadata`, `external_ref`, `created_at`, `updated_at`, `closed_at`.

Metadata object fields:
- `rig`, `worktree_path`, `branch`, `source_branch`, `phase`, `sprint`.
- `plan_file`, `plan_section`, `plan_sprint_id`.
- `branches_to_merge`.
- `dev_agent_path`, `dev_model`, `dev_prompts`.
- `qa_agents`.
- `max_retry_attempts`, `attempt_count`.
- `scrum_master_session_id`, `dev_agent_session_id`.
- `dev_agent_executions`, `qa_agent_executions`.
- `pr_url`, `pr_number`, `scrum_result`.

Defaults:
- `status` = "open".
- `priority` = 1.
- `assignee` = "beads-ralph-scrum-master".
- `owner` = null.
- `comments` = []
- `external_ref` = null.
- `created_at` and `updated_at` = current ISO 8601 time.
- `closed_at` = null.
- `rig` = "beads-ralph".
- `max_retry_attempts` = 3.
- `attempt_count` = 0.

Issue type:
- Work bead: `issue_type = "beads-ralph-work"`, `branches_to_merge = null`.
- Merge bead: `issue_type = "beads-ralph-merge"`, `branches_to_merge = [...]`.

## Database Insertion (Required)

Prohibited:
- Writing JSON to `beads/` directory.
- Direct SQLite/Dolt file access.

Required:
- Use `bd create --json` to insert.
- Use `bd show --json` to verify if requested.

Insertion workflow:
```bash
# Validate
echo '<bead-json>' | python3 scripts/validate-bead-schema.py

# Insert
echo '<bead-json>' | bd create --json -

# Verify (optional)
bd show <bead-id> --json
```

## Output Format

Success:
```json
{
  "success": true,
  "data": {
    "mode": "direct",
    "beads_created": 3,
    "bead_ids": ["bd-1-1-schema", "bd-1-2a-work", "bd-1-2b-merge"],
    "sprints_processed": ["1.1", "1.2a", "1.2b"],
    "database_status": "inserted",
    "plan_annotated": true,
    "plan_file_updated": true
  },
  "error": null
}
```

Failure:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DATABASE.INSERT_FAILED",
    "message": "Failed to insert bead bd-1-2a-work into database",
    "details": "bd create command failed with exit code 1: duplicate key constraint",
    "recoverable": true,
    "suggested_action": "Check if bead already exists: bd show bd-1-2a-work --json"
  }
}
```

## Error Codes

- `DATABASE.CLI_NOT_FOUND`
- `DATABASE.NOT_INITIALIZED`
- `DATABASE.DAEMON_NOT_RUNNING`
- `DATABASE.INSERT_FAILED`
- `DATABASE.TIMEOUT`
- `VALIDATION.BEAD_SCHEMA`
- `VALIDATION.MISSING_FIELD`
- `VALIDATION.INVALID_PATTERN`
- `VALIDATION.CONSTRAINT`
- `DEPENDENCY.UNRESOLVED`
- `DEPENDENCY.CYCLE_DETECTED`
- `DEPENDENCY.DUPLICATE_ID`
- `DEPENDENCY.SELF_DEP`
- `PARSE.MARKDOWN`
- `PARSE.MISSING_SECTION`
- `PARSE.INVALID_PATTERN`
- `IO.FILE_NOT_FOUND`
- `IO.PERMISSION_DENIED`

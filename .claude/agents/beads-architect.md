---
name: beads-architect
version: 1.0.0
description: Converts implementation plan markdown to executable bead JSON with proper dependencies and metadata.
---

# Beads Architect Agent

## Purpose

Convert implementation plan markdown files into validated, executable bead JSON files with complete metadata and dependency relationships.

## Inputs

- `plan_file_path` (string, required): Absolute path to implementation plan markdown file
- `sprint_filter` (string, optional): Specific sprint ID to process (e.g., "1.2a", "3.1"). If not provided, processes all sprints.

## Execution Steps

1. **Parse Markdown Plan**
   - Read plan file from `plan_file_path`
   - Extract sprints using regex pattern: `### Sprint (\d+)\.(\d+)([a-c])?:`
   - Parse sprint sections for metadata (worktree, branch, agents, tasks)

2. **Extract Sprint Metadata**
   - Phase number from sprint ID (e.g., "1" from "1.2a")
   - Sprint number (e.g., "1.2a")
   - Worktree path from "**Worktree**:" line
   - Branch name from "**Branch**:" line
   - Source branch from "**Source Branch**:" line
   - Dev agents from "**Dev Agents**:" section
   - QA agents from "**QA Agents**:" section
   - Tasks from "**Tasks**:" section
   - Acceptance criteria from "**Acceptance Criteria**:" section

3. **Compile Dependencies**
   - Sequential sprints: `1.1 → 1.2` means `1.2` depends on `1.1`
   - Parallel sprints: `1.2a` and `1.2b` both depend on `1.1` (no dependency between them)
   - Merge sprints: `1.3` after `1.2a, 1.2b` means `1.3` depends on `["1.2a", "1.2b"]`
   - Phase transitions: Track last sprint of previous phase for dependency
   - Convert sprint IDs to bead IDs using pattern: `bd-<phase>-<sprint>-<name>`

4. **Generate Bead JSON**
   - Create complete bead object with all 34 required fields
   - Core fields: `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`, `owner`, `dependencies`, `labels`, `comments`, `external_ref`, `created_at`, `updated_at`, `closed_at`
   - Metadata fields (19): `rig`, `worktree_path`, `branch`, `source_branch`, `phase`, `sprint`, `plan_file`, `plan_section`, `plan_sprint_id`, `branches_to_merge`, `dev_agent_path`, `dev_model`, `dev_prompts`, `qa_agents`, `max_retry_attempts`, `attempt_count`, `scrum_master_session_id`, `dev_agent_session_id`, agent execution tracking arrays
   - **CRITICAL**: All beads MUST include `"rig": "beads-ralph"` in metadata
   - Set `issue_type` to `"beads-ralph-work"` for work beads or `"beads-ralph-merge"` for merge beads
   - Parse dev agents and map to model (haiku/sonnet/opus)
   - Parse QA agents with proper output schema including `status` enum: `["pass", "fail", "stop"]`

5. **Generate Bead IDs**
   - Pattern: `bd-<phase>-<sprint>-<name>`
   - Examples: `bd-1-1-schema`, `bd-1-2a-work`, `bd-3a-2b-validation`
   - Derive name from sprint title (lowercase, hyphenated)

6. **Validate Beads**
   - Run `python3 scripts/validate-bead-schema.py` on each generated bead JSON
   - Catch validation errors and report with field paths
   - Only include valid beads in final output

7. **Return Structured Result**
   - Wrap output in fenced JSON markdown block
   - Use minimal response envelope
   - Include array of generated bead file paths
   - Include validation results

## Output Format

Return fenced JSON using minimal response envelope:

```json
{
  "success": true,
  "data": {
    "beads_created": 3,
    "bead_files": [
      "beads/bd-1-1-schema.json",
      "beads/bd-1-2a-work.json",
      "beads/bd-1-2b-merge.json"
    ],
    "sprints_processed": ["1.1", "1.2a", "1.2b"]
  },
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION.BEAD_SCHEMA",
    "message": "Bead validation failed for sprint 1.2a",
    "recoverable": true,
    "suggested_action": "Review pydantic validation errors in details field"
  }
}
```

## Key Patterns

### Dependency Resolution

**Sequential Sprints** (1.1 → 1.2 → 1.3):
```json
{
  "bd-1-1-schema": { "dependencies": [] },
  "bd-1-2-work": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-3-integration": { "dependencies": ["bd-1-2-work"] }
}
```

**Parallel Sprints** (1.2a, 1.2b both after 1.1):
```json
{
  "bd-1-1-schema": { "dependencies": [] },
  "bd-1-2a-work": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-2b-merge": { "dependencies": ["bd-1-1-schema"] }
}
```

**Merge Sprint** (1.3 waits for both 1.2a and 1.2b):
```json
{
  "bd-1-2a-work": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-2b-merge": { "dependencies": ["bd-1-1-schema"] },
  "bd-1-3-integration": { "dependencies": ["bd-1-2a-work", "bd-1-2b-merge"] }
}
```

### Bead Schema Fields

All beads must include exactly 34 fields:

**Core Fields (15)**:
- `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`, `owner`, `dependencies`, `labels`, `comments`, `external_ref`, `created_at`, `updated_at`, `closed_at`

**Metadata Fields (19)**:
- `rig` (**REQUIRED**: always "beads-ralph")
- `worktree_path`, `branch`, `source_branch`, `phase`, `sprint`
- `plan_file`, `plan_section`, `plan_sprint_id`
- `branches_to_merge` (null for work beads, array for merge beads)
- `dev_agent_path`, `dev_model`, `dev_prompts`
- `qa_agents` (array of QAAgent objects)
- `max_retry_attempts`, `attempt_count`
- `scrum_master_session_id`, `dev_agent_session_id`
- `dev_agent_executions`, `qa_agent_executions` (initially empty arrays)
- `pr_url`, `pr_number`, `scrum_result` (initially null)

### QA Agent Output Schema

Every QA agent MUST have an `output_schema` that defines:

```json
{
  "type": "object",
  "properties": {
    "status": {
      "enum": ["pass", "fail", "stop"],
      "description": "Validation result"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message"
    }
  },
  "required": ["status", "message"]
}
```

Status values:
- `pass`: Validation succeeded, proceed to next step
- `fail`: Validation failed, dev agent should retry
- `stop`: Critical failure, do not retry (e.g., security vulnerability)

## Error Handling

### Parse Errors (recoverable)

- Code: `PARSE.MARKDOWN`
- Suggested action: "Verify plan file follows expected format with '### Sprint X.Y:' headings"

### Validation Errors (recoverable)

- Code: `VALIDATION.BEAD_SCHEMA`
- Suggested action: "Review pydantic validation errors; ensure all required fields present"

### File Not Found (fatal)

- Code: `IO.FILE_NOT_FOUND`
- Suggested action: "Verify plan_file_path exists and is readable"

### Invalid Dependencies (recoverable)

- Code: `DEPENDENCY.UNRESOLVED`
- Suggested action: "Verify referenced sprint IDs exist in plan; check dependency chain"

## Plan Back-Annotation (Bi-directional Tracking)

After beads are successfully generated and validated, the plan file can be back-annotated with bead IDs to enable bi-directional navigation between plans and beads. This creates an audit trail and allows both human reviewers and automated tools to track work from plan to execution and back.

### Annotation Format

Back-annotations use HTML comment syntax to remain invisible in rendered markdown while being easily parseable:

```markdown
### Sprint 1.2: User Authentication
<!-- beads-ralph: bd-1-2-user-auth -->

**Worktree**: `../beads-ralph-worktrees/feature/1-2-user-auth`
**Branch**: `feature/1-2-user-auth`
```

**Format Rules**:
- HTML comment inserted immediately after sprint heading line
- Format: `<!-- beads-ralph: <bead-id> -->`
- Must include exactly one space after `<!--` and before `-->`
- Bead ID must match the generated bead's `id` field
- One annotation per sprint (no duplicate annotations)

### Sprint Heading Detection

Use this regex pattern to find sprint headings in plan files:

```python
import re

SPRINT_HEADING_PATTERN = r'^### Sprint (\d+)\.(\d+)([a-c])?:\s*(.+)$'

def find_sprint_headings(plan_content: str) -> list[tuple[int, str, str]]:
    """
    Find all sprint headings in plan file.

    Returns:
        List of (line_number, sprint_id, heading_text) tuples
    """
    headings = []
    lines = plan_content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        match = re.match(SPRINT_HEADING_PATTERN, line)
        if match:
            phase = match.group(1)
            sprint_num = match.group(2)
            suffix = match.group(3) or ""  # a, b, c, or empty
            title = match.group(4)

            sprint_id = f"{phase}.{sprint_num}{suffix}"
            headings.append((line_num, sprint_id, line))

    return headings
```

**Pattern Components**:
- `^### Sprint` - Matches level-3 heading starting with "Sprint"
- `(\d+)\.(\d+)` - Captures phase and sprint numbers (e.g., "1.2")
- `([a-c])?` - Optional parallel sprint suffix (a, b, or c)
- `:\s*(.+)$` - Colon separator and sprint title

**Examples of Valid Headings**:
- `### Sprint 1.1: Core Schema Validation Script`
- `### Sprint 2.3a: Parallel Work Bead Execution`
- `### Sprint 5.2: Final Integration & Testing`

### Sprint ID to Bead ID Mapping

The beads-architect agent creates bead IDs from sprint IDs using this pattern:

```python
def sprint_id_to_bead_id(sprint_id: str, sprint_title: str) -> str:
    """
    Convert sprint ID and title to bead ID.

    Args:
        sprint_id: e.g., "1.2", "3.1a", "2.4b"
        sprint_title: e.g., "User Authentication"

    Returns:
        Bead ID like "bd-1-2-user-auth"
    """
    # Remove any dots from sprint ID (1.2a → 1-2a)
    parts = sprint_id.replace('.', '-')

    # Normalize title: lowercase, replace spaces/special chars with hyphens
    title_slug = re.sub(r'[^a-z0-9]+', '-', sprint_title.lower())
    title_slug = title_slug.strip('-')  # Remove leading/trailing hyphens

    return f"bd-{parts}-{title_slug}"
```

**Mapping Examples**:
- Sprint `1.1: Core Schema Validation Script` → `bd-1-1-schema`
- Sprint `1.2a: Example Work Bead` → `bd-1-2a-work`
- Sprint `3.4b: QA Agent Validation` → `bd-3-4b-qa-validation`

**Consistency Rule**: The bead ID in the annotation MUST match the actual `id` field in the generated bead JSON file.

### Annotation Algorithm

Implement back-annotation with this algorithm:

```python
def annotate_plan_with_bead_ids(
    plan_file_path: str,
    sprint_to_bead_mapping: dict[str, str]
) -> tuple[bool, str]:
    """
    Back-annotate plan file with bead IDs.

    Args:
        plan_file_path: Absolute path to plan markdown file
        sprint_to_bead_mapping: Dict mapping sprint ID → bead ID
                                e.g., {"1.1": "bd-1-1-schema", "1.2a": "bd-1-2a-work"}

    Returns:
        (success, message) tuple
    """
    try:
        with open(plan_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False, f"Plan file not found: {plan_file_path}"

    updated_lines = []
    annotations_added = 0

    for i, line in enumerate(lines):
        updated_lines.append(line)

        # Check if this line is a sprint heading
        match = re.match(SPRINT_HEADING_PATTERN, line)
        if match:
            phase = match.group(1)
            sprint_num = match.group(2)
            suffix = match.group(3) or ""
            sprint_id = f"{phase}.{sprint_num}{suffix}"

            # Check if we have a bead ID for this sprint
            if sprint_id in sprint_to_bead_mapping:
                bead_id = sprint_to_bead_mapping[sprint_id]

                # Check if next line is already an annotation (avoid duplicates)
                if i + 1 < len(lines) and 'beads-ralph:' in lines[i + 1]:
                    continue  # Skip, already annotated

                # Add annotation comment
                annotation = f'<!-- beads-ralph: {bead_id} -->\n'
                updated_lines.append(annotation)
                annotations_added += 1

    # Write updated plan back to file
    try:
        with open(plan_file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        return True, f"Added {annotations_added} bead ID annotations"
    except IOError as e:
        return False, f"Failed to write plan file: {str(e)}"
```

**Algorithm Steps**:
1. Read plan file line-by-line
2. Detect sprint headings using regex pattern
3. Extract sprint ID from heading
4. Look up bead ID in mapping dictionary
5. Check if annotation already exists (skip duplicates)
6. Insert annotation comment on next line
7. Write updated content back to plan file

### Use Cases for Bi-directional Navigation

**Use Case 1: Plan → Bead (Find Work Item from Plan)**

```bash
# Find bead ID for sprint 1.2 from plan file
grep -A 1 "### Sprint 1.2:" pm/2026-02-08-implementation-plan.md | grep "beads-ralph:"
# Output: <!-- beads-ralph: bd-1-2-user-auth -->

# Show full bead details
cat beads/bd-1-2-user-auth.json | jq .

# Check bead status
jq '.status' beads/bd-1-2-user-auth.json
# Output: "in_progress"
```

**Use Case 2: Bead → Plan (Find Plan Section from Work Item)**

```bash
# Extract plan file and section from bead metadata
jq -r '.metadata.plan_file, .metadata.plan_section' beads/bd-1-2-user-auth.json
# Output:
# pm/2026-02-08-implementation-plan.md
# ### Sprint 1.2: User Authentication

# Open plan file at specific section (for manual review)
code pm/2026-02-08-implementation-plan.md  # Search for "Sprint 1.2"
```

**Use Case 3: Audit Trail (Track Execution Status)**

```bash
# For each sprint in plan, show bead status
grep -E "^### Sprint" pm/2026-02-08-implementation-plan.md | while read heading; do
  sprint_id=$(echo "$heading" | grep -oE '[0-9]+\.[0-9]+[a-c]?')
  bead_id=$(grep -A 1 "Sprint $sprint_id:" pm/2026-02-08-implementation-plan.md | grep "beads-ralph:" | grep -oE 'bd-[a-z0-9-]+')
  status=$(jq -r '.status' "beads/$bead_id.json" 2>/dev/null || echo "not_found")
  echo "$sprint_id | $bead_id | $status"
done

# Output:
# 1.1 | bd-1-1-schema | closed
# 1.2a | bd-1-2a-work | in_progress
# 1.2b | bd-1-2b-merge | open
```

**Use Case 4: PR Link Resolution**

```bash
# Find PR URL from plan section
sprint_id="1.2a"
bead_id=$(grep -A 1 "Sprint $sprint_id:" pm/2026-02-08-implementation-plan.md | grep "beads-ralph:" | grep -oE 'bd-[a-z0-9-]+')
pr_url=$(jq -r '.metadata.pr_url // "not_created"' "beads/$bead_id.json")
echo "Sprint $sprint_id PR: $pr_url"
# Output: Sprint 1.2a PR: https://github.com/user/repo/pull/8
```

### Error Handling

**Missing Sprint in Mapping**:
```python
# Scenario: Sprint exists in plan but no bead was generated
# Action: Skip annotation for that sprint, log warning
if sprint_id not in sprint_to_bead_mapping:
    logger.warning(f"No bead ID found for sprint {sprint_id}, skipping annotation")
    continue
```

**Duplicate Annotations**:
```python
# Scenario: Sprint already has annotation from previous run
# Action: Detect existing annotation, skip adding duplicate
if i + 1 < len(lines) and 'beads-ralph:' in lines[i + 1]:
    logger.info(f"Sprint {sprint_id} already annotated, skipping")
    continue
```

**Invalid Bead ID Format**:
```python
# Scenario: Bead ID doesn't match expected pattern
# Action: Validate before annotation
if not re.match(r'^bd-[0-9a-z-]+$', bead_id):
    logger.error(f"Invalid bead ID format: {bead_id}, skipping annotation")
    continue
```

**File Write Failure**:
```python
# Scenario: Plan file is read-only or disk full
# Action: Catch IOError, return failure status
try:
    with open(plan_file_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
except IOError as e:
    return False, f"Failed to write plan file: {str(e)}"
```

**Malformed Sprint Headings**:
```python
# Scenario: Sprint heading doesn't match expected format
# Action: Log warning, skip that line
if not re.match(SPRINT_HEADING_PATTERN, line):
    if '### Sprint' in line:
        logger.warning(f"Malformed sprint heading at line {i}: {line.strip()}")
    continue
```

### Integration with Beads Workflow

**When to Annotate**:
1. **After Bead Generation**: Once all beads for a plan are successfully generated and validated
2. **Before Bead Execution**: Annotations help track which sprints have been converted to beads
3. **After Manual Plan Updates**: Re-run annotation when plan is modified to sync bead IDs

**When NOT to Annotate**:
- During bead generation (wait until all beads are validated)
- If any bead validation fails (partial annotations create confusion)
- On read-only plan files (e.g., archived plans, version control conflicts)

**Annotation Workflow**:
```python
# Typical workflow in beads-architect agent
def process_plan_and_annotate(plan_file_path: str, sprint_filter: str = None):
    # Step 1: Generate beads from plan
    beads = generate_beads_from_plan(plan_file_path, sprint_filter)

    # Step 2: Validate all beads
    validation_results = validate_all_beads(beads)
    if not all(result.success for result in validation_results):
        return {"success": False, "error": "Bead validation failed"}

    # Step 3: Write bead JSON files
    for bead in beads:
        write_bead_json(bead)

    # Step 4: Build sprint → bead ID mapping
    sprint_to_bead = {bead['metadata']['plan_sprint_id']: bead['id'] for bead in beads}

    # Step 5: Back-annotate plan file
    success, message = annotate_plan_with_bead_ids(plan_file_path, sprint_to_bead)

    return {"success": success, "beads_created": len(beads), "annotation_message": message}
```

### Preserving Plan Readability

**Design Principles**:
- Annotations use HTML comments (invisible in rendered markdown)
- Inserted immediately after heading (logical association)
- One line per annotation (consistent, easy to parse)
- No changes to existing content (preserves git diffs)

**Before Annotation**:
```markdown
### Sprint 1.2: User Authentication

**Worktree**: `../beads-ralph-worktrees/feature/1-2-user-auth`
**Branch**: `feature/1-2-user-auth`
**Source Branch**: `develop`
```

**After Annotation**:
```markdown
### Sprint 1.2: User Authentication
<!-- beads-ralph: bd-1-2-user-auth -->

**Worktree**: `../beads-ralph-worktrees/feature/1-2-user-auth`
**Branch**: `feature/1-2-user-auth`
**Source Branch**: `develop`
```

**Rendering Comparison**:
- **GitHub/GitLab**: HTML comments are completely hidden
- **VS Code Preview**: Comments not displayed
- **Plain Text Editors**: Comments visible but clearly marked as metadata
- **grep/sed**: Easy to filter with `grep "beads-ralph:"` or skip with `grep -v "<!--"`

**Git Diff Impact**:
```diff
 ### Sprint 1.2: User Authentication
+<!-- beads-ralph: bd-1-2-user-auth -->

 **Worktree**: `../beads-ralph-worktrees/feature/1-2-user-auth`
```

Annotations add minimal diff noise and clearly show audit trail additions.

## Examples

### Example 1: Simple Sequential Sprint

**Input Plan Section**:
```markdown
### Sprint 1.1: Core Schema Validation Script

**Worktree**: `../beads-ralph-worktrees/feature/1-1-schema-validator`
**Branch**: `feature/1-1-schema-validator`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)

**QA Agents**:
- `qa-python-tests` (haiku) - Run pytest with >90% coverage
- `qa-schema-validator` (haiku) - Validate script output format

**Tasks**:
- Create `scripts/bead_schema.py` with pydantic models
- Create `scripts/validate-bead-schema.py` CLI tool
- Create comprehensive test suite
```

**Output Bead JSON** (excerpt):
```json
{
  "id": "bd-1-1-schema",
  "title": "Core Schema Validation Script",
  "description": "Create scripts/bead_schema.py with pydantic models and scripts/validate-bead-schema.py CLI tool with comprehensive test suite",
  "status": "open",
  "priority": 1,
  "issue_type": "beads-ralph-work",
  "assignee": "beads-ralph-scrum-master",
  "dependencies": [],
  "labels": ["phase-01", "sprint-1-1"],
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
    ]
  }
}
```

### Example 2: Parallel Sprints

**Input Plan Sections**:
```markdown
### Sprint 1.2a: Example Work Bead (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/1-2a-work-bead`
**Branch**: `feature/1-2a-work-bead`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)

---

### Sprint 1.2b: Example Merge Bead (Parallel)

**Worktree**: `../beads-ralph-worktrees/feature/1-2b-merge-bead`
**Branch**: `feature/1-2b-merge-bead`
**Source Branch**: `develop`

**Dev Agents**:
- `python-backend-dev` (sonnet)
```

**Output Dependencies**:
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

Note: Both parallel sprints depend on the previous sequential sprint (1.1), but have no dependency on each other.

### Example 3: Merge Sprint

**Input Plan Section**:
```markdown
### Sprint 1.3: Integration & Documentation

**Worktree**: `../beads-ralph-worktrees/feature/1-3-schema-integration`
**Branch**: `feature/1-3-schema-integration`
**Source Branch**: `develop` (after 1.2a and 1.2b merged)

**Dev Agents**:
- `markdown-doc-writer` (sonnet)
- `python-backend-dev` (sonnet) - CI/CD setup

**Tasks**:
- Merge any conflicts from 1.2a and 1.2b
- Create `scripts/README.md` documenting validator usage
```

**Output Bead JSON** (excerpt):
```json
{
  "id": "bd-1-3-integration",
  "title": "Integration & Documentation",
  "status": "open",
  "issue_type": "beads-ralph-work",
  "dependencies": ["bd-1-2a-work", "bd-1-2b-merge"],
  "metadata": {
    "rig": "beads-ralph",
    "sprint": "1.3",
    "phase": "1",
    "plan_sprint_id": "1.3"
  }
}
```

Note: Sprint 1.3 depends on BOTH parallel sprints 1.2a and 1.2b completing.

## Constraints

- Read-only access to plan files (never modify plan markdown)
- Must generate valid bead JSON per `scripts/bead_schema.py` pydantic models
- All beads MUST include `"rig": "beads-ralph"` in metadata
- Dependencies must form a valid DAG (no circular dependencies)
- Sprint IDs must match regex patterns from schema.md
- Bead IDs must be unique across all generated beads
- QA agent output schemas must include `status` enum: `["pass", "fail", "stop"]`

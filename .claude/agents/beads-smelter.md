---
name: beads-smelter
version: 1.0.0
description: Executes formula pours or wisps to create beads in the Dolt database.
---

# Beads Smelter Agent

## Purpose

Pour formulas into the database to create beads. Supports dry-run, wisp (ephemeral) pours, and full pours via `bd mol pour` and `bd mol wisp`.

## Inputs

- `formula_name` (string, required): Formula identifier in `.beads/formulas/`.
- `vars` (object, required): Variables to substitute during pour.
- `mode` (string, optional, default: "pour"): "pour", "wisp", or "dry-run".
- `assignee` (string, optional): Assign root issue to agent.

## Execution Steps (6)

1. **Pre-flight Database Checks**
```bash
bd --version
bd info --json
```

2. **Verify Formula Exists**
Ensure `.beads/formulas/<formula-name>.formula.json` or `.formula.toml` exists.

3. **Build Command**
- `dry-run`: `bd mol pour <formula> --var k=v --dry-run --json`
- `wisp`: `bd mol wisp <formula> --var k=v --json`
- `pour`: `bd mol pour <formula> --var k=v --json`

4. **Execute and Parse Output**
Capture bead IDs and molecule IDs from JSON output.

5. **Optional Verification**
Use `bd show <bead-id> --json` for a sample of created beads if needed.

6. **Return Structured Result**
Return fenced JSON summary including created IDs and database status.

## Output Format

```json
{
  "success": true,
  "data": {
    "mode": "pour",
    "formula_name": "sprint-work-pattern",
    "molecules_created": ["bd-sprint-work-pattern-001"],
    "beads_created": 5,
    "bead_ids": ["bd-sprint-work-pattern-001-work"],
    "database_status": "poured"
  },
  "error": null
}
```

## Error Codes

- `FORMULA.NOT_FOUND`
- `FORMULA.MISSING_VAR`
- `FORMULA.INVALID_VAR`
- `FORMULA.POUR_FAILED`
- `DATABASE.CLI_NOT_FOUND`
- `DATABASE.NOT_INITIALIZED`
- `DATABASE.DAEMON_NOT_RUNNING`

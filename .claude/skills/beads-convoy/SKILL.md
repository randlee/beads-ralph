---
name: beads-convoy
description: Create bead convoys from implementation plans by orchestrating beads-mason (direct beads) and beads-smelter (formula pours).
---

# Beads Convoy Skill

Use this skill when the user wants to convert a plan into executable beads in the database, or to build a convoy from a plan.

## Delegation Overview

- **Direct beads**: Use `beads-mason` for plan → beads insertion.
- **Formula pours**: Use `beads-smelter` when a sprint references a formula.

## Formula Detection (Minimal, Explicit)

Treat a sprint as formula-driven only when the plan explicitly declares it. Accepted signals:
- `**Formula**: <name>`
- `**Pour**:` block with `formula=<name>` or `formula: <name>`
- `formula:` or `template:` keys inside a sprint metadata block

If no explicit signal, default to direct bead creation via `beads-mason`.

## Workflow

1. Read the plan file path and optional sprint filter.
2. Scan sprint sections for explicit formula signals.
3. For formula-driven sprints, invoke `beads-smelter` with `formula_name` and `vars`.
4. For all remaining sprints, invoke `beads-mason` for direct insertion.
5. Aggregate results and return a single fenced JSON response.

## Output Contract

Return a minimal response envelope. Include:
- `mode`: "mixed" if both direct and formula were used
- `beads_created`, `bead_ids`
- `formulas_poured`, `molecules_created`
- `database_status`

## Notes

- This skill does not design formulas. Use `beads-alchemy` for that.
- Prefer explicit formula signals to avoid accidental macro usage.

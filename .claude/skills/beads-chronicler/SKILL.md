---
name: beads-chronicler
description: Chronicle implementation plans into beads database by orchestrating beads-mason (direct beads), beads-smelter (formula pours), and beads-scribe (plan annotation).
---

# Beads Chronicler Skill

## See Also

- [Agent Architecture Documentation](../../../docs/agent-architecture.md) - Agent and skill design patterns


Use this skill when the user wants to chronicle a plan into the beads database - converting plan sections into beads, creating tracking containers (convoys), and annotating the plan with bead IDs.

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

- This skill chronicles plans by creating beads and tracking structures.
- It does not design formulas - use `beads-alchemy` for formula design.
- It delegates to `beads-scribe` for plan annotation (recording bead IDs).
- Prefer explicit formula signals to avoid accidental macro usage.
- Creates convoy tracking containers (gastown-style) for work coordination.

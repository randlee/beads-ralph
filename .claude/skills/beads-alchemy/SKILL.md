---
name: beads-alchemy
description: Design and maintain reusable formula templates for beads, with optional dry-run or wisp testing.
---

# Beads Alchemy Skill

## See Also

- [Agent Architecture Documentation](../../../docs/agent-architecture.md) - Agent and skill design patterns


Use this skill when the user wants to design, update, or validate formula templates for reusable sprint patterns.

## Delegation Overview

- **Design formulas**: Use `beads-alchemist`.
- **Test pours**: Use `beads-smelter` in `dry-run` or `wisp` mode.

## Workflow

1. Extract the target pattern from the user or plan.
2. Ask `beads-alchemist` to produce or update the formula file.
3. If testing requested, call `beads-smelter` with `mode: dry-run` or `mode: wisp` and representative variables.
4. Return a concise summary: formula path, vars, steps, and test outcome.

## Output Contract

Return a minimal response envelope. Include:
- `formula_name`, `formula_path`
- `vars`
- `steps`
- `test_mode` and `test_result` if testing was run

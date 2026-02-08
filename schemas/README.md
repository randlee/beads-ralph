# beads-ralph Schema Registry

**Centralized schema management** for multi-layer bead architecture (beads → gastown → ralph).

## Purpose

This registry provides:
1. **Version tracking** for upstream dependencies (beads, gastown)
2. **Schema layering** documentation (what comes from where)
3. **Change detection** when upstream repos update
4. **Conflict analysis** between extension mechanisms
5. **Single source of truth** for schema references

## Directory Structure

```
schemas/
├── README.md                    # This file
├── registry.yaml                # Version tracking & composition
├── base/
│   └── beads-v0.49.4.yaml      # Base beads schema (43 SQL columns)
├── extensions/
│   ├── gastown-v0.5.0.yaml     # Gastown description-field extensions
│   └── ralph-v0.1.0.yaml       # beads-ralph metadata JSON extensions
├── compiled/
│   └── (future) full-schema.yaml
└── DISCREPANCIES.md            # Doc/code mismatches

```

## Quick Reference

### Current Versions

| Component | Version | Commit | Extension Mechanism |
|-----------|---------|--------|---------------------|
| **beads** | v0.49.4-52-g249609de | 249609de | SQL columns (43 base + migrations) |
| **gastown** | v0.5.0-329-g7cf6e82d | 7cf6e82d | Description-field encoding |
| **ralph** | v0.1.0 (planned) | - | Metadata JSON column (22 fields) |

### Extension Mechanisms

**beads base**: Defines core SQL columns in `issues` table
- 43 columns in base CREATE TABLE
- Additional columns added via migrations
- `metadata TEXT NOT NULL DEFAULT '{}'` is the official extension point (GH#1406)

**gastown extensions**: Uses description-field encoding
- Stores structured data as `key: value` lines in `description` field
- Example: `role_type: polecat\nrig: main\nagent_state: working`
- Pros: Works without schema changes
- Cons: Fragile parsing, no type safety

**ralph extensions**: Uses metadata JSON column
- Stores 22 custom fields as structured JSON in `metadata` field
- Type-safe with pydantic v2 validation
- Example: `{"worktree_path": "/path/to/worktree", "phase": "1", "sprint": "1.1", ...}`
- Pros: Clean, type-safe, purpose-built
- Cons: Requires beads migration 042+

### No Conflicts!

Gastown and beads-ralph use **different extension mechanisms**:
- Gastown: `description` field (text)
- ralph: `metadata` field (JSON)
- **Zero field name conflicts**

## Usage

### For Developers

**Read the complete schema**:
1. Start with `registry.yaml` for overview
2. Check `base/beads-v0.49.4.yaml` for core fields
3. Check `extensions/gastown-v0.5.0.yaml` if integrating with gastown
4. Check `extensions/ralph-v0.1.0.yaml` for our custom fields

**Validate bead JSON**:
```bash
# Use the pydantic validator
python scripts/validate-bead-schema.py my-bead.json

# Or with stdin
cat my-bead.json | python scripts/validate-bead-schema.py
```

**Access metadata via bd CLI**:
```bash
# Read full bead including metadata
bd show bd-abc123 --json | jq .

# Read just metadata
bd show bd-abc123 --json | jq .metadata

# Update metadata
bd update bd-abc123 --metadata '{"phase": "2", "sprint": "2.1", ...}'
```

### For Schema Updates

**When beads or gastown releases a new version**:

1. **Fetch updates**:
   ```bash
   cd ../beads && git fetch --tags
   cd ../gastown && git fetch --tags
   ```

2. **Check for schema changes**:
   ```bash
   # Check beads schema
   cd ../beads
   git diff v0.49.4..HEAD -- internal/storage/sqlite/schema.go
   git diff v0.49.4..HEAD -- internal/storage/sqlite/migrations/

   # Check gastown fields
   cd ../gastown
   git diff v0.5.0..HEAD -- internal/beads/fields.go
   git diff v0.5.0..HEAD -- internal/beads/beads_*.go
   ```

3. **Update registry**:
   - Update version/commit in `registry.yaml`
   - Update `last_checked` date
   - If schema changed:
     - Create new `base/beads-vX.Y.Z.yaml` or `extensions/gastown-vX.Y.Z.yaml`
     - Update `registry.yaml` to reference new files
     - Document changes in `DISCREPANCIES.md` if docs are wrong

4. **Regenerate pydantic models** (if base changed):
   ```bash
   # Update scripts/bead_schema.py to match new schema
   # Re-run tests
   pytest scripts/tests/ -v --cov=scripts
   ```

## Schema Layers Explained

### Layer 1: Base Beads (SQL)

**Source**: `../beads/internal/storage/sqlite/schema.go`

The foundation. Defines 43 SQL columns in the `issues` table:
- Core fields: `id`, `title`, `description`, `status`, `priority`, `issue_type`, `assignee`
- Metadata extension point: `metadata TEXT NOT NULL DEFAULT '{}'`
- Many specialized fields: `wisp_type`, `mol_type`, `crystallizes`, `quality_score`, etc.

Additional columns added via migrations:
- `due_at`, `defer_until`, `close_reason`
- Agent fields: `hook_bead`, `role_bead`, `agent_state`, `last_activity`, `role_type`, `rig`
- Slot fields: `holder`

**Go struct**: `../beads/internal/types/types.go` (Issue struct has ~80+ fields)

### Layer 2: Gastown Extensions (Description Text)

**Source**: `../gastown/internal/beads/`

Extends beads without modifying the schema by encoding structured data in the `description` field.

**Approach**: Line-by-line `key: value` parsing
**Parsers**: `AgentFields`, `MRFields`, `AttachmentFields`, `EscalationFields`, etc.
**Custom types**: 11 issue types (agent, role, rig, convoy, slot, queue, event, message, molecule, gate, merge-request)

**Example**:
```
title: Agent gt:polecat-main
description: |
  role_type: polecat
  rig: main
  agent_state: working
  hook_bead: bd-abc123
  cleanup_status: clean
```

### Layer 3: beads-ralph Extensions (Metadata JSON)

**Source**: `docs/schema.md`, `scripts/bead_schema.py`

Uses the purpose-built `metadata` JSON column as intended by beads core (GH#1406).

**Approach**: Structured JSON with pydantic validation
**Fields**: 22 custom fields across 6 categories
**Custom types**: 2 issue types (beads-ralph-work, beads-ralph-merge)

**Example**:
```json
{
  "worktree_path": "/Users/dev/beads-ralph-worktrees/feature/1-1-schema-validator",
  "branch": "feature/1-1-schema-validator",
  "source_branch": "develop",
  "phase": "1",
  "sprint": "1.1",
  "plan_file": "pm/2026-02-08-implementation-plan.md",
  "dev_agent_path": ".claude/agents/python-backend-dev.md",
  "dev_model": "sonnet",
  "dev_prompts": ["Implement schema validation..."],
  "qa_agents": [...]
}
```

## Implementation Status

### Sprint 1.1 ✅ Complete

- [x] Created pydantic models for ralph extensions (`scripts/bead_schema.py`)
- [x] Created CLI validator (`scripts/validate-bead-schema.py`)
- [x] Comprehensive test suite (38 tests, 95% coverage)
- [x] Schema registry structure
- [x] Verified against beads/gastown source code
- [x] Documented 8 discrepancies in research docs

### Sprint 1.3 (Planned)

- [ ] Generate compiled full-schema.yaml
- [ ] Add schema update tooling (detect upstream changes)
- [ ] Update github-research docs with verified info
- [ ] Add schema documentation to main README.md

## Known Issues & Discrepancies

See [`DISCREPANCIES.md`](./DISCREPANCIES.md) for complete list.

**Summary**: 8 discrepancies found between research docs and actual code:
- 6 beads issues (mostly research doc inaccuracies)
- 2 gastown issues (missing metadata documentation)
- Priority: Fix dependencies PRIMARY KEY, document gastown extension mechanism

## Related Documentation

- [beads-ralph schema spec](../docs/schema.md) - Our metadata field definitions
- [Pydantic models](../scripts/bead_schema.py) - Implementation
- [Validation tests](../scripts/tests/) - Test coverage
- [Beads research](https://github-research/beads/) - Existing research (needs updates)
- [Gastown research](https://github-research/gastown/) - Existing research (needs updates)

## Contributing

When adding new metadata fields to beads-ralph:

1. Update `docs/schema.md` with field definition
2. Update `schemas/extensions/ralph-vX.Y.Z.yaml` (create new version if needed)
3. Update `scripts/bead_schema.py` pydantic models
4. Add tests in `scripts/tests/test_bead_schema.py`
5. Update `schemas/registry.yaml` if version bumped
6. Run validation: `pytest scripts/tests/ -v --cov=scripts`

## Questions?

- **"Where is field X defined?"** → Check registry.yaml, follow source references
- **"Can I use field Y?"** → Check DISCREPANCIES.md for conflicts
- **"How do I access metadata?"** → Use `bd show <id> --json | jq .metadata`
- **"Upstream changed, now what?"** → Follow "For Schema Updates" section above

---

**Last Updated**: 2026-02-08
**Maintained By**: beads-ralph development team
**Status**: ✅ Active, version-tracked, code-verified

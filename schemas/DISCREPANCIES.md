# Schema Documentation Discrepancies

This document tracks mismatches between documentation and actual source code for beads and gastown schemas.

**Last Updated**: 2026-02-08
**Source Agent**: a3c11b5 (schema-registry-researcher, opus model)
**Session ID**: ee0b0536-5b06-4033-b483-97a8dceb3051
**Verified Against**:
- beads v0.49.4-52-g249609de (commit 249609de)
- gastown v0.5.0-329-g7cf6e82d (commit 7cf6e82d)

**Agent Resurrection**: Use claude-history tool with agent ID `a3c11b5` to:
- Ask about specific discrepancies
- Request re-verification after upstream updates
- Clarify source code analysis methodology

---

## Summary

| Component | Discrepancies Found | Severity |
|-----------|---------------------|----------|
| Beads | 6 issues | Medium-High |
| Gastown | 2 issues | Medium |
| **Total** | **8 issues** | **Mixed** |

---

## Beads Discrepancies

### Issue 1: metadata Column Default Value

**Location**: Research doc `/Users/randlee/Documents/github/github-research/beads/database-schema-architecture.md` lines 193-257

**Documented as**: `metadata TEXT` (no default listed)
**Actually is**: `metadata TEXT NOT NULL DEFAULT '{}'`
**Source**: `../beads/internal/storage/sqlite/schema.go` line 54

**Impact**: Medium - The NOT NULL and DEFAULT '{}' are critical for ralph's usage. Without this information, developers might not know that metadata is always initialized as empty JSON.

**Recommendation**: Update research doc line ~250 to:
```sql
metadata TEXT NOT NULL DEFAULT '{}',  -- JSON storage for extensions (GH#1406)
```

---

### Issue 2: NOT NULL Constraints on Text Fields

**Location**: Research doc `/Users/randlee/Documents/github/github-research/beads/database-schema-architecture.md` lines 193-257

**Documented as**: `description TEXT`, `design TEXT`, `acceptance_criteria TEXT`, `notes TEXT` (nullable)
**Actually is**: All have `NOT NULL DEFAULT ''`
**Source**: `../beads/internal/storage/sqlite/schema.go` lines 9-12

**Impact**: Medium - These fields cannot be NULL; they default to empty string. Code expecting NULL will fail.

**Recommendation**: Update research doc to add NOT NULL DEFAULT '' for these fields.

---

### Issue 3: estimated_minutes CHECK Constraint

**Location**: Research doc `/Users/randlee/Documents/github/github-research/beads/database-schema-architecture.md` lines 193-257

**Documented as**: `CHECK(estimated_minutes >= 0)`
**Actually is**: No CHECK constraint
**Source**: `../beads/internal/storage/sqlite/schema.go` line 17

**Impact**: Low - The constraint was removed or never existed. Code should not rely on database-level validation for this field.

**Recommendation**: Remove CHECK constraint from research doc, or add note that validation is application-level only.

---

### Issue 4: closed_at CHECK Constraint

**Location**: Research doc `/Users/randlee/Documents/github/github-research/beads/database-schema-architecture.md` lines 193-257

**Documented as**: Simpler constraint (closed issues must have closed_at)
**Actually is**: More complex constraint that also allows tombstone status to have NULL closed_at
**Source**: `../beads/internal/storage/sqlite/schema.go` lines 63-67

**Actual Constraint**:
```sql
CHECK (
    (status = 'closed' AND closed_at IS NOT NULL) OR
    (status = 'tombstone') OR
    (status NOT IN ('closed', 'tombstone') AND closed_at IS NULL)
)
```

**Impact**: Medium - Tombstone beads can have NULL closed_at, which is a special case not documented.

**Recommendation**: Update research doc with full constraint including tombstone case.

---

### Issue 5: dependencies Table Primary Key

**Location**: Research doc `/Users/randlee/Documents/github/github-research/beads/database-schema-architecture.md` lines 193-257

**Documented as**: `PRIMARY KEY (issue_id, depends_on_id, type)`
**Actually is**: `PRIMARY KEY (issue_id, depends_on_id)`
**Source**: `../beads/internal/storage/sqlite/schema.go` lines 78-82

**Impact**: **HIGH** - The primary key does NOT include `type` column. This means you cannot have multiple dependency relationships with different types between the same two beads.

**Recommendation**: Update research doc to remove `type` from PRIMARY KEY. This is a significant schema difference.

---

### Issue 6: Agent Fields in Base CREATE TABLE

**Location**: Research doc `/Users/randlee/Documents/github/github-research/beads/database-schema-architecture.md` lines 193-257

**Documented as**: CREATE TABLE includes columns like `hook_bead`, `role_bead`, `agent_state`, `last_activity`, `role_type`, `rig`, etc.
**Actually is**: These fields are NOT in the base schema.go CREATE TABLE statement
**Source**:
- Base schema: `../beads/internal/storage/sqlite/schema.go` lines 1-68 (does NOT include these)
- Go struct: `../beads/internal/types/types.go` lines 115-121 (DOES include these)
- Added via migrations (not in base CREATE TABLE)

**Impact**: **HIGH** - The research doc conflates the base schema with the post-migration schema. The base CREATE TABLE has 43 columns, but the research doc shows a schema with additional migration-added columns.

**Recommendation**:
1. Create two sections in research doc:
   - "Base Schema (from schema.go)"
   - "Migration-Added Columns"
2. Clearly distinguish which columns are in the base vs added later
3. Reference specific migration files where possible

---

## Gastown Discrepancies

### Issue 7: Gastown Issue Struct vs Beads Issue Struct

**Location**: Gastown's simplified `Issue` struct at `/Users/randlee/Documents/github/gastown/internal/beads/beads.go` lines 26-59

**Documented as**: (Not explicitly documented, but implied to match beads)
**Actually is**: Gastown's Issue struct is a **simplified CLI-output model**, not the full beads model

**Missing from Gastown's Issue struct**:
- `Design`, `AcceptanceCriteria`, `Notes`
- `SpecID`, `Metadata`, `ExternalRef`
- Many agent fields, HOP fields, gate fields, molecule fields
- Compaction fields, deletion fields, event fields

**Extra in Gastown's Issue struct**:
- `Parent`, `Children` (flattened from dependency table)
- `DependsOn`, `Blocks`, `BlockedBy` (flattened from dependency table)

**Impact**: **Medium** - Gastown cannot access the `metadata` JSON field via its wrapper. beads-ralph must use `bd` CLI directly with `--json` to read/write metadata, or extend gastown's Issue struct.

**Recommendation**:
1. Document in research that gastown's Issue struct is incomplete
2. beads-ralph should use `bd show <id> --json` directly for full bead access
3. Consider extending gastown's Issue struct to include Metadata field

---

### Issue 8: Gastown Metadata Usage Not Documented

**Location**: Research doc `/Users/randlee/Documents/github/github-research/gastown/agent-communications.md`

**Documented as**: Schema section (line 209) describes beads schema but does not mention the `metadata` column at all
**Actually is**: Gastown does NOT use the metadata column; uses description-field encoding instead

**Impact**: **Medium** - This is a critical architectural difference that should be documented prominently. Without this knowledge, developers might assume gastown uses metadata and create conflicts.

**Recommendation**: Add section to gastown research doc:
```markdown
## Gastown Extension Mechanism

Gastown does NOT use the `metadata` JSON column. Instead, gastown extends
beads through **description-field encoding** - storing structured data as
`key: value` lines within the description text field.

This approach:
- Predates the metadata column (added in beads GH#1406)
- Is more fragile (parsing freetext)
- Has no type safety
- Cannot conflict with other systems using metadata JSON

See `/Users/randlee/Documents/github/gastown/internal/beads/fields.go` for
parsing implementations.
```

---

## Discrepancies NOT Found

The following were verified and found to be **correct** in existing documentation:

1. **Gastown custom types count**: Research doc says 11 types, code confirms 11 types (agent, role, rig, convoy, slot, queue, event, message, molecule, gate, merge-request) ✅

2. **Base beads core fields**: The core fields (id, title, description, status, priority, issue_type, assignee) are correctly documented ✅

3. **Dependencies table structure**: The edge schema approach (source/target relationship) is correctly documented, aside from the PRIMARY KEY issue noted above ✅

---

## Action Items

### Immediate (beads-ralph)

- [x] Create schema registry with verified information
- [x] Document discrepancies in this file
- [ ] Update Sprint 1.3 to include schema registry documentation
- [ ] Reference schema registry in main README.md

### Short-term (github-research updates)

Priority order for fixing research docs:

1. **High Priority**:
   - Fix dependencies PRIMARY KEY (Issue 5)
   - Separate base schema from migration-added columns (Issue 6)
   - Document gastown metadata non-usage (Issue 8)

2. **Medium Priority**:
   - Update metadata column definition (Issue 1)
   - Add NOT NULL constraints to text fields (Issue 2)
   - Update closed_at constraint (Issue 4)
   - Document gastown Issue struct limitations (Issue 7)

3. **Low Priority**:
   - Remove estimated_minutes CHECK constraint (Issue 3)

### Long-term (upstream PRs)

Consider submitting PRs to upstream repos:

**beads repo**:
- PR to improve schema.go comments explaining base vs migration-added columns
- PR to add SCHEMA.md documentation file

**gastown repo**:
- PR to extend Issue struct with Metadata field
- PR to add SCHEMA.md documenting extension mechanism
- Consider PR to migrate to metadata JSON (major breaking change)

---

## Verification Log

| Date | Verifier | Action |
|------|----------|--------|
| 2026-02-08 | schema-registry-researcher (opus) | Initial comprehensive analysis |
| 2026-02-08 | beads-ralph team | Schema registry creation |

---

## Notes

- All line numbers are approximate and may shift as code evolves
- Always trust source code over documentation when conflicts arise
- Run `git fetch` in ../beads and ../gastown before relying on this document
- Check beads/gastown versions match those listed at top of document

---

**Status**: ✅ **8 discrepancies documented, ready for research doc updates**

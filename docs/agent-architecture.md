# Beads-Ralph Agent Architecture

**Version**: 1.0.0
**Last Updated**: 2026-02-09
**Status**: Living Document

---

## 📚 Required Reading

**CRITICAL**: Before designing or implementing any agent or skill in beads-ralph, you MUST read these synaptic-canvas documents. They define best practices for prompt engineering, tool use, and agent design:

1. **[Agent Tool Use Best Practices](../../synaptic-canvas/docs/agent-tool-use-best-practices.md)**
   Essential guidelines for designing effective agents, tool patterns, and prompt structure.

2. **[Agent Runner Comprehensive](../../synaptic-canvas/docs/agent-runner-comprehensive.md)**
   Complete guide to agent orchestration, delegation patterns, and multi-agent coordination.

**Note**: All agent and skill designs in this document follow the patterns and conventions defined in these references.

---

## 🎯 Core Design Principle: Extensible Agent Templates

### Philosophy

**Agents roles are carefully defined, but implementations are extensible.**

Beads-ralph agents follow a **template-based architecture** where:

1. **Role Definition**: What the agent does (e.g., "maintain record-keeping")
2. **Interface Contract**: Input/output schemas, error codes, behavior guarantees
3. **Backend Implementations**: Multiple concrete implementations (Azure, Jira, GitHub, local, etc.)
4. **Configuration-Driven**: Users select backends via config, not code changes

### Why Templates?

**Problem**: Different teams use different tools (Azure DevOps, Jira, GitHub Issues, etc.) but need the same core functionality.

**Solution**: Create **agent templates** with:
- Core logic shared across implementations
- Backend-specific adapters via custom scripts
- Tool integration via CLIs (Azure CLI, gh, jira-cli, etc.)
- Clean separation: role vs implementation

### Template Architecture

```
┌─────────────────────────────────────────┐
│         Agent Role Definition           │
│  (What the agent does - invariant)      │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼─────┐ ┌──▼─────┐ ┌──▼─────────┐
│ Backend A   │ │Backend │ │ Backend C  │
│ (Azure)     │ │   B    │ │ (GitHub)   │
│             │ │(Jira)  │ │            │
│ - CLI tools │ │- REST  │ │ - gh CLI   │
│ - Scripts   │ │  API   │ │ - Scripts  │
│ - Adapters  │ │- Auth  │ │ - Webhooks │
└─────────────┘ └────────┘ └────────────┘
```

### Example: beads-scribe Agent

**Role**: Maintain synchronization between beads database and external record-keeping systems.

**Backends**:
- **Plan file** (local markdown) - Always enabled, core functionality
- **GitHub Issues** - Optional, uses `gh` CLI
- **Azure DevOps** - Optional, uses `az boards` CLI + custom scripts
- **Jira** - Optional, uses Jira REST API + authentication
- **None** - Database-only mode (no external systems)

**Configuration**:
```yaml
# .beads/config.yaml
scribe:
  record_keepers:
    plan:
      enabled: true  # Always on

    github_issues:
      enabled: true
      repo: "randlee/beads-ralph"
      cli: "gh"  # Uses GitHub CLI

    azure_devops:
      enabled: false
      organization: "myorg"
      project: "beads-ralph"
      cli: "az"  # Uses Azure CLI
      script: ".beads/scripts/azure-adapter.sh"

    jira:
      enabled: false
      base_url: "https://company.atlassian.net"
      auth_type: "api_token"
```

**Implementation Pattern**:
```markdown
## beads-scribe.md (Agent Definition)

### Backend Detection
1. Read `.beads/config.yaml`
2. Determine enabled backends
3. Validate CLI tools available (`gh --version`, `az --version`, etc.)
4. Load backend-specific scripts from `.beads/scripts/`

### Execution Flow
For each enabled backend:
1. Call backend adapter function
2. Pass standardized payload (bead data, action, metadata)
3. Adapter translates to backend-specific format
4. Execute CLI command or API call
5. Collect results
6. Aggregate success/failure across all backends

### Error Handling
- One backend failure doesn't block others
- Log all failures with context
- Return partial success (e.g., "plan updated, GitHub failed")
```

---

## 🏗️ Agent Registry

All agents in beads-ralph, their roles, and requirements.

### Production Agents

| Agent | Version | Role | Template | Deliverable | Requirements |
|-------|---------|------|----------|-------------|--------------|
| **beads-mason** | 2.0.0 | Build beads from plans | No | Yes | [beads-mason-requirements.txt](../.claude/agents/beads-mason-requirements.txt) |
| **beads-alchemist** | 1.0.0 | Design formula templates | No | Yes | (in agent definition) |
| **beads-smelter** | 1.0.0 | Pour formulas to create beads | No | Yes | (in agent definition) |
| **beads-scribe** | 1.0.0 | Maintain record-keeping | **Yes** | Yes | [beads-scribe-requirements.txt](../.claude/agents/beads-scribe-requirements.txt) |
| **beads-research-expert** | 1.0.0 | System design Q&A | No | **No** (local) | (in agent definition) |

### Planned Agents (Future Phases)

| Agent | Phase | Role | Template |
|-------|-------|------|----------|
| **beads-ralph-scrum-master** | 5 | Orchestrate dev/QA for single bead | No |
| **plan-review** | 3 | Validate bead schema and dependencies | No |
| **backend-dev** | 6 | Python/Go backend implementation | No |
| **frontend-dev** | 6 | TypeScript/React frontend work | No |
| **merge-specialist** | 6 | Resolve merge conflicts | No |
| **qa-unit-tests** | 6 | Run unit tests | No |
| **qa-security-scan** | 6 | Security scanning | No |
| **qa-lint** | 6 | Code linting | No |

---

## 🛠️ Skill Registry

Skills orchestrate agents and provide user-facing workflows.

### Production Skills

| Skill | Role | Delegates To | Deliverable | Requirements |
|-------|------|--------------|-------------|--------------|
| **beads-chronicler** | Chronicle plan → beads/convoys/annotations | mason, smelter, scribe | Yes | (in skill definition) |
| **beads-alchemy** | Design and test formula templates | alchemist, smelter | Yes | (in skill definition) |

### Planned Skills (Future Phases)

| Skill | Phase | Role | Delegates To |
|-------|-------|------|--------------|
| **beads-ralph-planner** | 3 | Plan refinement and validation | mason, plan-review |

---

## 📋 Agent Requirements Documents

### Current Requirements

1. **[beads-mason-requirements.txt](../.claude/agents/beads-mason-requirements.txt)** (5 lines)
   - Core bead creation from plans
   - Dependency compilation
   - Database insertion via `bd create --json`

2. **[beads-scribe-requirements.txt](../.claude/agents/beads-scribe-requirements.txt)** (95 pages, ~3,000 lines)
   - Plan annotation and completion marking
   - GitHub Issues integration (advanced)
   - Azure DevOps integration (advanced)
   - Jira integration (advanced)
   - Webhook support (advanced)
   - Plugin architecture (advanced)

### Requirements Format

All requirements documents follow this structure:

```markdown
# Agent Name - Requirements Specification

## Overview
Brief description, core principle

## Core Requirements (MVP)
Must-have functionality for Phase X

## Advanced Requirements (Future/Extensible)
Optional features, integrations, extensibility

## Implementation Strategy
Phased approach (MVP → Advanced → Extensions)

## Configuration Schema
YAML examples for all modes

## Error Handling & Resilience
Failure modes, idempotency, observability

## Testing Requirements
Unit, integration, performance tests

## Security Considerations
Credentials, validation, audit trail

## Dependencies
Core libraries, optional integrations

## Success Criteria
Measurable outcomes for MVP and Advanced

## Open Questions
Unresolved design decisions
```

---

## 🔧 Creating Extensible Agents

### Step-by-Step Template Design

#### 1. Define the Core Role

**Ask**: What is the invariant responsibility of this agent?

**Example** (beads-scribe):
> "Maintain synchronization between beads database and external record-keeping systems."

**Non-examples** (too specific):
- ❌ "Update GitHub Issues when beads complete" (ties to one backend)
- ❌ "Write markdown annotations to plan files" (misses external systems)

#### 2. Define the Interface Contract

**Inputs** (standardized across all backends):
```json
{
  "action": "annotate|complete|update",
  "bead_id": "bd-1-2-user-auth",
  "sprint_id": "1.2",
  "metadata": {
    "pr_number": 42,
    "completed_date": "2026-02-09",
    "commit_hash": "abc123"
  }
}
```

**Outputs** (standardized):
```json
{
  "success": true,
  "backends": {
    "plan": {"status": "success", "updated": true},
    "github": {"status": "success", "issue_id": "123"},
    "azure": {"status": "failed", "error": "AUTH_FAILED"}
  },
  "error": null
}
```

**Error Codes** (standardized):
- `BACKEND.NOT_CONFIGURED`
- `BACKEND.CLI_NOT_FOUND`
- `BACKEND.AUTH_FAILED`
- `BACKEND.RATE_LIMIT`
- `BACKEND.NETWORK_ERROR`

#### 3. Design Backend Adapters

Each backend gets:

**Adapter Script** (`.beads/scripts/backends/<backend>-adapter.sh`):
```bash
#!/usr/bin/env bash
# Azure DevOps adapter for beads-scribe

ACTION=$1       # annotate|complete|update
BEAD_ID=$2
METADATA_JSON=$3

case $ACTION in
  annotate)
    # Create work item
    az boards work-item create \
      --type Task \
      --title "Sprint $(extract_sprint_id $BEAD_ID)" \
      --project "$AZURE_PROJECT" \
      --fields "Beads.BeadID=$BEAD_ID"
    ;;

  complete)
    # Close work item
    WORK_ITEM_ID=$(find_work_item_by_bead_id "$BEAD_ID")
    az boards work-item update \
      --id "$WORK_ITEM_ID" \
      --state "Closed" \
      --fields "Microsoft.VSTS.Common.ClosedDate=$(date -u +%Y-%m-%d)"
    ;;
esac
```

**Config Schema** (`.beads/config.yaml`):
```yaml
scribe:
  record_keepers:
    azure_devops:
      enabled: true
      organization: "myorg"
      project: "beads-ralph"
      cli: "az"
      script: ".beads/scripts/backends/azure-adapter.sh"
      env:
        AZURE_DEVOPS_PAT: "${AZURE_DEVOPS_PAT}"  # From environment
```

#### 4. Implement Agent Logic

**Agent Prompt** (`.claude/agents/beads-scribe.md`):
```markdown
## Execution Steps

1. **Read Configuration**
   Load `.beads/config.yaml`, parse `scribe.record_keepers`

2. **Validate Backends**
   For each enabled backend:
   - Check CLI tool available (`which gh`, `which az`, etc.)
   - Verify credentials (`gh auth status`, `az account show`)
   - Load adapter script if specified

3. **Execute Action Across Backends**
   For each backend:
   - Call adapter with standardized inputs
   - Capture stdout/stderr
   - Parse result (exit code, JSON output)
   - Log success/failure

4. **Aggregate Results**
   Return combined status across all backends

5. **Handle Partial Failures**
   If some backends succeed and others fail:
   - Mark overall as "partial_success"
   - Include details for each backend
   - Log warnings, don't fail entire operation
```

#### 5. Document Backend Requirements

In requirements file, for each backend:

```markdown
### Backend: Azure DevOps

**CLI Tool**: `az` (Azure CLI)
**Install**: `brew install azure-cli` or `pip install azure-cli`
**Auth**: Personal Access Token via `AZURE_DEVOPS_PAT` env var
**Permissions**: `Work Items (Read, Write)`, `Project (Read)`

**Configuration**:
```yaml
azure_devops:
  enabled: true
  organization: "myorg"
  project: "beads-ralph"
  work_item_type: "Task"
```

**Testing**:
```bash
# Verify CLI installed
az --version

# Verify authentication
az devops login

# Test work item creation
az boards work-item create --type Task --title "Test" --project beads-ralph
```

**Rate Limits**: 200 requests per user per minute
**Error Handling**: Retry with exponential backoff (3 attempts)
```

#### 6. Create Minimal Backend (Always Works)

**Always include a "none" or "local-only" backend** that works without external dependencies:

```yaml
scribe:
  record_keepers:
    plan:
      enabled: true  # Local plan file - always works

    # All others optional
    github_issues:
      enabled: false
```

This ensures the agent is **always functional** even if users don't configure external systems.

---

## 🎨 Design Patterns

### Pattern 1: CLI-First Integration

**Principle**: Prefer CLI tools over direct API calls when available.

**Why**:
- CLIs handle auth/credentials (system keychain, config files)
- Simpler than managing API tokens in code
- Better error messages (designed for humans)
- Automatic retries and rate limiting built-in

**Examples**:
- GitHub: Use `gh` CLI, not REST API
- Azure: Use `az` CLI, not Python SDK
- Jira: Use `jira-cli` if available, fall back to REST API

**Implementation**:
```bash
# Good: Use CLI
gh issue create --title "Sprint 1.2" --body "..." --label "sprint-1"

# Avoid: Direct API
curl -X POST https://api.github.com/repos/owner/repo/issues \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Sprint 1.2", ...}'
```

### Pattern 2: Adapter Script Pattern

**Principle**: Backend-specific logic lives in separate scripts, not in agent prompts.

**Directory Structure**:
```
.beads/
├── config.yaml              # Configuration
└── scripts/
    └── backends/
        ├── github-adapter.sh
        ├── azure-adapter.sh
        ├── jira-adapter.py
        └── webhook-adapter.sh
```

**Agent calls adapter**:
```bash
# Agent executes:
.beads/scripts/backends/azure-adapter.sh annotate bd-1-2-user-auth '{"pr":42}'

# Adapter script handles Azure-specific details
# Agent just collects results
```

**Benefits**:
- Agent prompts stay focused on orchestration
- Backend logic is testable independently
- Easy to add new backends (new script, update config)
- Scripts can be versioned and shared across projects

### Pattern 3: Fail-Independent Backends

**Principle**: One backend failure doesn't cascade to others.

**Anti-pattern**:
```python
# BAD: Serial execution with early exit
update_plan()       # If this fails, nothing else runs
update_github()     # Never reached on plan failure
update_azure()      # Never reached
```

**Good Pattern**:
```python
# GOOD: Parallel/independent execution
results = {}
results['plan'] = try_update_plan()
results['github'] = try_update_github()
results['azure'] = try_update_azure()

# Aggregate results
overall = "success" if all_succeeded(results) else "partial_success"
return {"success": overall, "backends": results}
```

**Implementation**:
- Use background tasks (`&` in bash, threads in Python)
- Collect all results before returning
- Report partial success (some backends worked)

### Pattern 4: Configuration Validation at Startup

**Principle**: Validate all backend configs before executing actions.

**Validation Steps**:
```markdown
1. Parse `.beads/config.yaml`
2. For each enabled backend:
   - Check CLI tool installed (`which gh`)
   - Verify credentials (`gh auth status`)
   - Test connectivity (`gh api /user`)
   - Validate required fields in config
3. Report validation results
4. Disable backends that fail validation
5. Proceed with working backends only
```

**Early Failure**:
- If NO backends are configured → error `NO_BACKENDS_ENABLED`
- If critical backend fails (e.g., "plan") → error `CRITICAL_BACKEND_FAILED`
- If optional backend fails → warning, continue with others

### Pattern 5: Observability & Logging

**Principle**: Log all backend operations for debugging and audit.

**Log Format**:
```json
{
  "timestamp": "2026-02-09T12:34:56Z",
  "agent": "beads-scribe",
  "action": "complete",
  "bead_id": "bd-1-2-user-auth",
  "backend": "github",
  "operation": "close_issue",
  "result": "success",
  "duration_ms": 234,
  "details": {
    "issue_id": "123",
    "issue_url": "https://github.com/randlee/beads-ralph/issues/123"
  }
}
```

**Logging Levels**:
- **INFO**: All backend operations (success/failure)
- **WARN**: Backend failures, retries, partial success
- **ERROR**: Critical failures (database, plan file)
- **DEBUG**: CLI commands, API calls, raw responses

**Centralized Logging**:
```yaml
scribe:
  logging:
    level: "INFO"
    file: ".beads/logs/scribe.jsonl"  # JSON Lines format
    backends:
      github: "DEBUG"    # Override for specific backend
      azure: "WARN"
```

---

## 🧪 Testing Extensible Agents

### Unit Tests (Per Backend)

**Test each adapter independently**:

```bash
# Test GitHub adapter
./tests/backends/test-github-adapter.sh

# Test Azure adapter
./tests/backends/test-azure-adapter.sh
```

**Mock external services**:
- Use `gh --help` exit code to detect CLI presence
- Mock API responses with test servers
- Use Docker containers for integration tests (e.g., local Jira)

### Integration Tests (Agent + Backends)

**Test agent orchestration**:

```python
def test_scribe_partial_failure():
    """Test scribe handles one backend failing gracefully"""
    # Setup: Configure plan (works) + github (fails)
    config = {
        "plan": {"enabled": True},
        "github": {"enabled": True, "repo": "fake/repo"}
    }

    # Execute
    result = beads_scribe.complete_bead("bd-test", config)

    # Assert
    assert result["success"] == "partial_success"
    assert result["backends"]["plan"]["status"] == "success"
    assert result["backends"]["github"]["status"] == "failed"
    assert "NETWORK_ERROR" in result["backends"]["github"]["error"]
```

### Configuration Tests

**Validate config schema**:

```python
def test_invalid_backend_config():
    """Test agent rejects invalid backend config"""
    config = {
        "github": {
            "enabled": True,
            # Missing required "repo" field
        }
    }

    with pytest.raises(ValidationError):
        beads_scribe.validate_config(config)
```

---

## 📦 Agent Distribution & Reuse

### Packaging Template Agents

**Directory Structure**:
```
beads-ralph/
├── .claude/
│   ├── agents/
│   │   ├── beads-scribe.md              # Agent definition
│   │   └── beads-scribe-requirements.txt
│   └── scripts/
│       └── backends/
│           ├── github-adapter.sh
│           ├── azure-adapter.sh
│           ├── jira-adapter.py
│           └── README.md                # Backend setup docs
├── .beads/
│   ├── config.yaml                      # User's config
│   └── config.example.yaml              # Example config
```

### Sharing Adapters

**Backend adapters are reusable**:
- Publish adapters as standalone scripts
- Document dependencies (CLI tools, env vars)
- Provide test scripts for validation
- Version adapters independently from agents

**Example**: `github-adapter.sh` could be used by multiple agents:
- `beads-scribe` (record-keeping)
- `beads-notifier` (send notifications)
- `beads-reporter` (generate reports)

---

## 🔐 Security Considerations

### Credential Management

**Never hardcode credentials**:
```yaml
# ❌ BAD
azure_devops:
  token: "abc123xyz"  # Plain text token

# ✅ GOOD
azure_devops:
  token_env: "AZURE_DEVOPS_PAT"  # Reference env var
```

**Use system credential stores**:
- macOS: Keychain
- Linux: gnome-keyring, secret-service
- Windows: Credential Manager

**CLI tools handle credentials**:
- `gh auth login` → stores in keychain
- `az login` → uses browser auth, stores token
- `jira-cli config` → stores API token securely

### Least Privilege

**Grant minimum required permissions**:

| Backend | Required Permissions | Optional Permissions |
|---------|---------------------|----------------------|
| GitHub | `repo` (private) or `public_repo` | `workflow` (if modifying Actions) |
| Azure DevOps | `Work Items (Read, Write)` | `Code (Read)` for PR linking |
| Jira | `Browse Projects`, `Create Issues` | `Administer Projects` (only for setup) |

### Audit Logging

**Log all external system modifications**:
```json
{
  "timestamp": "2026-02-09T12:34:56Z",
  "agent": "beads-scribe",
  "action": "close_issue",
  "backend": "github",
  "actor": "beads-ralph-bot",
  "target": "https://github.com/randlee/beads-ralph/issues/123",
  "result": "success"
}
```

**Retain logs for forensics**:
- Minimum 90 days retention
- Immutable append-only logs
- Include actor (agent or human) for all operations

---

## 📊 Performance Considerations

### Parallel Backend Execution

**Execute backends concurrently**:
```bash
# Bash example
update_plan &
PID_PLAN=$!

update_github &
PID_GITHUB=$!

update_azure &
PID_AZURE=$!

# Wait for all
wait $PID_PLAN $PID_GITHUB $PID_AZURE
```

**Benefits**:
- 3 backends in parallel = 3x faster than serial
- One slow backend doesn't block others
- Overall latency = max(backend_latencies), not sum

### Rate Limiting

**Respect backend rate limits**:

| Backend | Rate Limit | Strategy |
|---------|-----------|----------|
| GitHub API | 5000 req/hour | Exponential backoff + retry |
| Azure DevOps | 200 req/min/user | Token bucket algorithm |
| Jira Cloud | ~100 req/sec | Sliding window limiter |

**Implementation**:
- Track requests per backend
- Sleep if approaching limit
- Use batch APIs when available (GitHub GraphQL, Azure batch)

### Caching

**Cache backend state to reduce API calls**:

```yaml
scribe:
  cache:
    enabled: true
    ttl_seconds: 300  # 5 minutes
    backends:
      github:
        cache_issue_ids: true      # Don't re-fetch issue IDs
      azure:
        cache_work_item_ids: true
```

**What to cache**:
- Issue/work item IDs (stable, don't change)
- Backend availability status (avoid repeated health checks)
- Mapping data (bead ID → issue ID)

**What NOT to cache**:
- Status (changes frequently)
- Comments/descriptions (mutable)
- Credentials (security risk)

---

## 🚀 Future Extensions

### Planned Template Agents

1. **beads-notifier** (Phase 6)
   - Role: Send notifications on bead lifecycle events
   - Backends: Slack, Email, Discord, Teams, webhooks
   - Template: Similar to scribe (multi-backend, config-driven)

2. **beads-reporter** (Phase 7)
   - Role: Generate progress reports and dashboards
   - Backends: Markdown, HTML, PDF, Confluence, SharePoint
   - Template: Multi-format export with backend adapters

3. **beads-metrics** (Phase 8)
   - Role: Collect and publish metrics
   - Backends: Prometheus, Datadog, CloudWatch, local JSON
   - Template: Pluggable metrics exporters

### Community Adapters

**Allow community-contributed backend adapters**:
- GitHub repository for adapters: `beads-ralph-adapters`
- Standard adapter interface (input/output/error codes)
- Verified adapters (tested, security reviewed)
- User-contributed adapters (use at own risk)

**Adapter Registry**:
```yaml
# .beads/adapter-registry.yaml
adapters:
  - name: "clickup"
    type: "project-management"
    author: "community"
    url: "https://github.com/beads-ralph-adapters/clickup"
    verified: false

  - name: "notion"
    type: "documentation"
    author: "randlee"
    url: "https://github.com/beads-ralph-adapters/notion"
    verified: true
```

---

## 📝 Documentation Requirements

### Agent README

Every template agent must include:

1. **Overview**: What the agent does, why it exists
2. **Core Functionality**: Works without external dependencies
3. **Backend Options**: List of supported backends
4. **Setup Guide**: Per-backend configuration instructions
5. **Examples**: Common use cases with config snippets
6. **Troubleshooting**: Common errors and solutions

### Backend Adapter README

Every adapter must include:

1. **Requirements**: CLI tools, libraries, permissions
2. **Installation**: Step-by-step setup instructions
3. **Authentication**: How to configure credentials
4. **Configuration**: YAML schema and examples
5. **Testing**: How to verify adapter works
6. **API Reference**: Commands, inputs, outputs, errors

### Example Structure

```
.claude/agents/
├── beads-scribe.md                  # Agent definition
├── beads-scribe-requirements.txt    # Requirements
└── backends/
    ├── README.md                    # Overview of all backends
    ├── github/
    │   ├── README.md                # GitHub backend docs
    │   ├── setup.sh                 # Setup script
    │   └── test.sh                  # Test script
    ├── azure/
    │   ├── README.md
    │   ├── setup.sh
    │   └── test.sh
    └── jira/
        ├── README.md
        ├── setup.sh
        └── test.sh
```

---

## ✅ Checklist: Creating a Template Agent

Use this checklist when designing a new extensible agent:

### Design Phase
- [ ] Define core role (invariant across backends)
- [ ] Identify 3+ potential backends
- [ ] Design standardized input/output schemas
- [ ] Define error codes (generic, not backend-specific)
- [ ] Choose CLI-first vs API-first per backend
- [ ] Document "minimal backend" (always works)

### Implementation Phase
- [ ] Create agent definition (`.claude/agents/<agent>.md`)
- [ ] Create requirements file (`<agent>-requirements.txt`)
- [ ] Implement core logic (orchestration, validation)
- [ ] Create backend adapters (`.beads/scripts/backends/`)
- [ ] Define configuration schema (`.beads/config.yaml`)
- [ ] Add backend validation at startup
- [ ] Implement parallel execution (where possible)
- [ ] Add comprehensive logging

### Testing Phase
- [ ] Unit tests for each adapter
- [ ] Integration tests (agent + backends)
- [ ] Configuration validation tests
- [ ] Partial failure scenarios
- [ ] Rate limiting tests
- [ ] Security review (credentials, input validation)

### Documentation Phase
- [ ] Agent README (overview, setup, examples)
- [ ] Backend setup guides (per backend)
- [ ] Configuration examples (`.beads/config.example.yaml`)
- [ ] Troubleshooting guide
- [ ] Update this agent-architecture.md

### Release Phase
- [ ] Version agent (semantic versioning)
- [ ] Update agent registry in this document
- [ ] Tag release in git
- [ ] Announce new backends in release notes

---

## 🎓 Learning Resources

### Synaptic Canvas References (Required)

1. **[Agent Tool Use Best Practices](../../synaptic-canvas/docs/agent-tool-use-best-practices.md)**
   - Prompt engineering patterns
   - Tool use conventions
   - Error handling strategies
   - Testing approaches

2. **[Agent Runner Comprehensive](../../synaptic-canvas/docs/agent-runner-comprehensive.md)**
   - Multi-agent coordination
   - Delegation patterns
   - Task decomposition
   - Result aggregation

### External Resources

- **Claude Prompt Engineering**: https://docs.anthropic.com/en/docs/prompt-engineering
- **CLI Design Patterns**: https://clig.dev/
- **YAML Best Practices**: https://yaml.org/spec/1.2/spec.html
- **Bash Scripting Guide**: https://mywiki.wooledge.org/BashGuide

---

## 📅 Maintenance

### Updating This Document

**When to update**:
- New agent added → Update agent registry
- New skill added → Update skill registry
- New backend adapter → Update examples
- Design pattern change → Update patterns section
- Requirements file added → Update requirements section

**Who can update**:
- Primary: ARCH-RALPH (autonomous agent)
- Secondary: Project maintainers
- Process: PR to `develop` branch, review required

**Version History**:
- 1.0.0 (2026-02-09): Initial version with template-based architecture

---

**Document Owner**: ARCH-RALPH
**Review Cadence**: After each phase completion
**Next Review**: After Phase 3 (Planning System) completes

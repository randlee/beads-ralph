# beads-ralph

![Python Tests](https://github.com/randlee/beads-ralph/actions/workflows/python-tests.yml/badge.svg)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-90%25+-success.svg)](scripts/)

**Autonomous multi-agent development orchestration system**

beads-ralph converts complete implementation plans into executable beads (work items) and executes them autonomously in parallel using isolated git worktrees, coordinating multiple Claude Code agents via a Go orchestration loop.

## Status

**Phase 1 in progress**: Schema & Validation (3 of 26 sprints complete - 12%)

- ✅ Sprint 1.1: Core Schema Validation Script
- ✅ Sprint 1.2a: Example Work Bead
- ✅ Sprint 1.2b: Example Merge Bead
- 🚧 Sprint 1.3: Integration & Documentation (current)

## Features

- **Plan-to-Bead Conversion**: Automated conversion of markdown plans into structured work items
- **Parallel Execution**: Isolated worktree-based execution for maximum parallelization
- **Dev-QA Loops**: Built-in retry loops with QA validation gates
- **Audit Trail**: Complete execution history with PR-based human review
- **CI/CD Integration**: Automated testing across Mac/Windows/Linux
- **Agent Coordination**: Multi-agent orchestration via Go loop

## Quick Start

### Validating Bead Files

```bash
# Install dependencies
cd scripts
pip install -r requirements.txt

# Validate a bead file
python3 validate-bead-schema.py examples/example-work-bead.json
```

**Output**:
```
✓ Valid bead
```

### Running Tests

```bash
cd scripts
pytest tests/ -v --cov=. --cov-report=term-missing
```

**Coverage**: >90% on all modules

## Project Structure

```
beads-ralph/
├── scripts/              # Schema validation tools
│   ├── bead_schema.py    # Pydantic models
│   ├── validate-bead-schema.py  # CLI validator
│   ├── requirements.txt  # Python dependencies
│   └── tests/            # Test suite (>90% coverage)
├── examples/             # Example bead files
│   ├── example-work-bead.json   # Work bead example
│   └── example-merge-bead.json  # Merge bead example
├── docs/                 # Design documentation
│   ├── schema.md         # Bead schema specification
│   ├── architecture.md   # System architecture
│   └── numbering.md      # Phase/sprint numbering
├── pm/                   # Project management
│   └── 2026-02-08-implementation-plan.md  # MVP implementation plan
└── .github/workflows/    # CI/CD automation
    └── python-tests.yml  # Multi-platform test matrix
```

## CI/CD

Tests run automatically on every PR:

- **Platforms**: Ubuntu (Linux), macOS, Windows
- **Python versions**: 3.9, 3.10, 3.11, 3.12
- **Total matrix**: 12 test combinations
- **Coverage threshold**: 90% (PRs fail if below)
- **Validation**: All example beads tested

## Bead Schema

Beads are JSON work items with 34 fields:

- **14 core fields**: id, title, description, status, priority, etc.
- **20 metadata fields**: worktree paths, agents, QA configs, execution tracking

**Types**:
- **Work Bead** (`issue_type: "beads-ralph-work"`): Standard development tasks
- **Merge Bead** (`issue_type: "beads-ralph-merge"`): Parallel sprint integration

See [`examples/`](examples/) for complete examples and [`scripts/README.md`](scripts/README.md) for validation details.

## Documentation

- **[Schema Specification](docs/schema.md)** - Complete bead schema with validation rules
- **[Architecture](docs/architecture.md)** - System design and data flow
- **[Implementation Plan](pm/2026-02-08-implementation-plan.md)** - 6-phase, 26-sprint MVP plan
- **[Validator Usage](scripts/README.md)** - Schema validation tools and API

## Development

### Requirements

- Python 3.9+ for schema validation
- Go 1.21+ for ralph loop (Phase 4+)
- Git with worktree support
- Claude Code CLI

### Branch Strategy

- **`develop`** - Integration branch (target for all PRs)
- **`main`** - Stable releases
- **Feature branches** - Created in worktrees via `sc-git-worktree` skill

### Workflow

1. Create worktree from `develop`
2. Implement feature
3. Run tests locally
4. Create PR to `develop`
5. CI runs tests on Mac/Windows/Linux
6. Merge after review

## Roadmap

### Phase 1: Schema & Validation ⏳
- ✅ 1.1: Schema validator with tests
- ✅ 1.2a/b: Example beads (work + merge)
- 🚧 1.3: Documentation + CI/CD

### Phase 2: Beads Architect Agent
- Convert plans to beads
- Dependency compilation
- Plan back-annotation

### Phase 3: Planning System
- Planning skill integration
- Plan review agent
- Validation workflow

### Phase 4: Go Ralph Loop
- Core orchestration loop
- Bead claiming (CAS)
- Scrum-master launcher

### Phase 5: Scrum-Master Agent
- Dev/QA orchestration
- Retry loop management
- PR creation

### Phase 6: MVP Testing
- Example agents
- End-to-end test
- Documentation

## Contributing

This project is currently in MVP development and not yet accepting external contributions. Watch this space for updates.

## License

MIT License (to be added)

## Acknowledgments

Built using Claude Code and the beads framework concept.
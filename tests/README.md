# Beads-Ralph Test Suite

Comprehensive test suite for the beads-ralph autonomous development orchestration system.

## Test Organization

### tests/test_beads_architect/

Tests for the beads-mason agent that converts implementation plans to executable beads.

#### Test Modules

- **test_plan_parsing.py** - Plan markdown parsing and sprint metadata extraction
  - Sprint header parsing (sequential, parallel, phase splits)
  - Metadata extraction (worktree, branch, agents, tasks)
  - Edge cases (malformed markdown, Unicode, missing fields)

- **test_dependency_generation.py** - Dependency resolution algorithm
  - Sequential dependencies (1.1 → 1.2 → 1.3)
  - Parallel dependencies (1.2a, 1.2b both depend on 1.1)
  - Merge dependencies (1.3 depends on [1.2a, 1.2b])
  - Phase splits (3a.1, 3b.1 start from same base)
  - Phase convergence (4.1 depends on last of 3a and 3b)

- **test_bead_generation.py** - Complete bead JSON generation
  - Bead ID generation (bd-<sprint>-<title-slug>)
  - Core fields (15 required fields)
  - Metadata fields (19+ metadata fields)
  - Dev/QA agent configuration
  - Complete bead structure validation

- **test_validation.py** - Schema validation integration
  - Integration with validate-bead-schema.py
  - Valid bead acceptance
  - Invalid bead rejection
  - QA agent output schema validation
  - Batch validation
  - Error reporting

- **test_back_annotation.py** - Plan back-annotation functionality
  - HTML comment format (<!-- beads-ralph: bd-id -->)
  - Comment insertion after sprint headings
  - Bi-directional tracking (plan ↔ bead)
  - Annotation workflow
  - Edge cases (Unicode, special chars, multiple files)

#### Test Fixtures

Located in `tests/test_beads_architect/fixtures/`:

- **simple-plan.md** - 3 sprint sequential plan
- **parallel-plan.md** - Plan with parallel execution (1.2a, 1.2b)
- **complex-plan.md** - Multi-phase with splits and convergence
- **expected-simple-dependencies.json** - Expected dependencies for simple plan
- **expected-parallel-dependencies.json** - Expected dependencies for parallel plan
- **expected-complex-dependencies.json** - Expected dependencies for complex plan

## Running Tests

### Run All Tests

```bash
# From repository root
pytest tests/

# With coverage
pytest tests/ --cov=scripts --cov-report=term-missing

# With verbose output
pytest tests/ -v
```

### Run Specific Test Module

```bash
# Run only plan parsing tests
pytest tests/test_beads_architect/test_plan_parsing.py

# Run only dependency generation tests
pytest tests/test_beads_architect/test_dependency_generation.py -v

# Run only validation tests
pytest tests/test_beads_architect/test_validation.py
```

### Run Specific Test Class or Function

```bash
# Run specific test class
pytest tests/test_beads_architect/test_plan_parsing.py::TestSprintHeaderParsing

# Run specific test function
pytest tests/test_beads_architect/test_dependency_generation.py::TestSequentialDependencies::test_simple_sequential_chain

# Run tests matching pattern
pytest tests/ -k "parallel"
```

### Run with Coverage Report

```bash
# Generate terminal coverage report
pytest tests/ --cov=scripts --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=scripts --cov-report=html
# Open htmlcov/index.html in browser

# Set minimum coverage threshold
pytest tests/ --cov=scripts --cov-fail-under=90
```

## Test Dependencies

Install test dependencies:

```bash
pip install -r scripts/requirements.txt
```

Required packages:
- pytest >= 7.0
- pytest-cov >= 4.0
- pydantic >= 2.0

## Coverage Goals

Target coverage levels:
- Overall: >90%
- Core modules (bead_schema.py): >95%
- Validation scripts: >85%

Current coverage can be checked with:
```bash
pytest tests/ --cov=scripts --cov-report=term-missing
```

## CI/CD Integration

These tests are designed for integration with GitHub Actions CI/CD pipeline:

- Run on every PR to `develop` branch
- Run on push to `develop` branch
- Matrix build: Python 3.9, 3.10, 3.11, 3.12
- Platforms: Ubuntu (linux), macOS, Windows
- Coverage reporting with codecov or similar

Example GitHub Actions workflow:
```yaml
name: Python Tests
on:
  pull_request:
    branches: [develop]
  push:
    branches: [develop]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -r scripts/requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=scripts --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Strategy

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (<1s per test)

### Integration Tests
- Test interaction between components
- Use real validation scripts
- Test complete workflows

### Fixture-Based Tests
- Use sample plans for realistic scenarios
- Validate expected outputs match actual
- Test against real examples from repository

## Writing New Tests

When adding new tests:

1. **Choose the right module**
   - Plan parsing → test_plan_parsing.py
   - Dependencies → test_dependency_generation.py
   - Bead generation → test_bead_generation.py
   - Validation → test_validation.py
   - Back-annotation → test_back_annotation.py

2. **Use descriptive names**
   - Test class: `TestFeatureName`
   - Test method: `test_specific_behavior`
   - Be specific: `test_parallel_sprints_same_base` vs `test_parallel`

3. **Include docstrings**
   ```python
   def test_sequential_dependencies(self):
       """Test that sequential sprints have correct dependency chain."""
   ```

4. **Use fixtures**
   - Reuse shared fixtures from conftest.py
   - Create new fixtures for complex setup
   - Keep fixtures focused and reusable

5. **Use parametrize for variations**
   ```python
   @pytest.mark.parametrize("sprint_id,expected", [
       ("1.1", "bd-1-1-..."),
       ("1.2a", "bd-1-2a-..."),
   ])
   def test_bead_id_format(self, sprint_id, expected):
       ...
   ```

6. **Test edge cases**
   - Empty inputs
   - Malformed data
   - Unicode characters
   - Missing required fields

7. **Verify error handling**
   - Test that errors are raised when expected
   - Verify error messages are helpful
   - Check error codes match specification

## Test Maintenance

### Keep Tests Fast
- Use mocking for slow operations
- Avoid unnecessary file I/O
- Run integration tests separately if needed

### Keep Tests Independent
- Each test should run in isolation
- Don't rely on test execution order
- Clean up any created files/state

### Keep Tests Readable
- Clear arrange-act-assert structure
- Descriptive variable names
- Comments for complex logic

### Keep Tests Current
- Update tests when requirements change
- Remove obsolete tests
- Add tests for new features

## Troubleshooting

### Tests Fail on Import
```bash
# Ensure you're in the repository root
cd /path/to/beads-ralph

# Install dependencies
pip install -r scripts/requirements.txt

# Run tests
pytest tests/
```

### Coverage Too Low
```bash
# Identify uncovered lines
pytest tests/ --cov=scripts --cov-report=term-missing

# Focus on uncovered areas
pytest tests/test_beads_architect/test_validation.py --cov=scripts/validate-bead-schema.py
```

### Tests Pass Locally But Fail in CI
- Check Python version differences
- Check platform-specific path handling
- Verify all dependencies in requirements.txt
- Check for race conditions in parallel execution

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [beads-ralph schema documentation](../docs/schema.md)
- [beads-mason agent definition](../.claude/agents/beads-mason.md)

## Questions?

For questions about testing strategy or adding new tests, consult:
- Implementation plan: `pm/2026-02-08-implementation-plan.md`
- Schema documentation: `docs/schema.md`
- Agent definition: `.claude/agents/beads-mason.md`

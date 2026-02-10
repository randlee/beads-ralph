# Bead Claiming Design

## Overview

The bead claiming system implements atomic Compare-And-Swap (CAS) semantics to ensure that only one agent can claim a specific bead at a time, preventing race conditions in distributed environments.

## Atomic CAS Behavior

### Command Interface

The `bd claim <bead-id>` command provides the atomic claiming mechanism:

```bash
bd claim bd-1234
```

**Success**: Exit code 0, bead is now claimed by this agent
**Already Claimed**: Exit code 2 or stderr contains "already claimed"
**Other Errors**: Exit code 1 with descriptive error message

### Atomicity Guarantees

The `bd claim` command ensures atomicity through one of these mechanisms:

1. **Database-level transactions** (PostgreSQL, MySQL, etc.)
2. **File-based locking** with atomic operations (mkdir, O_EXCL)
3. **Distributed locks** (Redis, etcd, etc.)

The specific implementation is handled by the `bd` CLI, but the guarantees remain the same:
- **Mutual exclusion**: Only one agent can successfully claim a bead
- **No race conditions**: Concurrent claim attempts are serialized
- **Idempotency**: Re-claiming an already-claimed bead returns ErrAlreadyClaimed

## Retry Logic

### Exponential Backoff

The claiming system implements exponential backoff for transient failures:

```go
config := ClaimConfig{
    MaxRetries:        3,
    InitialBackoff:    100 * time.Millisecond,
    MaxBackoff:        5 * time.Second,
    BackoffMultiplier: 2.0,
}
```

**Backoff Sequence**: 100ms → 200ms → 400ms → 800ms (capped at 5s)

### Retry Categories

**Retried**:
- Network timeouts
- Temporary service unavailability
- Rate limiting
- Transient database errors

**NOT Retried**:
- `ErrAlreadyClaimed` (permanent failure for this agent)
- Invalid bead ID
- Permission denied
- Authentication failures

### Example Timeline

```
Attempt 1: Network timeout (wait 100ms)
Attempt 2: Network timeout (wait 200ms)
Attempt 3: Network timeout (wait 400ms)
Attempt 4: Success! (total: ~700ms)
```

## Concurrency Safety

### Race Condition Prevention

The claiming logic is designed to handle concurrent claim attempts safely:

```go
// 10 agents try to claim the same bead concurrently
results := make(chan error, 10)
for i := 0; i < 10; i++ {
    go func() {
        err := claimBead(ctx, "bd-1234")
        results <- err
    }()
}

// Result: Exactly 1 success, 9 ErrAlreadyClaimed
```

### Context Cancellation

All claim operations respect context cancellation:

```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

err := claimBead(ctx, "bd-1234")
// Returns context error if cancelled during claim or backoff
```

## Error Handling

### Error Types

```go
// Permanent failure - do not retry
var ErrAlreadyClaimed = errors.New("bead already claimed")

// Example transient errors (retried automatically)
- "network timeout"
- "connection refused"
- "service unavailable"
```

### Error Detection

```go
err := claimBead(ctx, beadID)
if errors.Is(err, ErrAlreadyClaimed) {
    // This bead is taken, try another one
    log.Printf("Bead %s already claimed, skipping", beadID)
    continue
}
if err != nil {
    // Fatal error after retries
    return fmt.Errorf("claim failed: %w", err)
}
// Success - proceed with work
```

## Testing Strategy

### Test Coverage

- **Unit tests**: Mock `bd` command behavior
- **Integration tests**: Real command execution with test beads
- **Concurrency tests**: Race detector enabled, parallel claims
- **Timing tests**: Verify exponential backoff behavior

### Key Test Scenarios

1. **Successful claim on first attempt**
2. **Already-claimed detection** (no retries)
3. **Transient failure with retry** (exponential backoff)
4. **Retry exhaustion** (all attempts fail)
5. **Context cancellation** (during claim or backoff)
6. **Concurrent claims** (race condition prevention)
7. **Empty bead ID validation**

### Running Tests

```bash
# Run all tests with race detector
go test -v -race ./ralph/...

# Run with coverage
go test -race -coverprofile=coverage.out ./ralph/...
go tool cover -func=coverage.out

# Run specific test
go test -v -race -run TestConcurrentClaimAttempts ./ralph/...
```

## Usage Example

```go
import (
    "context"
    "github.com/randlee/beads-ralph/ralph"
    "log"
)

func processBeads(ctx context.Context, beads []Bead) {
    for _, bead := range beads {
        // Attempt to claim the bead
        err := claimBead(ctx, bead.ID)

        if errors.Is(err, ErrAlreadyClaimed) {
            log.Printf("Bead %s already claimed, skipping", bead.ID)
            continue
        }

        if err != nil {
            log.Printf("Failed to claim bead %s: %v", bead.ID, err)
            continue
        }

        // Successfully claimed - proceed with work
        log.Printf("Claimed bead %s, starting work", bead.ID)
        doWork(ctx, bead)
    }
}
```

## Future Enhancements

1. **Claim lease expiration**: Auto-release claims after timeout
2. **Priority claims**: Higher-priority agents get preference
3. **Claim transfer**: Transfer claim between agents
4. **Metrics**: Track claim success rate, retry counts, latency
5. **Distributed tracing**: OpenTelemetry integration

## References

- [Beads Schema Documentation](../../docs/schema.md)
- [Corner Cases & Failure Scenarios](../../docs/corner-cases.md)
- [Implementation Plan Sprint 4.2a](../../pm/2026-02-08-implementation-plan.md#sprint-42a-bead-claiming-logic-parallel)

package ralph

import (
	"context"
	"errors"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

// ErrAlreadyClaimed is returned when a bead is already claimed by another agent
var ErrAlreadyClaimed = errors.New("bead already claimed")

// ClaimConfig defines the retry behavior for claiming beads
type ClaimConfig struct {
	MaxRetries        int           // Maximum number of retry attempts
	InitialBackoff    time.Duration // Initial backoff duration
	MaxBackoff        time.Duration // Maximum backoff duration
	BackoffMultiplier float64       // Exponential backoff multiplier
}

// DefaultClaimConfig returns sensible defaults for claiming beads
func DefaultClaimConfig() ClaimConfig {
	return ClaimConfig{
		MaxRetries:        3,
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        5 * time.Second,
		BackoffMultiplier: 2.0,
	}
}

// claimBead attempts to claim a bead by calling `bd claim <bead-id>`
//
// This function implements atomic Compare-And-Swap (CAS) semantics via the `bd claim` command.
// The bd claim command ensures that only one agent can claim a specific bead at a time,
// preventing race conditions in distributed environments.
//
// Returns:
// - nil: Successfully claimed the bead
// - ErrAlreadyClaimed: Bead was already claimed by another agent
// - other error: Command execution failed (network, permissions, etc.)
func claimBead(ctx context.Context, beadID string) error {
	return claimBeadWithRetry(ctx, beadID, DefaultClaimConfig())
}

// claimBeadWithRetry attempts to claim a bead with exponential backoff retry logic
//
// Retry behavior:
// - Retries only transient failures (network errors, temporary unavailability)
// - Does NOT retry ErrAlreadyClaimed (permanent failure for this agent)
// - Uses exponential backoff with configurable parameters
//
// Returns:
// - nil: Successfully claimed the bead
// - ErrAlreadyClaimed: Bead was already claimed (not retried)
// - other error: Command failed after all retry attempts
func claimBeadWithRetry(ctx context.Context, beadID string, config ClaimConfig) error {
	if beadID == "" {
		return fmt.Errorf("beadID cannot be empty")
	}

	var lastErr error
	backoff := config.InitialBackoff

	for attempt := 0; attempt <= config.MaxRetries; attempt++ {
		// Check context cancellation before each attempt
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("context cancelled during claim: %w", err)
		}

		// Attempt to claim
		err := executeClaim(ctx, beadID)
		if err == nil {
			// Success!
			return nil
		}

		// Check if already claimed (permanent failure)
		if errors.Is(err, ErrAlreadyClaimed) {
			return ErrAlreadyClaimed
		}

		// Store the error for potential return
		lastErr = err

		// Check if we should retry
		if attempt < config.MaxRetries {
			// Apply exponential backoff
			select {
			case <-time.After(backoff):
				// Continue to next attempt
			case <-ctx.Done():
				return fmt.Errorf("context cancelled during backoff: %w", ctx.Err())
			}

			// Increase backoff for next iteration
			backoff = time.Duration(float64(backoff) * config.BackoffMultiplier)
			if backoff > config.MaxBackoff {
				backoff = config.MaxBackoff
			}
		}
	}

	// All retries exhausted
	return fmt.Errorf("claim failed after %d attempts: %w", config.MaxRetries+1, lastErr)
}

// executeClaim performs a single claim attempt by executing `bd claim <bead-id>`
func executeClaim(ctx context.Context, beadID string) error {
	cmd := exec.CommandContext(ctx, "bd", "claim", beadID)
	output, err := cmd.CombinedOutput()

	if err != nil {
		// Parse stderr to detect already-claimed error
		outputStr := string(output)
		if strings.Contains(outputStr, "already claimed") ||
			strings.Contains(outputStr, "AlreadyClaimed") ||
			strings.Contains(outputStr, "already_claimed") {
			return ErrAlreadyClaimed
		}

		// Check for exit code
		if exitErr, ok := err.(*exec.ExitError); ok {
			// Exit code 2 conventionally means "already exists/claimed"
			if exitErr.ExitCode() == 2 {
				return ErrAlreadyClaimed
			}
			return fmt.Errorf("bd claim failed (exit %d): %s", exitErr.ExitCode(), outputStr)
		}

		return fmt.Errorf("bd claim command failed: %w (output: %s)", err, outputStr)
	}

	return nil
}

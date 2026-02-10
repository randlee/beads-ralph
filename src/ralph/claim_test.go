package ralph

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

// TestExecuteClaimSuccess tests successful bead claiming
func TestExecuteClaimSuccess(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	// Create a mock bd command that succeeds
	mockBd := createMockBdCommand(t, "claim", 0, "")

	// Override PATH to use mock
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx := context.Background()
	err := executeClaim(ctx, "test-bead-1")

	if err != nil {
		t.Errorf("Expected successful claim, got error: %v", err)
	}
}

// TestExecuteClaimAlreadyClaimed tests already-claimed detection
func TestExecuteClaimAlreadyClaimed(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	tests := []struct {
		name       string
		exitCode   int
		stderr     string
		wantErrMsg string
	}{
		{
			name:       "already claimed in output",
			exitCode:   1,
			stderr:     "Error: bead test-bead-1 already claimed by agent-123",
			wantErrMsg: "already claimed",
		},
		{
			name:       "AlreadyClaimed in output",
			exitCode:   1,
			stderr:     "Error: AlreadyClaimed: bead is not available",
			wantErrMsg: "already claimed",
		},
		{
			name:       "already_claimed in output",
			exitCode:   1,
			stderr:     "Error: status already_claimed",
			wantErrMsg: "already claimed",
		},
		{
			name:       "exit code 2 convention",
			exitCode:   2,
			stderr:     "resource exists",
			wantErrMsg: "already claimed",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockBd := createMockBdCommand(t, "claim", tt.exitCode, tt.stderr)

			origPath := os.Getenv("PATH")
			defer os.Setenv("PATH", origPath)
			pathSep := getPathSeparator()
			os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

			ctx := context.Background()
			err := executeClaim(ctx, "test-bead-1")

			if !errors.Is(err, ErrAlreadyClaimed) {
				t.Errorf("Expected ErrAlreadyClaimed, got: %v", err)
			}
		})
	}
}

// TestExecuteClaimOtherErrors tests other error conditions
func TestExecuteClaimOtherErrors(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	tests := []struct {
		name     string
		exitCode int
		stderr   string
		wantErr  bool
	}{
		{
			name:     "network error",
			exitCode: 1,
			stderr:   "network connection failed",
			wantErr:  true,
		},
		{
			name:     "permission denied",
			exitCode: 1,
			stderr:   "permission denied",
			wantErr:  true,
		},
		{
			name:     "invalid bead id",
			exitCode: 1,
			stderr:   "bead not found",
			wantErr:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockBd := createMockBdCommand(t, "claim", tt.exitCode, tt.stderr)

			origPath := os.Getenv("PATH")
			defer os.Setenv("PATH", origPath)
			pathSep := getPathSeparator()
			os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

			ctx := context.Background()
			err := executeClaim(ctx, "test-bead-1")

			if (err != nil) != tt.wantErr {
				t.Errorf("Expected error=%v, got: %v", tt.wantErr, err)
			}
			if err != nil && errors.Is(err, ErrAlreadyClaimed) {
				t.Errorf("Should not return ErrAlreadyClaimed for non-claim errors, got: %v", err)
			}
		})
	}
}

// TestClaimBeadWithRetrySuccess tests successful claim on first attempt
func TestClaimBeadWithRetrySuccess(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	mockBd := createMockBdCommand(t, "claim", 0, "")
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx := context.Background()
	config := ClaimConfig{
		MaxRetries:        3,
		InitialBackoff:    10 * time.Millisecond,
		MaxBackoff:        100 * time.Millisecond,
		BackoffMultiplier: 2.0,
	}

	start := time.Now()
	err := claimBeadWithRetry(ctx, "test-bead-1", config)
	duration := time.Since(start)

	if err != nil {
		t.Errorf("Expected success, got error: %v", err)
	}

	// Should complete quickly (no retries) - be generous with timing in CI
	if duration > 200*time.Millisecond {
		t.Errorf("Expected fast completion, took %v", duration)
	}
}

// TestClaimBeadWithRetryAlreadyClaimed tests that already-claimed is not retried
func TestClaimBeadWithRetryAlreadyClaimed(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	mockBd := createMockBdCommand(t, "claim", 2, "already claimed")
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx := context.Background()
	config := ClaimConfig{
		MaxRetries:        3,
		InitialBackoff:    10 * time.Millisecond,
		MaxBackoff:        100 * time.Millisecond,
		BackoffMultiplier: 2.0,
	}

	start := time.Now()
	err := claimBeadWithRetry(ctx, "test-bead-1", config)
	duration := time.Since(start)

	if !errors.Is(err, ErrAlreadyClaimed) {
		t.Errorf("Expected ErrAlreadyClaimed, got: %v", err)
	}

	// Should fail immediately without retries - be generous with timing in CI
	if duration > 200*time.Millisecond {
		t.Errorf("Expected immediate failure, took %v (retried when shouldn't)", duration)
	}
}

// TestClaimBeadWithRetryExponentialBackoff tests retry logic with exponential backoff
func TestClaimBeadWithRetryExponentialBackoff(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	// Create a mock that fails twice then succeeds
	attemptCount := 0
	var mu sync.Mutex

	countFile := filepath.Join(t.TempDir(), "attempt_count")
	var mockBdScript string

	if runtime.GOOS == "windows" {
		// Use a simpler approach for Windows - write/read count to file
		mockBdScript = fmt.Sprintf(`@echo off
setlocal enabledelayedexpansion
set count_file=%s
set count=0
if exist "%%count_file%%" (
    set /p count=<"%%count_file%%"
)
set /a count=!count! + 1
echo !count!>"%%count_file%%"

if !count! LEQ 2 (
    echo network error 1>&2
    exit /b 1
)
exit /b 0
`, countFile)
	} else {
		mockBdScript = fmt.Sprintf(`#!/bin/bash
count_file="%s"
count=0
if [ -f "$count_file" ]; then
    count=$(cat "$count_file")
fi
count=$((count + 1))
echo "$count" > "$count_file"

if [ "$count" -le 2 ]; then
    echo "network error" >&2
    exit 1
fi
exit 0
`, countFile)
	}

	mockBd := createMockBdCommandFromScript(t, mockBdScript)
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx := context.Background()
	config := ClaimConfig{
		MaxRetries:        3,
		InitialBackoff:    50 * time.Millisecond,
		MaxBackoff:        500 * time.Millisecond,
		BackoffMultiplier: 2.0,
	}

	start := time.Now()
	err := claimBeadWithRetry(ctx, "test-bead-1", config)
	duration := time.Since(start)

	mu.Lock()
	_ = attemptCount
	mu.Unlock()

	if err != nil {
		t.Errorf("Expected eventual success, got error: %v", err)
	}

	// Should take at least: 50ms + 100ms = 150ms (two backoffs)
	expectedMin := 100 * time.Millisecond
	if duration < expectedMin {
		t.Errorf("Expected at least %v with backoff, took only %v", expectedMin, duration)
	}

	// But should complete within reasonable time
	expectedMax := 1 * time.Second
	if duration > expectedMax {
		t.Errorf("Expected completion within %v, took %v", expectedMax, duration)
	}
}

// TestClaimBeadWithRetryExhaustion tests that retries eventually give up
func TestClaimBeadWithRetryExhaustion(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	// Mock that always fails with transient error
	mockBd := createMockBdCommand(t, "claim", 1, "network timeout")
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx := context.Background()
	config := ClaimConfig{
		MaxRetries:        2,
		InitialBackoff:    10 * time.Millisecond,
		MaxBackoff:        50 * time.Millisecond,
		BackoffMultiplier: 2.0,
	}

	err := claimBeadWithRetry(ctx, "test-bead-1", config)

	if err == nil {
		t.Error("Expected error after retry exhaustion, got nil")
	}

	if !strings.Contains(err.Error(), "claim failed after") {
		t.Errorf("Expected retry exhaustion message, got: %v", err)
	}
}

// TestClaimBeadContextCancellation tests context cancellation handling
func TestClaimBeadContextCancellation(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	// Mock that takes a long time (never actually completes)
	var mockBdScript string
	if runtime.GOOS == "windows" {
		// Use ping as a sleep alternative that respects termination better
		mockBdScript = `@echo off
ping -n 11 127.0.0.1 >nul
exit /b 0
`
	} else {
		mockBdScript = `#!/bin/bash
sleep 10
exit 0
`
	}
	mockBd := createMockBdCommandFromScript(t, mockBdScript)
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	config := ClaimConfig{
		MaxRetries:        3,
		InitialBackoff:    10 * time.Millisecond,
		MaxBackoff:        100 * time.Millisecond,
		BackoffMultiplier: 2.0,
	}

	err := claimBeadWithRetry(ctx, "test-bead-1", config)

	if err == nil {
		t.Error("Expected context cancellation error, got nil")
	}

	if !strings.Contains(err.Error(), "context") {
		t.Errorf("Expected context-related error, got: %v", err)
	}
}

// TestClaimBeadEmptyID tests validation of empty bead ID
func TestClaimBeadEmptyID(t *testing.T) {
	ctx := context.Background()
	config := DefaultClaimConfig()

	err := claimBeadWithRetry(ctx, "", config)

	if err == nil {
		t.Error("Expected error for empty bead ID, got nil")
	}

	if !strings.Contains(err.Error(), "empty") {
		t.Errorf("Expected 'empty' in error message, got: %v", err)
	}
}

// TestConcurrentClaimAttempts tests race conditions with concurrent claims
// This test verifies that the atomic CAS behavior prevents race conditions
func TestConcurrentClaimAttempts(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	// Create a mock that only succeeds once using an atomic lock file
	lockFile := filepath.Join(t.TempDir(), "claim_lock")
	var mockBdScript string

	if runtime.GOOS == "windows" {
		mockBdScript = fmt.Sprintf(`@echo off
set lockfile=%s
if not exist "%%lockfile%%" (
    mkdir "%%lockfile%%" 2>nul
    if errorlevel 1 (
        echo already claimed 1>&2
        exit /b 2
    )
    timeout /t 1 /nobreak >nul 2>nul
    exit /b 0
) else (
    echo already claimed 1>&2
    exit /b 2
)
`, lockFile)
	} else {
		mockBdScript = fmt.Sprintf(`#!/bin/bash
lockfile="%s"
# Use mkdir for atomic operation (not touch which has race conditions)
if ! mkdir "$lockfile" 2>/dev/null; then
    echo "already claimed" >&2
    exit 2
fi
sleep 0.01  # Small delay to ensure race detection
exit 0
`, lockFile)
	}

	mockBd := createMockBdCommandFromScript(t, mockBdScript)
	origPath := os.Getenv("PATH")
	defer os.Setenv("PATH", origPath)
	pathSep := getPathSeparator()
	os.Setenv("PATH", filepath.Dir(mockBd)+pathSep+origPath)

	ctx := context.Background()
	config := DefaultClaimConfig()

	// Launch multiple concurrent claim attempts
	const numAgents = 10
	var wg sync.WaitGroup
	results := make(chan error, numAgents)

	for i := 0; i < numAgents; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			err := claimBeadWithRetry(ctx, "test-bead-concurrent", config)
			results <- err
		}()
	}

	wg.Wait()
	close(results)

	// Count successes and already-claimed errors
	successCount := 0
	alreadyClaimedCount := 0

	for err := range results {
		if err == nil {
			successCount++
		} else if errors.Is(err, ErrAlreadyClaimed) {
			alreadyClaimedCount++
		} else {
			t.Errorf("Unexpected error: %v", err)
		}
	}

	// Exactly one agent should succeed
	if successCount != 1 {
		t.Errorf("Expected exactly 1 success, got %d", successCount)
	}

	// All others should get already-claimed
	if alreadyClaimedCount != numAgents-1 {
		t.Errorf("Expected %d already-claimed errors, got %d", numAgents-1, alreadyClaimedCount)
	}
}

// TestDefaultClaimConfig tests the default configuration
func TestDefaultClaimConfig(t *testing.T) {
	config := DefaultClaimConfig()

	if config.MaxRetries < 1 {
		t.Errorf("Expected MaxRetries >= 1, got %d", config.MaxRetries)
	}
	if config.InitialBackoff <= 0 {
		t.Errorf("Expected InitialBackoff > 0, got %v", config.InitialBackoff)
	}
	if config.MaxBackoff <= config.InitialBackoff {
		t.Errorf("Expected MaxBackoff > InitialBackoff, got %v <= %v",
			config.MaxBackoff, config.InitialBackoff)
	}
	if config.BackoffMultiplier <= 1.0 {
		t.Errorf("Expected BackoffMultiplier > 1.0, got %v", config.BackoffMultiplier)
	}
}

// Helper function to get OS-specific PATH separator
func getPathSeparator() string {
	if runtime.GOOS == "windows" {
		return ";"
	}
	return ":"
}

// Helper function to create a mock bd command that exits with a specific code
func createMockBdCommand(t *testing.T, subcommand string, exitCode int, stderr string) string {
	var script string

	if runtime.GOOS == "windows" {
		// Windows batch script
		stderrLine := ""
		if stderr != "" {
			stderrLine = fmt.Sprintf("echo %s 1>&2\n", stderr)
		}
		script = fmt.Sprintf(`@echo off
if not "%%1"=="%s" (
    echo unexpected subcommand: %%1 1>&2
    exit /b 1
)
%sexit /b %d
`, subcommand, stderrLine, exitCode)
	} else {
		// Unix bash script
		stderrLine := ""
		if stderr != "" {
			stderrLine = fmt.Sprintf(`    echo "%s" >&2
`, stderr)
		}
		script = fmt.Sprintf(`#!/bin/bash
if [ "$1" != "%s" ]; then
    echo "unexpected subcommand: $1" >&2
    exit 1
fi
%sexit %d
`, subcommand, stderrLine, exitCode)
	}

	return createMockBdCommandFromScript(t, script)
}

// Helper function to create a mock bd command from a script
func createMockBdCommandFromScript(t *testing.T, script string) string {
	tmpDir := t.TempDir()

	// Use appropriate file extension based on OS
	mockName := "bd"
	if runtime.GOOS == "windows" {
		mockName = "bd.cmd"
	}
	mockPath := filepath.Join(tmpDir, mockName)

	err := os.WriteFile(mockPath, []byte(script), 0755)
	if err != nil {
		t.Fatalf("Failed to create mock bd command: %v", err)
	}

	return mockPath
}

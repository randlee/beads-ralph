package config

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/randlee/beads-ralph/ralph"
)

func TestLoadConfig_Success(t *testing.T) {
	// Create temp config file
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "test-config.yaml")

	configContent := `
repo_name: beads-ralph
max_parallel_sessions: 4
poll_interval: 30s
scrum_master_timeout: 15m
dev_agent_timeout: 30m
qa_agent_timeout: 10m
max_retry_attempts: 3
pr_creation_retries: 3
source_branch: develop
cleanup_on_complete: true
min_free_gb: 5
check_before_start: true
max_network_retries: 3
retry_backoff: exponential
network_timeout: 30s
agent_defaults:
  default_model: sonnet
  default_executable: claude
  default_options:
    - "--dangerously-skip-permissions"
    - "--output-format"
    - "json"
  role_models:
    polecat: opus
    witness: haiku
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	// Load config
	cfg, err := LoadConfig(configPath)
	if err != nil {
		t.Fatalf("LoadConfig failed: %v", err)
	}

	// Verify loaded values
	if cfg.RepoName != "beads-ralph" {
		t.Errorf("Expected repo_name 'beads-ralph', got '%s'", cfg.RepoName)
	}
	if cfg.MaxParallelSessions != 4 {
		t.Errorf("Expected max_parallel_sessions 4, got %d", cfg.MaxParallelSessions)
	}
	if cfg.PollInterval != 30*time.Second {
		t.Errorf("Expected poll_interval 30s, got %v", cfg.PollInterval)
	}
	if cfg.ScrumMasterTimeout != 15*time.Minute {
		t.Errorf("Expected scrum_master_timeout 15m, got %v", cfg.ScrumMasterTimeout)
	}
	if cfg.DevAgentTimeout != 30*time.Minute {
		t.Errorf("Expected dev_agent_timeout 30m, got %v", cfg.DevAgentTimeout)
	}
	if cfg.QAAgentTimeout != 10*time.Minute {
		t.Errorf("Expected qa_agent_timeout 10m, got %v", cfg.QAAgentTimeout)
	}
	if cfg.MaxRetryAttempts != 3 {
		t.Errorf("Expected max_retry_attempts 3, got %d", cfg.MaxRetryAttempts)
	}
	if cfg.PRCreationRetries != 3 {
		t.Errorf("Expected pr_creation_retries 3, got %d", cfg.PRCreationRetries)
	}
	if cfg.SourceBranch != "develop" {
		t.Errorf("Expected source_branch 'develop', got '%s'", cfg.SourceBranch)
	}
	if !cfg.CleanupOnComplete {
		t.Errorf("Expected cleanup_on_complete true, got false")
	}
	if cfg.MinFreeGB != 5 {
		t.Errorf("Expected min_free_gb 5, got %d", cfg.MinFreeGB)
	}
	if !cfg.CheckBeforeStart {
		t.Errorf("Expected check_before_start true, got false")
	}
	if cfg.MaxNetworkRetries != 3 {
		t.Errorf("Expected max_network_retries 3, got %d", cfg.MaxNetworkRetries)
	}
	if cfg.RetryBackoff != "exponential" {
		t.Errorf("Expected retry_backoff 'exponential', got '%s'", cfg.RetryBackoff)
	}
	if cfg.NetworkTimeout != 30*time.Second {
		t.Errorf("Expected network_timeout 30s, got %v", cfg.NetworkTimeout)
	}

	// Verify agent defaults
	if cfg.AgentDefaults.DefaultModel != "sonnet" {
		t.Errorf("Expected default_model 'sonnet', got '%s'", cfg.AgentDefaults.DefaultModel)
	}
	if cfg.AgentDefaults.DefaultExecutable != "claude" {
		t.Errorf("Expected default_executable 'claude', got '%s'", cfg.AgentDefaults.DefaultExecutable)
	}
	if len(cfg.AgentDefaults.DefaultOptions) != 3 {
		t.Errorf("Expected 3 default options, got %d", len(cfg.AgentDefaults.DefaultOptions))
	}
	if cfg.AgentDefaults.RoleModels["polecat"] != "opus" {
		t.Errorf("Expected role_models[polecat] 'opus', got '%s'", cfg.AgentDefaults.RoleModels["polecat"])
	}
	if cfg.AgentDefaults.RoleModels["witness"] != "haiku" {
		t.Errorf("Expected role_models[witness] 'haiku', got '%s'", cfg.AgentDefaults.RoleModels["witness"])
	}
}

func TestLoadConfig_WithDefaults(t *testing.T) {
	// Create minimal config with only required fields
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "minimal-config.yaml")

	configContent := `
repo_name: test-repo
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	cfg, err := LoadConfig(configPath)
	if err != nil {
		t.Fatalf("LoadConfig failed: %v", err)
	}

	// Verify defaults were applied
	if cfg.MaxParallelSessions != 4 {
		t.Errorf("Expected default max_parallel_sessions 4, got %d", cfg.MaxParallelSessions)
	}
	if cfg.PollInterval != 30*time.Second {
		t.Errorf("Expected default poll_interval 30s, got %v", cfg.PollInterval)
	}
	if cfg.SourceBranch != "develop" {
		t.Errorf("Expected default source_branch 'develop', got '%s'", cfg.SourceBranch)
	}
	if cfg.AgentDefaults.DefaultModel != "sonnet" {
		t.Errorf("Expected default model 'sonnet', got '%s'", cfg.AgentDefaults.DefaultModel)
	}
	if cfg.AgentDefaults.DefaultExecutable != "claude" {
		t.Errorf("Expected default executable 'claude', got '%s'", cfg.AgentDefaults.DefaultExecutable)
	}
	if cfg.RetryBackoff != "exponential" {
		t.Errorf("Expected default retry_backoff 'exponential', got '%s'", cfg.RetryBackoff)
	}
}

func TestLoadConfig_MissingRepoName(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "invalid-config.yaml")

	// Config without required repo_name
	configContent := `
max_parallel_sessions: 4
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	_, err := LoadConfig(configPath)
	if err == nil {
		t.Fatal("Expected error for missing repo_name, got nil")
	}
	if err.Error() != "invalid configuration: repo_name is required" {
		t.Errorf("Unexpected error message: %v", err)
	}
}

func TestLoadConfig_InvalidMaxParallelSessions(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "invalid-config.yaml")

	configContent := `
repo_name: test-repo
max_parallel_sessions: -1
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	_, err := LoadConfig(configPath)
	if err == nil {
		t.Fatal("Expected error for negative max_parallel_sessions, got nil")
	}
}

func TestLoadConfig_InvalidRetryBackoff(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "invalid-config.yaml")

	configContent := `
repo_name: test-repo
retry_backoff: invalid
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	_, err := LoadConfig(configPath)
	if err == nil {
		t.Fatal("Expected error for invalid retry_backoff, got nil")
	}
}

func TestLoadConfig_FileNotFound(t *testing.T) {
	_, err := LoadConfig("/nonexistent/config.yaml")
	if err == nil {
		t.Fatal("Expected error for missing file, got nil")
	}
}

func TestLoadConfig_InvalidYAML(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "invalid-yaml.yaml")

	// Malformed YAML
	configContent := `
repo_name: test-repo
max_parallel_sessions: [unclosed
`
	if err := os.WriteFile(configPath, []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	_, err := LoadConfig(configPath)
	if err == nil {
		t.Fatal("Expected error for invalid YAML, got nil")
	}
}

func TestValidateConfig_NegativeRetries(t *testing.T) {
	cfg := &ralph.Config{
		RepoName:            "test-repo",
		MaxParallelSessions: 1,
		PollInterval:        1 * time.Second,
		ScrumMasterTimeout:  1 * time.Minute,
		DevAgentTimeout:     1 * time.Minute,
		QAAgentTimeout:      1 * time.Minute,
		MaxRetryAttempts:    -1, // Invalid
		NetworkTimeout:      1 * time.Second,
	}
	cfg.AgentDefaults.DefaultModel = "sonnet"
	cfg.AgentDefaults.DefaultExecutable = "claude"

	err := validateConfig(cfg)
	if err == nil {
		t.Fatal("Expected error for negative max_retry_attempts, got nil")
	}
}

func TestValidateConfig_NegativeDiskSpace(t *testing.T) {
	cfg := &ralph.Config{
		RepoName:            "test-repo",
		MaxParallelSessions: 1,
		PollInterval:        1 * time.Second,
		ScrumMasterTimeout:  1 * time.Minute,
		DevAgentTimeout:     1 * time.Minute,
		QAAgentTimeout:      1 * time.Minute,
		MinFreeGB:           -1, // Invalid
		NetworkTimeout:      1 * time.Second,
	}
	cfg.AgentDefaults.DefaultModel = "sonnet"
	cfg.AgentDefaults.DefaultExecutable = "claude"

	err := validateConfig(cfg)
	if err == nil {
		t.Fatal("Expected error for negative min_free_gb, got nil")
	}
}

func TestValidateConfig_ZeroTimeout(t *testing.T) {
	cfg := &ralph.Config{
		RepoName:            "test-repo",
		MaxParallelSessions: 1,
		PollInterval:        1 * time.Second,
		ScrumMasterTimeout:  0, // Invalid
		DevAgentTimeout:     1 * time.Minute,
		QAAgentTimeout:      1 * time.Minute,
		NetworkTimeout:      1 * time.Second,
	}
	cfg.AgentDefaults.DefaultModel = "sonnet"
	cfg.AgentDefaults.DefaultExecutable = "claude"

	err := validateConfig(cfg)
	if err == nil {
		t.Fatal("Expected error for zero scrum_master_timeout, got nil")
	}
}

func TestLoadConfig_DefaultPath(t *testing.T) {
	// Save current directory
	oldWd, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get working directory: %v", err)
	}
	defer os.Chdir(oldWd)

	// Create temp directory with default config file
	tmpDir := t.TempDir()
	if err := os.Chdir(tmpDir); err != nil {
		t.Fatalf("Failed to change directory: %v", err)
	}

	configContent := `
repo_name: test-repo
`
	if err := os.WriteFile("beads-ralph.yaml", []byte(configContent), 0644); err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}

	// Load with empty path (should use default)
	cfg, err := LoadConfig("")
	if err != nil {
		t.Fatalf("LoadConfig with default path failed: %v", err)
	}

	if cfg.RepoName != "test-repo" {
		t.Errorf("Expected repo_name 'test-repo', got '%s'", cfg.RepoName)
	}
}

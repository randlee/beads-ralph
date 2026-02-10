package config

import (
	"fmt"
	"os"
	"time"

	"github.com/randlee/beads-ralph/ralph"
	"gopkg.in/yaml.v3"
)

// LoadConfig loads and validates configuration from YAML file
func LoadConfig(path string) (*ralph.Config, error) {
	// Default to beads-ralph.yaml if no path provided
	if path == "" {
		path = "beads-ralph.yaml"
	}

	// Read file
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file %s: %w", path, err)
	}

	// Parse YAML
	var cfg ralph.Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse YAML: %w", err)
	}

	// Apply defaults
	applyDefaults(&cfg)

	// Validate
	if err := validateConfig(&cfg); err != nil {
		return nil, fmt.Errorf("invalid configuration: %w", err)
	}

	return &cfg, nil
}

// applyDefaults sets default values for optional fields
func applyDefaults(cfg *ralph.Config) {
	// Ralph loop defaults
	if cfg.MaxParallelSessions == 0 {
		cfg.MaxParallelSessions = 4
	}
	if cfg.PollInterval == 0 {
		cfg.PollInterval = 30 * time.Second
	}

	// Timeout defaults
	if cfg.ScrumMasterTimeout == 0 {
		cfg.ScrumMasterTimeout = 15 * time.Minute
	}
	if cfg.DevAgentTimeout == 0 {
		cfg.DevAgentTimeout = 30 * time.Minute
	}
	if cfg.QAAgentTimeout == 0 {
		cfg.QAAgentTimeout = 10 * time.Minute
	}

	// Retry defaults
	if cfg.MaxRetryAttempts == 0 {
		cfg.MaxRetryAttempts = 3
	}
	if cfg.PRCreationRetries == 0 {
		cfg.PRCreationRetries = 3
	}

	// Worktree defaults
	if cfg.SourceBranch == "" {
		cfg.SourceBranch = "develop"
	}
	// cleanup_on_complete defaults to false

	// Disk space defaults
	if cfg.MinFreeGB == 0 {
		cfg.MinFreeGB = 5
	}
	// check_before_start defaults to false

	// Network defaults
	if cfg.MaxNetworkRetries == 0 {
		cfg.MaxNetworkRetries = 3
	}
	if cfg.RetryBackoff == "" {
		cfg.RetryBackoff = "exponential"
	}
	if cfg.NetworkTimeout == 0 {
		cfg.NetworkTimeout = 30 * time.Second
	}

	// Agent defaults
	if cfg.AgentDefaults.DefaultModel == "" {
		cfg.AgentDefaults.DefaultModel = "sonnet"
	}
	if cfg.AgentDefaults.DefaultExecutable == "" {
		cfg.AgentDefaults.DefaultExecutable = "claude"
	}
	if len(cfg.AgentDefaults.DefaultOptions) == 0 {
		cfg.AgentDefaults.DefaultOptions = []string{
			"--dangerously-skip-permissions",
			"--output-format", "json",
		}
	}
}

// validateConfig validates all required fields and constraints
func validateConfig(cfg *ralph.Config) error {
	// Validate required fields
	if cfg.RepoName == "" {
		return fmt.Errorf("repo_name is required")
	}

	// Validate positive values
	if cfg.MaxParallelSessions <= 0 {
		return fmt.Errorf("max_parallel_sessions must be positive, got %d", cfg.MaxParallelSessions)
	}
	if cfg.PollInterval <= 0 {
		return fmt.Errorf("poll_interval must be positive, got %v", cfg.PollInterval)
	}
	if cfg.ScrumMasterTimeout <= 0 {
		return fmt.Errorf("scrum_master_timeout must be positive, got %v", cfg.ScrumMasterTimeout)
	}
	if cfg.DevAgentTimeout <= 0 {
		return fmt.Errorf("dev_agent_timeout must be positive, got %v", cfg.DevAgentTimeout)
	}
	if cfg.QAAgentTimeout <= 0 {
		return fmt.Errorf("qa_agent_timeout must be positive, got %v", cfg.QAAgentTimeout)
	}

	// Validate retry settings
	if cfg.MaxRetryAttempts < 0 {
		return fmt.Errorf("max_retry_attempts cannot be negative, got %d", cfg.MaxRetryAttempts)
	}
	if cfg.PRCreationRetries < 0 {
		return fmt.Errorf("pr_creation_retries cannot be negative, got %d", cfg.PRCreationRetries)
	}

	// Validate disk space settings
	if cfg.MinFreeGB < 0 {
		return fmt.Errorf("min_free_gb cannot be negative, got %d", cfg.MinFreeGB)
	}

	// Validate network settings
	if cfg.MaxNetworkRetries < 0 {
		return fmt.Errorf("max_network_retries cannot be negative, got %d", cfg.MaxNetworkRetries)
	}
	if cfg.RetryBackoff != "exponential" && cfg.RetryBackoff != "linear" && cfg.RetryBackoff != "constant" {
		return fmt.Errorf("retry_backoff must be 'exponential', 'linear', or 'constant', got %s", cfg.RetryBackoff)
	}
	if cfg.NetworkTimeout <= 0 {
		return fmt.Errorf("network_timeout must be positive, got %v", cfg.NetworkTimeout)
	}

	// Validate agent defaults
	if cfg.AgentDefaults.DefaultModel == "" {
		return fmt.Errorf("agent_defaults.default_model is required")
	}
	if cfg.AgentDefaults.DefaultExecutable == "" {
		return fmt.Errorf("agent_defaults.default_executable is required")
	}

	return nil
}

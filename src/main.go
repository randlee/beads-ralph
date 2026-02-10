package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/randlee/beads-ralph/ralph"
	"gopkg.in/yaml.v3"
)

func main() {
	// Load configuration
	config, err := loadConfig("beads-ralph.yaml")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Create root context with signal handling
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Setup signal handlers for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("Received signal %v, initiating graceful shutdown...", sig)
		cancel()
	}()

	// Run the ralph loop
	log.Println("Starting beads-ralph orchestrator...")
	if err := ralph.RalphLoop(ctx, config); err != nil {
		if err == context.Canceled {
			log.Println("Shutdown complete.")
			os.Exit(0)
		}
		log.Fatalf("Ralph loop failed: %v", err)
	}

	log.Println("All work completed successfully.")
}

// loadConfig loads configuration from beads-ralph.yaml
func loadConfig(path string) (ralph.Config, error) {
	var config ralph.Config

	data, err := os.ReadFile(path)
	if err != nil {
		return config, fmt.Errorf("read config file: %w", err)
	}

	// Parse YAML with nested structure
	var rawConfig struct {
		Ralph struct {
			MaxParallelSessions int    `yaml:"max_parallel_sessions"`
			PollInterval        string `yaml:"poll_interval"`
		} `yaml:"ralph"`
		Timeouts struct {
			ScrumMaster string `yaml:"scrum_master"`
			DevAgent    string `yaml:"dev_agent"`
			QAAgent     string `yaml:"qa_agent"`
		} `yaml:"timeouts"`
		Retry struct {
			MaxAttempts       int `yaml:"max_attempts"`
			PRCreationRetries int `yaml:"pr_creation_retries"`
		} `yaml:"retry"`
		Worktrees struct {
			RepoName          string `yaml:"repo_name"`
			SourceBranch      string `yaml:"source_branch"`
			CleanupOnComplete bool   `yaml:"cleanup_on_complete"`
		} `yaml:"worktrees"`
		Disk struct {
			MinFreeGB        int  `yaml:"min_free_gb"`
			CheckBeforeStart bool `yaml:"check_before_start"`
		} `yaml:"disk"`
		Network struct {
			MaxRetries   int    `yaml:"max_retries"`
			RetryBackoff string `yaml:"retry_backoff"`
			Timeout      string `yaml:"timeout"`
		} `yaml:"network"`
	}

	if err := yaml.Unmarshal(data, &rawConfig); err != nil {
		return config, fmt.Errorf("parse yaml: %w", err)
	}

	// Convert to Config struct with parsed durations
	pollInterval, err := time.ParseDuration(rawConfig.Ralph.PollInterval)
	if err != nil {
		return config, fmt.Errorf("parse poll_interval: %w", err)
	}

	scrumMasterTimeout, err := time.ParseDuration(rawConfig.Timeouts.ScrumMaster)
	if err != nil {
		return config, fmt.Errorf("parse scrum_master timeout: %w", err)
	}

	devAgentTimeout, err := time.ParseDuration(rawConfig.Timeouts.DevAgent)
	if err != nil {
		return config, fmt.Errorf("parse dev_agent timeout: %w", err)
	}

	qaAgentTimeout, err := time.ParseDuration(rawConfig.Timeouts.QAAgent)
	if err != nil {
		return config, fmt.Errorf("parse qa_agent timeout: %w", err)
	}

	networkTimeout, err := time.ParseDuration(rawConfig.Network.Timeout)
	if err != nil {
		return config, fmt.Errorf("parse network timeout: %w", err)
	}

	config.MaxParallelSessions = rawConfig.Ralph.MaxParallelSessions
	config.PollInterval = pollInterval
	config.ScrumMasterTimeout = scrumMasterTimeout
	config.DevAgentTimeout = devAgentTimeout
	config.QAAgentTimeout = qaAgentTimeout
	config.MaxRetryAttempts = rawConfig.Retry.MaxAttempts
	config.PRCreationRetries = rawConfig.Retry.PRCreationRetries
	config.RepoName = rawConfig.Worktrees.RepoName
	config.SourceBranch = rawConfig.Worktrees.SourceBranch
	config.CleanupOnComplete = rawConfig.Worktrees.CleanupOnComplete
	config.MinFreeGB = rawConfig.Disk.MinFreeGB
	config.CheckBeforeStart = rawConfig.Disk.CheckBeforeStart
	config.MaxNetworkRetries = rawConfig.Network.MaxRetries
	config.RetryBackoff = rawConfig.Network.RetryBackoff
	config.NetworkTimeout = networkTimeout

	return config, nil
}

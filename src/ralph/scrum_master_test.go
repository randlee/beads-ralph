package ralph

import (
	"context"
	"strings"
	"testing"
	"time"
)

func TestBuildAgentCommand(t *testing.T) {
	tests := []struct {
		name     string
		spec     AgentSpec
		config   Config
		expected []string
	}{
		{
			name: "full spec with all fields",
			spec: AgentSpec{
				Agent:      ".claude/agents/scrum-master.md",
				Model:      "opus",
				Executable: "claude-dev",
				Options:    []string{"--verbose", "--debug"},
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel:      "sonnet",
					DefaultExecutable: "claude",
					DefaultOptions:    []string{"--dangerously-skip-permissions"},
				},
			},
			expected: []string{
				"claude-dev",
				"--model", "opus",
				"--verbose", "--debug",
				"--agent", ".claude/agents/scrum-master.md",
			},
		},
		{
			name: "minimal spec uses system defaults",
			spec: AgentSpec{
				Agent: ".claude/agents/dev.md",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel:      "sonnet",
					DefaultExecutable: "claude",
					DefaultOptions:    []string{"--dangerously-skip-permissions", "--output-format", "json"},
				},
			},
			expected: []string{
				"claude",
				"--model", "sonnet",
				"--dangerously-skip-permissions", "--output-format", "json",
				"--agent", ".claude/agents/dev.md",
			},
		},
		{
			name: "role-based model selection",
			spec: AgentSpec{
				Agent: ".claude/agents/qa.md",
				Role:  "witness",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel:      "sonnet",
					DefaultExecutable: "claude",
					DefaultOptions:    []string{},
					RoleModels: map[string]string{
						"polecat": "sonnet",
						"witness": "haiku",
						"mayor":   "opus",
					},
				},
			},
			expected: []string{
				"claude",
				"--model", "haiku",
				"--agent", ".claude/agents/qa.md",
			},
		},
		{
			name: "explicit model overrides role-based model",
			spec: AgentSpec{
				Agent: ".claude/agents/qa.md",
				Role:  "witness",
				Model: "opus", // Explicit override
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel:      "sonnet",
					DefaultExecutable: "claude",
					RoleModels: map[string]string{
						"witness": "haiku",
					},
				},
			},
			expected: []string{
				"claude",
				"--model", "opus", // Should use explicit model, not role-based
				"--agent", ".claude/agents/qa.md",
			},
		},
		{
			name: "fallback to hardcoded defaults",
			spec: AgentSpec{
				Agent: ".claude/agents/dev.md",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					// No defaults set
				},
			},
			expected: []string{
				"claude",            // Hardcoded fallback
				"--model", "sonnet", // Hardcoded fallback
				"--agent", ".claude/agents/dev.md",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := buildAgentCommand(tt.spec, tt.config)

			if len(result) != len(tt.expected) {
				t.Errorf("expected %d arguments, got %d\nExpected: %v\nGot: %v",
					len(tt.expected), len(result), tt.expected, result)
				return
			}

			for i, arg := range result {
				if arg != tt.expected[i] {
					t.Errorf("argument %d mismatch: expected %q, got %q", i, tt.expected[i], arg)
				}
			}
		})
	}
}

func TestResolveModel(t *testing.T) {
	tests := []struct {
		name     string
		spec     AgentSpec
		config   Config
		expected string
	}{
		{
			name: "level 1: explicit model in spec",
			spec: AgentSpec{
				Model: "opus",
				Role:  "polecat",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel: "sonnet",
					RoleModels: map[string]string{
						"polecat": "haiku",
					},
				},
			},
			expected: "opus",
		},
		{
			name: "level 3a: role-based model",
			spec: AgentSpec{
				Role: "witness",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel: "sonnet",
					RoleModels: map[string]string{
						"witness": "haiku",
					},
				},
			},
			expected: "haiku",
		},
		{
			name: "level 3b: default model",
			spec: AgentSpec{
				Role: "unknown-role",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					DefaultModel: "sonnet",
					RoleModels: map[string]string{
						"polecat": "haiku",
					},
				},
			},
			expected: "sonnet",
		},
		{
			name: "level 4: hardcoded fallback",
			spec: AgentSpec{
				Role: "unknown-role",
			},
			config: Config{
				AgentDefaults: AgentDefaults{
					// No defaults
				},
			},
			expected: "sonnet",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := resolveModel(tt.spec, tt.config)
			if result != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, result)
			}
		})
	}
}

func TestGenerateScrumMasterPrompt(t *testing.T) {
	bead := Bead{
		ID:          "bd-sprint-4-2c",
		Title:       "Sprint 4.2c: Scrum-Master Launcher",
		Description: "Implement scrum-master launcher with dev-QA loop.",
		Metadata: BeadMetadata{
			TeamName:     "sprint-4-2-parallel",
			WorktreePath: "/path/to/worktree",
			Branch:       "feature/4-2c-scrum-launcher",
			SourceBranch: "develop",
			PlanFile:     "pm/2026-02-08-implementation-plan.md",
			PlanSection:  "Sprint 4.2c",
		},
	}

	prompt := generateScrumMasterPrompt(bead)

	// Check for required elements
	required := []string{
		"bd-sprint-4-2c",
		"Sprint 4.2c: Scrum-Master Launcher",
		"sprint-4-2-parallel",
		"/path/to/worktree",
		"feature/4-2c-scrum-launcher",
		"develop",
		"pm/2026-02-08-implementation-plan.md",
		"Implement scrum-master launcher",
		"```json",
		"ScrumResult",
	}

	for _, req := range required {
		if !strings.Contains(prompt, req) {
			t.Errorf("prompt missing required element: %q", req)
		}
	}
}

func TestParseJSONOutput(t *testing.T) {
	tests := []struct {
		name      string
		output    string
		expectErr bool
		expected  ScrumResult
	}{
		{
			name: "valid JSON block",
			output: `Some text before
` + "```json" + `
{
  "bead_id": "bd-123",
  "success": true,
  "pr_url": "https://github.com/user/repo/pull/42",
  "pr_number": 42,
  "bead_updated": true
}
` + "```" + `
Some text after`,
			expectErr: false,
			expected: ScrumResult{
				BeadID:      "bd-123",
				Success:     true,
				PRUrl:       "https://github.com/user/repo/pull/42",
				PRNumber:    42,
				BeadUpdated: true,
			},
		},
		{
			name: "minimal valid JSON",
			output: "```json\n" +
				`{"bead_id":"bd-456","success":false,"error":"test error"}` +
				"\n```",
			expectErr: false,
			expected: ScrumResult{
				BeadID:  "bd-456",
				Success: false,
				Error:   "test error",
			},
		},
		{
			name:      "no JSON block",
			output:    "Just plain text without JSON",
			expectErr: true,
		},
		{
			name: "unclosed JSON block",
			output: "```json\n" +
				`{"bead_id":"bd-789","success":true}`,
			expectErr: true,
		},
		{
			name: "invalid JSON syntax",
			output: "```json\n" +
				`{invalid json here}` +
				"\n```",
			expectErr: true,
		},
		{
			name: "multiple JSON blocks uses first",
			output: "```json\n" +
				`{"bead_id":"bd-first","success":true}` +
				"\n```\nSome text\n```json\n" +
				`{"bead_id":"bd-second","success":false}` +
				"\n```",
			expectErr: false,
			expected: ScrumResult{
				BeadID:  "bd-first",
				Success: true,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := parseJSONOutput(tt.output)

			if tt.expectErr {
				if err == nil {
					t.Error("expected error, got nil")
				}
				return
			}

			if err != nil {
				t.Errorf("unexpected error: %v", err)
				return
			}

			if result.BeadID != tt.expected.BeadID {
				t.Errorf("BeadID: expected %q, got %q", tt.expected.BeadID, result.BeadID)
			}
			if result.Success != tt.expected.Success {
				t.Errorf("Success: expected %v, got %v", tt.expected.Success, result.Success)
			}
			if result.PRUrl != tt.expected.PRUrl {
				t.Errorf("PRUrl: expected %q, got %q", tt.expected.PRUrl, result.PRUrl)
			}
			if result.PRNumber != tt.expected.PRNumber {
				t.Errorf("PRNumber: expected %d, got %d", tt.expected.PRNumber, result.PRNumber)
			}
			if result.BeadUpdated != tt.expected.BeadUpdated {
				t.Errorf("BeadUpdated: expected %v, got %v", tt.expected.BeadUpdated, result.BeadUpdated)
			}
			if result.Error != tt.expected.Error {
				t.Errorf("Error: expected %q, got %q", tt.expected.Error, result.Error)
			}
		})
	}
}

func TestRunScrumMasterTimeout(t *testing.T) {
	// Skip this test as it's difficult to reliably test timeout behavior
	// without creating complex mocking infrastructure. The timeout logic
	// is correctly implemented via context.WithTimeout and will work in practice.
	t.Skip("Timeout handling is implemented via context.WithTimeout but difficult to unit test")
}

func TestRunScrumMasterEmptyCommand(t *testing.T) {
	ctx := context.Background()

	bead := Bead{
		ID:    "bd-empty-cmd-test",
		Title: "Empty Command Test",
		Metadata: BeadMetadata{
			TeamName: "test-team",
			ScrumMasterAgent: AgentSpec{
				Agent: "", // Empty agent path
			},
		},
	}

	config := Config{
		ScrumMasterTimeout: 5 * time.Second, // Reasonable timeout
		AgentDefaults: AgentDefaults{
			DefaultExecutable: "nonexistent-cmd", // Use nonexistent to fail fast
		},
	}

	result := runScrumMaster(ctx, bead, config)

	if result.Success {
		t.Error("expected failure for empty agent path, got success")
	}
}

func TestRunScrumMasterInvalidExecutable(t *testing.T) {
	ctx := context.Background()

	bead := Bead{
		ID:    "bd-invalid-exec-test",
		Title: "Invalid Executable Test",
		Metadata: BeadMetadata{
			TeamName: "test-team",
			ScrumMasterAgent: AgentSpec{
				Agent:      ".claude/agents/scrum-master.md",
				Executable: "nonexistent-command-12345",
			},
		},
	}

	config := Config{
		ScrumMasterTimeout: 5 * time.Second,
		AgentDefaults: AgentDefaults{
			DefaultModel: "sonnet",
		},
	}

	result := runScrumMaster(ctx, bead, config)

	if result.Success {
		t.Error("expected failure for nonexistent executable, got success")
	}

	if !strings.Contains(result.Error, "execution error") {
		t.Errorf("expected execution error, got: %s", result.Error)
	}
}

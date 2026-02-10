package ralph

import (
	"context"
	"testing"
	"time"
)

// Test groupByTeam function
func TestGroupByTeam(t *testing.T) {
	tests := []struct {
		name     string
		beads    []Bead
		expected map[string]int // team_name -> count
	}{
		{
			name:     "empty input",
			beads:    []Bead{},
			expected: map[string]int{},
		},
		{
			name: "single team",
			beads: []Bead{
				{ID: "bd-1", Metadata: BeadMetadata{TeamName: "team-alpha"}},
				{ID: "bd-2", Metadata: BeadMetadata{TeamName: "team-alpha"}},
				{ID: "bd-3", Metadata: BeadMetadata{TeamName: "team-alpha"}},
			},
			expected: map[string]int{
				"team-alpha": 3,
			},
		},
		{
			name: "multiple teams",
			beads: []Bead{
				{ID: "bd-1", Metadata: BeadMetadata{TeamName: "team-alpha"}},
				{ID: "bd-2", Metadata: BeadMetadata{TeamName: "team-beta"}},
				{ID: "bd-3", Metadata: BeadMetadata{TeamName: "team-alpha"}},
				{ID: "bd-4", Metadata: BeadMetadata{TeamName: "team-gamma"}},
			},
			expected: map[string]int{
				"team-alpha": 2,
				"team-beta":  1,
				"team-gamma": 1,
			},
		},
		{
			name: "empty team name uses default",
			beads: []Bead{
				{ID: "bd-1", Metadata: BeadMetadata{TeamName: ""}},
				{ID: "bd-2", Metadata: BeadMetadata{TeamName: ""}},
			},
			expected: map[string]int{
				"default-team": 2,
			},
		},
		{
			name: "mixed empty and named teams",
			beads: []Bead{
				{ID: "bd-1", Metadata: BeadMetadata{TeamName: "team-alpha"}},
				{ID: "bd-2", Metadata: BeadMetadata{TeamName: ""}},
				{ID: "bd-3", Metadata: BeadMetadata{TeamName: "team-alpha"}},
			},
			expected: map[string]int{
				"team-alpha":   2,
				"default-team": 1,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := groupByTeam(tt.beads)

			// Check number of teams
			if len(result) != len(tt.expected) {
				t.Errorf("Expected %d teams, got %d", len(tt.expected), len(result))
			}

			// Check each team's bead count
			for teamName, expectedCount := range tt.expected {
				beads, exists := result[teamName]
				if !exists {
					t.Errorf("Team %s not found in result", teamName)
					continue
				}
				if len(beads) != expectedCount {
					t.Errorf("Team %s: expected %d beads, got %d", teamName, expectedCount, len(beads))
				}
			}
		})
	}
}

// Test teamNames function
func TestTeamNames(t *testing.T) {
	tests := []struct {
		name     string
		groups   map[string][]Bead
		expected int // number of team names
	}{
		{
			name:     "empty groups",
			groups:   map[string][]Bead{},
			expected: 0,
		},
		{
			name: "single team",
			groups: map[string][]Bead{
				"team-alpha": {{ID: "bd-1"}},
			},
			expected: 1,
		},
		{
			name: "multiple teams",
			groups: map[string][]Bead{
				"team-alpha": {{ID: "bd-1"}},
				"team-beta":  {{ID: "bd-2"}},
				"team-gamma": {{ID: "bd-3"}},
			},
			expected: 3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := teamNames(tt.groups)
			if len(result) != tt.expected {
				t.Errorf("Expected %d team names, got %d", tt.expected, len(result))
			}
		})
	}
}

// Test processResults function
func TestProcessResults(t *testing.T) {
	tests := []struct {
		name              string
		results           []ScrumResult
		expectedSuccess   bool
		expectedFatalErr  bool
	}{
		{
			name:             "all successful",
			results:          []ScrumResult{
				{BeadID: "bd-1", Success: true, PRUrl: "https://github.com/user/repo/pull/1"},
				{BeadID: "bd-2", Success: true, PRUrl: "https://github.com/user/repo/pull/2"},
			},
			expectedSuccess:  true,
			expectedFatalErr: false,
		},
		{
			name:             "all failed",
			results:          []ScrumResult{
				{BeadID: "bd-1", Success: false, Error: "dev agent failed"},
				{BeadID: "bd-2", Success: false, Error: "qa validation failed"},
			},
			expectedSuccess:  false,
			expectedFatalErr: false,
		},
		{
			name:             "mixed success and failure",
			results:          []ScrumResult{
				{BeadID: "bd-1", Success: true, PRUrl: "https://github.com/user/repo/pull/1"},
				{BeadID: "bd-2", Success: false, Error: "timeout"},
			},
			expectedSuccess:  false,
			expectedFatalErr: false,
		},
		{
			name:             "skipped beads",
			results:          []ScrumResult{
				{BeadID: "bd-1", Success: true, PRUrl: "https://github.com/user/repo/pull/1"},
				{BeadID: "bd-2", Skipped: true},
			},
			expectedSuccess:  true,
			expectedFatalErr: false,
		},
		{
			name:             "empty results",
			results:          []ScrumResult{},
			expectedSuccess:  true,
			expectedFatalErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create channel and populate with results
			resultChan := make(chan ScrumResult, len(tt.results))
			for _, result := range tt.results {
				resultChan <- result
			}
			close(resultChan)

			// Process results
			allSuccess, fatalErr := processResults(resultChan)

			if allSuccess != tt.expectedSuccess {
				t.Errorf("Expected allSuccess=%v, got %v", tt.expectedSuccess, allSuccess)
			}

			if (fatalErr != nil) != tt.expectedFatalErr {
				t.Errorf("Expected fatalErr=%v, got %v", tt.expectedFatalErr, fatalErr != nil)
			}
		})
	}
}

// Test validateAgentPath function
func TestValidateAgentPath(t *testing.T) {
	tests := []struct {
		name      string
		agentPath string
		wantErr   bool
	}{
		{
			name:      "valid path",
			agentPath: ".claude/agents/backend-dev",
			wantErr:   false,
		},
		{
			name:      "valid nested path",
			agentPath: ".claude/agents/qa/unit-tests",
			wantErr:   false,
		},
		{
			name:      "invalid path - wrong prefix",
			agentPath: "agents/backend-dev",
			wantErr:   true,
		},
		{
			name:      "invalid path - absolute",
			agentPath: "/home/user/.claude/agents/dev",
			wantErr:   true,
		},
		{
			name:      "invalid path - empty",
			agentPath: "",
			wantErr:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateAgentPath(tt.agentPath)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateAgentPath() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// Test context cancellation in RalphLoop
func TestRalphLoopContextCancellation(t *testing.T) {
	config := Config{
		MaxParallelSessions: 5,
		PollInterval:        1 * time.Second,
	}

	// Create a context that's already cancelled
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	// RalphLoop should return immediately with context.Canceled error
	err := RalphLoop(ctx, config)
	if err != context.Canceled {
		t.Errorf("Expected context.Canceled, got %v", err)
	}
}

package ralph

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
)

// findReadyBeads calls `bd ready --json` and filters by issue_type
func findReadyBeads(ctx context.Context, config Config) ([]Bead, error) {
	// Execute `bd ready --json`
	cmd := exec.CommandContext(ctx, "bd", "ready", "--json")
	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("bd ready failed: %s (stderr: %s)", err, string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("bd ready failed: %w", err)
	}

	// Parse JSON output
	var beads []Bead
	if err := json.Unmarshal(output, &beads); err != nil {
		return nil, fmt.Errorf("parse bd ready output: %w", err)
	}

	// Filter by issue_type (only beads-ralph-work and beads-ralph-merge)
	filtered := make([]Bead, 0, len(beads))
	for _, bead := range beads {
		if bead.IssueType == "beads-ralph-work" || bead.IssueType == "beads-ralph-merge" {
			filtered = append(filtered, bead)
		}
	}

	return filtered, nil
}

// groupByTeam groups beads by metadata.team_name
// This allows flexible team composition:
// - One team with multiple beads on different branches
// - Sequential dev→review→fix→qa workflows in one team
// - Multiple isolated teams for parallel sprints
func groupByTeam(beads []Bead) map[string][]Bead {
	groups := make(map[string][]Bead)
	for _, bead := range beads {
		teamName := bead.Metadata.TeamName
		if teamName == "" {
			// Default team name if not specified
			teamName = "default-team"
		}
		groups[teamName] = append(groups[teamName], bead)
	}
	return groups
}

// teamNames extracts team names from team groups for logging
func teamNames(groups map[string][]Bead) []string {
	names := make([]string, 0, len(groups))
	for name := range groups {
		names = append(names, name)
	}
	return names
}

// validateAgentPath checks if an agent path exists in .claude/agents/
func validateAgentPath(agentPath string) error {
	if !strings.HasPrefix(agentPath, ".claude/agents/") {
		return fmt.Errorf("invalid agent path: must start with .claude/agents/")
	}
	// TODO: Check if file exists on disk (requires knowing repo root)
	return nil
}

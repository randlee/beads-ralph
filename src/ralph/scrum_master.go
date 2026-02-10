package ralph

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os/exec"
	"strings"
	"time"
)

// runScrumMaster launches a scrum-master Claude session for a single bead
// Returns ScrumResult with PR information or error details
func runScrumMaster(ctx context.Context, bead Bead, config Config) ScrumResult {
	startTime := time.Now()
	log.Printf("Launching scrum-master for bead %s (team: %s)", bead.ID, bead.Metadata.TeamName)

	// Apply timeout from config
	timeout := config.ScrumMasterTimeout
	if timeout == 0 {
		timeout = 30 * time.Minute // Default fallback
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Build Claude command from AgentSpec
	cmdArgs := buildAgentCommand(bead.Metadata.ScrumMasterAgent, config)
	if len(cmdArgs) == 0 {
		return ScrumResult{
			BeadID:  bead.ID,
			Success: false,
			Error:   "empty command generated from AgentSpec",
		}
	}

	// Generate initial prompt from bead metadata
	prompt := generateScrumMasterPrompt(bead)

	// Launch subprocess
	cmd := exec.CommandContext(ctx, cmdArgs[0], cmdArgs[1:]...)

	// Add prompt to stdin
	cmd.Stdin = strings.NewReader(prompt)

	// Capture stdout/stderr
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	elapsed := time.Since(startTime)
	log.Printf("Scrum-master for bead %s completed in %s", bead.ID, elapsed)

	// Check for timeout
	if ctx.Err() == context.DeadlineExceeded {
		return ScrumResult{
			BeadID:  bead.ID,
			Success: false,
			Error:   fmt.Sprintf("timeout after %s", timeout),
		}
	}

	// Check for execution error
	if err != nil {
		log.Printf("Scrum-master execution error for bead %s: %v", bead.ID, err)
		return ScrumResult{
			BeadID:  bead.ID,
			Success: false,
			Error:   fmt.Sprintf("execution error: %v", err),
		}
	}

	// Parse JSON output
	result, parseErr := parseJSONOutput(outputStr)
	if parseErr != nil {
		log.Printf("Failed to parse scrum-master output for bead %s: %v", bead.ID, parseErr)
		log.Printf("Output was: %s", outputStr)
		return ScrumResult{
			BeadID:  bead.ID,
			Success: false,
			Error:   fmt.Sprintf("invalid JSON output: %v", parseErr),
		}
	}

	// Ensure BeadID is set (in case agent didn't include it)
	if result.BeadID == "" {
		result.BeadID = bead.ID
	}

	return result
}

// buildAgentCommand constructs the Claude Code command from AgentSpec and system defaults
// Returns command as string array (executable + arguments)
func buildAgentCommand(spec AgentSpec, config Config) []string {
	// 1. Resolve executable
	executable := spec.Executable
	if executable == "" {
		executable = config.AgentDefaults.DefaultExecutable
	}
	if executable == "" {
		executable = "claude" // Ultimate fallback
	}

	cmd := []string{executable}

	// 2. Resolve model (4-level priority)
	model := resolveModel(spec, config)
	if model != "" {
		cmd = append(cmd, "--model", model)
	}

	// 3. Add options (from spec or system defaults)
	options := spec.Options
	if len(options) == 0 {
		options = config.AgentDefaults.DefaultOptions
	}
	cmd = append(cmd, options...)

	// 4. Add agent flag (required)
	if spec.Agent != "" {
		cmd = append(cmd, "--agent", spec.Agent)
	}

	return cmd
}

// resolveModel implements 4-level model resolution priority
// 1. AgentSpec.Model (explicit override in bead)
// 2. Agent YAML frontmatter (recommended_model) - NOT IMPLEMENTED YET
// 3. System config (default_model or role-based)
// 4. Hardcoded fallback: "sonnet"
func resolveModel(spec AgentSpec, config Config) string {
	// Level 1: Explicit override in AgentSpec
	if spec.Model != "" {
		return spec.Model
	}

	// Level 2: Agent frontmatter (TODO: Parse .md file YAML frontmatter)
	// This will be implemented in a future sprint
	// if agentFrontmatter := loadAgentFrontmatter(spec.Agent); agentFrontmatter.RecommendedModel != "" {
	//     return agentFrontmatter.RecommendedModel
	// }

	// Level 3: System config
	// Try role-based model first
	if spec.Role != "" {
		if roleModel, ok := config.AgentDefaults.RoleModels[spec.Role]; ok && roleModel != "" {
			return roleModel
		}
	}

	// Try default model
	if config.AgentDefaults.DefaultModel != "" {
		return config.AgentDefaults.DefaultModel
	}

	// Level 4: Hardcoded fallback
	return "sonnet"
}

// generateScrumMasterPrompt creates the initial prompt for the scrum-master agent
// Based on bead metadata (title, description, worktree path, etc.)
func generateScrumMasterPrompt(bead Bead) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("Execute Sprint: %s\n\n", bead.Title))
	sb.WriteString(fmt.Sprintf("**Bead ID**: %s\n", bead.ID))
	sb.WriteString(fmt.Sprintf("**Team**: %s\n", bead.Metadata.TeamName))
	sb.WriteString(fmt.Sprintf("**Worktree**: %s\n", bead.Metadata.WorktreePath))
	sb.WriteString(fmt.Sprintf("**Branch**: %s\n", bead.Metadata.Branch))
	sb.WriteString(fmt.Sprintf("**Source Branch**: %s\n\n", bead.Metadata.SourceBranch))

	if bead.Description != "" {
		sb.WriteString("**Description**:\n")
		sb.WriteString(bead.Description)
		sb.WriteString("\n\n")
	}

	if bead.Metadata.PlanFile != "" {
		sb.WriteString(fmt.Sprintf("**Plan Reference**: %s", bead.Metadata.PlanFile))
		if bead.Metadata.PlanSection != "" {
			sb.WriteString(fmt.Sprintf(" (%s)", bead.Metadata.PlanSection))
		}
		sb.WriteString("\n\n")
	}

	sb.WriteString("**CRITICAL**: You must return fenced JSON output with ScrumResult:\n\n")
	sb.WriteString("```json\n")
	sb.WriteString("{\n")
	sb.WriteString(fmt.Sprintf("  \"bead_id\": \"%s\",\n", bead.ID))
	sb.WriteString("  \"success\": true,\n")
	sb.WriteString("  \"pr_url\": \"https://github.com/user/repo/pull/42\",\n")
	sb.WriteString("  \"pr_number\": 42,\n")
	sb.WriteString("  \"bead_updated\": true,\n")
	sb.WriteString("  \"error\": null\n")
	sb.WriteString("}\n")
	sb.WriteString("```\n")

	return sb.String()
}

// parseJSONOutput extracts the ScrumResult from the agent's output
// Looks for fenced JSON block (```json ... ```)
func parseJSONOutput(output string) (ScrumResult, error) {
	// Find JSON fenced code block
	startMarker := "```json"
	endMarker := "```"

	startIdx := strings.Index(output, startMarker)
	if startIdx == -1 {
		return ScrumResult{}, fmt.Errorf("no JSON code block found (missing ```json)")
	}

	// Skip past the ```json marker
	jsonStart := startIdx + len(startMarker)

	// Find the closing ```
	endIdx := strings.Index(output[jsonStart:], endMarker)
	if endIdx == -1 {
		return ScrumResult{}, fmt.Errorf("unclosed JSON code block (missing closing ```)")
	}

	// Extract JSON content
	jsonStr := strings.TrimSpace(output[jsonStart : jsonStart+endIdx])

	// Parse JSON
	var result ScrumResult
	if err := json.Unmarshal([]byte(jsonStr), &result); err != nil {
		return ScrumResult{}, fmt.Errorf("invalid JSON: %w", err)
	}

	return result, nil
}

package ralph

import (
	"context"
	"fmt"
	"log"
	"sync"
)

// RalphLoop is the main orchestration loop
// It finds ready beads, groups them by team, and launches parallel scrum-master sessions
func RalphLoop(ctx context.Context, config Config) error {
	for {
		// Check if context is cancelled
		select {
		case <-ctx.Done():
			log.Println("Context cancelled, shutting down ralph loop")
			return ctx.Err()
		default:
		}

		// 1. Find ready beads
		readyBeads, err := findReadyBeads(ctx, config)
		if err != nil {
			return fmt.Errorf("find ready beads: %w", err)
		}

		if len(readyBeads) == 0 {
			log.Println("No ready beads. All work complete or blocked.")
			break
		}

		// 2. Group by team (NOT by sprint!)
		teamGroups := groupByTeam(readyBeads)
		log.Printf("Found %d team(s) ready: %v", len(teamGroups), teamNames(teamGroups))

		// 3. Launch parallel scrum-masters (one Claude session per team)
		var wg sync.WaitGroup
		results := make(chan ScrumResult, len(readyBeads))
		semaphore := make(chan struct{}, config.MaxParallelSessions)

		for teamName, beads := range teamGroups {
			log.Printf("Starting team %s with %d bead(s)", teamName, len(beads))

			// Launch one scrum-master session per bead in the team
			// TODO Sprint 4.2: Change to one session per team using agent-teams
			for _, bead := range beads {
				wg.Add(1)

				go func(b Bead) {
					defer wg.Done()

					// Acquire semaphore (limit parallelism)
					semaphore <- struct{}{}
					defer func() { <-semaphore }()

					// TODO Sprint 4.2: Replace with runScrumMasterTeam(ctx, teamName, beads, config)
					result := runScrumMaster(ctx, b, config)
					results <- result
				}(bead)
			}
		}

		// 4. Wait for all scrum-masters to complete
		wg.Wait()
		close(results)

		// 5. Process results
		allSuccess, fatalError := processResults(results)

		if fatalError != nil {
			return fmt.Errorf("fatal error: %w", fatalError)
		}

		if !allSuccess {
			log.Println("Some beads failed. Check status and retry.")
			// Continue to next iteration (may have other ready work)
		}
	}

	log.Println("Ralph loop completed successfully.")
	return nil
}

// runScrumMaster launches a single scrum-master session for one bead
// This is a placeholder for Sprint 4.1 - full implementation comes in Sprint 4.2
func runScrumMaster(ctx context.Context, bead Bead, config Config) ScrumResult {
	log.Printf("TODO: Launch scrum-master for bead %s (team: %s)", bead.ID, bead.Metadata.TeamName)

	// Placeholder implementation
	return ScrumResult{
		BeadID:  bead.ID,
		Success: false,
		Error:   "runScrumMaster not yet implemented (Sprint 4.2)",
	}
}

// processResults processes all scrum-master results
// Returns (allSuccess, fatalError)
func processResults(results chan ScrumResult) (bool, error) {
	allSuccess := true
	var fatalError error

	for result := range results {
		if result.Skipped {
			log.Printf("Bead %s was skipped (already claimed)", result.BeadID)
			continue
		}

		if !result.Success {
			allSuccess = false
			log.Printf("Bead %s failed: %s", result.BeadID, result.Error)

			// Check for fatal errors (non-recoverable)
			// For now, all errors are considered retryable
			// Fatal error detection will be added in Sprint 4.3
		} else {
			log.Printf("Bead %s completed successfully (PR: %s)", result.BeadID, result.PRUrl)
		}
	}

	return allSuccess, fatalError
}

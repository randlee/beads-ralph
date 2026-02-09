# Corner Cases & Failure Scenarios

Comprehensive analysis of edge cases, failure modes, and mitigation strategies for beads-ralph.

## Failure Categories

1. **Scrum-Master Failures** - Issues with orchestration agent
2. **Dev Agent Failures** - Issues with development work
3. **QA Agent Failures** - Issues with validation
4. **Infrastructure Failures** - Git, disk, network issues
5. **Concurrency Failures** - Race conditions, locks
6. **Schema/Configuration Failures** - Invalid data

---

## 1. Scrum-Master Failures

### 1.1 Scrum-Master Fails to Create PR

**Scenario**: Dev + QA succeed, but scrum-master doesn't create PR

**Detection**:
```go
if result.Success == true && result.PR_URL == "" {
    // PR creation failed
}
```

**Root Causes**:
- `gh` CLI not authenticated
- Network failure during PR creation
- Rate limit on GitHub API
- Scrum-master forgot to call `gh pr create`

**Mitigation**:
1. Restart scrum-master with explicit prompt:
   ```
   CRITICAL: Your previous run succeeded but did NOT create a PR.
   You MUST create a PR now for branch {branch}.
   Run: gh pr create --title "{title}" --body "{body}"
   ```
2. Verify PR created before returning success
3. Max 2 retries for PR creation
4. If still fails: mark as fatal, require manual intervention

**Implementation**:
```go
func retryScrumMasterPRCreation(ctx context.Context, bead Bead, prevResult ScrumResult) ScrumResult {
    prompt := fmt.Sprintf(`
CRITICAL RECOVERY MODE: PR Creation Failed

Previous run completed work successfully but PR was NOT created.

Branch: %s
Title: %s

YOUR TASK: Create PR and update bead.

1. Verify branch exists: git branch --list %s
2. Create PR: gh pr create --title "%s" --body "Sprint %s work" --head %s
3. Capture PR URL from output
4. Update bead: bd update %s --metadata '{"pr_url": "URL", "pr_number": NUM}'
5. Update bead status: bd update %s --status closed

Return fenced JSON with pr_url and pr_number populated.
`, bead.Metadata.Branch, bead.Title, bead.Metadata.Branch, bead.Title,
   bead.Metadata.Sprint, bead.Metadata.Branch, bead.ID, bead.ID)

    return runScrumMaster(ctx, bead, prompt)
}
```

### 1.2 Scrum-Master Fails to Update Bead

**Scenario**: Work complete, PR created, but bead status not updated

**Detection**:
```go
if result.Success == true && result.BeadUpdated == false {
    // Bead update failed
}
```

**Root Causes**:
- Beads daemon not running
- Database locked
- Scrum-master forgot to call `bd update`
- Invalid bead ID reference

**Mitigation**:
1. Restart scrum-master with explicit prompt:
   ```
   CRITICAL: Bead {bead_id} status was NOT updated.
   Run: bd update {bead_id} --status closed
   Run: bd update {bead_id} --metadata '{json}'
   ```
2. Verify bead updated: `bd show {bead_id} --json`
3. Check `status` field is `closed` and `metadata` has `pr_url`

### 1.3 Scrum-Master Gives Up (Fatal Error)

**Scenario**: After max attempts, scrum-master returns `fatal: true`

**Detection**:
```go
if result.Fatal == true {
    // Unrecoverable error
    log.Fatal(result.Error)
}
```

**Root Causes**:
- Merge conflict cannot be resolved
- Tests fail after multiple fix attempts
- Security vulnerability cannot be remediated
- Build completely broken
- Environmental issue (missing dependencies)

**Mitigation (MVP)**:
1. Stop ralph loop immediately
2. Log full error context:
   ```
   FATAL ERROR on bead {bead_id}:
   Sprint: {sprint}
   Phase: {phase}
   Attempts: {attempt_count}
   Error: {error_message}
   QA Results: {qa_results}
   ```
3. Mark bead as `blocked` in beads
4. Require human intervention
5. **No automatic recovery in MVP**

**Future Mitigation**:
- Create escalation bead for human review
- Notify via Slack/email
- Create rollback bead to revert changes
- Alternative agent strategies (different model, different agent)

### 1.4 Scrum-Master Timeout

**Scenario**: Scrum-master runs indefinitely, never returns

**Detection**:
```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
defer cancel()

result := runScrumMaster(ctx, bead)
```

**Root Causes**:
- Infinite dev/QA retry loop
- Dev agent stuck in interactive prompt
- QA agent running very long test suite
- Claude API timeout

**Mitigation**:
1. Set timeout on Claude command execution (30 minutes default)
2. Kill Claude process on timeout
3. Mark attempt as failure
4. Increment `attempt_count`
5. If under max attempts: retry with shorter timeout
6. If at max attempts: mark as fatal

**Configuration**:
```yaml
# beads-ralph.yaml
timeouts:
  scrum_master: 30m
  dev_agent: 20m
  qa_agent: 10m
```

---

## 2. Dev Agent Failures

### 2.1 Dev Agent Breaks Build

**Scenario**: Dev agent introduces syntax errors, build fails

**Detection**: QA agent (build/test) returns `fail`

**Mitigation**:
1. Pass QA failure message to dev agent:
   ```
   Your changes broke the build. QA agent reported:
   {qa_message}
   {qa_details}

   Fix the issues and ensure build passes.
   ```
2. Dev agent fixes issues
3. QA runs again
4. Loop continues until success or max attempts

**Implementation**:
```go
func devQALoop(ctx context.Context, bead Bead) error {
    for attempt := 1; attempt <= bead.Metadata.MaxRetryAttempts; attempt++ {
        // Run dev agent
        devResult := runDevAgent(ctx, bead)

        // Run QA agents
        qaResults := runQAAgents(ctx, bead)

        // Check QA results
        allPass := true
        stopRequested := false
        var failureMessages []string

        for _, qa := range qaResults {
            if qa.Status == "fail" {
                allPass = false
                failureMessages = append(failureMessages, qa.Message)
            } else if qa.Status == "stop" {
                stopRequested = true
                break
            }
        }

        if stopRequested {
            return fmt.Errorf("QA requested stop: critical issue")
        }

        if allPass {
            return nil // Success
        }

        // Pass failures back to dev agent
        feedbackPrompt := buildQAFeedbackPrompt(failureMessages)
        runDevAgentWithFeedback(ctx, bead, feedbackPrompt)
    }

    return fmt.Errorf("max retry attempts reached")
}
```

### 2.2 Dev Agent Creates Wrong Files

**Scenario**: Dev agent creates files outside worktree or in wrong location

**Detection**: QA agent (file structure check) verifies file locations

**Mitigation**:
1. QA agent validates:
   - All changed files are within worktree path
   - No files created in system directories
   - No files created in other worktrees
2. If violation detected: QA returns `fail` with details
3. Dev agent corrects file locations

**Prevention**:
- Include worktree path in dev prompt
- Instruct dev agent to use relative paths
- Add file location check QA agent

### 2.3 Dev Agent Introduces Security Vulnerability

**Scenario**: Dev agent adds SQL injection, hardcoded secrets, etc.

**Detection**: QA agent (security scan) returns `stop` (not `fail`)

**Mitigation**:
1. QA security agent returns `status: stop` for critical issues:
   ```json
   {
     "status": "stop",
     "message": "CRITICAL: SQL injection vulnerability detected",
     "details": {
       "severity": "high",
       "file": "api/auth.go",
       "line": 42,
       "issue": "Unsanitized user input in SQL query"
     }
   }
   ```
2. Scrum-master sees `stop` and marks as fatal
3. Ralph loop stops
4. **No retry attempts for security stops**

**QA Agent Configuration**:
```json
{
  "agent_path": ".claude/agents/qa-security-scan",
  "model": "sonnet",
  "prompt": "Run security scanner. Return 'stop' for HIGH/CRITICAL vulnerabilities, 'fail' for medium/low.",
  "output_schema": {
    "properties": {
      "status": {"enum": ["pass", "fail", "stop"]},
      "vulnerabilities": {"type": "array"}
    }
  }
}
```

---

## 3. QA Agent Failures

### 3.1 QA Agent Never Returns (Timeout)

**Scenario**: QA agent hangs indefinitely

**Detection**: Timeout on Claude command

**Root Causes**:
- Infinite test loop
- QA waiting for user input
- Very slow test suite
- Claude API timeout

**Mitigation**:
1. Set timeout on each QA agent execution
2. Kill Claude process on timeout
3. Treat as QA failure (retry dev agent)
4. Log timeout for debugging

**Implementation**:
```go
func runQAAgent(ctx context.Context, qa QAAgent, bead Bead) QAResult {
    qaCtx, cancel := context.WithTimeout(ctx, 10*time.Minute)
    defer cancel()

    cmd := exec.CommandContext(qaCtx, "claude",
        "--agent", qa.AgentPath,
        "-p", buildQAPrompt(qa, bead))

    output, err := cmd.Output()
    if err != nil {
        if qaCtx.Err() == context.DeadlineExceeded {
            return QAResult{
                Status: "fail",
                Message: "QA agent timed out after 10 minutes",
            }
        }
        return QAResult{Status: "fail", Message: err.Error()}
    }

    return parseQAOutput(output)
}
```

### 3.2 QA Agent Returns Invalid JSON

**Scenario**: QA agent output doesn't match schema

**Detection**: JSON parse error or schema validation failure

**Root Causes**:
- QA agent didn't use fenced JSON
- QA agent returned malformed JSON
- Extra text outside fenced block
- Wrong schema structure

**Mitigation**:
1. Attempt to extract JSON from output (find `'''json` blocks)
2. Validate against expected schema
3. If invalid: treat as QA failure, return:
   ```json
   {
     "status": "fail",
     "message": "QA agent returned invalid output format"
   }
   ```
4. Dev agent doesn't get specific feedback (generic failure)
5. May require human inspection

**Implementation**:
```go
func parseQAOutput(output []byte) QAResult {
    // Try to extract JSON from fenced code blocks
    jsonPattern := regexp.MustCompile("```json\n(.*?)\n```")
    matches := jsonPattern.FindSubmatch(output)

    var result QAResult
    if len(matches) > 1 {
        err := json.Unmarshal(matches[1], &result)
        if err != nil {
            return QAResult{
                Status: "fail",
                Message: "QA agent returned invalid JSON",
            }
        }
    } else {
        // Try parsing entire output as JSON
        err := json.Unmarshal(output, &result)
        if err != nil {
            return QAResult{
                Status: "fail",
                Message: "QA agent did not return JSON",
            }
        }
    }

    // Validate required fields
    if result.Status == "" || result.Message == "" {
        return QAResult{
            Status: "fail",
            Message: "QA agent missing required fields",
        }
    }

    return result
}
```

### 3.3 QA Agents Disagree

**Scenario**: One QA passes, another fails

**Detection**: Mixed pass/fail results from multiple QA agents

**Resolution**: **ALL QA agents must pass**

**Logic**:
```go
allPass := true
for _, qa := range qaResults {
    if qa.Status == "stop" {
        return "stop"  // Any stop = immediate halt
    }
    if qa.Status == "fail" {
        allPass = false
    }
}

if allPass {
    return "pass"
} else {
    return "fail"  // Any fail = retry dev agent
}
```

### 3.4 QA Tests Are Flaky

**Scenario**: QA passes on retry but results inconsistent

**Detection**: Hard to detect automatically (MVP limitation)

**Mitigation (Future)**:
- Track QA result history per bead
- Flag if status changes between attempts
- Add QA reliability score
- Alert on flaky tests

**MVP Approach**: Trust QA results, accept flakiness risk

---

## 4. Infrastructure Failures

### 4.1 Worktree Creation Fails

**Scenario**: `sc-git-worktree` skill fails

**Root Causes**:
- Disk full
- Permission denied
- Invalid branch name
- Worktree already exists
- Git repository corruption

**Detection**: Scrum-master receives error from skill

**Mitigation**:
1. Check disk space before starting ralph loop
2. Validate branch names in planning phase
3. Clean up stale worktrees before starting
4. On worktree creation failure:
   - Log full error
   - Mark as fatal
   - Stop ralph loop

**Pre-flight Check**:
```bash
# Before starting ralph loop
df -h | awk '$5 > 80 {print "WARNING: Disk " $6 " is " $5 " full"}'

# Clean stale worktrees
git worktree prune
```

### 4.2 Multiple Scrum-Masters Claim Same Bead (Race Condition)

**Scenario**: Two Go routines try to claim same bead simultaneously

**Detection**: `bd claim` atomic operation fails for one

**Mitigation**: beads `bd claim` uses CAS (compare-and-swap)

**How It Works**:
```sql
-- Atomic claim operation in beads
UPDATE issues
SET assignee = 'beads-ralph-scrum-master'
WHERE id = 'bd-abc123'
  AND assignee = '';  -- Only succeeds if unclaimed
```

**Go Implementation**:
```go
func claimBead(ctx context.Context, beadID string) error {
    cmd := exec.CommandContext(ctx, "bd", "claim", beadID)
    err := cmd.Run()
    if err != nil {
        // Already claimed by another scrum-master
        return ErrAlreadyClaimed
    }
    return nil
}

func runScrumMaster(ctx context.Context, bead Bead) ScrumResult {
    // Atomic claim
    err := claimBead(ctx, bead.ID)
    if err == ErrAlreadyClaimed {
        // Skip this bead, another scrum-master claimed it
        return ScrumResult{Success: true, Skipped: true}
    }

    // Continue with work...
}
```

**Result**: First claim succeeds, second fails gracefully. No duplicate work.

### 4.3 Disk Space Exhaustion

**Scenario**: Creating N worktrees fills disk

**Detection**: Worktree creation or git operation fails with disk space error

**Mitigation**:
1. **Pre-flight check** before starting ralph loop:
   ```go
   func checkDiskSpace(path string, requiredGB int) error {
       var stat syscall.Statfs_t
       syscall.Statfs(path, &stat)
       availableGB := (stat.Bavail * uint64(stat.Bsize)) / (1024 * 1024 * 1024)
       if availableGB < uint64(requiredGB) {
           return fmt.Errorf("insufficient disk space: %dGB available, %dGB required",
               availableGB, requiredGB)
       }
       return nil
   }
   ```

2. **Estimate required space**:
   - Worktree size = repo size × number of parallel sprints
   - Add 20% buffer for build artifacts

3. **Configuration**:
   ```yaml
   # beads-ralph.yaml
   disk:
     min_free_gb: 10
     worktree_base: "/Volumes/WorkDrive/worktrees"
   ```

### 4.4 Git Daemon Lock Contention

**Scenario**: Multiple scrum-masters access git simultaneously, causing lock errors

**Detection**: Git operations fail with "unable to create lock file" error

**Mitigation**:
1. **Worktrees isolate most operations** - each worktree has independent working directory
2. **Shared operations** (fetch, push) use beads daemon (serializes via RPC)
3. **Retry with exponential backoff**:
   ```go
   func retryGitOperation(fn func() error, maxRetries int) error {
       for attempt := 0; attempt < maxRetries; attempt++ {
           err := fn()
           if err == nil {
               return nil
           }
           if strings.Contains(err.Error(), "lock") {
               backoff := time.Duration(math.Pow(2, float64(attempt))) * time.Second
               time.Sleep(backoff + time.Duration(rand.Intn(1000))*time.Millisecond)
               continue
           }
           return err
       }
       return fmt.Errorf("max retries exceeded")
   }
   ```

### 4.5 Network Partition (No GitHub Access)

**Scenario**: Can't push branches or create PRs due to network failure

**Detection**:
- `git push` fails with network error
- `gh pr create` fails with API error

**Mitigation**:
1. **Retry with backoff** (network may recover)
2. **Distinguish temporary vs persistent failure**:
   - Temporary: DNS resolution failure, timeout
   - Persistent: Authentication failure, invalid remote
3. **If persistent failure**:
   - Mark as fatal
   - Stop ralph loop
   - Work remains in local worktrees (can resume later)
4. **Recovery**: When network restored, restart ralph loop (PRs will be created)

**Configuration**:
```yaml
# beads-ralph.yaml
network:
  max_retries: 5
  retry_backoff: exponential
  timeout: 30s
```

### 4.6 Claude API Rate Limits

**Scenario**: Parallel sessions hit Claude API rate limits

**Detection**: Claude CLI returns rate limit error (HTTP 429)

**Mitigation**:
1. **Exponential backoff with jitter**:
   ```go
   if isRateLimitError(err) {
       backoff := time.Duration(math.Pow(2, float64(attempt))) * time.Second
       jitter := time.Duration(rand.Intn(1000)) * time.Millisecond
       time.Sleep(backoff + jitter)
       retry()
   }
   ```

2. **Dynamic parallelism reduction**:
   ```go
   var activeSessions int32
   const maxSessions = 10

   func runScrumMaster(bead Bead) {
       for {
           if atomic.LoadInt32(&activeSessions) < maxSessions {
               atomic.AddInt32(&activeSessions, 1)
               defer atomic.AddInt32(&activeSessions, -1)
               break
           }
           time.Sleep(1 * time.Second)
       }

       // Run scrum-master...
   }
   ```

3. **Queue beads, throttle launches**:
   - Ralph loop tracks active sessions
   - Waits before launching new sessions if at limit

**Configuration**:
```yaml
# beads-ralph.yaml
claude:
  max_parallel_sessions: 10
  rate_limit_backoff: exponential
  max_retries: 5
```

---

## 5. Concurrency Failures

### 5.1 Race Condition in Bead Updates

**Scenario**: Two scrum-masters update same bead simultaneously

**Mitigation**: beads daemon serializes writes via RPC (Unix domain socket)

**How It Works**:
```
Scrum-Master 1:  bd update bd-abc → RPC → Daemon → SQLite (write 1)
Scrum-Master 2:  bd update bd-def → RPC → Daemon → SQLite (write 2)
```

All writes go through single daemon process, preventing race conditions.

### 5.2 Deadlock in Dependency Graph

**Scenario**: Circular dependencies in bead graph

**Example**:
```
Bead A depends on Bead B
Bead B depends on Bead C
Bead C depends on Bead A  ← Cycle!
```

**Detection**: Planning phase must validate dependency graph

**Mitigation**:
1. **Cycle detection during planning**:
   ```python
   def detect_cycle(graph):
       visited = set()
       rec_stack = set()

       def dfs(node):
           visited.add(node)
           rec_stack.add(node)
           for neighbor in graph[node]:
               if neighbor not in visited:
                   if dfs(neighbor):
                       return True
               elif neighbor in rec_stack:
                   return True
           rec_stack.remove(node)
           return False

       for node in graph:
           if node not in visited:
               if dfs(node):
                   return True
       return False
   ```

2. **Validation in beads-mason agent**
3. **Error if cycle detected**: Refuse to create beads

**beads Built-in Protection**:
```bash
# beads has cycle detection
bd dep cycles

# Returns list of cycles if any exist
```

---

## 6. Schema/Configuration Failures

### 6.1 Corrupted Bead Metadata

**Scenario**: Metadata JSON is malformed or missing required fields

**Detection**:
- JSON parse error
- Schema validation failure
- Missing required fields

**Mitigation**:
1. **Validate during planning phase** (before creating beads)
2. **Validate in ralph loop** before launching scrum-master:
   ```go
   func validateBead(bead Bead) error {
       if bead.Metadata.WorktreePath == "" {
           return fmt.Errorf("missing worktree_path")
       }
       if bead.Metadata.Branch == "" {
           return fmt.Errorf("missing branch")
       }
       // ... validate all required fields
       return nil
   }
   ```
3. **If validation fails**:
   - Log error
   - Mark bead as `blocked`
   - Continue with other beads (don't stop entire loop)

### 6.2 Invalid Phase/Sprint Numbers

**Scenario**: Bead has invalid phase or sprint format

**Detection**: Regex validation fails

**Mitigation**:
1. **Validate during planning** using regex patterns:
   ```python
   if not PHASE_PATTERN.match(metadata['phase']):
       raise ValueError(f"Invalid phase: {metadata['phase']}")
   if not SPRINT_PATTERN.match(metadata['sprint']):
       raise ValueError(f"Invalid sprint: {metadata['sprint']}")
   ```
2. **Refuse to create invalid beads**
3. **Planning skill ensures valid numbering**

### 6.3 Missing Agent or Skill Files

**Scenario**: Bead references non-existent agent path

**Example**: `dev_agent_path: ".claude/agents/missing-agent"`

**Detection**:
- File not found error when scrum-master tries to launch agent
- Claude fails to load agent

**Mitigation**:
1. **Validate during planning** (check files exist):
   ```python
   if not os.path.exists(metadata['dev_agent_path']):
       raise FileNotFoundError(f"Agent not found: {metadata['dev_agent_path']}")
   ```
2. **If detected at runtime**:
   - Mark as fatal error
   - Log missing agent path
   - Stop ralph loop (configuration error, not recoverable)

---

## 7. Merge-Specific Failures

### 7.1 Merge Conflict Cannot Be Resolved

**Scenario**: Merge bead attempts to merge incompatible branches

**Detection**: Git merge command fails with conflicts

**Mitigation**:
1. **Scrum-master for merge bead** attempts conflict resolution
2. **If conflicts are complex**:
   - Try automated resolution strategies:
     - Accept ours for specific file types (docs)
     - Accept theirs for specific file types (generated code)
   - Use merge specialist agent with conflict resolution skills
3. **If cannot resolve after attempts**:
   - Return `fatal: true`
   - Log conflict details
   - Stop ralph loop
   - Require human intervention (MVP)

**Future Enhancement**:
- Create escalation bead for human review
- Provide conflict visualization
- Track conflict patterns for learning

### 7.2 Merge Succeeds But Tests Fail

**Scenario**: Branches merge cleanly but integration tests fail

**Detection**: QA agent returns `fail` after merge

**Mitigation**:
- Same as regular dev/QA loop
- Merge specialist agent fixes integration issues
- Retry up to max attempts
- If fails: mark as fatal

---

## Summary Table

| Failure Type | Detection | Mitigation | Recoverable? |
|--------------|-----------|------------|--------------|
| Scrum-master fails to create PR | `result.PR_URL == ""` | Restart with explicit prompt | ✅ Yes |
| Scrum-master fails to update bead | `result.BeadUpdated == false` | Restart with explicit prompt | ✅ Yes |
| Scrum-master gives up | `result.Fatal == true` | Stop loop, log error | ❌ No (MVP) |
| Scrum-master timeout | Context deadline exceeded | Kill process, retry | ✅ Yes (limited) |
| Dev agent breaks build | QA returns `fail` | Pass feedback to dev | ✅ Yes |
| Dev agent wrong files | QA returns `fail` | Pass feedback to dev | ✅ Yes |
| Security vulnerability | QA returns `stop` | Mark fatal, stop loop | ❌ No |
| QA agent timeout | Context deadline exceeded | Treat as failure | ✅ Yes |
| QA agent invalid JSON | Parse error | Treat as failure | ✅ Yes |
| Worktree creation fails | Skill returns error | Mark fatal, stop loop | ❌ No |
| Race condition (bead claim) | `bd claim` fails | Skip bead (already claimed) | ✅ Yes |
| Disk space exhaustion | Pre-flight check fails | Refuse to start | ❌ No |
| Git lock contention | Lock file error | Retry with backoff | ✅ Yes |
| Network partition | Push/PR fails | Retry with backoff | ✅ Yes (temporary) |
| Claude API rate limit | HTTP 429 | Backoff, reduce parallelism | ✅ Yes |
| Corrupted bead metadata | JSON parse error | Mark blocked, continue others | ✅ Partial |
| Invalid phase/sprint | Regex validation fails | Refuse to create bead | ✅ Yes (planning) |
| Missing agent file | File not found | Mark fatal, stop loop | ❌ No |
| Merge conflict | Git merge fails | Attempt resolution, may fail | ⚠️ Sometimes |
| Dependency cycle | Cycle detection | Refuse to create beads | ✅ Yes (planning) |

---

## Recovery Procedures

### Restart Ralph Loop After Failure

```bash
# 1. Check status
bd list --status=in_progress --assignee=beads-ralph-scrum-master

# 2. Review failed beads
bd list --status=blocked --label=beads-ralph

# 3. Fix issues (manual intervention)
# ... fix code, fix config, etc.

# 4. Reopen blocked beads
bd update bd-abc123 --status open

# 5. Restart ralph loop
beads-ralph run --config beads-ralph.yaml
```

### Rollback to Previous Sprint

```bash
# 1. Identify last successful sprint
bd list --status=closed --label=sprint-1-2 --json

# 2. Close all beads after that sprint
bd list --status=open --label=sprint-1-3 --json | \
  jq -r '.[].id' | \
  xargs -I {} bd close {} --reason "Rollback"

# 3. Delete worktrees for rolled-back sprints
git worktree remove worktrees/main/1-3-*

# 4. Delete branches
git branch -D main/1-3-*

# 5. Delete PRs (optional)
gh pr list --label sprint-1-3 | \
  awk '{print $1}' | \
  xargs -I {} gh pr close {}

# 6. Reopen beads from failed sprint with fixes
# (manual planning adjustment)
```

### Emergency Stop

```bash
# 1. Identify all active scrum-masters
ps aux | grep "claude.*beads-ralph-scrum-master"

# 2. Kill all Claude processes
pkill -f "claude.*beads-ralph-scrum-master"

# 3. Stop ralph loop
pkill -f "beads-ralph run"

# 4. Mark all in-progress beads as open
bd list --status=in_progress --assignee=beads-ralph-scrum-master --json | \
  jq -r '.[].id' | \
  xargs -I {} bd update {} --status open
```

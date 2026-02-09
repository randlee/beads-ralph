package ralph

import "time"

// Bead represents a work item from `bd ready --json` output
type Bead struct {
	ID           string       `json:"id"`
	Title        string       `json:"title"`
	Description  string       `json:"description"`
	Status       string       `json:"status"`
	Priority     int          `json:"priority"`
	IssueType    string       `json:"issue_type"`
	Assignee     string       `json:"assignee"`
	Owner        string       `json:"owner"`
	Dependencies []string     `json:"dependencies"`
	Labels       []string     `json:"labels"`
	Comments     []string     `json:"comments"`
	ExternalRef  string       `json:"external_ref"`
	CreatedAt    time.Time    `json:"created_at"`
	UpdatedAt    time.Time    `json:"updated_at"`
	ClosedAt     *time.Time   `json:"closed_at"`
	Metadata     BeadMetadata `json:"metadata"`
}

// BeadMetadata contains beads-ralph-specific extended fields
type BeadMetadata struct {
	// Work identification
	Rig           string `json:"rig"`
	WorktreePath  string `json:"worktree_path"`
	Branch        string `json:"branch"`
	SourceBranch  string `json:"source_branch"`
	Phase         string `json:"phase"`
	Sprint        string `json:"sprint"`
	TeamName      string `json:"team_name"` // CRITICAL: Group beads by this field

	// Plan tracking
	PlanFile      string `json:"plan_file"`
	PlanSection   string `json:"plan_section"`
	PlanSprintID  string `json:"plan_sprint_id"`

	// Merge bead fields (nullable for work beads)
	BranchesToMerge []string `json:"branches_to_merge,omitempty"`

	// Dev agent configuration
	DevAgentPath string   `json:"dev_agent_path"`
	DevModel     string   `json:"dev_model"`
	DevPrompts   []string `json:"dev_prompts"`

	// QA agent configuration
	QAAgents []QAAgent `json:"qa_agents"`

	// Retry configuration
	MaxRetryAttempts int `json:"max_retry_attempts"`
	AttemptCount     int `json:"attempt_count"`

	// Execution tracking
	ScrumMasterSessionID string          `json:"scrum_master_session_id,omitempty"`
	DevAgentSessionID    string          `json:"dev_agent_session_id,omitempty"`
	DevAgentExecutions   []DevExecution  `json:"dev_agent_executions,omitempty"`
	QAAgentExecutions    []QAExecution   `json:"qa_agent_executions,omitempty"`

	// Result tracking
	PRUrl        string       `json:"pr_url,omitempty"`
	PRNumber     int          `json:"pr_number,omitempty"`
	ScrumResult  *ScrumResult `json:"scrum_result,omitempty"`
}

// QAAgent represents a QA agent configuration
type QAAgent struct {
	AgentPath    string                 `json:"agent_path"`
	Model        string                 `json:"model"`
	Prompt       string                 `json:"prompt"`
	InputSchema  map[string]interface{} `json:"input_schema,omitempty"`
	OutputSchema map[string]interface{} `json:"output_schema"`
}

// DevExecution tracks a single dev agent execution attempt
type DevExecution struct {
	Attempt     int       `json:"attempt"`
	SessionID   string    `json:"session_id"`
	AgentPath   string    `json:"agent_path"`
	Model       string    `json:"model"`
	StartedAt   time.Time `json:"started_at"`
	CompletedAt time.Time `json:"completed_at"`
	Status      string    `json:"status"` // "completed", "failed", "timeout"
	Error       string    `json:"error,omitempty"`
}

// QAExecution tracks a single QA agent execution
type QAExecution struct {
	Attempt     int                    `json:"attempt"`
	SessionID   string                 `json:"session_id"`
	AgentPath   string                 `json:"agent_path"`
	Model       string                 `json:"model"`
	StartedAt   time.Time              `json:"started_at"`
	CompletedAt time.Time              `json:"completed_at"`
	Status      string                 `json:"status"` // "pass", "fail", "stop"
	Message     string                 `json:"message"`
	Details     map[string]interface{} `json:"details,omitempty"`
}

// ScrumResult represents the outcome of a scrum-master session
type ScrumResult struct {
	BeadID      string `json:"bead_id"`
	Success     bool   `json:"success"`
	Skipped     bool   `json:"skipped"` // True if bead was already claimed
	Error       string `json:"error,omitempty"`
	PRUrl       string `json:"pr_url,omitempty"`
	PRNumber    int    `json:"pr_number,omitempty"`
	BeadUpdated bool   `json:"bead_updated"` // True if bead metadata was updated
}

// Config represents the beads-ralph.yaml configuration
type Config struct {
	// Ralph loop settings
	MaxParallelSessions int           `yaml:"max_parallel_sessions"`
	PollInterval        time.Duration `yaml:"poll_interval"`

	// Timeouts
	ScrumMasterTimeout time.Duration `yaml:"scrum_master_timeout"`
	DevAgentTimeout    time.Duration `yaml:"dev_agent_timeout"`
	QAAgentTimeout     time.Duration `yaml:"qa_agent_timeout"`

	// Retry settings
	MaxRetryAttempts    int `yaml:"max_retry_attempts"`
	PRCreationRetries   int `yaml:"pr_creation_retries"`

	// Worktree settings
	RepoName           string `yaml:"repo_name"`
	SourceBranch       string `yaml:"source_branch"`
	CleanupOnComplete  bool   `yaml:"cleanup_on_complete"`

	// Disk space checks
	MinFreeGB         int  `yaml:"min_free_gb"`
	CheckBeforeStart  bool `yaml:"check_before_start"`

	// Network settings
	MaxNetworkRetries int    `yaml:"max_network_retries"`
	RetryBackoff      string `yaml:"retry_backoff"`
	NetworkTimeout    time.Duration `yaml:"network_timeout"`
}

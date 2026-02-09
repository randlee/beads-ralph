#!/usr/bin/env python3
"""Pydantic models for beads-ralph schema validation."""

import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Valid enums
VALID_MODELS = ["sonnet", "opus", "haiku"]
VALID_STATUS = ["open", "in_progress", "closed", "blocked"]
VALID_QA_STATUS = ["pass", "fail", "stop"]
VALID_DEV_EXECUTION_STATUS = ["completed", "failed", "timeout"]
VALID_ISSUE_TYPES = ["beads-ralph-work", "beads-ralph-merge"]

# Regex patterns
PHASE_PATTERN = re.compile(r"^[0-9]+[a-z]*$")
SPRINT_PATTERN = re.compile(r"^[0-9]+[a-z]*\.[0-9]+[a-z]*$")


class QAAgent(BaseModel):
    """QA agent configuration."""

    model_config = ConfigDict(strict=True)

    agent_path: str = Field(..., description="Path to QA agent file")
    model: str = Field(..., description="Model for QA agent")
    prompt: str = Field(..., description="Prompt for QA agent")
    input_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON Schema for QA input"
    )
    output_schema: Dict[str, Any] = Field(..., description="JSON Schema for QA output")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model is one of the allowed values."""
        if v not in VALID_MODELS:
            raise ValueError(
                f"model must be one of {VALID_MODELS}, got: {v}"
            )
        return v

    @field_validator("output_schema")
    @classmethod
    def validate_output_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output schema has required fields."""
        properties = v.get("properties", {})

        # Check for status field
        if "status" not in properties:
            raise ValueError("output_schema must have 'status' property")

        # Check status enum if present
        status_prop = properties["status"]
        if "enum" in status_prop:
            status_enum = status_prop["enum"]
            if not all(s in VALID_QA_STATUS for s in status_enum):
                raise ValueError(
                    f"status enum must only contain {VALID_QA_STATUS}, got: {status_enum}"
                )

        # Check for message field
        if "message" not in properties:
            raise ValueError("output_schema must have 'message' property")

        return v


class DevExecution(BaseModel):
    """Dev execution tracking."""

    model_config = ConfigDict(strict=True)

    attempt: int = Field(..., description="Attempt number (1, 2, 3...)")
    session_id: str = Field(..., description="Claude session ID")
    agent_path: str = Field(..., description="Path to dev agent")
    model: str = Field(..., description="Model used for dev agent")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    status: str = Field(..., description="Execution status")
    feedback_from_qa: Optional[str] = Field(
        None, description="QA feedback if this was a retry"
    )

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model is one of the allowed values."""
        if v not in VALID_MODELS:
            raise ValueError(
                f"model must be one of {VALID_MODELS}, got: {v}"
            )
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of the allowed values."""
        if v not in VALID_DEV_EXECUTION_STATUS:
            raise ValueError(
                f"status must be one of {VALID_DEV_EXECUTION_STATUS}, got: {v}"
            )
        return v

    @field_validator("attempt")
    @classmethod
    def validate_attempt(cls, v: int) -> int:
        """Validate attempt is positive."""
        if v < 1:
            raise ValueError("attempt must be >= 1")
        return v


class QAExecution(BaseModel):
    """QA execution tracking."""

    model_config = ConfigDict(strict=True)

    attempt: int = Field(..., description="Which dev attempt this validated")
    session_id: str = Field(..., description="Claude session ID")
    agent_path: str = Field(..., description="Path to QA agent")
    model: str = Field(..., description="Model used for QA agent")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    status: str = Field(..., description="QA status")
    message: str = Field(..., description="QA message")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific result details"
    )

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model is one of the allowed values."""
        if v not in VALID_MODELS:
            raise ValueError(
                f"model must be one of {VALID_MODELS}, got: {v}"
            )
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of the allowed values."""
        if v not in VALID_QA_STATUS:
            raise ValueError(
                f"status must be one of {VALID_QA_STATUS}, got: {v}"
            )
        return v

    @field_validator("attempt")
    @classmethod
    def validate_attempt(cls, v: int) -> int:
        """Validate attempt is positive."""
        if v < 1:
            raise ValueError("attempt must be >= 1")
        return v


class QAResult(BaseModel):
    """QA result summary in scrum result."""

    model_config = ConfigDict(strict=True)

    agent_path: str = Field(..., description="Path to QA agent")
    status: str = Field(..., description="QA status")
    message: str = Field(..., description="QA message")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific result details"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of the allowed values."""
        if v not in VALID_QA_STATUS:
            raise ValueError(
                f"status must be one of {VALID_QA_STATUS}, got: {v}"
            )
        return v


class ScrumResult(BaseModel):
    """Scrum-master result."""

    model_config = ConfigDict(strict=True)

    bead_id: str = Field(..., description="Bead ID being worked on")
    success: bool = Field(..., description="Overall success status")
    pr_url: Optional[str] = Field(None, description="PR URL if created")
    pr_number: Optional[int] = Field(None, description="PR number if created")
    bead_updated: bool = Field(..., description="Whether bead status was updated")
    attempt_count: int = Field(..., description="Final retry attempt count")
    qa_results: List[QAResult] = Field(
        default_factory=list, description="Results from all QA agents"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    fatal: bool = Field(..., description="If true, stop ralph loop")

    @field_validator("attempt_count")
    @classmethod
    def validate_attempt_count(cls, v: int) -> int:
        """Validate attempt_count is non-negative."""
        if v < 0:
            raise ValueError("attempt_count must be >= 0")
        return v


class BeadMetadata(BaseModel):
    """Extended metadata for beads-ralph."""

    model_config = ConfigDict(strict=True)

    # Work identification
    rig: str = Field(..., description="Repository identifier (e.g., 'beads-ralph')")
    worktree_path: str = Field(..., description="Absolute path to worktree on disk")
    branch: str = Field(..., description="Branch name for this work")
    source_branch: str = Field(..., description="Branch to create worktree from")
    phase: str = Field(..., description="Phase number")
    sprint: str = Field(..., description="Sprint number")

    # Plan tracking
    plan_file: str = Field(..., description="Path to original plan file")
    plan_section: str = Field(..., description="Section identifier in plan")
    plan_sprint_id: str = Field(..., description="Sprint ID as written in plan")

    # Merge-specific (optional, only for merge beads)
    branches_to_merge: Optional[List[str]] = Field(
        None, description="Branches to merge (merge beads only)"
    )

    # Dev agent configuration
    dev_agent_path: str = Field(..., description="Path to dev agent")
    dev_model: str = Field(..., description="Model for dev agent")
    dev_prompts: List[str] = Field(..., description="Array of prompts for dev agent")

    # QA agent configuration
    qa_agents: List[QAAgent] = Field(..., description="Array of QA agent specifications")

    # Retry logic
    max_retry_attempts: int = Field(
        default=3, description="Maximum dev/QA retry loop iterations"
    )
    attempt_count: int = Field(default=0, description="Current retry attempt count")

    # Agent execution tracking
    scrum_master_session_id: Optional[str] = Field(
        None, description="Claude session ID of scrum-master"
    )
    dev_agent_session_id: Optional[str] = Field(
        None, description="Claude session ID of dev agent that did the work"
    )
    dev_agent_executions: List[DevExecution] = Field(
        default_factory=list, description="History of all dev agent execution attempts"
    )
    qa_agent_executions: List[QAExecution] = Field(
        default_factory=list, description="History of all QA agent executions"
    )

    # Output tracking
    pr_url: Optional[str] = Field(None, description="GitHub PR URL")
    pr_number: Optional[int] = Field(None, description="GitHub PR number")
    scrum_result: Optional[ScrumResult] = Field(
        None, description="Final result from scrum-master"
    )

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        """Validate phase matches pattern."""
        if not PHASE_PATTERN.match(v):
            raise ValueError(
                f"phase must match pattern ^[0-9]+[a-z]*$, got: {v}"
            )
        return v

    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v: str) -> str:
        """Validate sprint matches pattern."""
        if not SPRINT_PATTERN.match(v):
            raise ValueError(
                f"sprint must match pattern ^[0-9]+[a-z]*\\.[0-9]+[a-z]*$, got: {v}"
            )
        return v

    @field_validator("dev_model")
    @classmethod
    def validate_dev_model(cls, v: str) -> str:
        """Validate dev_model is one of the allowed values."""
        if v not in VALID_MODELS:
            raise ValueError(
                f"dev_model must be one of {VALID_MODELS}, got: {v}"
            )
        return v

    @field_validator("dev_prompts")
    @classmethod
    def validate_dev_prompts(cls, v: List[str]) -> List[str]:
        """Validate dev_prompts is non-empty."""
        if not v:
            raise ValueError("dev_prompts must be non-empty array")
        return v

    @field_validator("qa_agents")
    @classmethod
    def validate_qa_agents(cls, v: List[QAAgent]) -> List[QAAgent]:
        """Validate qa_agents is non-empty."""
        if not v:
            raise ValueError("qa_agents must be non-empty array")
        return v

    @field_validator("max_retry_attempts")
    @classmethod
    def validate_max_retry_attempts(cls, v: int) -> int:
        """Validate max_retry_attempts is positive."""
        if v < 1:
            raise ValueError("max_retry_attempts must be >= 1")
        return v

    @field_validator("attempt_count")
    @classmethod
    def validate_attempt_count(cls, v: int) -> int:
        """Validate attempt_count is non-negative."""
        if v < 0:
            raise ValueError("attempt_count must be >= 0")
        return v


class Bead(BaseModel):
    """Complete bead model."""

    model_config = ConfigDict(strict=True)

    # Core bead fields (standard beads schema)
    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Work item title")
    description: str = Field(..., description="Detailed description")
    status: str = Field(..., description="Bead status")
    priority: int = Field(..., description="Priority (0-4)")
    issue_type: str = Field(..., description="Issue type")
    assignee: str = Field(..., description="Assignee")
    owner: Optional[str] = Field(None, description="Creator/owner")
    dependencies: List[str] = Field(
        default_factory=list, description="Dependency relationships"
    )
    labels: List[str] = Field(default_factory=list, description="Tags")
    comments: List[Dict[str, Any]] = Field(
        default_factory=list, description="Dev/QA interaction history"
    )
    metadata: BeadMetadata = Field(..., description="Extended beads-ralph metadata")
    external_ref: Optional[str] = Field(None, description="PR URL after creation")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    closed_at: Optional[datetime] = Field(None, description="Completion time")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is non-empty."""
        if not v.strip():
            raise ValueError("title must be non-empty")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of the allowed values."""
        if v not in VALID_STATUS:
            raise ValueError(
                f"status must be one of {VALID_STATUS}, got: {v}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority is in range 0-4."""
        if v < 0 or v > 4:
            raise ValueError("priority must be between 0 and 4")
        return v

    @field_validator("issue_type")
    @classmethod
    def validate_issue_type(cls, v: str) -> str:
        """Validate issue_type is one of the allowed values."""
        if v not in VALID_ISSUE_TYPES:
            raise ValueError(
                f"issue_type must be one of {VALID_ISSUE_TYPES}, got: {v}"
            )
        return v

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, v: str) -> str:
        """Validate assignee is beads-ralph-scrum-master."""
        if v != "beads-ralph-scrum-master":
            raise ValueError(
                f"assignee must be 'beads-ralph-scrum-master', got: {v}"
            )
        return v

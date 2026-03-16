"""
Pydantic schemas for request / response validation.
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"

class BugCategory(str, Enum):
    LOGIC_ERROR        = "logic_error"
    NULL_REFERENCE     = "null_reference"
    MEMORY_LEAK        = "memory_leak"
    SECURITY_VULN      = "security_vulnerability"
    PERFORMANCE        = "performance"
    RACE_CONDITION     = "race_condition"
    EXCEPTION_HANDLING = "exception_handling"
    TYPE_MISMATCH      = "type_mismatch"
    DEAD_CODE          = "dead_code"
    DEPENDENCY_ISSUE   = "dependency_issue"

class AnalysisStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


# ── Request schemas ────────────────────────────────────────────────────────────

class RepoAnalysisRequest(BaseModel):
    repo_url: Optional[HttpUrl] = Field(None, description="Public GitHub/GitLab repo URL")
    branch: str = Field("main", description="Branch to analyse")
    focus_paths: Optional[List[str]] = Field(
        None, description="Specific file paths or globs to focus on"
    )
    ignore_paths: Optional[List[str]] = Field(
        None, description="Paths to exclude from analysis"
    )
    max_files: int = Field(200, ge=1, le=1000)
    language_hint: Optional[str] = None

    @validator("repo_url", pre=True, always=True)
    def validate_repo_url(cls, v):
        if v and "github.com" not in str(v) and "gitlab.com" not in str(v):
            raise ValueError("Only GitHub and GitLab repositories are supported.")
        return v


class InlineCodeRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    language: Optional[str] = None


# ── Response schemas ───────────────────────────────────────────────────────────

class FileInfo(BaseModel):
    path: str
    language: str
    lines: int
    size_bytes: int


class BugFinding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    severity: Severity
    category: BugCategory
    title: str
    description: str
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    references: List[str] = []


class AnalysisSummary(BaseModel):
    total_files_scanned: int
    total_lines_scanned: int
    total_bugs_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    languages_detected: List[str]
    analysis_duration_seconds: float


class AnalysisReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: AnalysisStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    repo_url: Optional[str] = None
    branch: Optional[str] = None
    summary: Optional[AnalysisSummary] = None
    findings: List[BugFinding] = []
    files_scanned: List[FileInfo] = []
    raw_llm_analysis: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True


class AnalysisJobResponse(BaseModel):
    """Returned immediately when a job is submitted (async flow)."""
    job_id: str
    status: AnalysisStatus
    message: str
    poll_url: str


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

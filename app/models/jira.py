"""Pydantic models for Jira issues (Capability / Epic / Story hierarchy)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JiraIssue(BaseModel):
    """Represents a Jira issue pulled for EVM visualization."""

    key: str = Field(..., description="Jira issue key e.g. PROJ-1234")
    summary: str
    issuetype: str = Field(..., description="Capability, Epic, Story, etc.")
    status: str
    assignee: Optional[str] = None

    # Custom fields we care about
    ims_id: Optional[str] = Field(None, description="Matches to IMSTask.ims_id")
    forecast_start: Optional[datetime] = None
    forecast_finish: Optional[datetime] = None

    # Hierarchy pointers
    parent_key: Optional[str] = None

    # For tree display
    level: int = Field(default=0, description="0=Capability, 1=Epic, 2=Story")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
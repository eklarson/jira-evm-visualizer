"""Pydantic models for Microsoft Project IMS data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IMSTask(BaseModel):
    """Represents a single task from the Microsoft Project IMS XML export."""

    uid: str = Field(..., description="Unique identifier in MS Project")
    id: str = Field(..., description="Task ID (WBS number often)")
    name: str = Field(..., description="Task name")
    outline_level: int = Field(..., description="WBS hierarchy level")
    is_summary: bool = Field(default=False)
    start: Optional[datetime] = None
    finish: Optional[datetime] = None
    baseline_start: Optional[datetime] = None
    baseline_finish: Optional[datetime] = None
    percent_complete: float = Field(default=0.0)

    # Custom fields resolved by the parser
    ims_id: Optional[str] = Field(
        None, description="The key field used to match to Jira (e.g. 'IMS-2001')"
    )
    control_account: Optional[str] = None
    work_package: Optional[str] = None

    # Dependency data (enriched)
    predecessors: list[str] = Field(default_factory=list, description="List of IMS IDs")
    successors: list[str] = Field(default_factory=list, description="List of IMS IDs")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

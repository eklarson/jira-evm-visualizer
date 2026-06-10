"""Combined models that merge IMS schedule data with Jira issue data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScheduleVariance(BaseModel):
    """Calculated schedule variance metrics."""

    start_variance_days: Optional[int] = None
    finish_variance_days: Optional[int] = None
    is_on_track: bool = True


class CombinedTask(BaseModel):
    """
    The unified view of a work item.
    This is what gets sent to the frontend for the AG-Grid.
    """

    # Identity
    id: str = Field(..., description="Composite ID e.g. 'CAP-123' or 'IMS-2001'")
    name: str
    level: int = Field(..., description="0=Capability, 1=Epic, 2=Story")
    parent_id: Optional[str] = None

    # Source system
    jira_key: Optional[str] = None
    ims_uid: Optional[str] = None
    ims_id: Optional[str] = None

    # Dates (merged, with IMS taking precedence for schedule)
    baseline_start: Optional[datetime] = None
    baseline_finish: Optional[datetime] = None
    forecast_start: Optional[datetime] = None
    forecast_finish: Optional[datetime] = None

    # Progress
    percent_complete: float = 0.0
    status: str = "Unknown"

    # EVM / Variance
    schedule_variance: Optional[ScheduleVariance] = None

    # Hierarchy helpers for AG-Grid tree data
    children_count: int = 0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class HierarchyNode(BaseModel):
    """Tree structure returned by the API (used by AG-Grid tree data mode)."""

    data: CombinedTask
    children: list["HierarchyNode"] = Field(default_factory=list)

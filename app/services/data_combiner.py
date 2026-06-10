"""
Data Combiner Service

Merges IMS schedule data with Jira hierarchy using IMS ID as the join key.
Produces the tree structure expected by the AG-Grid frontend.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

from app.models.combined import CombinedTask, HierarchyNode, ScheduleVariance
from app.models.ims import IMSTask
from app.models.jira import JiraIssue

logger = logging.getLogger(__name__)


class DataCombinerService:
    """Combines IMS and Jira data into a unified hierarchical view."""

    def __init__(self):
        self.last_refresh: Optional[datetime] = None
        self._cached_tree: Optional[list[HierarchyNode]] = None

    def combine(
        self,
        ims_tasks: list[IMSTask],
        jira_issues: list[JiraIssue],
    ) -> list[HierarchyNode]:
        """
        Main entry point. Returns a tree ready for AG-Grid tree data mode.
        """
        logger.info(
            f"Combining {len(ims_tasks)} IMS tasks with {len(jira_issues)} Jira issues"
        )

        # Index by IMS ID for joining
        ims_by_ims_id: dict[str, IMSTask] = {t.ims_id: t for t in ims_tasks if t.ims_id}

        # Also index Jira by key for parent relationships
        jira_by_key: dict[str, JiraIssue] = {j.key: j for j in jira_issues}

        combined_map: dict[str, CombinedTask] = {}

        # First pass: create CombinedTask from Jira issues (they define the hierarchy)
        for jira_issue in jira_issues:
            key = jira_issue.ims_id or jira_issue.key
            ims_task = (
                ims_by_ims_id.get(jira_issue.ims_id) if jira_issue.ims_id else None
            )

            combined = CombinedTask(
                id=key,
                name=jira_issue.summary,
                level=jira_issue.level,
                parent_id=jira_issue.parent_key,
                jira_key=jira_issue.key,
                ims_id=jira_issue.ims_id,
                ims_uid=ims_task.uid if ims_task else None,
                baseline_start=ims_task.baseline_start if ims_task else None,
                baseline_finish=ims_task.baseline_finish if ims_task else None,
                forecast_start=jira_issue.forecast_start
                or (ims_task.start if ims_task else None),
                forecast_finish=jira_issue.forecast_finish
                or (ims_task.finish if ims_task else None),
                percent_complete=ims_task.percent_complete if ims_task else 0.0,
                status=jira_issue.status,
                schedule_variance=self._calculate_variance(ims_task),
            )
            combined_map[key] = combined

        # Second pass: add pure IMS tasks that have no Jira counterpart (orphans)
        for ims in ims_tasks:
            if ims.ims_id and ims.ims_id not in combined_map:
                combined_map[ims.ims_id] = CombinedTask(
                    id=ims.ims_id,
                    name=ims.name,
                    level=ims.outline_level,
                    jira_key=None,
                    ims_id=ims.ims_id,
                    ims_uid=ims.uid,
                    baseline_start=ims.baseline_start,
                    baseline_finish=ims.baseline_finish,
                    forecast_start=ims.start,
                    forecast_finish=ims.finish,
                    percent_complete=ims.percent_complete,
                    schedule_variance=self._calculate_variance(ims),
                )

        # Build tree structure
        tree = self._build_tree(list(combined_map.values()), jira_by_key)
        self._cached_tree = tree
        self.last_refresh = datetime.utcnow()

        return tree

    def _calculate_variance(
        self, ims_task: Optional[IMSTask]
    ) -> Optional[ScheduleVariance]:
        if not ims_task or not ims_task.baseline_start or not ims_task.start:
            return None

        start_var = (
            (ims_task.start - ims_task.baseline_start).days
            if ims_task.start and ims_task.baseline_start
            else None
        )
        finish_var = (
            (ims_task.finish - ims_task.baseline_finish).days
            if ims_task.finish and ims_task.baseline_finish
            else None
        )

        return ScheduleVariance(
            start_variance_days=start_var,
            finish_variance_days=finish_var,
            is_on_track=(start_var or 0) <= 0 and (finish_var or 0) <= 0,
        )

    def _build_tree(
        self,
        items: list[CombinedTask],
        jira_by_key: dict[str, JiraIssue],
    ) -> list[HierarchyNode]:
        """Convert flat list into nested tree structure."""
        children_map: dict[Optional[str], list[CombinedTask]] = defaultdict(list)

        for item in items:
            parent = item.parent_id
            children_map[parent].append(item)

        def build_node(item: CombinedTask) -> HierarchyNode:
            node = HierarchyNode(data=item)
            for child in children_map.get(item.id, []):
                node.children.append(build_node(child))
            item.children_count = len(node.children)
            return node

        # Roots are items with no parent or parent not in the dataset
        roots = [
            item
            for item in items
            if not item.parent_id or item.parent_id not in {i.id for i in items}
        ]
        return [build_node(r) for r in roots]

    def get_cached_tree(self) -> Optional[list[HierarchyNode]]:
        return self._cached_tree

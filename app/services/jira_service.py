"""
Jira Service

Responsible for fetching Capability → Epic → Story hierarchy from Jira
and enriching with custom fields (especially IMS ID, Forecast dates).
"""
import logging
from typing import Optional

from app.models.jira import JiraIssue

logger = logging.getLogger(__name__)


class JiraService:
    """
    Placeholder / skeleton for Jira integration.

    In a real implementation you would:
    - Use the jira-integration-wrapper (recommended)
    - Or direct Jira REST API with httpx + JQL
    - Cache results
    """

    def __init__(self, jira_client=None):
        self.client = jira_client  # Will be your existing wrapper

    async def fetch_hierarchy(self, project_key: Optional[str] = None) -> list[JiraIssue]:
        """
        Fetch Capability → Epic → Story hierarchy.

        This is a stub that returns sample data for now.
        Replace with real Jira calls.
        """
        logger.warning("JiraService is using stub data. Implement real integration.")

        # TODO: Replace with real data from Jira
        sample = [
            JiraIssue(
                key="PROJ-100",
                summary="Satellite Program Capability",
                issuetype="Capability",
                status="In Progress",
                ims_id="IMS-1001",
                level=0,
            ),
            JiraIssue(
                key="PROJ-101",
                summary="Requirements Definition Epic",
                issuetype="Epic",
                status="Done",
                parent_key="PROJ-100",
                ims_id="IMS-2001",
                level=1,
            ),
            JiraIssue(
                key="PROJ-102",
                summary="Define system requirements",
                issuetype="Story",
                status="Done",
                parent_key="PROJ-101",
                level=2,
            ),
        ]
        return sample

    async def refresh(self) -> list[JiraIssue]:
        """Force refresh from Jira."""
        return await self.fetch_hierarchy()
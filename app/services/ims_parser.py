"""
IMS Parser Service

Adapted from the proven MSProjectXMLParser in jira-evm-pipeline.
This version returns strongly-typed Pydantic models and is designed
to be called from FastAPI background tasks / refresh endpoints.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.ims import IMSTask

logger = logging.getLogger(__name__)


class IMSParserService:
    """Service responsible for parsing Microsoft Project XML exports."""

    def __init__(self):
        self._ns: str = ""
        self.custom_field_map: dict[str, dict] = {}
        self.uid_to_ims_id: dict[str, str] = {}

    def _get_ns_tag(self, tag: str) -> str:
        if self._ns:
            return f"{{{self._ns}}}{tag}"
        return tag

    def parse(self, xml_path: Path | str) -> list[IMSTask]:
        """Parse an MS Project XML file and return typed IMSTask objects."""
        xml_path = Path(xml_path)
        if not xml_path.exists():
            raise FileNotFoundError(f"IMS XML file not found: {xml_path}")

        logger.info(f"Parsing IMS XML: {xml_path.name}")
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Detect namespace (Microsoft Project uses a default namespace)
        tag = root.tag
        self._ns = tag[1 : tag.index("}")] if tag.startswith("{") else ""

        self._build_custom_field_map(root)
        tasks = self._parse_tasks(root)

        logger.info(f"Successfully parsed {len(tasks)} tasks from IMS")
        return tasks

    def _build_custom_field_map(self, root: ET.Element) -> None:
        """Build FieldID -> display name mapping."""
        self.custom_field_map = {}
        extended = root.find(self._get_ns_tag("ExtendedAttributes"))
        if extended is None:
            logger.warning("No ExtendedAttributes section found in XML")
            return

        for ea in extended.findall(self._get_ns_tag("ExtendedAttribute")):
            field_id = ea.findtext(self._get_ns_tag("FieldID"))
            alias = ea.findtext(self._get_ns_tag("Alias")) or ""
            field_name = ea.findtext(self._get_ns_tag("FieldName")) or ""

            if field_id:
                self.custom_field_map[field_id] = {
                    "display_name": alias or field_name,
                    "field_name": field_name,
                }

        logger.info(f"Discovered {len(self.custom_field_map)} custom fields")

    def _get_display_name(self, field_id: str) -> str:
        info = self.custom_field_map.get(field_id, {})
        return info.get("display_name", f"Unknown_{field_id}")

    def _parse_tasks(self, root: ET.Element) -> list[IMSTask]:
        tasks_element = root.find(self._get_ns_tag("Tasks"))
        if tasks_element is None:
            return []

        raw_tasks: list[dict] = []

        for task_elem in tasks_element.findall(self._get_ns_tag("Task")):
            task = self._parse_single_task(task_elem)
            if task:
                raw_tasks.append(task)

        # Build UID -> IMS ID map
        self.uid_to_ims_id = {
            t["uid"]: t["ims_id"] for t in raw_tasks if t.get("ims_id")
        }

        # Enrich with predecessor IMS IDs
        for task in raw_tasks:
            self._enrich_predecessors(task)

        # Convert to Pydantic models
        return [IMSTask(**t) for t in raw_tasks]

    def _parse_single_task(self, elem: ET.Element) -> Optional[dict]:
        def get_text(tag: str) -> Optional[str]:
            val = elem.findtext(self._get_ns_tag(tag))
            return val.strip() if val else None

        uid = get_text("UID")
        if not uid:
            return None

        # Standard fields
        data = {
            "uid": uid,
            "id": get_text("ID") or uid,
            "name": get_text("Name") or "Unnamed Task",
            "outline_level": int(get_text("OutlineLevel") or 0),
            "is_summary": get_text("IsSummary") in ("1", "true"),
            "start": self._parse_date(get_text("Start")),
            "finish": self._parse_date(get_text("Finish")),
            "baseline_start": self._parse_date(get_text("BaselineStart")),
            "baseline_finish": self._parse_date(get_text("BaselineFinish")),
            "percent_complete": float(get_text("PercentComplete") or 0),
        }

        # Custom fields
        custom_fields: dict[str, str] = {}
        for ext in elem.findall(self._get_ns_tag("ExtendedAttribute")):
            fid = ext.findtext(self._get_ns_tag("FieldID"))
            val = ext.findtext(self._get_ns_tag("Value"))
            if fid and val:
                name = self._get_display_name(fid)
                custom_fields[name] = val.strip()

        data["ims_id"] = custom_fields.get("IMS ID")
        data["control_account"] = custom_fields.get("Control Account")
        data["work_package"] = custom_fields.get("Work Package")

        # Predecessor links (raw)
        pred_links = []
        for pl in elem.findall(self._get_ns_tag("PredecessorLink")):
            puid = pl.findtext(self._get_ns_tag("PredecessorUID"))
            if puid:
                pred_links.append({"uid": puid})
        data["_raw_predecessor_uids"] = pred_links

        return data

    def _enrich_predecessors(self, task: dict) -> None:
        """Resolve predecessor UIDs to IMS IDs."""
        resolved = []
        for link in task.get("_raw_predecessor_uids", []):
            uid = link["uid"]
            if uid in self.uid_to_ims_id:
                resolved.append(self.uid_to_ims_id[uid])
        task["predecessors"] = resolved
        # We don't have successors in this XML format easily

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            # Microsoft Project often uses ISO format with T
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

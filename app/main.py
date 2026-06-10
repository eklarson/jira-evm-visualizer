"""
jira-evm-visualizer - FastAPI Application

Main entry point. Provides:
- REST API for combined IMS + Jira data
- Prometheus /metrics endpoint
- Static frontend (AG-Grid dashboard)
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.routers import data, metrics as metrics_router
from app.services.data_combiner import DataCombinerService
from app.services.ims_parser import IMSParserService
from app.services.jira_service import JiraService
from app.services.metrics import app_info, record_refresh, update_task_counts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-evm-visualizer")

# Global services (simple DI for now)
ims_parser = IMSParserService()
jira_service = JiraService()
combiner = DataCombinerService()

# Path to static files
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown."""
    logger.info("Starting jira-evm-visualizer")
    app_info.info({"version": "0.1.0", "component": "jira-evm-visualizer"})

    # Optional: load sample data on startup for demo purposes
    # await refresh_all_data()

    yield
    logger.info("Shutting down jira-evm-visualizer")


app = FastAPI(
    title="Jira EVM Visualizer",
    description="Hierarchical view of IMS schedule data combined with Jira issues",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS (useful during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics (standard location)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Mount static frontend
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Include routers
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(metrics_router.router, prefix="/api/v1", tags=["metrics"])


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Serve the main AG-Grid dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>jira-evm-visualizer</h1><p>Frontend not built yet. Visit <a href='/docs'>/docs</a></p>"


async def refresh_all_data(ims_path: str | None = None):
    """Background task to refresh both IMS and Jira data."""
    start = time.time()

    ims_tasks = []
    jira_issues = []

    # 1. Load IMS data (if path provided)
    if ims_path:
        try:
            ims_tasks = ims_parser.parse(ims_path)
            record_refresh("ims", time.time() - start)
            logger.info(f"Loaded {len(ims_tasks)} tasks from IMS XML")
        except Exception as exc:
            logger.exception("Failed to parse IMS XML: %s", exc)

    # 2. Load Jira data
    start_jira = time.time()
    try:
        jira_issues = await jira_service.fetch_hierarchy()
        record_refresh("jira", time.time() - start_jira)
        logger.info(f"Loaded {len(jira_issues)} issues from Jira")
    except Exception as exc:
        logger.exception("Failed to fetch Jira data: %s", exc)

    # 3. Combine (protected)
    try:
        start_combine = time.time()
        tree = combiner.combine(ims_tasks, jira_issues)
        update_task_counts(tree)
        record_refresh("combined", time.time() - start_combine)
        logger.info("Data refresh complete. %d root nodes in hierarchy.", len(tree))
    except Exception as exc:
        logger.exception("Failed to combine IMS + Jira data: %s", exc)


@app.post("/api/v1/refresh", status_code=202)
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    ims_path: str | None = None,
):
    """
    Trigger a full data refresh.

    If no ims_path is provided, it will try to use the sample from the sibling
    jira-evm-pipeline project (great for demos).
    """
    if ims_path is None:
        # 1. Check environment variable (best for Docker / configured environments)
        env_path = os.environ.get("IMS_XML_PATH")
        if env_path and Path(env_path).exists():
            ims_path = env_path
            logger.info(f"Using IMS_XML_PATH from environment: {ims_path}")
        else:
            # 2. Fall back to sibling project sample (good for local non-Docker dev)
            default_sample = (
                Path(__file__).parent.parent.parent
                / "jira-evm-pipeline/tests/fixtures/sample_ims_export.xml"
            )
            if default_sample.exists():
                ims_path = str(default_sample)
                logger.info(f"Using default sample IMS file: {ims_path}")

    background_tasks.add_task(refresh_all_data, ims_path)
    return {"status": "refresh_scheduled", "ims_path_used": ims_path}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

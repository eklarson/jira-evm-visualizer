"""Additional metrics-related endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics/status")
async def metrics_status():
    """Simple status endpoint for the metrics system."""
    return {
        "status": "ok",
        "message": "Prometheus metrics available at /metrics",
        "available_metrics": [
            "evm_tasks_total",
            "evm_schedule_variance_days",
            "evm_schedule_on_track_ratio",
            "evm_data_refresh_total",
            "evm_data_refresh_duration_seconds",
        ],
    }
"""
Prometheus Metrics for EVM Visualizer

Exposes business-relevant metrics that can be scraped by Prometheus
and visualized in Grafana.
"""
from prometheus_client import Counter, Gauge, Histogram, Info

# --- Business Metrics ---

# Task counts
tasks_total = Gauge(
    "evm_tasks_total",
    "Total number of tasks in the current dataset",
    ["level", "status"],
)

# Schedule performance
schedule_variance_days = Gauge(
    "evm_schedule_variance_days",
    "Schedule variance in days (positive = behind schedule)",
    ["id", "type"],  # type = start or finish
)

schedule_on_track_ratio = Gauge(
    "evm_schedule_on_track_ratio",
    "Percentage of tasks that are on or ahead of baseline",
)

# Refresh activity
data_refresh_total = Counter(
    "evm_data_refresh_total",
    "Number of times data has been refreshed from IMS or Jira",
    ["source"],  # "ims" or "jira" or "combined"
)

data_refresh_duration = Histogram(
    "evm_data_refresh_duration_seconds",
    "Time taken to refresh and combine data",
    ["source"],
)

# System info
app_info = Info("evm_visualizer", "Information about the running visualizer instance")


def update_task_counts(combined_tree: list) -> None:
    """Update Prometheus gauges from the current combined dataset."""
    # Reset previous values
    tasks_total.clear()

    def walk(nodes):
        for node in nodes:
            level_name = {0: "capability", 1: "epic", 2: "story"}.get(node.data.level, "unknown")
            tasks_total.labels(level=level_name, status=node.data.status).inc()
            if node.children:
                walk(node.children)

    walk(combined_tree)


def record_refresh(source: str, duration_seconds: float) -> None:
    """Record that a refresh occurred."""
    data_refresh_total.labels(source=source).inc()
    data_refresh_duration.labels(source=source).observe(duration_seconds)
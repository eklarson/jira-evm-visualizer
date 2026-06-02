# jira-evm-visualizer

Modern FastAPI + AG-Grid dashboard for visualizing Earned Value Management data by combining Microsoft Project IMS schedules with Jira issue hierarchy.

## Features

- **Hierarchical AG-Grid view** — Capability → Epic → Story with tree expansion
- **IMS + Jira data fusion** using IMS ID as the join key
- **Baseline vs Forecast dates** with schedule variance calculation
- **Prometheus metrics** at `/metrics` (ready for Grafana)
- **Refresh endpoints** for pulling latest IMS XML and Jira data

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload --port 8000
```

Then open http://localhost:8000

## Project Structure

```
app/
├── main.py                 # FastAPI app + lifespan + static mount
├── models/                 # Pydantic models (IMS, Jira, Combined)
├── services/
│   ├── ims_parser.py       # Microsoft Project XML parser (adapted from pipeline)
│   ├── jira_service.py     # Jira integration (stub ready for your wrapper)
│   ├── data_combiner.py    # Merges IMS + Jira into tree structure
│   └── metrics.py          # Prometheus business metrics
├── routers/
│   ├── data.py             # /hierarchy, /flat endpoints
│   └── metrics.py
└── static/
    └── index.html          # AG-Grid Community dashboard
```

## Key Endpoints

| Endpoint                    | Method | Description                          |
|----------------------------|--------|--------------------------------------|
| `/`                        | GET    | Main AG-Grid dashboard               |
| `/api/v1/data/hierarchy`   | GET    | Tree data for the grid               |
| `/api/v1/refresh`          | POST   | Trigger full data refresh            |
| `/metrics`                 | GET    | Prometheus metrics                   |
| `/docs`                    | GET    | Swagger UI                           |

## Connecting Real Data

1. **IMS XML**: Pass a path to your weekly export when calling `/api/v1/refresh?ims_path=/path/to/IMS.xml`
2. **Jira**: Replace the stub in `JiraService` with your `jira-integration-wrapper` or direct REST calls.

## Prometheus / Grafana

Useful metrics exposed:
- `evm_tasks_total`
- `evm_schedule_variance_days`
- `evm_schedule_on_track_ratio`
- `evm_data_refresh_total`
- `evm_data_refresh_duration_seconds`

## Development

```bash
ruff check .
pytest
```

## License

Internal project.
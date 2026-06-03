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
source .venv/bin/activate   # or .venv\Scripts/activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload --port 8000
```

Then open http://localhost:8000

## Monitoring with Prometheus + Grafana

See the dedicated guide: **[GRAFANA_SETUP.md](GRAFANA_SETUP.md)** for full instructions (including why the Docker stack may only show the 3 stub Jira tasks until you mount the IMS sample XML).

### Quick Start with Docker (Recommended)

**On macOS:** First open **Docker Desktop** and wait for the daemon to start.

```bash
docker compose up --build
```

(Use `docker-compose up --build` if you have the legacy version.)

Then visit:

- Visualizer: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (login: admin / admin)

Grafana is pre-configured with:
- Prometheus as data source
- A starter EVM dashboard showing task counts, schedule variance, refresh rates, etc.

See **[GRAFANA_SETUP.md](GRAFANA_SETUP.md)** for full instructions, including a "Verifying Everything is Working" section, port conflict fixes, the `scripts/stop-grafana.sh` helper, and manual setup.

If you see git errors like "not a git repository" or "untracked working tree files would be overwritten", see **GIT_RECOVERY.md** for how to properly connect your local directory to the GitHub repo (https://github.com/eklarson/jira-evm-visualizer). The local files were initially created outside of git during setup.

**Docker note:** The container shows only the 3 stub Jira tasks until you provide the IMS sample XML. Use:

```bash
IMS_XML_HOST_PATH=/path/to/sample_ims_export.xml docker compose up --build
```

See the dedicated "Providing Real IMS Data in Docker" section in GRAFANA_SETUP.md.

### Manual Installation

**On macOS:**

Using Homebrew (recommended for local dev):

```bash
brew install grafana
brew services start grafana
```

Then open http://localhost:3000

**Using Docker (isolated):**

```bash
docker run -d -p 3000:3000 grafana/grafana
```

**Other platforms:**

- Download from https://grafana.com/grafana/download
- Or use your distro's package manager (apt, yum, etc.)

### Setting up Prometheus (if not using docker-compose)

1. Install Prometheus (Homebrew: `brew install prometheus`)
2. Add this job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'jira-evm-visualizer'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
    scrape_interval: 10s
```

3. In Grafana:
   - Add data source → Prometheus → `http://localhost:9090`
   - Import the dashboard from `monitoring/grafana/dashboards/evm-dashboard.json`

## Project Structure

```
app/
├── main.py                 # FastAPI app + lifespan + static mount
├── models/                 # Pydantic models (IMS, Jira, Combined)
├── services/
│   ├── ims_parser.py       # Microsoft Project XML parser (adapted from pipeline)
├── jira_service.py     # Jira integration (stub ready for your wrapper)
├── data_combiner.py    # Merges IMS + Jira into tree structure
├── metrics.py          # Prometheus business metrics
├── routers/
│   ├── data.py             # /hierarchy, /flat endpoints
│   └── metrics.py
└── static/
    └── index.html          # AG-Grid Community dashboard
monitoring/
├── prometheus.yml
└── grafana/                # provisioning and dashboards
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
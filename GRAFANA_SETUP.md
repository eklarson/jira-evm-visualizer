# Connecting Grafana to jira-evm-visualizer

The visualizer exposes Prometheus-compatible metrics at `/metrics`.

## Quickest Way: docker-compose

```bash
cd jira-evm-visualizer
docker-compose up --build
```

This starts three services:
- `visualizer` (your app on port 8000)
- `prometheus` (scrapes the visualizer)
- `grafana` (port 3000, with Prometheus already configured)

Open Grafana: http://localhost:3000

Login: `admin` / `admin`

You should see a pre-provisioned Prometheus data source and an EVM dashboard.

## Manual Setup (Local Development)

### 1. Run the visualizer

```bash
cd jira-evm-visualizer
uvicorn app.main:app --reload
```

Confirm metrics are working:
http://localhost:8000/metrics

### 2. Run Prometheus

Install Prometheus:
```bash
brew install prometheus   # macOS
```

Use the provided config (edit `monitoring/prometheus.yml` for local use):

For local development, change the target to:

```yaml
- job_name: 'jira-evm-visualizer'
  static_configs:
    - targets: ['localhost:8000']
  metrics_path: /metrics
```

Start Prometheus:
```bash
prometheus --config.file=monitoring/prometheus.yml
```

### 3. Add Prometheus to Grafana

1. Open Grafana (http://localhost:3000)
2. Click the gear icon (Configuration) → **Data sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Set the URL:
   - If Prometheus is running in Docker: `http://prometheus:9090`
   - If running locally on host: `http://localhost:9090`
6. Click **Save & test**

### 4. Explore the Metrics

Go to **Explore** and try these queries:

```promql
# Total tasks broken down by hierarchy level
sum(evm_tasks_total) by (level)

# Schedule variance over time
evm_schedule_variance_days

# Percentage of work that is on track
evm_schedule_on_track_ratio

# How often data is being refreshed
rate(evm_data_refresh_total[5m])
```

### 5. Import the Dashboard

1. In Grafana, go to **Dashboards** → **Import**
2. Upload the file: `monitoring/grafana/dashboards/evm-dashboard.json`
3. Select your Prometheus data source
4. Click Import

You should now see panels for task counts, variance, and refresh activity.

## Troubleshooting

- **No data in Grafana**: Make sure Prometheus can reach the visualizer.
  - In Docker: use service name `visualizer:8000`
  - Locally: use `localhost:8000`
- **"Connection refused"**: Check that the visualizer is running and `/metrics` returns data.
- **Docker networking on macOS**: Use `host.docker.internal:8000` if needed in prometheus config.
- **Grafana can't reach Prometheus**: Use the correct URL based on how you started Prometheus.

## Useful Metric Names

From `app/services/metrics.py`:

- `evm_tasks_total{level="capability|epic|story", status="..."}`
- `evm_schedule_variance_days{id="...", type="start|finish"}`
- `evm_schedule_on_track_ratio`
- `evm_data_refresh_total{source="ims|jira|combined"}`
- `evm_data_refresh_duration_seconds{source="..."}`

These are the ones you can graph in Grafana.
# Connecting Grafana to jira-evm-visualizer

The visualizer exposes Prometheus-compatible metrics at `/metrics`.

## Quickest Way: Docker Compose (Recommended)

**Important first step on macOS:** Make sure **Docker Desktop** is running (open the Docker Desktop app from Applications). If the daemon is not running, you will get "Cannot connect to the Docker daemon" errors.

Use the modern Docker Compose plugin (no hyphen):

```bash
cd jira-evm-visualizer
docker compose up --build
```

(If you only have the legacy `docker-compose`, use `docker-compose up --build` instead, but upgrade if possible.)

This starts three services:
- `visualizer` (your app on port 8000)
- `prometheus` (scrapes the visualizer)
- `grafana` (port 3000, with Prometheus already configured)

Open Grafana: http://localhost:3000

Login: `admin` / `admin`

You should see a pre-provisioned Prometheus data source and an EVM dashboard.

> Note: We removed the obsolete `version:` key from docker-compose.yml (it is ignored in modern Compose and just produces a warning).

## Verifying Everything is Working

Once `docker compose up --build` is running:

1. **Check the services**:
   - Visualizer UI: http://localhost:8000 (you should see the AG-Grid dashboard)
   - Grafana: http://localhost:3000 (login admin/admin, look for the "Jira EVM Visualizer" dashboard)
   - Prometheus: http://localhost:9090

2. **Verify Prometheus is scraping the visualizer**:
   - Go to http://localhost:9090/targets
   - Look for the `jira-evm-visualizer` job — it should show "UP" (green).

3. **Query the metrics in Prometheus**:
   - Go to http://localhost:9090/graph
   - Try these queries:
     - `evm_tasks_total`
     - `sum(evm_tasks_total) by (level)`
     - `evm_schedule_variance_days`
     - `evm_schedule_on_track_ratio`

4. **Check Grafana dashboard**:
   - In Grafana, open the imported "Jira EVM Visualizer" dashboard.
   - If panels are empty, try:
     - Changing the time range (top right) to "Last 5 minutes" or "Last 15 minutes"
     - Refresh the dashboard (top right refresh button)
     - Go to Explore and run one of the queries above to confirm Prometheus has data.

5. **Check container logs** (useful for debugging):
   ```bash
   docker compose logs -f visualizer
   docker compose logs -f grafana
   docker compose logs -f prometheus
   ```

6. **Raw metrics endpoint**:
   ```bash
   curl http://localhost:8000/metrics
   ```

If you see data flowing through Prometheus and appearing in Grafana panels, the monitoring stack is working correctly with the visualizer.

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

### Providing Real IMS Data in Docker

By default the container only loads the 3 stub Jira tasks because the sibling `jira-evm-pipeline` sample XML is not available inside the container.

To load the full IMS schedule data:

1. (Recommended) Use an environment variable when starting the stack:

   ```bash
   # Adjust the path to wherever your sample_ims_export.xml lives
   IMS_XML_HOST_PATH=/Users/eklarson/Projects/jira-evm-pipeline/tests/fixtures/sample_ims_export.xml \
     docker compose up --build
   ```

   The compose file uses `${IMS_XML_HOST_PATH:-./sample_ims_export.xml}` so it falls back gracefully.

2. Or copy the sample locally for simpler command:

   ```bash
   cp ../jira-evm-pipeline/tests/fixtures/sample_ims_export.xml ./sample_ims_export.xml
   docker compose up --build
   ```

   The `docker-compose.yml` will mount it and set `IMS_XML_PATH=/samples/sample_ims_export.xml` inside the container.

After starting, the frontend auto-triggers a refresh, and you should see the full hierarchy (many IMS tasks + the Jira-linked ones).

The env var `IMS_XML_PATH` is also respected when running the app directly (outside Docker).

## Troubleshooting

- **No data in Grafana**: Make sure Prometheus can reach the visualizer.
  - In Docker: use service name `visualizer:8000`
  - Locally: use `localhost:8000`
- **"Connection refused"**: Check that the visualizer is running and `/metrics` returns data.
- **Docker networking on macOS**: Use `host.docker.internal:8000` if needed in prometheus config.
- **Grafana can't reach Prometheus**: Use the correct URL based on how you started Prometheus.
- **"Cannot connect to the Docker daemon" (most common on macOS)**: 
  - Open the **Docker Desktop** application (from your Applications folder or Spotlight).
  - Wait for it to fully start (you should see the whale icon in the menu bar and "Docker Desktop is running" ).
  - Then re-run `docker compose up --build`.
  - If it still fails, go to Docker Desktop → Settings → General and make sure "Start Docker Desktop when you log in" is enabled, or restart your Mac.
  - Confirm Docker is running with: `docker info` (should not error).
- **Port 3000 already in use** (this exact error): 
  - This almost always means you previously started Grafana via Homebrew (`brew services start grafana`) or another Docker container.
  - There's a helper script in the project:
    ```bash
    ./scripts/stop-grafana.sh
    ```
    (make it executable first: `chmod +x scripts/stop-grafana.sh`)
  - Manual steps:
    - Stop the Homebrew service first:
      ```bash
      brew services stop grafana
      brew services list | grep grafana   # should show "stopped"
      ```
    - Check what's using the port:
      ```bash
      lsof -i :3000
      ```
    - If it's a Docker container:
      ```bash
      docker ps | grep -i grafana
      docker stop <container-id-or-name>
      ```
    - Then try `docker compose up --build` again.
  - To avoid this in future: don't run both the brew service and the Docker version at the same time. Use only one.

See also GIT_RECOVERY.md in the project root if you are having trouble with `git status` or `git checkout` due to the way the local directory was initially set up (files written directly rather than via `git clone`). It contains step-by-step recovery commands.

## Useful Metric Names

From `app/services/metrics.py`:

- `evm_tasks_total{level="capability|epic|story", status="..."}`
- `evm_schedule_variance_days{id="...", type="start|finish"}`
- `evm_schedule_on_track_ratio`
- `evm_data_refresh_total{source="ims|jira|combined"}`
- `evm_data_refresh_duration_seconds{source="..."}`

These are the ones you can graph in Grafana.
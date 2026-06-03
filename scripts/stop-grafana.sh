#!/bin/bash
# Helper script to stop any existing Grafana instance (brew service or Docker)
# Run from the project root: ./scripts/stop-grafana.sh

echo "Checking for Grafana on port 3000..."
lsof -i :3000 || echo "No process found on port 3000"

echo ""
echo "Stopping Homebrew Grafana service (if running)..."
brew services stop grafana 2>/dev/null || echo "brew services not applicable or not running"
brew services list | grep -i grafana || true

echo ""
echo "Stopping any Docker containers named grafana..."
docker ps --filter "name=grafana" --format "{{.ID}} {{.Names}}" | while read id name; do
  if [ -n "$id" ]; then
    echo "Stopping container $id ($name)..."
    docker stop "$id" || true
  fi
done

echo ""
echo "Done. You can now run: docker compose up --build"
echo "Or manually start Grafana only via Docker if needed."
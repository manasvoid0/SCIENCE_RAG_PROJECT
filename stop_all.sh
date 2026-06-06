#!/bin/bash
# stop_all.sh -- stops the apps started by run_all.sh (by their ports).
# This does NOT stop Ollama itself.

for port in 8000 8001 8500 8501 8502 8503; do
  pids=$(lsof -ti tcp:$port)   # may be more than one process per port
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill 2>/dev/null && echo "Stopped service on port $port"
  fi
done
pkill -f "streamlit run" 2>/dev/null   # catch any stragglers
echo "Done."

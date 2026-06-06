#!/bin/bash
# stop_all.sh -- stops the apps started by run_all.sh (by their ports).
# This does NOT stop Ollama itself.

for port in 8000 8001 8500 8501 8502 8503; do
  pid=$(lsof -ti tcp:$port)   # find the process using each port
  if [ -n "$pid" ]; then
    kill "$pid" && echo "Stopped service on port $port"
  fi
done
echo "Done."

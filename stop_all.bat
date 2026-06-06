@echo off
REM stop_all.bat  --  stop the services started by run_all.bat (by their ports).
REM This does NOT stop the Ollama tray app.

for %%P in (8000 8001 8500 8501 8502 8503) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1 && echo Stopped service on port %%P
  )
)
echo Done.

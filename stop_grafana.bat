@echo off
echo 🛑 Stopping Grafana Dashboard
echo.

echo 🔍 Stopping containers...
docker-compose down

if %errorlevel% neq 0 (
    echo ❌ Error stopping containers
    echo.
    echo 🔍 Attempting force stop...
    docker stop grafana 2>nul
    docker stop prometheus 2>nul
    docker rm grafana 2>nul
    docker rm prometheus 2>nul
)

echo ✅ Containers stopped
echo.

echo 🔍 Checking status...
docker ps -a | findstr grafana
docker ps -a | findstr prometheus

echo.
echo 🚀 To restart use: start_grafana.bat
echo.
pause

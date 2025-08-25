@echo off
echo 🚀 Starting Grafana Dashboard for Courts API
echo.

echo 📋 Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not installed! Install Docker Desktop for Windows
    echo 📥 Download from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo ✅ Docker found
echo.

echo 🔍 Checking Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Desktop not running! Start Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker Desktop running
echo.

echo 🚀 Starting containers...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ❌ Error starting containers
    pause
    exit /b 1
)

echo ✅ Containers started
echo.

echo 📊 Opening dashboards...
timeout /t 3 /nobreak >nul

echo 🌐 Grafana Dashboard: http://localhost:3000
echo    Login: admin
echo    Password: admin123
echo.

echo 📈 Prometheus: http://localhost:9090
echo.

echo 🐍 Don't forget to start your Python API:
echo    cd python\app
echo    python main.py
echo.

echo 🎯 Send several API requests to see metrics
echo.

start http://localhost:3000
start http://localhost:9090

echo 🚀 Monitoring system started!
echo.
pause

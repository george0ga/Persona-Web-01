@echo off
echo 🔍 Checking Grafana Status
echo.

echo 📊 Container Status:
docker ps -a | findstr grafana
docker ps -a | findstr prometheus

echo.
echo 📝 Grafana Logs:
docker logs grafana --tail 20

echo.
echo 📝 Prometheus Logs:
docker logs prometheus --tail 20

echo.
echo 🌐 Port Check:
netstat -an | findstr :3000
netstat -an | findstr :9090

echo.
echo 🎯 Dashboard URLs:
echo Grafana: http://localhost:3000
echo Prometheus: http://localhost:9090

echo.
pause

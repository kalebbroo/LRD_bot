@echo off
echo Building Docker image for LRD Bot...
docker build -t lrd_bot:latest .

echo Starting LRD Bot container...
docker run lrd_bot:latest

pause

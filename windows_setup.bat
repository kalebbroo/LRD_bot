@echo off
echo Building Docker image for LRD Bot...
docker build -t lrd_bot:latest .

echo Starting LRD Bot container...
docker run --name lrd_bot -v %cd%\database:/app/database -v %cd%\showcase:/app/showcase lrd_bot:latest

pause

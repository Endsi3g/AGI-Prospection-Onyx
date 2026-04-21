@echo off
TITLE AGI Prospection Hub Deployment
CLS

echo ==========================================
echo    🚀 AGI PROSPECTION HUB DEPLOYMENT
echo ==========================================

set MODE=%1
if "%MODE%"=="" set MODE=docker

if "%MODE%"=="docker" goto DOCKER
if "%MODE%"=="local" goto LOCAL

:DOCKER
echo 🐳 Starting AGI Prospection in Docker mode...
cd deployment\docker_compose
docker compose up -d
echo.
echo ✅ AGI Prospection is running at http://localhost:3000
goto END

:LOCAL
echo 💻 Starting AGI Prospection in Local mode...
echo (Opening new windows for Backend and Frontend)
start powershell -NoExit -Command "cd backend; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; python main.py"
start powershell -NoExit -Command "cd web; npm install; npm run dev"
echo.
echo ✅ Local development servers triggered.
goto END

:END
echo.
echo ✨ Done!
pause

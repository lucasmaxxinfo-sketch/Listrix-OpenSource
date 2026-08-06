@echo off
title Listrix
echo ============================================
echo  Starting Listrix... keep this window open.
echo ============================================
where docker >nul 2>nul
if errorlevel 1 (
  echo.
  echo  Docker is not installed yet.
  echo  Please install it for free from:  https://www.docker.com/products/docker-desktop
  echo  Then run this file again.
  echo.
  pause
  exit /b 1
)
docker compose up --build
echo.
echo  Listrix stopped. Your data is safe.
pause

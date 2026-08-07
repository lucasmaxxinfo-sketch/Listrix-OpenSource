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
if errorlevel 1 (
  echo.
  echo  ============================================
  echo  [31m Listrix did not start.[0m
  echo  ============================================
  echo.
  echo  The most common fix is giving Docker more memory:
  echo.
  echo  1. Close this window and close other programs.
  echo  2. Open the Docker Desktop app (the whale icon).
  echo  3. Click Settings  -  Resources.
  echo  4. Set Memory to at least 4096 MB (4 GB).
  echo  5. Click Apply  Restart, wait for Docker to be ready.
  echo  6. Run this launcher again.
  echo.
  echo  If it still fails, take a photo of the error above
  echo  and send it - I will fix it for you.
  echo.
  pause
  exit /b 1
)
echo.
echo  Listrix stopped. Your data is safe.
pause

#!/usr/bin/env bash
# Listrix launcher for macOS / Linux. Keep this file inside the Listrix folder.
cd "$(dirname "$0")" || exit 1
echo "============================================"
echo " Starting Listrix... keep this window open."
echo "============================================"
if ! command -v docker >/dev/null 2>&1; then
  echo
  echo " Docker is not installed yet."
  echo " Please install it for free from:  https://www.docker.com/products/docker-desktop"
  echo " Then run this file again."
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi
# Open the browser once the app is up (best effort).
( sleep 10 && (open http://localhost 2>/dev/null || xdg-open http://localhost 2>/dev/null) ) &
docker compose up --build
status=$?
if [ $status -ne 0 ]; then
  echo
  echo "============================================"
  echo " Listrix did not start."
  echo "============================================"
  echo
  echo "The most common fix is giving Docker more memory:"
  echo
  echo "  1. Close this window and close other programs."
  echo "  2. Open the Docker Desktop app (the whale icon)."
  echo "  3. Click Settings  -  Resources."
  echo "  4. Set Memory to at least 4 GB."
  echo "  5. Click Apply & Restart, wait for Docker to be ready."
  echo "  6. Run this launcher again."
  echo
  echo "If it still fails, take a photo of the error above"
  echo "and send it - I will fix it for you."
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi
echo
echo "Listrix stopped. Your data is safe."

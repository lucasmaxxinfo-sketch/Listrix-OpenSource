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
echo
echo "Listrix stopped. Your data is safe."

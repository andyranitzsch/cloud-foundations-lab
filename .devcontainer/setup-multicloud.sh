#!/bin/bash
# Clona los emuladores de GCP y Azure en vendor/ para que el compose pueda buildearlos.
# Corre una sola vez al crear el Codespace (postCreateCommand).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p vendor

clone_if_missing() {
  local url="$1"
  local dest="$2"
  if [[ -d "$dest/.git" ]]; then
    echo "✓ $dest ya existe"
  else
    echo "→ clonando $url..."
    git clone --depth 1 "$url" "$dest"
  fi
}

clone_if_missing "https://github.com/cmarin78/gcp-emulator"        "vendor/gcp-emulator"
clone_if_missing "https://github.com/cmarin78/azure-cloud-emulator" "vendor/azure-emulator"

echo ""
echo "Emuladores listos en vendor/. El compose los buildea al primer 'docker compose up'."

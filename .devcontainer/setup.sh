#!/bin/bash
# Setup del Codespace / devcontainer.
# Corre una sola vez al crear el entorno (postCreateCommand).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "→ Paquetes del sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq postgresql-client

echo "→ OpenTofu (para iac/ y para los hooks de pre-commit)..."
if ! command -v tofu > /dev/null; then
  curl -fsSL https://get.opentofu.org/install-opentofu.sh -o /tmp/install-opentofu.sh
  bash /tmp/install-opentofu.sh --install-method deb >/dev/null
  rm /tmp/install-opentofu.sh
fi
tofu version | head -1

echo "→ Dependencias Python..."
python3 -m pip install --quiet -r requirements.txt

echo "→ Pre-commit hooks..."
pre-commit install --install-hooks

echo "→ .env desde .env.example..."
[[ -f .env ]] || cp .env.example .env

echo ""
echo "Listo. Verificar: tofu version, pre-commit --version, awslocal --version"

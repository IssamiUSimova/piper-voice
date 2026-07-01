#!/usr/bin/env bash
set -e

# Verifica se o Python 3 está instalado
if ! command -v python3 &>/dev/null; then
    echo "[ERRO] Python 3 não encontrado."
    echo "  macOS:  brew install python"
    echo "  Ubuntu: sudo apt install python3 python3-venv"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cria o ambiente virtual na primeira vez
if [ ! -d ".venv" ]; then
    echo "[setup] Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Ativa o ambiente virtual
source .venv/bin/activate

# Instala dependencias se necessario
if ! python -c "import piper" &>/dev/null; then
    echo "[setup] Instalando dependencias..."
    pip install -r requirements.txt
    echo
fi

# Roda o script com os argumentos passados
if [ $# -eq 0 ]; then
    python say.py --demo
else
    python say.py "$@"
fi

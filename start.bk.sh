#!/bin/bash

# Cambia alla directory del progetto (IMPORTANTE per cron)
cd /home/remote/api-citylog

# Attiva l'ambiente virtuale
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Creo ambiente virtuale..."
    uv sync
    source .venv/bin/activate
fi

# Usa il percorso assoluto di uvicorn
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 3000 --reload --log-level debug

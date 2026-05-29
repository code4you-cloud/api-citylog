#!/bin/bash
cd /home/remote/api-citylog

# Verifica che poetry sia disponibile
if ! command -v poetry &> /dev/null; then
    echo "$(date): ERRORE - poetry non trovato"
    exit 1
fi

# Controlla se uvicorn è già in esecuzione
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "$(date): uvicorn già attivo, nessuna azione"
    exit 0
fi

echo "$(date): avvio uvicorn..."

nohup poetry run uvicorn main:app \
    --host 0.0.0.0 \
    --port 3000 \
    --log-level debug \
    >> /var/log/uvicorn-citylog.log 2>&1 &

echo "$(date): uvicorn avviato con PID $!"

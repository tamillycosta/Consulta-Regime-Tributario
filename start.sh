#!/bin/bash

echo "Iniciando Consulta Regime Tributário (FastAPI + React)..."

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo " Criando ambiente virtual Python..."
    python3 -m venv venv
    ./venv/bin/pip install -r api/requirements.txt
fi

# Start Backend FastAPI
echo "⚡ Iniciando API FastAPI em http://localhost:8000..."
PYTHONPATH=api ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend React (Vite)
echo " Iniciando Frontend React em http://localhost:5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "Aplicação iniciada!"
echo " Acesse no navegador: http://localhost:5173"
echo "Pressione Ctrl+C para encerrar."

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait

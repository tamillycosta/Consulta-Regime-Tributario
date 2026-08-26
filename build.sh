#!/usr/bin/env bash
# exit on error
set -o errexit

echo " Instalando dependências do Python..."
python3 -m venv venv
./venv/bin/pip install -r api/requirements.txt

echo "Construindo o Frontend em React..."
cd frontend
npm install
npm run build
cd ..

echo " Build concluído com sucesso!"

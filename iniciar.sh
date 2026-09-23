#!/bin/bash
# Script de inicialização rápida do Sistema de Auditoria Simples Nacional
cd "$(dirname "$0")"

echo "=========================================================="
echo "  🏛️ Sistema de Auditoria Fiscal - Simples Nacional"
echo "=========================================================="

if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv .venv
fi

echo "Ativando ambiente virtual..."
source .venv/bin/activate

echo "Verificando dependências..."
pip install -r requirements.txt -q

echo "Iniciando servidor Streamlit..."
echo "Acesse no navegador: http://localhost:8501"
echo "Pressione Ctrl+C para encerrar."
echo "=========================================================="

streamlit run app.py

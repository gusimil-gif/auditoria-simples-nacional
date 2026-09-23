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

echo "Iniciando servidor e túnel público online..."
echo "=========================================================="
echo "  🔑 CREDENCIAIS MASTER DE ACESSO:"
echo "  Usuário: admin"
echo "  Senha:   Auditoria@2026"
echo "=========================================================="

# Inicia o Streamlit em segundo plano
streamlit run app.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

sleep 2

# Inicia o túnel Cloudflare público se o binário existir
if [ -f "./cloudflared" ]; then
    echo "Iniciando túnel online público (HTTPS seguro)..."
    ./cloudflared tunnel --url http://localhost:8501
else
    echo "Acesse localmente em: http://localhost:8501"
    wait $STREAMLIT_PID
fi

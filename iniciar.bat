@echo off
title Sistema de Auditoria Fiscal - Simples Nacional
cd /d "%~dp0"

echo ==========================================================
echo   Sistema de Auditoria Fiscal - Simples Nacional
echo ==========================================================

if not exist ".venv" (
    echo Criando ambiente virtual Python...
    python -m venv .venv
)

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo Verificando dependencias...
pip install -r requirements.txt -q

echo Iniciando servidor Streamlit...
echo Acesse no navegador: http://localhost:8501
echo ==========================================================

streamlit run app.py
pause

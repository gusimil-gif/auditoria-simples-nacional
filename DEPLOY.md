# 🚀 Guia de Publicação e Hospedagem Gratuita

Este documento ensina como colocar o **Sistema de Auditoria Fiscal e Consulta do Simples Nacional** online em poucos minutos, de forma **100% gratuita**, para que qualquer membro da sua equipe de auditoria contábil/fiscal possa acessar via navegador de qualquer lugar.

---

## Opção 1: Streamlit Community Cloud (Recomendada)
*A forma mais fácil, rápida e sem custo de manter um app Streamlit no ar.*

### Pré-requisitos
- Uma conta no [GitHub](https://github.com) (gratuita).
- Uma conta no [Streamlit Community Cloud](https://share.streamlit.io/) (gratuita, conectada com seu GitHub).

### Passo a Passo
1. **Subir os arquivos para o GitHub:**
   - Crie um novo repositório no seu GitHub (ex.: `auditoria-simples-hileia`). O repositório pode ser **Público** ou **Privado**.
   - No seu terminal, dentro da pasta deste projeto:
     ```bash
     git init
     git add .
     git commit -m "Versao inicial do sistema de auditoria"
     git branch -M main
     git remote add origin https://github.com/SEU_USUARIO/auditoria-simples-hileia.git
     git push -u origin main
     ```
2. **Conectar e Publicar no Streamlit Cloud:**
   - Acesse [share.streamlit.io](https://share.streamlit.io/) e faça login com seu GitHub.
   - Clique no botão **"New app"** (ou **"Create app"**).
   - Preencha os campos:
     - **Repository:** `SEU_USUARIO/auditoria-simples-hileia`
     - **Branch:** `main`
     - **Main file path:** `app.py`
   - Clique em **"Deploy!"**.
3. **Pronto!**
   - Em cerca de 1 a 2 minutos, seu aplicativo estará no ar em uma URL segura com HTTPS como: `https://auditoria-simples-hileia.streamlit.app`.

---

## Opção 2: Hugging Face Spaces (Alternativa 100% Gratuita)
1. Acesse [huggingface.co](https://huggingface.co/) e crie sua conta gratuita.
2. Clique no seu perfil > **New Space**.
3. Escolha um nome para o Space.
4. Em **Space SDK**, selecione **Streamlit**.
5. Selecione a opção **Public** ou **Private** e clique em **Create Space**.
6. Faça o upload dos arquivos ou sincronize via git. O Hugging Face construirá o container automaticamente.

---

## Opção 3: Render (Web Service Gratuito)
1. Crie uma conta no [Render](https://render.com/).
2. Clique em **New +** > **Web Service**.
3. Conecte seu repositório GitHub.
4. Preencha as configurações:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Instance Type:** `Free`
5. Clique em **Deploy Web Service**.

---

## 🔒 Padrões de Segurança e Privacidade (LGPD)

O sistema foi concebido com rigorosos padrões de segurança contábil e fiscal:
1. **Dados Protegidos:** Apenas os 14 dígitos numéricos do CNPJ são enviados para as APIs públicas de consulta da Receita Federal (BrasilAPI e Minha Receita). Nenhum valor financeiro, chave de NFe privada, endereço interno ou informação de produto sai da sua máquina ou do seu servidor.
2. **Sem Vazamento de Dados Pessoais:** O sistema atende à LGPD pois CNPJs são registros de pessoas jurídicas de domínio público. CPFs eventualmente presentes em notas de pessoa física são sanitizados e não enviados.
3. **Expurgo de Cache Sob Demanda:** A barra lateral contém o botão **"Limpar Cache"** e **"Zerar Sessão"**, permitindo expurgar todos os dados da memória imediatamente após finalizar o download do parecer.

---

## 💻 Como Rodar Localmente no seu Computador

Se preferir rodar no seu computador (Mac, Windows ou Linux):

1. Abra o Terminal nesta pasta.
2. Ative o ambiente virtual:
   - **Mac/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
3. Inicie o sistema:
   ```bash
   streamlit run app.py
   ```
4. O navegador abrirá automaticamente em `http://localhost:8501`.

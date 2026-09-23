"""
Aplicação Web Streamlit: Sistema de Auditoria Fiscal e Consulta em Lote de Optantes pelo Simples Nacional.
Permite a importação de planilhas de faturamento/compras, consulta automatizada via APIs da Receita Federal,
emissão de pareceres tributários e exportação em Excel profissional (.xlsx) e CSV.
"""

import os
import time
import io
import pandas as pd
import streamlit as st

from core.validator import formatar_cnpj, validar_cnpj, limpar_cnpj
from core.cache import CNPJCache
from core.api_client import CNPJClient
from core.auditor import emitir_parecer_fiscal, formatar_data_br
from core.processor import carregar_planilha, detectar_coluna_cnpj, processar_lote_cnpjs
from core.exporter import exportar_para_excel, exportar_para_csv
from core.auth import autenticar_usuario, obter_credenciais_master

# Configuração da página Streamlit
st.set_page_config(
    page_title="Auditoria Simples Nacional | Hiléia",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização de estado de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "cache" not in st.session_state:
    st.session_state.cache = CNPJCache()
if "client" not in st.session_state:
    st.session_state.client = CNPJClient(cache=st.session_state.cache, delay_between_requests=0.15)
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "cancel_requested" not in st.session_state:
    st.session_state.cancel_requested = False

# --- TELA DE LOGIN (ACESSO RESTRITO) ---
if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <img src="https://cdn-icons-png.flaticon.com/512/2830/2830284.png" width="85" style="margin-bottom: 10px;" />
            <h1 style="color: #1E3A8A; font-size: 2rem; margin-bottom: 0;">Portal de Auditoria Fiscal</h1>
            <p style="color: #4B5563; font-size: 1.05rem;">Hiléia Alimentos — Verificação do Simples Nacional</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            st.subheader("🔐 Acesso Restrito")
            st.caption("Insira suas credenciais master para acessar o sistema de auditoria.")
            user_input = st.text_input("Usuário Master", placeholder="Ex: admin", value="admin")
            pass_input = st.text_input("Senha Master", type="password", placeholder="Digite sua senha")
            btn_entrar = st.form_submit_button("🚀 Entrar no Sistema", type="primary", use_container_width=True)

            if btn_entrar:
                if autenticar_usuario(user_input, pass_input):
                    st.session_state.authenticated = True
                    st.session_state.usuario_logado = user_input.strip()
                    st.success("Autenticação realizada com sucesso!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Verifique o usuário e a senha informados.")

        creds = obter_credenciais_master()
        st.info(
            f"🔑 **Credenciais Master Configuradas:**\n\n"
            f"- **Usuário:** `{creds['usuario']}`\n"
            f"- **Senha:** `{creds['senha']}`",
            icon="ℹ️"
        )
    st.stop()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=65)
    st.title("Auditoria Fiscal")
    st.caption("Verificação de Optantes pelo Simples Nacional")
    st.markdown("---")

    col_u1, col_u2 = st.columns([2, 1])
    with col_u1:
        st.markdown(f"👤 **{st.session_state.usuario_logado or 'Master'}** *(Master)*")
    with col_u2:
        if st.button("🚪 Sair", help="Encerrar sessão atual"):
            st.session_state.authenticated = False
            st.session_state.usuario_logado = None
            st.session_state.audit_data = None
            st.rerun()

    st.markdown("---")
    st.subheader("⚙️ Configuração das APIs")
    provider_option = st.selectbox(
        "Provedor Primário",
        ["BrasilAPI (Automático + Fallback)", "Minha Receita (RFB)", "ReceitaWS"],
        index=0,
        help="BrasilAPI com transbordo automático para Minha Receita em caso de instabilidade."
    )
    
    speed_option = st.slider(
        "Velocidade das Consultas (Delay)",
        min_value=0.05,
        max_value=0.6,
        value=0.15,
        step=0.05,
        help="Intervalo entre requisições para evitar rate limit de IP."
    )
    st.session_state.client.delay = speed_option

    st.markdown("---")
    st.subheader("🛡️ Segurança & LGPD")
    cache_count = st.session_state.cache.count()
    st.info(f"**Cache Seguro Ativo:** {cache_count} CNPJs salvos localmente.", icon="🔒")
    
    col_limpar1, col_limpar2 = st.columns(2)
    with col_limpar1:
        if st.button("Limpar Cache", help="Exclui os CNPJs armazenados no banco local"):
            st.session_state.cache.clear()
            st.success("Cache zerado!")
            st.rerun()
    with col_limpar2:
        if st.button("Zerar Sessão", help="Remove arquivos e relatórios da memória"):
            st.session_state.audit_data = None
            st.rerun()

    st.markdown("---")
    st.subheader("📖 Manual de Instruções")
    pdf_manual_path = "Manual_Operacao_Auditoria_Simples_Nacional.pdf"
    if os.path.exists(pdf_manual_path):
        with open(pdf_manual_path, "rb") as f_pdf:
            st.download_button(
                label="📥 Baixar Manual em PDF",
                data=f_pdf.read(),
                file_name="Manual_Operacao_Auditoria_Simples_Nacional.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Baixe o manual completo de operação do sistema em PDF (4 páginas)."
            )

    st.markdown("---")
    st.subheader("📁 Amostras de Teste (Hiléia)")
    st.caption("Carregue dados simulados prontos para testar:")
    col_amostra1, col_amostra2 = st.columns(2)
    with col_amostra1:
        if st.button("NF Vendas", help="Notas faturadas pela Hiléia para clientes"):
            p = "sample_data/notas_faturadas_hileia_exemplo.xlsx"
            if os.path.exists(p):
                with open(p, "rb") as f:
                    st.session_state.arquivo_teste = (f.read(), "notas_faturadas_hileia_exemplo.xlsx")
                    st.rerun()
    with col_amostra2:
        if st.button("NF Compras", help="Notas fiscais de compras da Hiléia (fornecedores)"):
            p = "sample_data/notas_compras_hileia_exemplo.xlsx"
            if os.path.exists(p):
                with open(p, "rb") as f:
                    st.session_state.arquivo_teste = (f.read(), "notas_compras_hileia_exemplo.xlsx")
                    st.rerun()


# --- CABEÇALHO PRINCIPAL ---
st.title("🏛️ Sistema de Auditoria e Verificação de Optantes pelo Simples Nacional")
st.markdown(
    "Audite relatórios de **notas fiscais faturadas (clientes)**, **notas de compra (fornecedores)** ou **cadastros gerais** "
    "para validar a opção pelo Simples Nacional, SIMEI, situação cadastral na RFB e emitir parecer fiscal com exportação em lote."
)

# Abas da Aplicação
tab_lote, tab_individual, tab_historico, tab_deploy = st.tabs([
    "📊 Auditoria em Lote (Planilhas)",
    "🔍 Consulta Individual Avulsa",
    "📋 Histórico & Pareceres",
    "🚀 Como Hospedar Grátis"
])


# =========================================================================
# TAB 1: AUDITORIA EM LOTE (PLANILHAS)
# =========================================================================
with tab_lote:
    st.subheader("1. Importar Planilha de Auditoria")
    st.markdown("Faça o upload do seu relatório em formato **Excel (.xlsx, .xls)** ou **CSV (.csv)**.")

    uploaded_file = st.file_uploader(
        "Selecione a planilha para auditoria",
        type=["xlsx", "xls", "csv"],
        help="Pode ser qualquer relatório contendo colunas com CNPJ (Notas fiscais emitidas, recebidas, compras, clientes, etc.)"
    )

    # Se usuário clicou em botão de amostra na sidebar
    bytes_arquivo = None
    nome_arquivo = None
    if uploaded_file is not None:
        bytes_arquivo = uploaded_file.getvalue()
        nome_arquivo = uploaded_file.name
    elif "arquivo_teste" in st.session_state and st.session_state.arquivo_teste:
        bytes_arquivo, nome_arquivo = st.session_state.arquivo_teste
        st.success(f"Carregada planilha de exemplo: **{nome_arquivo}**", icon="📌")

    if bytes_arquivo and nome_arquivo:
        try:
            df_bruto = carregar_planilha(bytes_arquivo, nome_arquivo)
            st.markdown(f"**Arquivo carregado:** `{nome_arquivo}` | **Total de linhas:** `{len(df_bruto):,}`")

            # Detecção inteligente da coluna de CNPJ
            col_detectada, todas_colunas = detectar_coluna_cnpj(df_bruto)
            
            c_col1, c_col2 = st.columns([2, 1])
            with c_col1:
                idx_default = todas_colunas.index(col_detectada) if col_detectada in todas_colunas else 0
                coluna_selecionada = st.selectbox(
                    "Coluna com o CNPJ a ser consultado:",
                    options=todas_colunas,
                    index=idx_default,
                    help="O sistema detectou automaticamente a coluna provável, mas você pode alterar caso necessário."
                )

            with c_col2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                btn_iniciar = st.button("🚀 Iniciar Auditoria em Lote", type="primary", use_container_width=True)

            with st.expander("👁️ Pré-visualizar Primeiras Linhas da Planilha", expanded=False):
                st.dataframe(df_bruto.head(10), use_container_width=True)

            # Execução do Lote
            if btn_iniciar:
                st.session_state.cancel_requested = False
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                cancel_btn_placeholder = st.empty()

                def progress_cb(current, total, cnpj, razao):
                    pct = current / total if total > 0 else 1.0
                    progress_bar.progress(pct)
                    status_text.markdown(
                        f"⏳ **Consultando:** `{formatar_cnpj(cnpj)}` — *{razao[:40]}* ({current}/{total})"
                    )

                def check_cancel():
                    return st.session_state.cancel_requested

                start_time = time.time()
                with st.spinner("Processando auditoria e consultando bases oficiais da Receita Federal..."):
                    df_auditado, df_resumo, kpis = processar_lote_cnpjs(
                        df=df_bruto,
                        coluna_cnpj=coluna_selecionada,
                        client=st.session_state.client,
                        progress_callback=progress_cb,
                        cancel_check=check_cancel
                    )

                elapsed = round(time.time() - start_time, 1)
                progress_bar.progress(1.0)
                status_text.success(f"✅ Auditoria concluída com sucesso em {elapsed}s!")

                # Salva resultado no estado
                st.session_state.audit_data = {
                    "df_completo": df_auditado,
                    "df_resumo": df_resumo,
                    "kpis": kpis,
                    "nome_arquivo": nome_arquivo
                }

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

    # Exibição dos Resultados da Auditoria
    if st.session_state.audit_data:
        data = st.session_state.audit_data
        df_comp = data["df_completo"]
        df_res = data["df_resumo"]
        kpis = data["kpis"]

        st.markdown("---")
        st.subheader("2. Parecer e Indicadores de Auditoria Fiscal")

        # Cartões de KPIs
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Linhas Auditadas", f"{kpis['total_linhas']:,}")
        k2.metric("CNPJs Únicos", f"{kpis['total_unicos']:,}")
        k3.metric("Optantes Simples", f"{kpis['total_simples']}", f"{kpis['perc_simples']}%")
        k4.metric("SIMEI (MEI)", f"{kpis['total_mei']}", f"{kpis['perc_mei']}%")
        k5.metric("Não Optantes", f"{kpis['total_nao_optantes']}", f"{kpis['perc_nao_optantes']}%")
        
        irreg = kpis['total_irregulares']
        if irreg > 0:
            k6.metric("⚠️ Risco Baixada/Inapta", f"{irreg}", delta="-Alerta!", delta_color="inverse")
        else:
            k6.metric("Risco Cadastral", "0 Baixadas", "100% Regulares")

        # Botões de Exportação
        st.markdown("#### 📥 Exportar Resultados da Auditoria")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        nome_base = os.path.splitext(data['nome_arquivo'])[0]
        
        excel_bytes = exportar_para_excel(df_comp, df_res, kpis, titulo_auditoria=f"Auditoria {nome_base}")
        with col_exp1:
            st.download_button(
                label="📥 Baixar Relatório Completo (.xlsx)",
                data=excel_bytes,
                file_name=f"Auditoria_Simples_{nome_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
                help="Gera arquivo Excel profissional com 3 abas: Base Completa, Resumo por CNPJ e Parecer Executivo."
            )

        with col_exp2:
            csv_bytes = exportar_para_csv(df_comp)
            st.download_button(
                label="📥 Baixar Base em CSV (.csv)",
                data=csv_bytes,
                file_name=f"Auditoria_Simples_{nome_base}.csv",
                mime="text/csv",
                use_container_width=True,
                help="Exporta em formato CSV (UTF-8 com BOM e ponto-e-vírgula) pronto para o Excel."
            )

        with col_exp3:
            csv_res_bytes = exportar_para_csv(df_res)
            st.download_button(
                label="📥 Baixar Resumo CNPJs (.csv)",
                data=csv_res_bytes,
                file_name=f"Resumo_CNPJs_{nome_base}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Filtros e visualização interativa
        st.markdown("---")
        st.subheader("3. Detalhamento e Filtragem dos Registros")
        
        f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
        with f_col1:
            filtro_enquadramento = st.selectbox(
                "Filtrar por Enquadramento:",
                ["Todos"] + list(df_comp["Enquadramento"].unique())
            )
        with f_col2:
            filtro_risco = st.selectbox(
                "Filtrar por Risco Fiscal:",
                ["Todos"] + list(df_comp["Risco Fiscal"].unique())
            )
        with f_col3:
            busca_texto = st.text_input("Buscar por CNPJ ou Razão Social:", "")

        df_filtrado = df_comp.copy()
        if filtro_enquadramento != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Enquadramento"] == filtro_enquadramento]
        if filtro_risco != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Risco Fiscal"] == filtro_risco]
        if busca_texto:
            b = busca_texto.lower()
            df_filtrado = df_filtrado[
                df_filtrado["CNPJ Formatado"].str.lower().str.contains(b, na=False) |
                df_filtrado["Razão Social (RFB)"].str.lower().str.contains(b, na=False)
            ]

        st.caption(f"Exibindo **{len(df_filtrado)}** de **{len(df_comp)}** registros:")
        st.dataframe(
            df_filtrado[[
                "CNPJ Formatado", "Razão Social (RFB)", "Enquadramento", "Optante Simples?",
                "Data Opção Simples", "Optante MEI?", "Situação Cadastral", "Risco Fiscal",
                "Parecer da Auditoria"
            ]],
            use_container_width=True,
            height=400
        )


# =========================================================================
# TAB 2: CONSULTA INDIVIDUAL AVULSA
# =========================================================================
with tab_individual:
    st.subheader("Consulta Cadastral e Tributária Individual de CNPJ")
    st.markdown("Consulte qualquer CNPJ individualmente para emitir parecer instantâneo.")

    c_input, c_btn = st.columns([3, 1])
    with c_input:
        cnpj_input = st.text_input("Digite ou cole o CNPJ (com ou sem pontuação):", placeholder="Ex: 04.912.871/0001-32")
    with c_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_consultar_ind = st.button("🔍 Consultar CNPJ", type="primary", use_container_width=True)

    if btn_consultar_ind and cnpj_input:
        with st.spinner("Consultando bases oficiais da Receita Federal..."):
            dados = st.session_state.client.consultar(cnpj_input, use_cache=True)
            parecer = emitir_parecer_fiscal(dados)

        if not dados.get("sucesso"):
            st.error(f"❌ {parecer['parecer_completo']}")
        else:
            # Card Principal
            enq = parecer["classificacao"]
            badge_color = "#10B981" if "SIMPLES" in enq else ("#F59E0B" if "MEI" in enq else "#6B7280")
            
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border-left: 6px solid {badge_color}; padding: 18px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top:0; color: #1E3A8A;">{dados.get('razao_social', 'Razão Social não informada')}</h3>
                <p style="margin: 0; font-size: 1.15rem;">
                    <b>CNPJ:</b> {dados.get('cnpj_formatado')} &nbsp;|&nbsp;
                    <b>Nome Fantasia:</b> {dados.get('nome_fantasia') or '-'} &nbsp;|&nbsp;
                    <b>Situação:</b> <span style="font-weight: bold; color: {'green' if dados.get('situacao_cadastral') == 'ATIVA' else 'red'};">{dados.get('situacao_cadastral')}</span>
                </p>
                <h4 style="margin-top: 10px; margin-bottom: 5px; color: #0F172A;">Parecer Fiscal:</h4>
                <div style="background-color: #FFFFFF; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0; font-size: 0.95rem;">
                    {parecer['parecer_completo']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Detalhes em Colunas
            ci1, ci2 = st.columns(2)
            with ci1:
                st.markdown("#### 🏛️ Enquadramento Tributário")
                st.write(f"**Optante pelo Simples Nacional:** {'SIM' if dados.get('opcao_pelo_simples') else 'NÃO'}")
                st.write(f"**Data de Opção pelo Simples:** {formatar_data_br(dados.get('data_opcao_pelo_simples'))}")
                st.write(f"**Data de Exclusão do Simples:** {formatar_data_br(dados.get('data_exclusao_do_simples'))}")
                st.write(f"**Optante pelo SIMEI (MEI):** {'SIM' if dados.get('opcao_pelo_mei') else 'NÃO'}")
                st.write(f"**Porte da Empresa:** {dados.get('porte') or '-'}")
                st.write(f"**Natureza Jurídica:** {dados.get('natureza_juridica') or '-'}")

            with ci2:
                st.markdown("#### 📍 Localização & Atividade Econômica")
                st.write(f"**CNAE Principal:** {dados.get('cnae_fiscal_descricao') or '-'}")
                st.write(f"**Endereço:** {dados.get('logradouro', '')}, {dados.get('numero', '')} {dados.get('bairro', '')}")
                st.write(f"**Município / UF:** {dados.get('municipio', '')} - {dados.get('uf', '')}")
                st.write(f"**CEP:** {dados.get('cep', '-')}")
                st.write(f"**Fonte da Informação:** {dados.get('fonte', 'RFB')} *(Validado)*")

            # Quadro Societário (QSA)
            qsa = dados.get("qsa", [])
            if qsa:
                with st.expander(f"👥 Quadro de Sócios e Administradores - QSA ({len(qsa)} registros)", expanded=False):
                    df_qsa = pd.DataFrame(qsa)
                    cols_qsa = [c for c in ["nome_socio", "qualificacao_socio", "faixa_etaria", "data_entrada_sociedade"] if c in df_qsa.columns]
                    st.dataframe(df_qsa[cols_qsa], use_container_width=True)


# =========================================================================
# TAB 3: HISTÓRICO & PARECERES ACUMULADOS
# =========================================================================
with tab_historico:
    st.subheader("Histórico e Banco de Pareceres Auditados")
    st.markdown("Todos os CNPJs já auditados ficam registrados no banco local seguro, evitando retrabalho.")

    total_db = st.session_state.cache.count()
    st.metric("Total de CNPJs Cadastrados no Banco", f"{total_db:,}")

    if total_db > 0:
        # Carrega dados do banco SQLite
        import sqlite3
        conn = sqlite3.connect(st.session_state.cache.db_path)
        df_hist = pd.read_sql_query("""
            SELECT cnpj, razao_social, situacao_cadastral, 
                   CASE WHEN opcao_simples = 1 THEN 'SIM' ELSE 'NÃO' END as optante_simples,
                   data_opcao_simples, data_exclusao_simples,
                   CASE WHEN opcao_mei = 1 THEN 'SIM' ELSE 'NÃO' END as optante_mei,
                   cnae_principal, uf, municipio, consultado_em
            FROM cnpj_cache
            ORDER BY consultado_em DESC
        """, conn)
        conn.close()

        df_hist["cnpj_formatado"] = df_hist["cnpj"].apply(formatar_cnpj)
        
        st.dataframe(
            df_hist[[
                "cnpj_formatado", "razao_social", "optante_simples", "data_opcao_simples",
                "data_exclusao_simples", "optante_mei", "situacao_cadastral", "uf", "consultado_em"
            ]],
            use_container_width=True
        )

        csv_hist = exportar_para_csv(df_hist)
        st.download_button(
            "📥 Exportar Histórico Completo em CSV",
            data=csv_hist,
            file_name="Historico_Auditoria_CNPJs.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum CNPJ registrado ainda. Realize uma auditoria em lote ou consulta individual para alimentar o histórico.")


# =========================================================================
# TAB 4: COMO HOSPEDAR GRATUITAMENTE
# =========================================================================
with tab_deploy:
    st.subheader("🚀 Guia Passo a Passo: Hospedagem 100% Gratuita")
    st.markdown("""
    Este sistema foi construído pronto para ser publicado em nuvem de forma **totalmente gratuita**, permitindo que outros usuários e colaboradores acessem pelo navegador de qualquer lugar.
    """)

    st.markdown("""
    ### Opção 1: Streamlit Community Cloud (Recomendada - Mais Fácil e Rápida)
    1. Crie uma conta gratuita em [share.streamlit.io](https://share.streamlit.io/) com sua conta do GitHub.
    2. Suba esta pasta do projeto para um repositório no seu GitHub (público ou privado).
    3. No painel do Streamlit Cloud, clique em **"New App"**.
    4. Selecione o seu repositório, branch `main` e defina o arquivo principal como `app.py`.
    5. Clique em **"Deploy"**. Em cerca de 2 minutos seu sistema estará online com link público seguro (`https://seu-app.streamlit.app`) e HTTPS ativo!

    ---
    ### Opção 2: Hugging Face Spaces (100% Grátis)
    1. Crie uma conta gratuita em [huggingface.co](https://huggingface.co/).
    2. Clique em **"New Space"**, selecione o SDK **Streamlit** e escolha a camada gratuita (CPU Basic).
    3. Envie os arquivos do projeto via Git ou pela interface web.

    ---
    ### Opção 3: Render (Web Service Free)
    1. Crie conta em [render.com](https://render.com/).
    2. Crie um novo **Web Service** conectado ao seu GitHub.
    3. Comando de build: `pip install -r requirements.txt`
    4. Comando de início: `streamlit run app.py --server.port 10000 --server.address 0.0.0.0`
    """)

    st.info("💡 **Dica de Segurança:** No arquivo `DEPLOY.md` você encontra o tutorial detalhado com instruções para adicionar senha ou PIN de proteção para sua equipe.")

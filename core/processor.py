"""
Módulo de Ingestão e Processamento em Lote de Planilhas.
Suporta Excel (.xlsx, .xls) e CSV (.csv), com detecção heurística de colunas,
desduplicação para economia de requisições e mapeamento completo de volta à planilha original.
"""

import io
import re
import pandas as pd
from typing import Tuple, List, Dict, Any, Optional, Callable
from core.validator import limpar_cnpj, formatar_cnpj
from core.api_client import CNPJClient
from core.auditor import emitir_parecer_fiscal, formatar_data_br


def carregar_planilha(arquivo_bytes: bytes, nome_arquivo: str) -> pd.DataFrame:
    """
    Carrega o arquivo em memória (.xlsx, .xls, .csv), com tolerância a múltiplos encodings e delimitadores.
    """
    ext = nome_arquivo.lower().split(".")[-1]
    
    if ext in ["xlsx", "xls"]:
        return pd.read_excel(io.BytesIO(arquivo_bytes), dtype=str)
    elif ext == "csv":
        # Tenta detectar encoding e delimitador
        for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
            for sep in [";", ",", "\t", "|"]:
                try:
                    df = pd.read_csv(io.BytesIO(arquivo_bytes), encoding=enc, sep=sep, dtype=str)
                    if len(df.columns) > 1 or len(df) > 0:
                        return df
                except Exception:
                    continue
        # Fallback genérico para CSV
        return pd.read_csv(io.BytesIO(arquivo_bytes), dtype=str)
    else:
        raise ValueError(f"Extensão de arquivo '.{ext}' não suportada. Use .xlsx, .xls ou .csv.")


def detectar_coluna_cnpj(df: pd.DataFrame) -> Tuple[Optional[str], List[str]]:
    """
    Detecta de forma inteligente qual coluna contém os CNPJs da planilha.
    Usa análise semântica de cabeçalhos e verificação de dados por Regex.
    """
    colunas = [str(c) for c in df.columns]
    
    # 1. Padrões semânticos prioritários nos nomes das colunas
    padroes_prioritarios = [
        r"^cnpj$",
        r"cpf.?cnpj",
        r"cnpj.?cpf",
        r"cnpj_destinatario",
        r"destinatario_cnpj",
        r"cnpj_emitente",
        r"emitente_cnpj",
        r"cnpj_fornecedor",
        r"fornecedor_cnpj",
        r"cnpj_cliente",
        r"cliente_cnpj",
        r"doc(umento)?_destinatario",
        r"doc(umento)?_fornecedor",
        r"doc(umento)?_cliente",
        r"documento",
        r"^doc$"
    ]
    
    for padrao in padroes_prioritarios:
        for col in colunas:
            if re.search(padrao, col, re.IGNORECASE):
                return col, colunas

    # 2. Verificação por conteúdo das linhas (amostra dos primeiros 30 registros)
    melhor_coluna = None
    maior_score = 0
    
    amostra = df.head(30)
    for col in colunas:
        score = 0
        for val in amostra[col].dropna():
            digitos = re.sub(r"\D", "", str(val))
            if len(digitos) == 14 or (11 < len(digitos) <= 14):
                score += 1
        if score > maior_score:
            maior_score = score
            melhor_coluna = col
            
    if melhor_coluna and maior_score >= 2:
        return melhor_coluna, colunas

    # Fallback: primeira coluna
    return colunas[0] if colunas else None, colunas


def processar_lote_cnpjs(
    df: pd.DataFrame,
    coluna_cnpj: str,
    client: CNPJClient,
    progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executa a auditoria em lote para os CNPJs da coluna especificada.
    
    Retorna:
    - df_completo: DataFrame original com as colunas de auditoria anexadas.
    - df_resumo: DataFrame consolidado com 1 linha por CNPJ único.
    - kpis: Dicionário com métricas executivas da auditoria.
    """
    df_resultado = df.copy()
    
    # 1. Extração e sanitização dos CNPJs
    df_resultado["_cnpj_limpo"] = df_resultado[coluna_cnpj].apply(limpar_cnpj)
    
    # Identifica CNPJs únicos para evitar requisições repetidas
    cnpjs_unicos = [c for c in df_resultado["_cnpj_limpo"].unique() if c]
    total_unicos = len(cnpjs_unicos)
    
    mapa_resultados: Dict[str, Dict[str, Any]] = {}
    
    # 2. Processamento dos CNPJs únicos
    for idx, cnpj in enumerate(cnpjs_unicos):
        if cancel_check and cancel_check():
            break
            
        dados_api = client.consultar(cnpj, use_cache=True)
        parecer = emitir_parecer_fiscal(dados_api)
        
        # Junta os dados cadastrais e parecer
        consolidado = {**dados_api, **parecer}
        mapa_resultados[cnpj] = consolidado
        
        if progress_callback:
            razao = consolidado.get("razao_social") or consolidado.get("status_simples", "")
            progress_callback(idx + 1, total_unicos, cnpj, razao)

    # 3. Mapeia os resultados de volta para todas as linhas da planilha original
    def get_info(c, chave, default=""):
        if not c or c not in mapa_resultados:
            return default
        return mapa_resultados[c].get(chave, default)

    df_resultado["CNPJ Formatado"] = df_resultado["_cnpj_limpo"].apply(lambda c: formatar_cnpj(c) if c else "")
    df_resultado["Razão Social (RFB)"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "razao_social"))
    df_resultado["Situação Cadastral"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "situacao_cadastral"))
    df_resultado["Enquadramento"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "classificacao"))
    df_resultado["Optante Simples?"] = df_resultado["_cnpj_limpo"].apply(
        lambda c: "SIM" if get_info(c, "is_optante_simples") else "NÃO"
    )
    df_resultado["Data Opção Simples"] = df_resultado["_cnpj_limpo"].apply(
        lambda c: formatar_data_br(get_info(c, "data_opcao_pelo_simples"))
    )
    df_resultado["Data Exclusão Simples"] = df_resultado["_cnpj_limpo"].apply(
        lambda c: formatar_data_br(get_info(c, "data_exclusao_do_simples"))
    )
    df_resultado["Optante MEI?"] = df_resultado["_cnpj_limpo"].apply(
        lambda c: "SIM" if get_info(c, "is_mei") else "NÃO"
    )
    df_resultado["CNAE Principal"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "cnae_fiscal_descricao"))
    df_resultado["UF"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "uf"))
    df_resultado["Município"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "municipio"))
    df_resultado["Risco Fiscal"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "risco_fiscal"))
    df_resultado["Parecer da Auditoria"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "parecer_completo"))
    df_resultado["Data da Consulta"] = df_resultado["_cnpj_limpo"].apply(lambda c: get_info(c, "data_consulta"))

    # Remove coluna temporária auxiliar
    df_resultado.drop(columns=["_cnpj_limpo"], inplace=True)

    # 4. Criação do DataFrame de Resumo Consolidado (1 linha por CNPJ único)
    linhas_resumo = []
    contagem_ocorrencias = df[coluna_cnpj].apply(limpar_cnpj).value_counts().to_dict()

    for cnpj, dados in mapa_resultados.items():
        linhas_resumo.append({
            "CNPJ": formatar_cnpj(cnpj),
            "Razão Social": dados.get("razao_social", ""),
            "Qtd Notas/Ocorrências": contagem_ocorrencias.get(cnpj, 0),
            "Enquadramento": dados.get("classificacao", ""),
            "Optante Simples?": "SIM" if dados.get("is_optante_simples") else "NÃO",
            "Data Opção": formatar_data_br(dados.get("data_opcao_pelo_simples")),
            "Data Exclusão": formatar_data_br(dados.get("data_exclusao_do_simples")),
            "Optante MEI?": "SIM" if dados.get("is_mei") else "NÃO",
            "Situação Cadastral": dados.get("situacao_cadastral", ""),
            "Risco Fiscal": dados.get("risco_fiscal", ""),
            "UF": dados.get("uf", ""),
            "Município": dados.get("municipio", ""),
            "Parecer Resumido": dados.get("parecer_resumido", ""),
            "Fonte da Consulta": dados.get("fonte", "")
        })

    df_resumo = pd.DataFrame(linhas_resumo)

    # 5. Cálculo dos KPIs de Auditoria
    total_linhas = len(df)
    total_consultados = len(mapa_resultados)
    
    total_simples = sum(1 for d in mapa_resultados.values() if d.get("is_optante_simples") and not d.get("is_mei"))
    total_mei = sum(1 for d in mapa_resultados.values() if d.get("is_mei"))
    total_excluidos = sum(1 for d in mapa_resultados.values() if d.get("classificacao") == "EXCLUÍDO DO SIMPLES")
    total_nao_optantes = sum(1 for d in mapa_resultados.values() if d.get("classificacao") == "NÃO OPTANTE (REGIME GERAL)")
    total_irregulares = sum(1 for d in mapa_resultados.values() if d.get("situacao_cadastral") in ["BAIXADA", "INAPTA", "SUSPENSA", "NULA"])
    total_invalidos = sum(1 for d in mapa_resultados.values() if not d.get("sucesso"))

    kpis = {
        "total_linhas": total_linhas,
        "total_unicos": total_consultados,
        "total_simples": total_simples,
        "total_mei": total_mei,
        "total_excluidos": total_excluidos,
        "total_nao_optantes": total_nao_optantes,
        "total_irregulares": total_irregulares,
        "total_invalidos": total_invalidos,
        "perc_simples": round((total_simples / total_consultados * 100) if total_consultados else 0, 1),
        "perc_mei": round((total_mei / total_consultados * 100) if total_consultados else 0, 1),
        "perc_nao_optantes": round((total_nao_optantes / total_consultados * 100) if total_consultados else 0, 1)
    }

    return df_resultado, df_resumo, kpis

"""
Módulo de Exportação de Relatórios de Auditoria.
Gera arquivos Excel (.xlsx) profissionais e estilizados com múltiplas abas,
cabeçalhos corporativos, formatação condicional de cores e sumário executivo,
além de arquivos CSV compatíveis com o Excel do Brasil (UTF-8 BOM, separador ';').
"""

import io
from datetime import datetime
import pandas as pd
from typing import Dict, Any


def exportar_para_excel(
    df_completo: pd.DataFrame,
    df_resumo: pd.DataFrame,
    kpis: Dict[str, Any],
    titulo_auditoria: str = "Auditoria de Optantes pelo Simples Nacional"
) -> bytes:
    """
    Gera um arquivo Excel (.xlsx) com 3 abas estilizadas:
    1. Base Auditada (completa com notas)
    2. Resumo Consolidado (1 linha por CNPJ)
    3. Sumário Executivo (KPIs e parecer gerencial)
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        
        # Formatos visuais
        header_format = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "vcenter",
            "align": "center",
            "fg_color": "#1E3A8A", # Azul Marinho corporativo
            "font_color": "#FFFFFF",
            "border": 1
        })
        
        title_format = workbook.add_format({
            "bold": True,
            "font_size": 16,
            "font_color": "#1E3A8A",
            "align": "left",
            "valign": "vcenter"
        })
        
        subtitle_format = workbook.add_format({
            "italic": True,
            "font_size": 10,
            "font_color": "#4B5563"
        })
        
        card_title = workbook.add_format({
            "bold": True,
            "font_size": 11,
            "fg_color": "#E0E7FF",
            "border": 1,
            "align": "left"
        })
        
        card_val = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "border": 1,
            "align": "center"
        })

        cell_format = workbook.add_format({
            "border": 1,
            "valign": "vcenter"
        })

        # Cores condicionais
        fmt_simples = workbook.add_format({"bg_color": "#DCFCE7", "font_color": "#14532D", "border": 1})
        fmt_mei = workbook.add_format({"bg_color": "#FEF9C3", "font_color": "#713F12", "border": 1})
        fmt_excluido = workbook.add_format({"bg_color": "#FFEDD5", "font_color": "#7C2D12", "border": 1})
        fmt_nao_optante = workbook.add_format({"bg_color": "#F3F4F6", "font_color": "#1F2937", "border": 1})
        fmt_critico = workbook.add_format({"bg_color": "#FEE2E2", "font_color": "#7F1D1D", "bold": True, "border": 1})

        # --- ABA 1: Base Auditada ---
        df_completo.to_excel(writer, sheet_name="Base Auditada", index=False, startrow=1)
        ws_completo = writer.sheets["Base Auditada"]
        ws_completo.write(0, 0, f"{titulo_auditoria} - Base Completa de Registros", title_format)
        
        # Ajusta largura de colunas e formata cabeçalho
        for col_idx, col_name in enumerate(df_completo.columns):
            max_len = max(df_completo[col_name].astype(str).map(len).max(), len(col_name)) + 3
            ws_completo.set_column(col_idx, col_idx, min(max(max_len, 12), 45), cell_format)
            ws_completo.write(1, col_idx, col_name, header_format)

        # Regras condicionais para coluna "Enquadramento" e "Risco Fiscal"
        num_rows = len(df_completo) + 2
        if "Enquadramento" in df_completo.columns:
            c_idx = df_completo.columns.get_loc("Enquadramento")
            ws_completo.conditional_format(2, c_idx, num_rows, c_idx, {
                "type": "cell", "criteria": "equal to", "value": '"SIMPLES NACIONAL"', "format": fmt_simples
            })
            ws_completo.conditional_format(2, c_idx, num_rows, c_idx, {
                "type": "cell", "criteria": "equal to", "value": '"SIMEI (MEI)"', "format": fmt_mei
            })
            ws_completo.conditional_format(2, c_idx, num_rows, c_idx, {
                "type": "cell", "criteria": "equal to", "value": '"EXCLUÍDO DO SIMPLES"', "format": fmt_excluido
            })

        # --- ABA 2: Resumo Consolidado por CNPJ ---
        df_resumo.to_excel(writer, sheet_name="Resumo por CNPJ", index=False, startrow=1)
        ws_resumo = writer.sheets["Resumo por CNPJ"]
        ws_resumo.write(0, 0, "Consolidado por CNPJ Único", title_format)
        
        for col_idx, col_name in enumerate(df_resumo.columns):
            max_len = max(df_resumo[col_name].astype(str).map(len).max(), len(col_name)) + 3
            ws_resumo.set_column(col_idx, col_idx, min(max(max_len, 12), 45), cell_format)
            ws_resumo.write(1, col_idx, col_name, header_format)

        # --- ABA 3: Sumário Executivo & Metadados ---
        ws_sumario = workbook.add_worksheet("Sumário Executivo")
        ws_sumario.write(1, 1, "PARECER EXECUTIVO DE AUDITORIA FISCAL", title_format)
        ws_sumario.write(2, 1, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}", subtitle_format)
        ws_sumario.write(3, 1, "Finalidade: Validação cadastral e enquadramento tributário (Simples Nacional / SIMEI / Regime Geral)", subtitle_format)
        
        # Tabela de Indicadores
        ws_sumario.set_column(1, 1, 35)
        ws_sumario.set_column(2, 2, 20)
        
        ws_sumario.write(5, 1, "Métrica de Auditoria", header_format)
        ws_sumario.write(5, 2, "Quantidade / Percentual", header_format)
        
        metricas = [
            ("Total de Linhas / Notas Auditadas", str(kpis.get("total_linhas", 0))),
            ("Total de CNPJs Únicos Consultados", str(kpis.get("total_unicos", 0))),
            ("Optantes pelo Simples Nacional (Geral)", f"{kpis.get('total_simples', 0)} ({kpis.get('perc_simples', 0)}%)"),
            ("Microempreendedores Individuais (SIMEI)", f"{kpis.get('total_mei', 0)} ({kpis.get('perc_mei', 0)}%)"),
            ("Não Optantes (Lucro Presumido / Real)", f"{kpis.get('total_nao_optantes', 0)} ({kpis.get('perc_nao_optantes', 0)}%)"),
            ("Empresas Excluídas do Simples Nacional", str(kpis.get("total_excluidos", 0))),
            ("CNPJs com Situação Irregular (Baixada/Inapta)", str(kpis.get("total_irregulares", 0))),
            ("CNPJs com Erro / Inconsistência Cadastral", str(kpis.get("total_invalidos", 0)))
        ]
        
        for r_idx, (rotulo, valor) in enumerate(metricas, start=6):
            ws_sumario.write(r_idx, 1, rotulo, card_title)
            ws_sumario.write(r_idx, 2, valor, card_val)

        # Recomendações de Compliance
        r_rec = 6 + len(metricas) + 2
        ws_sumario.write(r_rec, 1, "RECOMENDAÇÕES DA EQUIPE DE AUDITORIA FISCAL:", title_format)
        recomendacoes = [
            "1. Notas de fornecedores Optantes pelo Simples dispensam retenção na fonte de PIS/COFINS/CSLL/IRRF (IN RFB 1.234/2012).",
            "2. Notas de fornecedores NÃO Optantes exigem retenção de tributos quando o serviço/fornecimento for tributável.",
            "3. Verificar com máxima urgência notas emitidas por CNPJs Baixados ou Inaptos, pois geram risco de glosa de ICMS/IPI/PIS/COFINS.",
            "4. As consultas foram realizadas na base aberta oficial da Receita Federal do Brasil (RFB) e possuem validade contábil."
        ]
        for idx, rec in enumerate(recomendacoes, start=r_rec+1):
            ws_sumario.write(idx, 1, rec, subtitle_format)

    output.seek(0)
    return output.getvalue()


def exportar_para_csv(df: pd.DataFrame) -> bytes:
    """
    Gera CSV formatado em UTF-8 com BOM (utf-8-sig) e separador ponto e vírgula (;),
    garantindo abertura direta e correta no Microsoft Excel em português.
    """
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

"""
Módulo de Parecer Fiscal e Auditoria Contábil/Tributária.
Analisa a situação perante o Simples Nacional, SIMEI, regime geral e risco cadastral de acordo com as normas da RFB.
"""

from datetime import datetime
from typing import Dict, Any, Optional


def formatar_data_br(data_iso: Optional[str]) -> str:
    """Converte 'YYYY-MM-DD' para 'DD/MM/AAAA'."""
    if not data_iso:
        return "-"
    try:
        dt = datetime.strptime(str(data_iso)[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(data_iso)


def emitir_parecer_fiscal(dados_cnpj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera a classificação tributária detalhada, avaliação de risco de conformidade e o parecer técnico de auditoria.
    """
    sucesso = dados_cnpj.get("sucesso", False)
    erro = dados_cnpj.get("erro")
    situacao = str(dados_cnpj.get("situacao_cadastral", "")).upper().strip()
    
    opt_simples = dados_cnpj.get("opcao_pelo_simples")
    dt_opcao_simples = dados_cnpj.get("data_opcao_pelo_simples")
    dt_exclusao_simples = dados_cnpj.get("data_exclusao_do_simples")
    
    opt_mei = dados_cnpj.get("opcao_pelo_mei")
    dt_opcao_mei = dados_cnpj.get("data_opcao_pelo_mei")
    dt_exclusao_mei = dados_cnpj.get("data_exclusao_do_mei")
    
    agora_br = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Caso 1: Falha na validação ou erro de consulta
    if not sucesso:
        if "inválido" in str(erro).lower() or situacao == "INVÁLIDO":
            return {
                "classificacao": "CNPJ INVÁLIDO",
                "status_simples": "Inválido",
                "is_optante_simples": False,
                "is_mei": False,
                "badge": "🔴 Inválido",
                "risco_fiscal": "CRÍTICO",
                "parecer_resumido": "CNPJ com dígitos verificadores inconsistentes.",
                "parecer_completo": f"CNPJ matematicamente inválido ({erro or 'Erro Módulo 11'}). Impossível prosseguir com faturamento ou contratação.",
                "data_consulta": agora_br
            }
        else:
            return {
                "classificacao": "NÃO LOCALIZADO / ERRO",
                "status_simples": "Não Localizado",
                "is_optante_simples": False,
                "is_mei": False,
                "badge": "⚪ Não Localizado",
                "risco_fiscal": "ALTO",
                "parecer_resumido": "Não localizado na base oficial.",
                "parecer_completo": f"Falha na consulta junto à Receita Federal: {erro or 'Registro não localizado'}. Recomenda-se verificação manual no portal da RFB.",
                "data_consulta": agora_br
            }

    # Caso 2: Alerta cadastral (BAIXADA, INAPTA, SUSPENSA, NULA)
    situacao_irregular = situacao in ["BAIXADA", "INAPTA", "SUSPENSA", "NULA"]

    # Caso 3: SIMEI (MEI)
    if opt_mei is True:
        dt_fmt = formatar_data_br(dt_opcao_mei)
        risco = "CRÍTICO" if situacao_irregular else "BAIXO"
        parecer = (
            f"MICROEMPREENDEDOR INDIVIDUAL (SIMEI) desde {dt_fmt}. "
            "Dispensa retenção federal na fonte (IRRF/CSLL/PIS/COFINS). "
        )
        if situacao_irregular:
            parecer += f" ATENÇÃO: Situação cadastral {situacao}! Notas emitidas após a baixa geram inidoneidade fiscal."
            
        return {
            "classificacao": "SIMEI (MEI)",
            "status_simples": "Optante (MEI)",
            "is_optante_simples": True,
            "is_mei": True,
            "badge": "🟡 MEI (Simples)",
            "risco_fiscal": risco,
            "parecer_resumido": f"Optante SIMEI desde {dt_fmt}" + (f" ({situacao})" if situacao_irregular else ""),
            "parecer_completo": parecer,
            "data_consulta": agora_br
        }

    # Caso 4: Optante pelo Simples Nacional
    if opt_simples is True:
        dt_fmt = formatar_data_br(dt_opcao_simples)
        risco = "CRÍTICO" if situacao_irregular else "BAIXO"
        parecer = (
            f"OPTANTE PELO SIMPLES NACIONAL desde {dt_fmt}. "
            "Dispensa de retenção na fonte de PIS, COFINS, CSLL e IRRF conforme art. 30 da Lei 10.833/2003 e IN RFB nº 1.234/2012. "
            "Exigir declaração de opção pelo Simples se for prestação de serviços."
        )
        if situacao_irregular:
            parecer = f"ALERTA FISCAL: Empresa é Optante pelo Simples, porém sua situação cadastral é {situacao}! Risco de glosa e passivo tributário."
            
        return {
            "classificacao": "SIMPLES NACIONAL",
            "status_simples": "Optante",
            "is_optante_simples": True,
            "is_mei": False,
            "badge": "🟢 Optante Simples",
            "risco_fiscal": risco,
            "parecer_resumido": f"Optante Simples desde {dt_fmt}" + (f" ({situacao})" if situacao_irregular else ""),
            "parecer_completo": parecer,
            "data_consulta": agora_br
        }

    # Caso 5: Excluída do Simples Nacional
    if dt_exclusao_simples:
        dt_excl_fmt = formatar_data_br(dt_exclusao_simples)
        dt_opc_fmt = formatar_data_br(dt_opcao_simples)
        risco = "MÉDIO" if not situacao_irregular else "CRÍTICO"
        parecer = (
            f"EXCLUÍDA DO SIMPLES NACIONAL em {dt_excl_fmt} (optou em {dt_opc_fmt}). "
            "Atualmente no Regime Normal (Lucro Presumido ou Lucro Real). "
            "Exige retenção regular na fonte de tributos (IRRF/CSLL/PIS/COFINS/ISS) para fatos geradores posteriores à data de exclusão."
        )
        return {
            "classificacao": "EXCLUÍDO DO SIMPLES",
            "status_simples": "Excluído",
            "is_optante_simples": False,
            "is_mei": False,
            "badge": "🟠 Excluído",
            "risco_fiscal": risco,
            "parecer_resumido": f"Excluído do Simples em {dt_excl_fmt}",
            "parecer_completo": parecer,
            "data_consulta": agora_br
        }

    # Caso 6: Não Optante (Regime Normal: Lucro Presumido / Real)
    risco = "BAIXO" if not situacao_irregular else "CRÍTICO"
    parecer = (
        "NÃO OPTANTE PELO SIMPLES NACIONAL (Regime Normal: Lucro Presumido ou Lucro Real). "
        "Sujeito às retenções normais na fonte de PIS, COFINS, CSLL e IRRF quando incidente sobre a operação."
    )
    if situacao_irregular:
        parecer = f"ALERTA GRAVE: Empresa Não Optante com situação cadastral {situacao}! Transações com este CNPJ configuram risco de inidoneidade fiscal."

    return {
        "classificacao": "NÃO OPTANTE (REGIME GERAL)",
        "status_simples": "Não Optante",
        "is_optante_simples": False,
        "is_mei": False,
        "badge": "⚪ Não Optante",
        "risco_fiscal": risco,
        "parecer_resumido": "Não Optante (Lucro Presumido / Real)" + (f" ({situacao})" if situacao_irregular else ""),
        "parecer_completo": parecer,
        "data_consulta": agora_br
    }

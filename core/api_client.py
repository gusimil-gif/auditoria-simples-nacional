"""
Cliente HTTP para consulta de CNPJs com sistema de fallback em cascata (BrasilAPI -> Minha Receita -> ReceitaWS).
Inclui cache local, retentativas e tratamento de erros de rede.
"""

import time
import requests
from typing import Dict, Any, Optional
from core.validator import validar_cnpj, formatar_cnpj
from core.cache import CNPJCache


class CNPJClient:
    def __init__(self, cache: Optional[CNPJCache] = None, delay_between_requests: float = 0.2):
        self.cache = cache if cache is not None else CNPJCache()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AuditoriaSimplesNacional/1.0 (Auditoria Fiscal Hiléia)",
            "Accept": "application/json"
        })

    def _consultar_brasil_api(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """Consulta via BrasilAPI (gratuita, rápida e oficial)."""
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        try:
            resp = self.session.get(url, timeout=7)
            if resp.status_code == 200:
                data = resp.json()
                data["_fonte"] = "BrasilAPI"
                return data
            elif resp.status_code == 404:
                return {"_erro": "CNPJ não encontrado na base da Receita Federal", "_fonte": "BrasilAPI"}
        except requests.exceptions.RequestException:
            pass
        return None

    def _consultar_minha_receita(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """Consulta via Minha Receita (espelho aberto da RFB, backup robusto)."""
        url = f"https://minhareceita.org/{cnpj}"
        try:
            resp = self.session.get(url, timeout=7)
            if resp.status_code == 200:
                data = resp.json()
                data["_fonte"] = "Minha Receita"
                return data
            elif resp.status_code == 404:
                return {"_erro": "CNPJ não encontrado na base Minha Receita", "_fonte": "Minha Receita"}
        except requests.exceptions.RequestException:
            pass
        return None

    def _consultar_receitaws(self, cnpj: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Consulta alternativa ReceitaWS (suporta token ou free com limitação)."""
        url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = self.session.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ERROR":
                    return {"_erro": data.get("message", "Erro na consulta ReceitaWS"), "_fonte": "ReceitaWS"}
                
                # Normaliza campos do ReceitaWS para o padrão unificado
                simples_obj = data.get("simples", {})
                simei_obj = data.get("simei", {})
                
                normalizado = {
                    "cnpj": cnpj,
                    "razao_social": data.get("nome"),
                    "nome_fantasia": data.get("fantasia"),
                    "descricao_situacao_cadastral": data.get("situacao"),
                    "data_situacao_cadastral": data.get("data_situacao"),
                    "opcao_pelo_simples": simples_obj.get("optante") if isinstance(simples_obj, dict) else None,
                    "data_opcao_pelo_simples": simples_obj.get("data_opcao") if isinstance(simples_obj, dict) else None,
                    "data_exclusao_do_simples": simples_obj.get("data_exclusao") if isinstance(simples_obj, dict) else None,
                    "opcao_pelo_mei": simei_obj.get("optante") if isinstance(simei_obj, dict) else None,
                    "data_opcao_pelo_mei": simei_obj.get("data_opcao") if isinstance(simei_obj, dict) else None,
                    "data_exclusao_do_mei": simei_obj.get("data_exclusao") if isinstance(simei_obj, dict) else None,
                    "porte": data.get("porte"),
                    "natureza_juridica": data.get("natureza_juridica"),
                    "cnae_fiscal_descricao": data.get("atividade_principal", [{}])[0].get("text", "") if data.get("atividade_principal") else "",
                    "logradouro": data.get("logradouro"),
                    "numero": data.get("numero"),
                    "bairro": data.get("bairro"),
                    "municipio": data.get("municipio"),
                    "uf": data.get("uf"),
                    "cep": data.get("cep"),
                    "_fonte": "ReceitaWS"
                }
                return normalizado
        except requests.exceptions.RequestException:
            pass
        return None

    def consultar(self, cnpj_raw: any, use_cache: bool = True, force_provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Consulta um CNPJ com validação matemática prévia, cache e fallback de provedores.
        Retorna dicionário padronizado.
        """
        is_valido, cnpj, erro_val = validar_cnpj(cnpj_raw)
        
        if not is_valido:
            return {
                "cnpj": cnpj,
                "cnpj_formatado": formatar_cnpj(cnpj),
                "sucesso": False,
                "erro": erro_val or "CNPJ Inválido",
                "opcao_pelo_simples": None,
                "opcao_pelo_mei": None,
                "situacao_cadastral": "INVÁLIDO",
                "fonte": "Validação Local"
            }

        # 1. Verifica cache se habilitado
        if use_cache and self.cache:
            cached = self.cache.get(cnpj)
            if cached:
                raw = cached.get("raw_json", {})
                return {
                    "cnpj": cnpj,
                    "cnpj_formatado": formatar_cnpj(cnpj),
                    "sucesso": True if cached.get("status_consulta") == "OK" else False,
                    "erro": None if cached.get("status_consulta") == "OK" else cached.get("status_consulta"),
                    "razao_social": cached.get("razao_social") or raw.get("razao_social", ""),
                    "nome_fantasia": raw.get("nome_fantasia", ""),
                    "situacao_cadastral": cached.get("situacao_cadastral") or raw.get("descricao_situacao_cadastral", "DESCONHECIDA"),
                    "opcao_pelo_simples": True if cached.get("opcao_simples") == 1 else (False if cached.get("opcao_simples") == 0 else None),
                    "data_opcao_pelo_simples": cached.get("data_opcao_simples") or raw.get("data_opcao_pelo_simples"),
                    "data_exclusao_do_simples": cached.get("data_exclusao_simples") or raw.get("data_exclusao_do_simples"),
                    "opcao_pelo_mei": True if cached.get("opcao_mei") == 1 else (False if cached.get("opcao_mei") == 0 else None),
                    "data_opcao_pelo_mei": cached.get("data_opcao_mei") or raw.get("data_opcao_pelo_mei"),
                    "data_exclusao_do_mei": cached.get("data_exclusao_mei") or raw.get("data_exclusao_do_mei"),
                    "cnae_fiscal_descricao": cached.get("cnae_principal") or raw.get("cnae_fiscal_descricao", ""),
                    "uf": cached.get("uf") or raw.get("uf", ""),
                    "municipio": cached.get("municipio") or raw.get("municipio", ""),
                    "porte": raw.get("porte", ""),
                    "natureza_juridica": raw.get("natureza_juridica", ""),
                    "logradouro": raw.get("logradouro", ""),
                    "numero": raw.get("numero", ""),
                    "bairro": raw.get("bairro", ""),
                    "cep": raw.get("cep", ""),
                    "qsa": raw.get("qsa", []),
                    "fonte": "Cache Local",
                    "consultado_em": cached.get("consultado_em")
                }

        # 2. Executa requisição na rede com delay amigável
        if self.delay > 0:
            time.sleep(self.delay)

        dados = None
        # Provedor 1: BrasilAPI
        if force_provider in (None, "brasilapi"):
            dados = self._consultar_brasil_api(cnpj)

        # Provedor 2: Minha Receita (Fallback se BrasilAPI falhar)
        if not dados and force_provider in (None, "minhareceita"):
            dados = self._consultar_minha_receita(cnpj)

        # Provedor 3: ReceitaWS (Fallback secundário)
        if not dados and force_provider in (None, "receitaws"):
            dados = self._consultar_receitaws(cnpj)

        # Se todas as fontes falharem
        if not dados:
            return {
                "cnpj": cnpj,
                "cnpj_formatado": formatar_cnpj(cnpj),
                "sucesso": False,
                "erro": "Instabilidade temporária nas APIs da Receita Federal. Tente novamente em instantes.",
                "opcao_pelo_simples": None,
                "opcao_pelo_mei": None,
                "situacao_cadastral": "ERRO_CONEXAO",
                "fonte": "Nenhuma API respondeu"
            }

        if "_erro" in dados:
            erro_msg = dados["_erro"]
            if use_cache and self.cache:
                self.cache.set(cnpj, {"razao_social": "", "descricao_situacao_cadastral": "NÃO ENCONTRADO"}, status_consulta=erro_msg)
            return {
                "cnpj": cnpj,
                "cnpj_formatado": formatar_cnpj(cnpj),
                "sucesso": False,
                "erro": erro_msg,
                "opcao_pelo_simples": None,
                "opcao_pelo_mei": None,
                "situacao_cadastral": "NÃO ENCONTRADO",
                "fonte": dados.get("_fonte", "API Externa")
            }

        # Normalização de dados recebidos
        res = {
            "cnpj": cnpj,
            "cnpj_formatado": formatar_cnpj(cnpj),
            "sucesso": True,
            "erro": None,
            "razao_social": dados.get("razao_social", ""),
            "nome_fantasia": dados.get("nome_fantasia", ""),
            "situacao_cadastral": dados.get("descricao_situacao_cadastral") or dados.get("situacao_cadastral", "DESCONHECIDA"),
            "data_situacao_cadastral": dados.get("data_situacao_cadastral"),
            "opcao_pelo_simples": dados.get("opcao_pelo_simples"),
            "data_opcao_pelo_simples": dados.get("data_opcao_pelo_simples"),
            "data_exclusao_do_simples": dados.get("data_exclusao_do_simples"),
            "opcao_pelo_mei": dados.get("opcao_pelo_mei"),
            "data_opcao_pelo_mei": dados.get("data_opcao_pelo_mei"),
            "data_exclusao_do_mei": dados.get("data_exclusao_do_mei"),
            "cnae_fiscal_descricao": dados.get("cnae_fiscal_descricao", ""),
            "uf": dados.get("uf", ""),
            "municipio": dados.get("municipio", ""),
            "porte": dados.get("porte", ""),
            "natureza_juridica": dados.get("natureza_juridica", ""),
            "logradouro": dados.get("logradouro", ""),
            "numero": dados.get("numero", ""),
            "bairro": dados.get("bairro", ""),
            "cep": dados.get("cep", ""),
            "qsa": dados.get("qsa", []),
            "fonte": dados.get("_fonte", "API Externa")
        }

        # Salva no cache para futuras consultas
        if use_cache and self.cache:
            self.cache.set(cnpj, dados, status_consulta="OK")

        return res

"""
Conjunto de testes automatizados para o sistema de auditoria fiscal e consulta de CNPJs.
"""

import os
import unittest
import pandas as pd
from core.validator import limpar_cnpj, validar_cnpj, formatar_cnpj
from core.cache import CNPJCache
from core.api_client import CNPJClient
from core.auditor import emitir_parecer_fiscal
from core.processor import carregar_planilha, detectar_coluna_cnpj, processar_lote_cnpjs
from core.exporter import exportar_para_excel, exportar_para_csv


class TestSistemaAuditoria(unittest.TestCase):
    def setUp(self):
        self.test_cache_path = "tests/test_cache.db"
        if os.path.exists(self.test_cache_path):
            os.remove(self.test_cache_path)
        self.cache = CNPJCache(db_path=self.test_cache_path)
        self.client = CNPJClient(cache=self.cache, delay_between_requests=0.0)

    def tearDown(self):
        if os.path.exists(self.test_cache_path):
            os.remove(self.test_cache_path)

    def test_validador_cnpj(self):
        # CNPJ válido conhecido (Banco do Brasil)
        valido, cnpj, err = validar_cnpj("00.000.000/0001-91")
        self.assertTrue(valido)
        self.assertEqual(cnpj, "00000000000191")
        self.assertIsNone(err)

        # CNPJ com zeros cortados pelo Excel (número com 13 dígitos)
        valido, cnpj, err = validar_cnpj(4912871000132)
        self.assertTrue(valido)
        self.assertEqual(cnpj, "04912871000132")

        # CNPJ com dígitos iguais (inválido)
        valido, _, err = validar_cnpj("11.111.111/1111-11")
        self.assertFalse(valido)

        # CNPJ com dígito verificador errado
        valido, _, err = validar_cnpj("00.000.000/0001-99")
        self.assertFalse(valido)

        # Formatação
        fmt = formatar_cnpj("00000000000191")
        self.assertEqual(fmt, "00.000.000/0001-91")

    def test_cache_sqlite(self):
        self.assertEqual(self.cache.count(), 0)
        self.cache.set("00000000000191", {
            "razao_social": "BANCO DO BRASIL SA",
            "descricao_situacao_cadastral": "ATIVA",
            "opcao_pelo_simples": False
        }, status_consulta="OK")

        self.assertEqual(self.cache.count(), 1)
        res = self.cache.get("00000000000191")
        self.assertIsNotNone(res)
        self.assertEqual(res["razao_social"], "BANCO DO BRASIL SA")
        self.assertEqual(res["opcao_simples"], 0)

        self.cache.clear()
        self.assertEqual(self.cache.count(), 0)

    def test_auditor_parecer(self):
        # Caso Optante Simples
        dados_simples = {
            "sucesso": True,
            "situacao_cadastral": "ATIVA",
            "opcao_pelo_simples": True,
            "data_opcao_pelo_simples": "2015-01-01",
            "opcao_pelo_mei": False
        }
        parecer = emitir_parecer_fiscal(dados_simples)
        self.assertEqual(parecer["classificacao"], "SIMPLES NACIONAL")
        self.assertTrue(parecer["is_optante_simples"])
        self.assertIn("OPTANTE PELO SIMPLES NACIONAL", parecer["parecer_completo"])

        # Caso Não Optante
        dados_nao_optante = {
            "sucesso": True,
            "situacao_cadastral": "ATIVA",
            "opcao_pelo_simples": False,
            "opcao_pelo_mei": False
        }
        parecer_nao = emitir_parecer_fiscal(dados_nao_optante)
        self.assertEqual(parecer_nao["classificacao"], "NÃO OPTANTE (REGIME GERAL)")
        self.assertFalse(parecer_nao["is_optante_simples"])

        # Caso Baixada / Inapta (Alerta Fiscal)
        dados_baixada = {
            "sucesso": True,
            "situacao_cadastral": "BAIXADA",
            "opcao_pelo_simples": False
        }
        parecer_bx = emitir_parecer_fiscal(dados_baixada)
        self.assertEqual(parecer_bx["risco_fiscal"], "CRÍTICO")

    def test_deteccao_coluna_e_processamento_lote(self):
        caminho_xlsx = "sample_data/notas_faturadas_hileia_exemplo.xlsx"
        with open(caminho_xlsx, "rb") as f:
            bytes_data = f.read()

        df = carregar_planilha(bytes_data, "notas_faturadas_hileia_exemplo.xlsx")
        coluna, todas = detectar_coluna_cnpj(df)
        self.assertEqual(coluna, "CNPJ_Cliente")

        # Processamento em lote
        df_completo, df_resumo, kpis = processar_lote_cnpjs(df, coluna, self.client)
        
        self.assertEqual(len(df_completo), len(df))
        self.assertIn("Enquadramento", df_completo.columns)
        self.assertIn("Optante Simples?", df_completo.columns)
        self.assertIn("Parecer da Auditoria", df_completo.columns)
        self.assertGreater(kpis["total_unicos"], 0)
        self.assertGreater(len(df_resumo), 0)

        # Teste de exportação Excel
        excel_bytes = exportar_para_excel(df_completo, df_resumo, kpis)
        self.assertGreater(len(excel_bytes), 1000)

        # Teste de exportação CSV
        csv_bytes = exportar_para_csv(df_completo)
        self.assertGreater(len(csv_bytes), 100)


if __name__ == "__main__":
    unittest.main()

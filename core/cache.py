"""
Módulo de Cache Local SQLite para CNPJs consultados.
Garante alta performance, minimiza requisições repetidas e assegura persistência controlada.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple


class CNPJCache:
    def __init__(self, db_path: str = "data/cnpj_cache.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cnpj_cache (
                    cnpj TEXT PRIMARY KEY,
                    razao_social TEXT,
                    situacao_cadastral TEXT,
                    opcao_simples INTEGER,
                    data_opcao_simples TEXT,
                    data_exclusao_simples TEXT,
                    opcao_mei INTEGER,
                    data_opcao_mei TEXT,
                    data_exclusao_mei TEXT,
                    cnae_principal TEXT,
                    uf TEXT,
                    municipio TEXT,
                    dados_completos_json TEXT,
                    status_consulta TEXT,
                    consultado_em TEXT
                )
            """)
            conn.commit()

    def get(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """Recupera dados em cache para um CNPJ limpo de 14 dígitos."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM cnpj_cache WHERE cnpj = ?", (cnpj,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                if res.get("dados_completos_json"):
                    try:
                        res["raw_json"] = json.loads(res["dados_completos_json"])
                    except Exception:
                        res["raw_json"] = {}
                return res
        return None

    def set(self, cnpj: str, data: Dict[str, Any], status_consulta: str = "OK"):
        """Salva ou atualiza os dados de um CNPJ no cache local."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cnpj_cache (
                    cnpj, razao_social, situacao_cadastral, opcao_simples,
                    data_opcao_simples, data_exclusao_simples, opcao_mei,
                    data_opcao_mei, data_exclusao_mei, cnae_principal,
                    uf, municipio, dados_completos_json, status_consulta, consultado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cnpj,
                data.get("razao_social") or "",
                data.get("descricao_situacao_cadastral") or data.get("situacao_cadastral") or "",
                1 if data.get("opcao_pelo_simples") is True else (0 if data.get("opcao_pelo_simples") is False else None),
                data.get("data_opcao_pelo_simples"),
                data.get("data_exclusao_do_simples"),
                1 if data.get("opcao_pelo_mei") is True else (0 if data.get("opcao_pelo_mei") is False else None),
                data.get("data_opcao_pelo_mei"),
                data.get("data_exclusao_do_mei"),
                data.get("cnae_fiscal_descricao") or "",
                data.get("uf") or "",
                data.get("municipio") or "",
                json.dumps(data, ensure_ascii=False),
                status_consulta,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def clear(self):
        """Limpa todo o cache (privacidade/LGPD ou reinício de auditoria)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cnpj_cache")
            conn.commit()

    def count(self) -> int:
        """Retorna o total de CNPJs em cache."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cnpj_cache")
            return cursor.fetchone()[0]

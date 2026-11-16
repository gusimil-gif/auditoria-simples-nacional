"""
Módulo de Autenticação e Controle de Acesso do Sistema de Auditoria.
Gerencia usuário master, senhas com hash criptográfico e controle de sessão.
"""

import hashlib
import os

# Usuário e senha padrão caso não configurados em variáveis de ambiente
DEFAULT_MASTER_USER = os.getenv("AUDIT_MASTER_USER", "gustavo")
DEFAULT_MASTER_PASS = os.getenv("AUDIT_MASTER_PASS", "123mudar")


def _hash_senha(senha: str) -> str:
    """Gera hash SHA-256 da senha."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


# Tabela de credenciais cadastradas (usuário: lista de hashes de senhas autorizadas)
USUARIOS_AUTORIZADOS = {
    "gustavo": [_hash_senha("123mudar"), _hash_senha("Auditoria@2026")],
    "admin": [_hash_senha("123mudar"), _hash_senha("Auditoria@2026")],
    "auditoria": [_hash_senha("Hileia@2026"), _hash_senha("123mudar")]
}


def autenticar_usuario(usuario: str, senha: str) -> bool:
    """Verifica se o usuário e senha são válidos."""
    if not usuario or not senha:
        return False
    
    usuario_norm = usuario.strip().lower()
    hashes_esperados = USUARIOS_AUTORIZADOS.get(usuario_norm)
    
    if not hashes_esperados:
        return False
        
    if isinstance(hashes_esperados, str):
        hashes_esperados = [hashes_esperados]
        
    return _hash_senha(senha.strip()) in hashes_esperados


def obter_credenciais_master() -> dict:
    """Retorna as credenciais configuradas para exibição autorizada."""
    return {
        "usuario": DEFAULT_MASTER_USER,
        "senha": DEFAULT_MASTER_PASS
    }

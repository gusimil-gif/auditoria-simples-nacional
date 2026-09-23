"""
Módulo de Autenticação e Controle de Acesso do Sistema de Auditoria.
Gerencia usuário master, senhas com hash criptográfico e controle de sessão.
"""

import hashlib
import os

# Usuário e senha padrão caso não configurados em variáveis de ambiente
DEFAULT_MASTER_USER = os.getenv("AUDIT_MASTER_USER", "admin")
DEFAULT_MASTER_PASS = os.getenv("AUDIT_MASTER_PASS", "Auditoria@2026")


def _hash_senha(senha: str) -> str:
    """Gera hash SHA-256 da senha."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


# Tabela de credenciais cadastradas (usuário: hash da senha)
USUARIOS_AUTORIZADOS = {
    DEFAULT_MASTER_USER: _hash_senha(DEFAULT_MASTER_PASS),
    "auditoria": _hash_senha("Hileia@2026"),
    "gustavo": _hash_senha("Auditoria@2026")
}


def autenticar_usuario(usuario: str, senha: str) -> bool:
    """Verifica se o usuário e senha são válidos."""
    if not usuario or not senha:
        return False
    
    usuario_norm = usuario.strip().lower()
    hash_esperado = USUARIOS_AUTORIZADOS.get(usuario_norm)
    
    if not hash_esperado:
        return False
        
    return _hash_senha(senha.strip()) == hash_esperado


def obter_credenciais_master() -> dict:
    """Retorna as credenciais configuradas para exibição autorizada."""
    return {
        "usuario": DEFAULT_MASTER_USER,
        "senha": DEFAULT_MASTER_PASS
    }

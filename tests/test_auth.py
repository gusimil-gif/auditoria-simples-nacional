import unittest
from core.auth import autenticar_usuario, obter_credenciais_master


class TestAuth(unittest.TestCase):
    def test_autenticacao_master(self):
        creds = obter_credenciais_master()
        self.assertTrue(autenticar_usuario(creds["usuario"], creds["senha"]))
        self.assertTrue(autenticar_usuario("admin", "Auditoria@2026"))
        self.assertTrue(autenticar_usuario("ADMIN", "Auditoria@2026"))
        self.assertFalse(autenticar_usuario("admin", "senha_errada"))
        self.assertFalse(autenticar_usuario("usuario_inexistente", "Auditoria@2026"))
        self.assertFalse(autenticar_usuario("", ""))


if __name__ == "__main__":
    unittest.main()

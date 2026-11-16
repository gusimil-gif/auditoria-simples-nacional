import unittest
from core.auth import autenticar_usuario, obter_credenciais_master


class TestAuth(unittest.TestCase):
    def test_autenticacao_master(self):
        creds = obter_credenciais_master()
        self.assertTrue(autenticar_usuario(creds["usuario"], creds["senha"]))
        self.assertTrue(autenticar_usuario("gustavo", "123mudar"))
        self.assertTrue(autenticar_usuario("Gustavo", "123mudar"))
        self.assertTrue(autenticar_usuario("admin", "123mudar"))
        self.assertTrue(autenticar_usuario("ADMIN", "123mudar"))
        self.assertTrue(autenticar_usuario("admin", "Auditoria@2026"))
        self.assertFalse(autenticar_usuario("gustavo", "senha_errada"))
        self.assertFalse(autenticar_usuario("usuario_inexistente", "123mudar"))
        self.assertFalse(autenticar_usuario("", ""))


if __name__ == "__main__":
    unittest.main()

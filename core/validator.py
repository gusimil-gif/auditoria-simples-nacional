"""
Módulo de validação e formatação de CNPJs.
Implementa o cálculo dos dígitos verificadores (Módulo 11) segundo regras da Receita Federal do Brasil.
"""

import re
from typing import Tuple, Optional


def limpar_cnpj(cnpj_raw: any) -> str:
    """
    Remove pontuação e caracteres não numéricos.
    Trata números vindos de Excel (ex: float ou int) e adiciona zeros à esquerda até 14 dígitos.
    """
    if cnpj_raw is None:
        return ""
    
    # Se for float (ex: 4912871000132.0 do Excel)
    if isinstance(cnpj_raw, float):
        cnpj_str = f"{int(cnpj_raw):014d}"
    else:
        cnpj_str = str(cnpj_raw).strip()
    
    # Remove qualquer caractere que não seja dígito
    apenas_digitos = re.sub(r"\D", "", cnpj_str)
    
    # Se o Excel cortou zeros à esquerda (ex: tamanho 12 ou 13), completa até 14
    if 0 < len(apenas_digitos) < 14:
        apenas_digitos = apenas_digitos.zfill(14)
        
    return apenas_digitos


def validar_cnpj(cnpj_raw: any) -> Tuple[bool, str, Optional[str]]:
    """
    Valida matematicamente se um CNPJ é válido de acordo com o Módulo 11.
    Retorna: (is_valido, cnpj_limpo, mensagem_erro)
    """
    cnpj = limpar_cnpj(cnpj_raw)
    
    if not cnpj:
        return False, "", "CNPJ vazio ou ausente"
        
    if len(cnpj) != 14:
        return False, cnpj, f"Tamanho inválido ({len(cnpj)} dígitos, esperado 14)"
        
    # Rejeita sequências repetidas conhecidas (ex: 00000000000000, 11111111111111, etc.)
    if cnpj == cnpj[0] * 14:
        return False, cnpj, "CNPJ com dígitos todos iguais (inválido)"
        
    # Cálculo do primeiro dígito verificador
    multiplicadores_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_1 = sum(int(cnpj[i]) * multiplicadores_1[i] for i in range(12))
    resto_1 = soma_1 % 11
    digito_1 = 0 if resto_1 < 2 else 11 - resto_1
    
    if int(cnpj[12]) != digito_1:
        return False, cnpj, "1º dígito verificador incorreto"
        
    # Cálculo do segundo dígito verificador
    multiplicadores_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_2 = sum(int(cnpj[i]) * multiplicadores_2[i] for i in range(13))
    resto_2 = soma_2 % 11
    digito_2 = 0 if resto_2 < 2 else 11 - resto_2
    
    if int(cnpj[13]) != digito_2:
        return False, cnpj, "2º dígito verificador incorreto"
        
    return True, cnpj, None


def formatar_cnpj(cnpj_raw: any) -> str:
    """
    Formata o CNPJ na máscara padrão: XX.XXX.XXX/XXXX-XX.
    Caso não tenha 14 dígitos, retorna a string limpa original.
    """
    cnpj = limpar_cnpj(cnpj_raw)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
    return cnpj

"""
Script para geração de planilhas de teste realistas simulando:
1. Relatório de Notas Fiscais Faturadas (Vendas da Hiléia para clientes)
2. Relatório de Notas Fiscais de Compra (Insumos e fornecedores da Hiléia)
Inclui mistura de CNPJs reais: optantes pelo Simples Nacional, Não Optantes (Grandes empresas), MEI, e casos para teste de validação.
"""

import os
import pandas as pd


def gerar_planilhas_teste():
    os.makedirs("sample_data", exist_ok=True)
    
    # Amostra de CNPJs com perfis tributários variados
    empresas_vendas = [
        {"cnpj": "04.912.871/0001-32", "nome": "PAINEIS BELVEDERE", "valor": 12450.00, "uf": "SC", "perfil": "Simples Nacional"},
        {"cnpj": "24119851000116", "nome": "LAVANDERIA PANDA LTDA", "valor": 3200.50, "uf": "SP", "perfil": "Simples Nacional"},
        {"cnpj": "14.210.667/0001-23", "nome": "COSME RODRIGUES DA SILVA", "valor": 890.00, "uf": "BA", "perfil": "Simples Nacional"},
        {"cnpj": "00.000.000/0001-91", "nome": "BANCO DO BRASIL SA", "valor": 45000.00, "uf": "DF", "perfil": "Não Optante (Lucro Real)"},
        {"cnpj": "33.000.167/0001-01", "nome": "PETROLEO BRASILEIRO S A PETROBRAS", "valor": 98500.00, "uf": "RJ", "perfil": "Não Optante (Lucro Real)"},
        {"cnpj": "07.526.557/0001-00", "nome": "AMBEV S.A.", "valor": 54300.00, "uf": "SP", "perfil": "Não Optante (Lucro Real)"},
        # Repetições propositais para testar desduplicação
        {"cnpj": "04.912.871/0001-32", "nome": "PAINEIS BELVEDERE", "valor": 8450.00, "uf": "SC", "perfil": "Simples Nacional"},
        {"cnpj": "24119851000116", "nome": "LAVANDERIA PANDA LTDA", "valor": 1500.00, "uf": "SP", "perfil": "Simples Nacional"},
        # CNPJ com número inteiro sem zeros (simulando corte de zeros pelo Excel)
        {"cnpj": 4912871000132, "nome": "PAINEIS BELVEDERE (SEM ZERO)", "valor": 7200.00, "uf": "SC", "perfil": "Simples Nacional"},
        # CNPJ inválido proposital para teste de validação
        {"cnpj": "11.111.111/1111-11", "nome": "EMPRESA TESTE INVÁLIDA", "valor": 1200.00, "uf": "PA", "perfil": "Inválido"}
    ]

    linhas_vendas = []
    for i, emp in enumerate(empresas_vendas, start=101):
        linhas_vendas.append({
            "Numero_NF": f"NF-{i:05d}",
            "Data_Emissao": f"2026-08-{((i % 25) + 1):02d}",
            "CNPJ_Cliente": emp["cnpj"],
            "Razao_Cliente": emp["nome"],
            "UF_Destino": emp["uf"],
            "Valor_Total_Nota": emp["valor"],
            "Natureza_Operacao": "Venda de Produção Própria (Hiléia)"
        })

    df_vendas = pd.DataFrame(linhas_vendas)
    vendas_path = "sample_data/notas_faturadas_hileia_exemplo.xlsx"
    df_vendas.to_excel(vendas_path, index=False)
    print(f"Criado: {vendas_path} ({len(df_vendas)} linhas)")

    # 2. Planilha de Compras da Hiléia (Fornecedores de insumos, trigo, embalagens, serviços)
    empresas_compras = [
        {"cnpj": "03.007.331/0001-41", "fornecedor": "MERCADO LIVRE BRASIL LTDA", "valor": 2840.00, "item": "Materiais de Escritório"},
        {"cnpj": "04.912.871/0001-32", "fornecedor": "PAINEIS BELVEDERE", "valor": 15400.00, "item": "Manutenção Predial e Painéis"},
        {"cnpj": "33.592.510/0001-54", "fornecedor": "VALE S.A.", "valor": 88000.00, "item": "Insumos e Matérias-Primas"},
        {"cnpj": "14210667000123", "fornecedor": "COSME RODRIGUES DA SILVA", "valor": 4500.00, "item": "Prestação de Serviços Especializados"},
        {"cnpj": "05.044.205/0001-92", "fornecedor": "A & L FASHION (BAIXADA)", "valor": 3100.00, "item": "Uniformes Industriais"},
        {"cnpj": "04.912.871/0001-32", "fornecedor": "PAINEIS BELVEDERE", "valor": 9800.00, "item": "Serviços Adicionais"}
    ]

    linhas_compras = []
    for i, emp in enumerate(empresas_compras, start=5001):
        linhas_compras.append({
            "Chave_NFe": f"152608049128710001325500100000{i}1234567890",
            "Numero_Doc": i,
            "Data_Entrada": f"2026-08-{((i % 20) + 1):02d}",
            "CNPJ_Fornecedor": emp["cnpj"],
            "Nome_Fornecedor": emp["fornecedor"],
            "Descricao_Insumo": emp["item"],
            "Valor_Contabil": emp["valor"],
            "Status_Entrada": "Recebida e Conferida"
        })

    df_compras = pd.DataFrame(linhas_compras)
    compras_path = "sample_data/notas_compras_hileia_exemplo.xlsx"
    df_compras.to_excel(compras_path, index=False)
    print(f"Criado: {compras_path} ({len(df_compras)} linhas)")

    # Também gera um exemplo em CSV para validar compatibilidade com CSV
    csv_path = "sample_data/cadastro_clientes_exemplo.csv"
    df_vendas.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
    print(f"Criado: {csv_path} ({len(df_vendas)} linhas)")


if __name__ == "__main__":
    gerar_planilhas_teste()

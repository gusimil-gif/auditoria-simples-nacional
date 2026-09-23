# 🏛️ Sistema de Auditoria Fiscal e Consulta do Simples Nacional (Hiléia)

Sistema web simples, robusto e funcional desenvolvido para automatizar a verificação cadastral e tributária de clientes e fornecedores a partir de relatórios de **Notas Fiscais Faturadas (Vendas)**, **Notas Fiscais de Compra** ou **Cadastros Gerais**.

O sistema consulta em lote e em tempo real a situação cadastral perante a **Receita Federal do Brasil (RFB)**, validando se o CNPJ é optante pelo **Simples Nacional**, **SIMEI (MEI)** ou **Regime Geral (Lucro Presumido / Lucro Real)**, emitindo pareceres técnicos de auditoria e exportando relatórios executivos em **Excel (.xlsx estilizado)** e **CSV**.

---

## ✨ Principais Funcionalidades

1. **Ingestão Inteligente de Planilhas:**
   - Suporte a `.xlsx`, `.xls` e `.csv`.
   - Detecção heurística automática da coluna de CNPJ (com opção de seleção manual).
   - Sanitização de dados: limpa pontuações e recupera zeros à esquerda cortados pelo Excel.
   - **Desduplicação em Lote:** agrupa CNPJs repetidos para consultar a API uma única vez, economizando tempo e evitando limites de taxa.

2. **Auditoria com APIs Oficiais Gratuitas:**
   - Validação prévia de dígitos verificadores (Módulo 11) para evitar chamadas de rede em CNPJs inválidos.
   - Cascata de APIs gratuitas e oficiais: **BrasilAPI** com failover automático para **Minha Receita (RFB)**.
   - Cache local SQLite seguro para consultas instantâneas e sem retrabalho.

3. **Parecer Técnico de Auditoria:**
   - Classificação tributária: *Optante Simples*, *SIMEI*, *Não Optante*, *Excluído do Simples*.
   - Risco cadastral: identifica empresas com situação cadastral *BAIXADA*, *INAPTA*, *SUSPENSA* ou *NULA* (alerta de inidoneidade fiscal).
   - Parecer fiscal técnico fundamentado na LC 123/2006 e IN RFB nº 1.234/2012 orientando sobre retenções tributárias de PIS, COFINS, CSLL, IRRF e ISS.

4. **Exportação Executiva Profissional:**
   - **Excel (.xlsx)** com múltiplas abas:
     - *Base Auditada*: notas originais com enquadramento e parecer linha por linha.
     - *Resumo por CNPJ*: visão consolidada com contagem de notas e parecer resumido.
     - *Sumário Executivo*: indicadores percentuais, totais e recomendações de compliance.
   - **CSV**: formatado com codificação UTF-8-BOM e separador `;` para abertura direta no Excel brasileiro.

5. **Consulta Individual Avulsa:**
   - Digitação avulsa de qualquer CNPJ com retorno em segundos do cartão cadastral completo, endereço, atividade (CNAE), quadro societário (QSA) e parecer fiscal.

6. **Segurança e LGPD:**
   - Apenas o número do CNPJ (dado público) é consultado nas bases abertas da Receita Federal.
   - Botões na barra lateral para expurgar dados de sessão e cache quando desejado.

7. **Pronto para Hospedagem 100% Gratuita:**
   - Compatível com **Streamlit Community Cloud**, **Hugging Face Spaces** e **Render**.
   - Consulte o arquivo `DEPLOY.md` para instruções passo a passo.

---

## 🚀 Como Executar Localmente

### 1. Clonar ou Acessar a Pasta
```bash
cd "APP Verificação Simples"
```

### 2. Ativar o Ambiente Virtual
- **Mac / Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```

### 3. Instalar Dependências (se ainda não instalado)
```bash
pip install -r requirements.txt
```

### 4. Executar o Aplicativo
```bash
streamlit run app.py
```
O sistema abrirá automaticamente no seu navegador padrão no endereço `http://localhost:8501`.

---

## 🧪 Amostras de Teste Inclusas

Na pasta `sample_data/` estão disponíveis relatórios prontos que você pode carregar diretamente pelo aplicativo:
- `notas_faturadas_hileia_exemplo.xlsx`: Simulação de notas de vendas da Hiléia para clientes.
- `notas_compras_hileia_exemplo.xlsx`: Simulação de notas de compras de insumos e matérias-primas.
- `cadastro_clientes_exemplo.csv`: Amostra em formato CSV.

Você também pode carregar estes exemplos clicando nos botões **"NF Vendas"** ou **"NF Compras"** na barra lateral do próprio sistema!

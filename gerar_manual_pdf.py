"""
Script para geração do Manual de Operação do Sistema de Auditoria Fiscal em formato PDF.
Design corporativo, estruturado em exatamente 4 páginas, com cabeçalho, rodapé e paginação.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas para inserção automática de numeração 'Página X de Y' e cabeçalho corporativo."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_header_footer(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E3A8A")) # Azul Corporativo
        
        # Cabeçalho (Páginas 2 em diante)
        if self._pageNumber > 1:
            self.drawString(45, 755, "HILÉIA ALIMENTOS | AUDITORIA CONTÁBIL, FISCAL E FINANCEIRA")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(565, 755, "Sistema de Verificação do Simples Nacional")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(45, 747, 565, 747)

        # Rodapé em todas as páginas
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(45, 45, 565, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(45, 33, "Manual de Operação do Usuário - Confidencial & Uso Interno")
        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(565, 33, page_str)
        self.restoreState()


def criar_manual_pdf(caminho_saida: str):
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    # Estilos customizados
    azul_escuro = colors.HexColor("#1E3A8A")
    azul_medio = colors.HexColor("#2563EB")
    cinza_texto = colors.HexColor("#1F2937")
    cinza_claro = colors.HexColor("#F8FAFC")
    verde_status = colors.HexColor("#166534")

    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=azul_escuro,
        alignment=0
    )

    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        alignment=0
    )

    style_h1 = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=azul_escuro,
        spaceBefore=10,
        spaceAfter=6
    )

    style_h2 = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=azul_medio,
        spaceBefore=7,
        spaceAfter=4
    )

    style_body = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.2,
        textColor=cinza_texto,
        spaceAfter=5
    )

    style_bullet = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12,
        textColor=cinza_texto,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    style_callout = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B")
    )

    elementos = []

    # =========================================================================
    # PÁGINA 1: CAPA & APRESENTAÇÃO EXECUTIVA
    # =========================================================================
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph("MANUAL DE OPERAÇÃO", style_subtitle))
    elementos.append(Paragraph("Sistema de Auditoria Fiscal & Verificação de Optantes pelo Simples Nacional", style_title))
    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph("Validação cadastral em lote de clientes e fornecedores perante a Receita Federal do Brasil (RFB)", style_subtitle))
    elementos.append(Spacer(1, 12))
    elementos.append(HRFlowable(width="100%", thickness=2, color=azul_escuro, spaceBefore=0, spaceAfter=12))

    # Tabela de Metadados do Sistema
    dados_meta = [
        [Paragraph("<b>Aplicação:</b>", style_body), Paragraph("Auditoria Fiscal Simples Nacional", style_body),
         Paragraph("<b>Versão:</b>", style_body), Paragraph("1.0.0 (Produção)", style_body)],
        [Paragraph("<b>Organização:</b>", style_body), Paragraph("Hiléia Alimentos", style_body),
         Paragraph("<b>Setor:</b>", style_body), Paragraph("Auditoria Contábil / Fiscal / Financeira", style_body)],
        [Paragraph("<b>Status Online:</b>", style_body), Paragraph("<b>100% Operacional (HTTPS)</b>", style_body),
         Paragraph("<b>Atualização:</b>", style_body), Paragraph("Setembro / 2026", style_body)]
    ]
    t_meta = Table(dados_meta, colWidths=[80, 180, 80, 180])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_meta)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("1. Visão Geral e Finalidade", style_h1))
    elementos.append(Paragraph(
        "Este sistema foi projetado especificamente para suprir a necessidade de auditoria e compliance "
        "tributário da <b>Hiléia</b>, automatizando a conferência de enquadramento tributário de clientes e fornecedores "
        "a partir de relatórios de <b>Notas Fiscais Faturadas (Vendas)</b>, <b>Notas Fiscais de Entrada (Compras)</b> ou <b>Cadastros Gerais</b>. "
        "Elimina completamente a consulta manual lenta e individual no site da Receita Federal, permitindo auditar centenas ou "
        "milhares de notas fiscais em segundos e emitir pareceres contábeis com fundamentação legal.",
        style_body
    ))

    elementos.append(Paragraph("2. Credenciais e Endereço de Acesso Online", style_h1))
    elementos.append(Paragraph(
        "O aplicativo está hospedado online e acessível publicamente via navegador em qualquer dispositivo (desktop, notebook ou tablet):",
        style_body
    ))

    dados_acesso = [
        [Paragraph("<b>Link Online Ativo:</b>", style_body), Paragraph("https://33e3e0a40fb261f3-179-98-75-109.serveousercontent.com", style_body)],
        [Paragraph("<b>Deploy Permanente 24/7 (Streamlit Cloud):</b>", style_body), Paragraph("https://github.com/gusimil-gif/auditoria-simples-nacional", style_body)],
        [Paragraph("<b>Endereço na Rede Local (Wi-Fi):</b>", style_body), Paragraph("http://192.168.15.132:8501", style_body)],
        [Paragraph("<b>Usuário Master:</b>", style_body), Paragraph("<font color='#1E3A8A'><b>admin</b></font>", style_body)],
        [Paragraph("<b>Senha Master:</b>", style_body), Paragraph("<font color='#1E3A8A'><b>Auditoria@2026</b></font>", style_body)],
        [Paragraph("<b>Usuários Adicionais:</b>", style_body), Paragraph("<b>auditoria</b> (Senha: Hileia@2026) | <b>gustavo</b> (Senha: Auditoria@2026)", style_body)]
    ]
    t_acesso = Table(dados_acesso, colWidths=[160, 360])
    t_acesso.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#FFFFFF")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_acesso)
    elementos.append(Spacer(1, 10))

    # Box de Destaque
    box_p1 = [
        [Paragraph("<b>Importante sobre Segurança & LGPD:</b> O acesso é restrito por credenciais master. "
                   "O sistema consulta apenas a base pública oficial da Receita Federal (RFB). "
                   "Nenhum valor financeiro de nota fiscal, chave de NFe ou dado confidencial da Hiléia sai do servidor seguro.", style_callout)]
    ]
    t_box_p1 = Table(box_p1, colWidths=[520])
    t_box_p1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(t_box_p1)

    elementos.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: PASSO A PASSO DA AUDITORIA EM LOTE (PLANILHAS)
    # =========================================================================
    elementos.append(Paragraph("3. Passo a Passo: Auditoria em Lote de Planilhas", style_h1))
    elementos.append(Paragraph(
        "A funcionalidade principal do sistema reside na aba <b>'📊 Auditoria em Lote (Planilhas)'</b>. "
        "Siga as etapas abaixo para auditar qualquer relatório de compras ou vendas:",
        style_body
    ))

    elementos.append(Paragraph("Passo 1: Preparação do Arquivo de Entrada", style_h2))
    elementos.append(Paragraph("• <b>Formatos Aceitos:</b> Arquivos Microsoft Excel (<code>.xlsx</code>, <code>.xls</code>) ou texto delimitado (<code>.csv</code>).", style_bullet))
    elementos.append(Paragraph("• <b>Conteúdo:</b> O arquivo pode ter qualquer quantidade de colunas (Número da NF, Data de Emissão, Valor, etc.). O único requisito é possuir ao menos uma coluna com o CNPJ do cliente ou fornecedor.", style_bullet))
    elementos.append(Paragraph("• <b>Tolerância de Formatação:</b> O sistema aceita CNPJs pontuados (<code>04.912.871/0001-32</code>), sem pontuação (<code>04912871000132</code>) e corrige automaticamente números onde o Excel removeu os zeros à esquerda (ex: 12 ou 13 dígitos).", style_bullet))

    elementos.append(Paragraph("Passo 2: Upload da Planilha no Sistema", style_h2))
    elementos.append(Paragraph("1. Acesse o sistema e selecione a primeira aba <b>'📊 Auditoria em Lote (Planilhas)'</b>.", style_bullet))
    elementos.append(Paragraph("2. Clique na caixa <b>'Browse files'</b> (ou arraste a planilha para a área indicada).", style_bullet))
    elementos.append(Paragraph("3. O sistema carregará o arquivo instantaneamente e informará a quantidade total de linhas detectadas.", style_bullet))

    elementos.append(Paragraph("Passo 3: Mapeamento Inteligente da Coluna de CNPJ", style_h2))
    elementos.append(Paragraph(
        "O sistema possui um algoritmo heurístico que identifica automaticamente a coluna correta através de palavras-chave "
        "(ex.: <code>CNPJ_Cliente</code>, <code>CNPJ_Fornecedor</code>, <code>CPF/CNPJ</code>, <code>Documento</code>) ou por padrão de 14 dígitos. "
        "Caso deseje auditar outra coluna, basta selecioná-la no menu suspenso disponibilizado.",
        style_body
    ))

    elementos.append(Paragraph("Passo 4: Disparo da Auditoria e Acompanhamento em Tempo Real", style_h2))
    elementos.append(Paragraph("1. Clique no botão de destaque azul <b>'🚀 Iniciar Auditoria em Lote'</b>.", style_bullet))
    elementos.append(Paragraph("2. Uma barra de progresso interativa exibirá a evolução percentual, o CNPJ em consulta e a Razão Social em tempo real.", style_bullet))
    elementos.append(Paragraph("3. Ao término, uma notificação de sucesso indicará o tempo total decorrido.", style_bullet))

    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph("Como Funciona o Motor de Otimização e Desduplicação:", style_h2))
    
    tabela_otim = [
        [Paragraph("<b>Etapa</b>", style_body), Paragraph("<b>Mecanismo Técnico</b>", style_body), Paragraph("<b>Benefício para a Hiléia</b>", style_body)],
        [Paragraph("<b>1. Filtro Módulo 11</b>", style_body), Paragraph("Validação matemática prévia dos dígitos verificadores.", style_body), Paragraph("Evita consultas externas para CNPJs digitados errados.", style_body)],
        [Paragraph("<b>2. Desduplicação</b>", style_body), Paragraph("Agrupamento de CNPJs únicos antes de chamar a rede.", style_body), Paragraph("Se 500 notas forem do mesmo fornecedor, consulta a API apenas 1 vez!", style_body)],
        [Paragraph("<b>3. Cache SQLite</b>", style_body), Paragraph("Persistência local no banco <code>cnpj_cache.db</code>.", style_body), Paragraph("Consultas já feitas em arquivos anteriores retornam em 0,001s.", style_body)],
        [Paragraph("<b>4. Fallback de APIs</b>", style_body), Paragraph("BrasilAPI oficial com transbordo para Minha Receita.", style_body), Paragraph("Zero risco de paralisação por instabilidade temporária.", style_body)]
    ]
    t_otim = Table(tabela_otim, colWidths=[100, 210, 210])
    t_otim.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    elementos.append(t_otim)

    elementos.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: INTERPRETAÇÃO DOS PARECERES E EXPORTAÇÃO
    # =========================================================================
    elementos.append(Paragraph("4. Indicadores de Auditoria e Pareceres Fiscais", style_h1))
    elementos.append(Paragraph(
        "Imediatamente após o processamento, o sistema exibe o painel de KPIs executivos e classifica cada CNPJ com base na legislação tributária vigente:",
        style_body
    ))

    tabela_classif = [
        [Paragraph("<b>Enquadramento</b>", style_body), Paragraph("<b>Identificação</b>", style_body), Paragraph("<b>Parecer Fiscal & Implicações de Auditoria</b>", style_body)],
        [Paragraph("<font color='#166534'><b>OPTANTE PELO SIMPLES</b></font>", style_body), Paragraph("<code>opcao_pelo_simples: True</code>", style_body), Paragraph("<b>Dispensa de Retenção:</b> Fornecedor dispensado de retenções federais na fonte de IRRF, CSLL, PIS e COFINS conforme art. 30 da Lei 10.833/2003 e IN RFB nº 1.234/2012.", style_body)],
        [Paragraph("<font color='#854D0E'><b>SIMEI (MEI)</b></font>", style_body), Paragraph("<code>opcao_pelo_mei: True</code>", style_body), Paragraph("<b>Microempreendedor Individual:</b> Dispensa ampla de retenções na fonte. Sujeito ao recolhimento mensal fixo (DAS-MEI).", style_body)],
        [Paragraph("<font color='#374151'><b>NÃO OPTANTE</b></font>", style_body), Paragraph("<code>opcao_pelo_simples: False</code>", style_body), Paragraph("<b>Regime Normal (Lucro Presumido / Lucro Real):</b> Obrigatória a verificação e incidência das retenções cabíveis na fonte nas notas de serviços/fornecimento.", style_body)],
        [Paragraph("<font color='#C2410C'><b>EXCLUÍDO DO SIMPLES</b></font>", style_body), Paragraph("Possui data de exclusão registrada", style_body), Paragraph("<b>Ex-Optante:</b> Conferir a data exata da exclusão em relação à data de emissão da NF para garantir que não houve omissão de tributos devidos.", style_body)],
        [Paragraph("<font color='#991B1B'><b>RISCO CADASTRAL (BAIXADA / INAPTA)</b></font>", style_body), Paragraph("Situação diferente de 'ATIVA'", style_body), Paragraph("<b>ALERTA GRAVE:</b> Risco iminente de inidoneidade fiscal da nota e glosa de créditos tributários (ICMS/PIS/COFINS). Exige abertura de averiguação imediata.", style_body)]
    ]
    t_classif = Table(tabela_classif, colWidths=[120, 120, 280])
    t_classif.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_classif)
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("5. Filtragem Dinâmica e Exportação dos Resultados", style_h1))
    elementos.append(Paragraph(
        "Abaixo dos indicadores, a equipe de auditoria conta com ferramentas interativas de navegação e exportação completa:",
        style_body
    ))
    elementos.append(Paragraph("• <b>Filtros por Enquadramento:</b> Permite isolar instantaneamente apenas fornecedores do Simples, MEI ou Não Optantes.", style_bullet))
    elementos.append(Paragraph("• <b>Filtro de Risco Fiscal:</b> Selecione 'CRÍTICO' para listar apenas empresas Baixadas, Inaptas ou com dados inconsistentes.", style_bullet))
    elementos.append(Paragraph("• <b>Busca Textual:</b> Campo de pesquisa rápida por CNPJ ou nome da Razão Social.", style_bullet))

    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph("Formatos de Download Disponibilizados:", style_h2))

    dados_exp = [
        [Paragraph("<b>📥 Relatório Completo (.xlsx)</b>", style_body), Paragraph("<b>Recomendado para Auditoria:</b> Pasta de trabalho do Excel com 3 abas estilizadas:<br/>"
                                                                                 "• <i>Aba 1 (Base Auditada):</i> Planilha original integral com as 13 colunas de auditoria anexadas e cores condicionais automáticas (Verde, Amarelo, Laranja, Cinza).<br/>"
                                                                                 "• <i>Aba 2 (Resumo por CNPJ):</i> 1 linha por parceiro com contagem de notas associadas.<br/>"
                                                                                 "• <i>Aba 3 (Sumário Executivo):</i> Resumo gerencial de indicadores e parecer contábil.", style_body)],
        [Paragraph("<b>📥 Base em CSV (.csv)</b>", style_body), Paragraph("Arquivo delimitado por ponto e vírgula (<code>;</code>) com codificação <b>UTF-8 com BOM</b>, garantindo acentuação perfeita e abertura direta no Microsoft Excel brasileiro.", style_body)],
        [Paragraph("<b>📥 Resumo de CNPJs (.csv)</b>", style_body), Paragraph("Exportação sintética com apenas os parceiros únicos para cadastros e sistemas ERP.", style_body)]
    ]
    t_exp = Table(dados_exp, colWidths=[160, 360])
    t_exp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#93C5FD")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_exp)

    elementos.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: CONSULTA INDIVIDUAL, GESTÃO DE CACHE E SUPORTE
    # =========================================================================
    elementos.append(Paragraph("6. Consulta Individual Avulsa (Cartão do CNPJ)", style_h1))
    elementos.append(Paragraph(
        "Para verificar um fornecedor ou cliente de forma pontual sem necessidade de planilha, use a aba <b>'🔍 Consulta Individual Avulsa'</b>:",
        style_body
    ))
    elementos.append(Paragraph("1. Digite o CNPJ no campo de busca (com ou sem máscara) e clique em <b>'🔍 Consultar CNPJ'</b>.", style_bullet))
    elementos.append(Paragraph("2. O sistema exibe o <b>Cartão Cadastral Completo</b> com badge visual de enquadramento:", style_bullet))
    elementos.append(Paragraph("   • Razão Social, Nome Fantasia, Situação Cadastral e Data da Situação.", style_bullet))
    elementos.append(Paragraph("   • Status do Simples Nacional, Data de Opção e Data de Exclusão.", style_bullet))
    elementos.append(Paragraph("   • Status do SIMEI (MEI), Porte da Empresa e Natureza Jurídica.", style_bullet))
    elementos.append(Paragraph("   • Endereço completo, Município, UF, CEP e CNAE Fiscal Principal.", style_bullet))
    elementos.append(Paragraph("   • <b>Quadro de Sócios e Administradores (QSA):</b> Nomes, qualificações e faixa etária de todos os sócios registrados na Receita Federal.", style_bullet))

    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph("7. Histórico Acumulado e Gestão de Cache", style_h1))
    elementos.append(Paragraph(
        "Na aba <b>'📋 Histórico & Pareceres'</b>, você tem acesso a todos os CNPJs já auditados desde o início do uso do sistema. "
        "É possível pesquisar parceiros consultados em sessões anteriores e baixar o arquivo <code>Historico_Auditoria_CNPJs.csv</code> completo.",
        style_body
    ))

    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph("8. Segurança, Boas Práticas e Encerramento de Sessão", style_h1))
    elementos.append(Paragraph("• <b>Botão 'Limpar Cache':</b> Localizado na barra lateral, permite zerar o banco SQLite caso deseje forçar nova consulta de todas as empresas.", style_bullet))
    elementos.append(Paragraph("• <b>Botão 'Zerar Sessão':</b> Limpa todas as planilhas carregadas da memória do servidor para garantir conformidade de confidencialidade.", style_bullet))
    elementos.append(Paragraph("• <b>Logout:</b> Clique no botão <b>'🚪 Sair'</b> na barra lateral ao terminar o trabalho para bloquear a interface.", style_bullet))

    elementos.append(Spacer(1, 6))
    elementos.append(Paragraph("9. Guia de Inicialização e Suporte Técnico", style_h1))

    dados_suporte = [
        [Paragraph("<b>Como rodar no computador:</b>", style_body), Paragraph("Execute o atalho <code>./iniciar.sh</code> (Mac/Linux) ou <code>iniciar.bat</code> (Windows). O sistema e o túnel seguro iniciam automaticamente.", style_body)],
        [Paragraph("<b>Relatórios de Exemplo:</b>", style_body), Paragraph("Clique nos botões <b>'NF Vendas'</b> ou <b>'NF Compras'</b> na barra lateral para carregar simulações prontas com dados da Hiléia.", style_body)],
        [Paragraph("<b>Controle de Acesso:</b>", style_body), Paragraph("Novos usuários ou alterações de senha podem ser configurados no arquivo <code>core/auth.py</code>.", style_body)],
        [Paragraph("<b>Compatibilidade:</b>", style_body), Paragraph("Compatível com Google Chrome, Microsoft Edge, Safari e Mozilla Firefox em qualquer resolução.", style_body)]
    ]
    t_sup = Table(dados_suporte, colWidths=[150, 370])
    t_sup.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_sup)

    elementos.append(Spacer(1, 14))
    # Box de Conclusão
    box_fim = [
        [Paragraph("<para align='center'><b>EQUIPE DE AUDITORIA CONTÁBIL, FISCAL E FINANCEIRA — HILÉIA ALIMENTOS</b><br/>"
                   "<font size=7 color='#64748B'>Documento homologado para fins de orientação operacional e compliance fiscal interno.</font></para>", style_body)]
    ]
    t_fim = Table(box_fim, colWidths=[520])
    t_fim.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#2563EB")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(t_fim)

    # Constrói o PDF
    doc.build(elementos, canvasmaker=NumberedCanvas)
    print(f"Manual em PDF gerado com sucesso em: {caminho_saida}")


if __name__ == "__main__":
    criar_manual_pdf("Manual_Operacao_Auditoria_Simples_Nacional.pdf")

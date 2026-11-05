"""Gera o Excel analitico a partir do pipeline. Nenhum numero digitado a mao."""
import json, pathlib
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = str(RAIZ / 'resultados')
M = json.load(open(f'{OUT}/metricas.json', encoding='utf-8'))
df = pd.read_pickle(f'{OUT}/tabelas/base_limpa.pkl')
t_drv = pd.read_csv(f'{OUT}/tabelas/tab_motoristas.csv')
t_reg = pd.read_csv(f'{OUT}/tabelas/tab_regiao.csv')
t_hor = pd.read_csv(f'{OUT}/tabelas/tab_hora.csv')
t_mes = pd.read_csv(f'{OUT}/tabelas/tab_mes.csv')
t_tam = pd.read_csv(f'{OUT}/tabelas/tab_tamanho_pedido.csv')

AZUL = '1F3864'; CINZA = 'F2F2F2'; VERM = 'C00000'; VERDE = '375623'
F = 'Arial'
h_font = Font(name=F, bold=True, color='FFFFFF', size=10)
h_fill = PatternFill('solid', fgColor=AZUL)
t_font = Font(name=F, bold=True, size=13, color=AZUL)
n_font = Font(name=F, size=10)
thin = Side(style='thin', color='BFBFBF')
box = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()


def cabecalho(ws, titulo, sub=None):
    ws['A1'] = titulo; ws['A1'].font = t_font
    if sub:
        ws['A2'] = sub
        ws['A2'].font = Font(name=F, size=9, italic=True, color='595959')
    return 4


def escrever_tabela(ws, dados, linha0, col0=1, larguras=None, nome=None, fmts=None):
    for j, c in enumerate(dados.columns):
        cel = ws.cell(row=linha0, column=col0 + j, value=c)
        cel.font = h_font; cel.fill = h_fill; cel.border = box
        cel.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    for i, (_, r) in enumerate(dados.iterrows(), start=1):
        for j, c in enumerate(dados.columns):
            v = r[c]
            if pd.isna(v):
                v = None
            elif hasattr(v, 'item'):
                v = v.item()
            cel = ws.cell(row=linha0 + i, column=col0 + j, value=v)
            cel.font = n_font; cel.border = box
            if fmts and c in fmts:
                cel.number_format = fmts[c]
    if larguras:
        for j, w in enumerate(larguras):
            ws.column_dimensions[get_column_letter(col0 + j)].width = w
    if nome:
        ref = (f'{get_column_letter(col0)}{linha0}:'
               f'{get_column_letter(col0 + len(dados.columns) - 1)}{linha0 + len(dados)}')
        t = Table(displayName=nome, ref=ref)
        t.tableStyleInfo = TableStyleInfo(name='TableStyleMedium2', showRowStripes=True)
        ws.add_table(t)
    return linha0 + len(dados) + 2


# ─────────────────────────── LEIA-ME ───────────────────────────
ws = wb.active; ws.title = 'Leia-me'
ws.column_dimensions['A'].width = 4
ws.column_dimensions['B'].width = 104
r = cabecalho(ws, 'Deteccao de Fraude em Entregas de Ultima Milha, 2023',
              'Metodologia, premissas e limitacoes. Leia antes de usar qualquer numero deste arquivo.')

blocos = [
    ('SOBRE A BASE: DATASET SINTETICO', [
        'Este e um dataset sintetico, usado como exercicio de analise. Nao sao dados operacionais',
        'de nenhuma empresa real, e nenhuma conclusao deste arquivo descreve uma operacao existente.',
        'Identificar que a base e gerada, e nao observada, foi um dos dois resultados da analise.',
        'A prova esta na aba Driver_Structure: o numero de faltas por motorista e funcao',
        f"deterministica do volume de entregas (qui-quadrado contra a binomial = {M['estrutura_motoristas']['qui2_vs_binomial']:,.0f}).".replace(',', '.'),
    ]),
    ('COMO ESTE ARQUIVO E GERADO', [
        'Todo numero deste workbook e produzido por src/pipeline.py a partir da base bruta.',
        'Nenhum valor foi digitado a mao. Os KPIs da aba Overview sao formulas vivas sobre a aba Data:',
        'alterar a base e recalcular atualiza todo o arquivo.',
    ]),
    ('TRATAMENTO APLICADO A BASE', [
        f"A coluna items_delivered esta truncada em {M['artefatos']['teto_items_delivered']} itens na base original.",
        f"Isso forca 100% de falta em todo pedido com items_total acima desse teto: {M['artefatos']['pedidos_removidos']} pedidos,",
        f"todos com falta, somando {M['artefatos']['faltas_removidas']} itens ({M['artefatos']['pct_das_faltas_brutas']:.1%} das faltas brutas).",
        'Esses pedidos foram REMOVIDOS da base analitica por serem artefato de geracao, nao ocorrencia operacional.',
        f"Base analitica final: {M['kpis']['pedidos']:,} pedidos.".replace(',', '.'),
    ]),
    ('DEFINICAO DOS KPIs', [
        'KPI PRIMARIO: Incidencia por pedido: pedidos com ao menos 1 item faltante / total de pedidos.',
        'A falta e um evento que ocorre NO PEDIDO, nao em cada item. Verificado na aba Order_Size:',
        f"a incidencia nao varia com o tamanho do pedido (Spearman rho = {M['evento_por_pedido']['spearman_incidencia_vs_tamanho']:.3f}, p = {M['evento_por_pedido']['spearman_incidencia_p']:.3f}).",
        '',
        'KPI SECUNDARIO: Taxa agregada de itens: soma dos itens faltantes / soma dos itens. Mede volume.',
        '',
        'METRICA PROIBIDA: media simples de (faltantes/total) por pedido. Da o mesmo peso a um pedido',
        f"de 2 itens e a um de 19, e infla o resultado em {M['kpis']['inflacao_da_metrica_incorreta']:.2f}x. Consta na aba Overview APENAS como contraste.",
    ]),
    ('DETECCAO DE ANOMALIA POR MOTORISTA', [
        'Teste binomial exato unilateral sobre pedidos, contra a incidencia base da operacao.',
        f"Foram testados {M['anomalia']['motoristas_testados']:,} motoristas, o que exige correcao para testes multiplos:".replace(',', '.'),
        f"a {int(M['anomalia']['falsos_positivos_esperados'])} falsos positivos sao esperados so por acaso a 5%.",
        'Aplicado Benjamini-Hochberg (FDR). A coluna q_valor e o criterio de decisao, nao o p_valor.',
        f"RESULTADO: {M['anomalia']['significativos_fdr']} motoristas significativos. Menor q-valor da base: {M['anomalia']['menor_q_valor']:.3f}.",
    ]),
    ('LIMITACAO CRITICA 1: A BASE NAO TEM VARIACAO INDIVIDUAL', [
        'O numero de entregas com falta por motorista e praticamente uma funcao deterministica',
        f"do volume de entregas (ver aba Driver_Structure). {M['estrutura_motoristas']['volumes_deterministicos']} dos {M['estrutura_motoristas']['volumes_distintos']} volumes distintos admitem",
        'um unico resultado possivel; os demais admitem dois. Sob um processo aleatorio a distribuicao',
        f"seria binomial. O observado diverge dela com qui-quadrado = {M['estrutura_motoristas']['qui2_vs_binomial']:,.0f}.".replace(',', '.'),
        'CONSEQUENCIA: nao existe sinal individual a detectar nesta base, nem verdadeiro nem falso.',
    ]),
    ('LIMITACAO CRITICA 2: PODER ESTATISTICO', [
        f"O motorista mais ativo da base tem {M['poder']['entregas_disponiveis_max']} entregas no ano.",
        f"Para detectar um motorista com o dobro da incidencia base, com 80% de poder e correcao para",
        f"{M['anomalia']['motoristas_testados']:,} testes, seriam necessarias {M['poder']['cenarios'][0]['entregas_necessarias']} entregas por motorista.".replace(',', '.'),
        f"O estudo esta {M['poder']['subdimensionamento']:.0f}x subdimensionado para deteccao individual.",
        'Nenhuma acusacao individual pode ser sustentada com esta base. A aba Drivers e um ranking',
        'de acompanhamento operacional, nao uma lista de suspeitos.',
    ]),
    ('O QUE ESTA BASE NAO PERMITE CONCLUIR', [
        'Nao ha coluna de produto, categoria, cliente ou reclamacao. Qualquer analise de mix de produto,',
        'SKU, perfil de cliente ou evolucao de reclamacoes esta fora do escopo possivel deste dado.',
        f"Variacao por regiao: nao significativa (qui-quadrado p = {M['dimensoes']['regiao']['p_valor']:.3f}).",
        f"Variacao por hora do dia: nao significativa (qui-quadrado p = {M['dimensoes']['hora']['p_valor']:.3f}).",
        f"Variacao por mes: nao significativa (qui-quadrado p = {M['dimensoes']['mes']['p_valor']:.3f}).",
    ]),
]
for tit, linhas in blocos:
    ws.cell(row=r, column=2, value=tit).font = Font(name=F, bold=True, size=10, color=AZUL)
    r += 1
    for L in linhas:
        c = ws.cell(row=r, column=2, value=L)
        c.font = Font(name=F, size=9.5,
                      color=VERM if L.startswith('RESULTADO') or 'PROIBIDA' in L else '000000')
        c.alignment = Alignment(wrap_text=False)
        r += 1
    r += 1

# ─────────────────────────── DATA ───────────────────────────
ws = wb.create_sheet('Data')
base = df[['driver_name', 'driver_id', 'region', 'data', 'delivery_hour_num',
           'items_delivered', 'items_missing', 'items_total', 'order_amount_clean']].copy()
base['data'] = base['data'].dt.strftime('%d/%m/%Y')
base.columns = ['motorista', 'motorista_id', 'regiao', 'data', 'hora',
                'itens_entregues', 'itens_faltantes', 'itens_total', 'valor_pedido']
escrever_tabela(ws, base, 1, larguras=[20, 13, 18, 11, 7, 13, 14, 11, 13], nome='tblData',
                fmts={'valor_pedido': '#,##0.00'})
N = len(base) + 1
ws.cell(row=1, column=10, value='pedido_com_falta').font = h_font
ws.cell(row=1, column=10).fill = h_fill
ws.cell(row=1, column=11, value='valor_itens_faltantes').font = h_font
ws.cell(row=1, column=11).fill = h_fill
for i in range(2, N + 1):
    ws.cell(row=i, column=10, value=f'=IF(G{i}>0,1,0)').font = n_font
    c = ws.cell(row=i, column=11, value=f'=I{i}/H{i}*G{i}')
    c.font = n_font; c.number_format = '#,##0.00'
ws.column_dimensions['J'].width = 16
ws.column_dimensions['K'].width = 20
ws.freeze_panes = 'A2'

# ─────────────────────────── OVERVIEW ───────────────────────────
ws = wb.create_sheet('Overview', 1)
r = cabecalho(ws, 'Overview: KPIs da operacao',
              'Todos os valores sao formulas vivas sobre a aba Data. Alterar a base e recalcular atualiza esta aba.')
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 42
ws.column_dimensions['C'].width = 16
ws.column_dimensions['D'].width = 62

D = f'Data!$G$2:$G${N}'; H = f'Data!$H$2:$H${N}'
I = f'Data!$I$2:$I${N}'; J = f'Data!$J$2:$J${N}'; K = f'Data!$K$2:$K${N}'

kpi_rows = [
    ('VOLUME', None, None, None),
    ('Pedidos analisados', f'=COUNT({H})', '#,##0',
     'Base limpa: pedidos com artefato de teto ja removidos.'),
    ('Itens transportados', f'=SUM({H})', '#,##0', None),
    ('Motoristas', f'=SUMPRODUCT((COUNTIF(Data!$B$2:$B${N},Data!$B$2:$B${N})>0)/COUNTIF(Data!$B$2:$B${N},Data!$B$2:$B${N}))',
     '#,##0', 'Contagem de IDs distintos.'),
    ('Faturamento (US$)', f'=SUM({I})', '$#,##0.00', None),
    ('OCORRENCIAS', None, None, None),
    ('Pedidos com ao menos 1 falta', f'=SUM({J})', '#,##0', None),
    ('Itens faltantes', f'=SUM({D})', '#,##0', None),
    ('KPIs', None, None, None),
    ('>> Incidencia por pedido  (KPI PRIMARIO)', f'=SUM({J})/COUNT({H})', '0.00%',
     'Pedidos com ao menos 1 item faltante / total de pedidos. E o evento que de fato ocorre.'),
    ('Taxa agregada de itens  (KPI secundario)', f'=SUM({D})/SUM({H})', '0.00%',
     'Soma dos faltantes / soma dos itens. Mede volume perdido.'),
    ('Benchmark de industria citado', '=0.015', '0.00%',
     'Premissa externa, nao calculada a partir da base. Fonte: benchmark citado no projeto original.'),
    ('Diferenca vs benchmark (p.p.)', None, '0.00',
     f"O IC95 da taxa ({M['kpis']['taxa_item_ic95'][0]:.2%}-{M['kpis']['taxa_item_ic95'][1]:.2%}) contem o benchmark: "
     'a diferenca nao e distinguivel de ruido amostral.'),
    ('FINANCEIRO', None, None, None),
    ('Valor dos itens faltantes (US$)', f'=SUM({K})', '$#,##0.00',
     'Valor do pedido rateado pelos itens, multiplicado pelos faltantes.'),
    ('% do faturamento', f'=SUM({K})/SUM({I})', '0.00%', None),
    ('CONTRASTE: NAO USAR', None, None, None),
    ('Media simples das razoes por pedido', f'=SUMPRODUCT({D}/{H})/COUNT({H})', '0.00%',
     'METRICA INCORRETA. Da o mesmo peso a pedidos de 2 e de 19 itens. Consta apenas para mostrar a distorcao.'),
    ('Inflacao da metrica incorreta', None, '0.00"x"',
     'Quantas vezes a metrica incorreta supera a taxa agregada correta.'),
]

primeira = r
for nome, form, fmt, nota in kpi_rows:
    if form is None and fmt is None:
        ws.cell(row=r, column=2, value=nome).font = Font(name=F, bold=True, size=9, color='FFFFFF')
        ws.cell(row=r, column=2).fill = PatternFill('solid', fgColor='7F7F7F')
        for cc in (3, 4):
            ws.cell(row=r, column=cc).fill = PatternFill('solid', fgColor='7F7F7F')
        r += 1
        continue
    destaque = nome.startswith('>>')
    contraste = 'INCORRETA' in (nota or '') or 'Inflacao' in nome
    c = ws.cell(row=r, column=2, value=nome)
    c.font = Font(name=F, size=10, bold=destaque,
                  color=VERM if contraste else (VERDE if destaque else '000000'))
    c.border = box
    v = ws.cell(row=r, column=3)
    if form:
        v.value = form
    v.number_format = fmt or 'General'
    v.font = Font(name=F, size=10, bold=destaque,
                  color=VERM if contraste else (VERDE if destaque else '000000'))
    v.border = box
    v.alignment = Alignment(horizontal='right')
    if nota:
        nc = ws.cell(row=r, column=4, value=nota)
        nc.font = Font(name=F, size=8.5, italic=True,
                       color=VERM if contraste else '595959')
    r += 1

# referencias cruzadas que dependem das linhas escritas acima
mapa = {}
for i in range(primeira, r):
    lbl = ws.cell(row=i, column=2).value
    if lbl:
        mapa[lbl] = i
ws.cell(row=mapa['Diferenca vs benchmark (p.p.)'], column=3).value = (
    f"=(C{mapa['Taxa agregada de itens  (KPI secundario)']}-C{mapa['Benchmark de industria citado']})*100")
ws.cell(row=mapa['Inflacao da metrica incorreta'], column=3).value = (
    f"=C{mapa['Media simples das razoes por pedido']}/C{mapa['Taxa agregada de itens  (KPI secundario)']}")

r += 1
ws.cell(row=r, column=2, value='CONCLUSAO DA DETECCAO').font = Font(name=F, bold=True, size=10, color=AZUL)
r += 1
for L in [
    f"Motoristas testados: {M['anomalia']['motoristas_testados']:,}".replace(',', '.'),
    f"Motoristas com desvio significativo apos correcao FDR: {M['anomalia']['significativos_fdr']}",
    f"Menor q-valor observado: {M['anomalia']['menor_q_valor']:.3f} (criterio: q < 0,05)",
    f"Motoristas com zero itens faltantes: {M['anomalia']['motoristas_com_zero_faltas']:,} ({M['anomalia']['pct_motoristas_zero_faltas']:.1%})".replace(',', '.'),
    'Nenhum motorista apresenta desvio estatisticamente significativo. Ver aba Power para o motivo.',
]:
    ws.cell(row=r, column=2, value=L).font = Font(name=F, size=9.5,
        color=VERM if L.startswith('Nenhum') else '000000')
    r += 1

# ─────────────────────────── DRIVERS ───────────────────────────
ws = wb.create_sheet('Drivers')
r = cabecalho(ws, 'Drivers: ranking de acompanhamento operacional',
              'NAO e uma lista de suspeitos. Nenhum motorista atinge significancia (q < 0,05). '
              'Ordenado por p-valor bruto; o criterio de decisao e o q-valor.')
d = t_drv.head(40).copy()
d = d[['rank', 'driver_id', 'driver_name', 'entregas', 'entregas_com_falta', 'incidencia',
       'esperado', 'itens', 'itens_faltantes', 'p_valor', 'q_valor', 'significativo_fdr']]
d.columns = ['rank', 'motorista_id', 'motorista', 'entregas', 'entregas_com_falta',
             'incidencia', 'esperado_pela_base', 'itens', 'itens_faltantes',
             'p_valor', 'q_valor', 'significativo']
d['significativo'] = d['significativo'].map({True: 'SIM', False: 'nao'})
escrever_tabela(ws, d, r, larguras=[7, 14, 20, 10, 17, 11, 17, 9, 15, 11, 11, 13],
                nome='tblDrivers',
                fmts={'incidencia': '0.0%', 'esperado_pela_base': '0.00',
                      'p_valor': '0.0000', 'q_valor': '0.000'})
rr = r + len(d) + 2
for L in [
    f"Exibidos os 40 motoristas com menor p-valor, de {M['anomalia']['motoristas_testados']:,} testados.".replace(',', '.'),
    f"{M['anomalia']['p_bruto_abaixo_05']} motoristas tem p bruto < 0,05; o esperado por puro acaso e {int(M['anomalia']['falsos_positivos_esperados'])}.",
    f"Apos correcao Benjamini-Hochberg: {M['anomalia']['significativos_fdr']} significativos. Menor q-valor: {M['anomalia']['menor_q_valor']:.3f}.",
    'Use esta aba para priorizar auditoria amostral, nunca para acao disciplinar individual.',
]:
    ws.cell(row=rr, column=1, value=L).font = Font(name=F, size=9.5, italic=True, color='595959')
    rr += 1

# ─────────────────────────── REGIONS / HOURS / MONTHS ───────────────────────────
for aba, tab, chave, rot, dimk in [
    ('Regions', t_reg, 'region', 'regiao', 'regiao'),
    ('Hours', t_hor, 'delivery_hour_num', 'hora', 'hora'),
    ('Months', t_mes, 'mes', 'mes', 'mes'),
]:
    ws = wb.create_sheet(aba)
    dd = M['dimensoes'][dimk]
    veredito = ('SIGNIFICATIVA' if dd['significativo'] else 'NAO SIGNIFICATIVA')
    r = cabecalho(ws, f'{aba}: incidencia por {rot}',
                  f"Qui-quadrado de aderencia: chi2 = {dd['qui2']:.2f}, {dd['gl']} g.l., "
                  f"p = {dd['p_valor']:.3f} -> variacao {veredito}. "
                  f"Amplitude entre o maior e o menor: {dd['amplitude_pp']:.2f} p.p.")
    t = tab.copy()
    t = t[[chave, 'pedidos', 'pedidos_com_falta', 'incidencia', 'ic_lo', 'ic_hi',
           'itens', 'faltas', 'taxa_item', 'faturamento']]
    t.columns = [rot, 'pedidos', 'pedidos_com_falta', 'incidencia', 'ic95_inferior',
                 'ic95_superior', 'itens', 'itens_faltantes', 'taxa_item', 'faturamento']
    escrever_tabela(ws, t, r, larguras=[20, 10, 18, 12, 14, 14, 10, 16, 12, 15],
                    nome=f'tbl{aba}',
                    fmts={'incidencia': '0.00%', 'ic95_inferior': '0.00%', 'ic95_superior': '0.00%',
                          'taxa_item': '0.00%', 'faturamento': '$#,##0.00'})
    rr = r + len(t) + 2
    nota = ('Os intervalos de confianca de 95% se sobrepoem entre praticamente todas as categorias: '
            'a variacao observada e compativel com flutuacao aleatoria.') if not dd['significativo'] else \
           'Variacao significativa: investigar.'
    ws.cell(row=rr, column=1, value=nota).font = Font(name=F, size=9.5, italic=True, color=VERM)

# ─────────────────────────── ORDER_SIZE ───────────────────────────
ws = wb.create_sheet('Order_Size')
ep = M['evento_por_pedido']
r = cabecalho(ws, 'Order_Size: por que o KPI antigo estava errado',
              f"A incidencia nao varia com o tamanho do pedido (Spearman rho = {ep['spearman_incidencia_vs_tamanho']:.3f}, "
              f"p = {ep['spearman_incidencia_p']:.3f}), mas a razao faltantes/total cai "
              f"{ep['queda_taxa_item']:.1f}x (rho = {ep['spearman_taxa_item_vs_tamanho']:.3f}). "
              f"A queda e efeito do denominador, nao de comportamento.")
t = t_tam.copy()
t.columns = ['tamanho_pedido', 'pedidos', 'incidencia_por_pedido', 'razao_faltantes_sobre_total']
escrever_tabela(ws, t, r, larguras=[18, 12, 22, 28], nome='tblOrderSize',
                fmts={'incidencia_por_pedido': '0.0%', 'razao_faltantes_sobre_total': '0.00%'})
rr = r + len(t) + 2
for L in ['Coluna 3 sem tendencia = o evento e por pedido.',
          'Coluna 4 despencando = a metrica antiga mede tamanho de pedido, nao comportamento.',
          'Consequencia: qualquer ranking de motorista feito sobre a coluna 4 ranqueia mix de pedido.']:
    ws.cell(row=rr, column=1, value=L).font = Font(name=F, size=9.5, italic=True, color='595959')
    rr += 1

# ─────────────────────────── POWER ───────────────────────────
ws = wb.create_sheet('Power')
pw = M['poder']
r = cabecalho(ws, 'Power: o que esta base consegue detectar',
              f"Poder alvo 80%, alpha corrigido para {M['anomalia']['motoristas_testados']:,} testes "
              f"({pw['alpha_corrigido']:.2e}).".replace(',', '.'))
tp = pd.DataFrame([{
    'cenario': f"motorista com {c['multiplo_da_taxa_base']:.0f}x a incidencia base",
    'incidencia_alvo': c['incidencia_alvo'],
    'entregas_necessarias': c['entregas_necessarias'],
    'entregas_disponiveis': pw['entregas_disponiveis_max'],
    'detectavel': 'SIM' if c['entregas_necessarias'] <= pw['entregas_disponiveis_max'] else 'NAO',
} for c in pw['cenarios']])
escrever_tabela(ws, tp, r, larguras=[42, 18, 22, 22, 13], nome='tblPower',
                fmts={'incidencia_alvo': '0.0%'})
rr = r + len(tp) + 2
for L in [
    f"Motorista mais ativo da base: {pw['entregas_disponiveis_max']} entregas no ano inteiro.",
    f"Mediana da frota: {M['anomalia']['mediana_entregas']:.0f} entregas.",
    f"O estudo esta {pw['subdimensionamento']:.0f}x subdimensionado para o cenario menos exigente.",
    '',
    'CONSEQUENCIA: a ausencia de motoristas significativos NAO prova que nao ha fraude.',
    'Prova que esta base nao tem volume por motorista para detectar fraude individual.',
    'Para viabilizar a deteccao: consolidar historico multi-ano por motorista ou agregar por',
    'equipe/rota, elevando o denominador ate a faixa de entregas necessarias acima.',
]:
    c = ws.cell(row=rr, column=1, value=L)
    c.font = Font(name=F, size=9.5, bold=L.startswith('CONSEQUENCIA'),
                  color=VERM if L.startswith(('CONSEQUENCIA', 'Prova')) else '595959')
    rr += 1

# ─────────────────────────── DRIVER_STRUCTURE ───────────────────────────
ws = wb.create_sheet('Driver_Structure')
em = M['estrutura_motoristas']
r = cabecalho(ws, 'Driver_Structure: a base admite variacao individual?',
              f"Nao. O numero de entregas com falta e funcao quase deterministica do volume. "
              f"Qui-quadrado contra a binomial: {em['qui2_vs_binomial']:,.0f}.".replace(',', '.'))
ws.cell(row=r, column=1, value='Motoristas por (entregas no ano x entregas com falta)').font = \
    Font(name=F, bold=True, size=10, color=AZUL)
r += 1
vols = sorted(int(v) for v in em['tabela_cruzada'])
kmax = max(int(k) for v in em['tabela_cruzada'].values() for k in v)
ct = pd.DataFrame(
    [[em['tabela_cruzada'][str(v)].get(str(k), 0) for k in range(kmax + 1)] for v in vols],
    columns=[f'{k} com falta' for k in range(kmax + 1)])
ct.insert(0, 'entregas no ano', vols)
r = escrever_tabela(ws, ct, r, larguras=[18] + [14] * (kmax + 1), nome='tblStructure')
ws.cell(row=r, column=1, value='Distribuicao observada vs esperada sob processo aleatorio (binomial)').font = \
    Font(name=F, bold=True, size=10, color=AZUL)
r += 1
comp = pd.DataFrame({
    'entregas_com_falta': [int(k) for k in sorted(em['observado'], key=int)],
    'motoristas_observados': [em['observado'][k] for k in sorted(em['observado'], key=int)],
    'esperado_se_aleatorio': [em['esperado_binomial'][k] for k in sorted(em['observado'], key=int)],
})
comp = comp[(comp.motoristas_observados > 0) | (comp.esperado_se_aleatorio >= 1)]
r = escrever_tabela(ws, comp, r, larguras=[22, 24, 24], nome='tblBinomial',
                    fmts={'esperado_se_aleatorio': '#,##0.0'})
for L in [
    f"Sob um processo aleatorio, {em['esperado_binomial']['1']:.0f} motoristas teriam exatamente 1 entrega com falta. A base tem {em['observado']['1']}.",
    f"Maior desvio observado na base inteira: {M['anomalia']['max_entregas_com_falta']} entregas com falta em {M['anomalia']['max_entregas_por_motorista']}.",
    f"Isso produz p = {M['anomalia']['menor_p_valor']:.4f}. Nenhum motorista atinge sequer o limiar bruto de 0,05.",
    '',
    'CONSEQUENCIA: a "taxa" de cada motorista e determinada pelo seu volume, nao pela conduta.',
    'Qualquer lista de suspeitos extraida desta base seria uma lista dos motoristas mais ativos.',
]:
    c = ws.cell(row=r, column=1, value=L)
    c.font = Font(name=F, size=9.5, bold=L.startswith('CONSEQUENCIA'),
                  color=VERM if L.startswith(('CONSEQUENCIA', 'Qualquer')) else '595959')
    r += 1

for s in wb.worksheets:
    s.sheet_view.showGridLines = False

wb.save(f'{OUT}/Analise_Fraude_Entregas_Last_Mile_2023.xlsx')
print('Excel gerado com', len(wb.worksheets), 'abas:', [s.title for s in wb.worksheets])

# ─────────────────────────── CSV corrigido ───────────────────────────
csv = t_drv.head(40)[['rank', 'driver_id', 'driver_name', 'entregas', 'entregas_com_falta',
                      'incidencia', 'esperado', 'itens', 'itens_faltantes',
                      'p_valor', 'q_valor', 'significativo_fdr']].copy()
csv.columns = ['rank', 'motorista_id', 'motorista', 'entregas', 'entregas_com_falta',
               'incidencia', 'esperado_pela_taxa_base', 'itens', 'itens_faltantes',
               'p_valor_bruto', 'q_valor_fdr', 'significativo_apos_correcao']
csv.to_csv(f'{OUT}/drivers_ranking_acompanhamento.csv', index=False,
           float_format='%.6f', encoding='utf-8')
print('CSV gerado:', len(csv), 'linhas | significativos:',
      int(csv.significativo_apos_correcao.sum()))

"""
Verificacao de consistencia cruzada.

Varre todo numero citado no deck e no relatorio e confere se ele e' derivavel
de output/metricas.json. Um numero que nao aparece no JSON e' um numero orfao:
exatamente o defeito que derrubou a versao anterior do projeto.
"""
import json, pathlib, re, glob, subprocess, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = str(RAIZ / 'resultados')
M = json.load(open(f'{OUT}/metricas.json', encoding='utf-8'))


def achatar(o, pref=''):
    """Todo valor numerico do JSON, recursivamente."""
    vals = []
    if isinstance(o, dict):
        for k, v in o.items():
            vals += achatar(v, f'{pref}.{k}')
    elif isinstance(o, list):
        for i, v in enumerate(o):
            vals += achatar(v, f'{pref}[{i}]')
    elif isinstance(o, bool):
        pass
    elif isinstance(o, (int, float)):
        vals.append((pref, float(o)))
    return vals


BRUTOS = achatar(M)

# Formatacoes usadas nos entregaveis, aplicadas a cada valor do JSON.
def formas(v):
    f = set()
    if v < 0:
        f |= {'-' + x for x in formas(-v)} | formas(-v)
    if v == int(v) and abs(v) < 1e9:
        f.add(f'{int(v):,}'.replace(',', '.'))
        f.add(str(int(v)))
    for c in (0, 1, 2, 3, 4):
        f.add(f'{v:.{c}f}'.replace('.', ','))
        f.add(f'{v*100:.{c}f}'.replace('.', ',') + '%')
        f.add(f'{v*100:,.{c}f}'.replace(',', '#').replace('.', ',').replace('#', '.') + '%')
    # milhares com separador (valores monetarios)
    f.add(f'{v:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    f.add(f'{round(v):,}'.replace(',', '.'))
    f.add(f'{round(v/1000):,}'.replace(',', '.'))
    return f


PERMITIDOS = {}
for chave, v in BRUTOS:
    for s in formas(v):
        PERMITIDOS.setdefault(s, chave)

# Numeros estruturais, nao derivados dos dados: escalas, rotulos, constantes
# metodologicas e a numeracao de secoes/fases.
ESTRUTURAIS = {
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
    '01', '02', '03', '04', '05', '06',
    '95', '99', '100', '80', '15', '24', '40', '2023', '2026',
    '0,05', '0,5', '1,5', '1,5%', '5%', '80%', '95%', '100%',
    '2×', '3×', '4×',
}

PADRAO = re.compile(r'-?\d[\d.,]*\s*(?:%|×)?')


def tokens(texto):
    out = []
    for m in PADRAO.finditer(texto):
        t = re.sub(r'\s+', '', m.group()).rstrip('.,')
        if t:
            out.append(t)
    return out


def pre_limpar(t):
    """Remove o que nao e' afirmacao numerica sobre os dados."""
    t = re.sub(r'WDID\s*\d+', ' ', t)                 # ids de motorista
    t = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', ' ', t)      # datas
    # numeracao de secao: "2.1 Artefato…", "4) Medidas…", no inicio da linha
    t = re.sub(r'(?m)^\s*\d+(?:\.\d+)*[.)]?\s+(?=[A-ZÀ-ÚÁÉÍÓÚÂÊÔÃÕÇ])', ' ', t)
    t = re.sub(r'\b(?:Anexo|Fase|Seção|seção)\s+\S+', ' ', t)
    t = re.sub(r'\bIC\s*95%', ' ', t)
    t = re.sub(r'\bp\.p\.?', ' ', t)                  # a unidade, nao o valor
    return t


def limpar_html(h):
    h = re.sub(r'<aside>.*?</aside>', ' ', h, flags=re.S)   # notas do apresentador
    h = re.sub(r'style="[^"]*"', ' ', h)                    # px, cores, larguras
    h = re.sub(r'(?:src|alt)="[^"]*"', ' ', h)              # assets e texto alternativo
    h = re.sub(r'<[^>]+>', ' ', h)
    return h


def conferir(nome, texto):
    orfaos = {}
    for t in tokens(texto):
        base = t.rstrip('×').replace('p.p.', '').strip()
        if t in ESTRUTURAIS or base in ESTRUTURAIS:
            continue
        if t in PERMITIDOS or base in PERMITIDOS:
            continue
        orfaos[t] = orfaos.get(t, 0) + 1
    return orfaos


falhas = 0
print('=' * 72)
print('VERIFICACAO DE CONSISTENCIA: todo numero deve existir em metricas.json')
print('=' * 72)

# ── deck ──
print('\n[DECK]')
for f in sorted(glob.glob(str(RAIZ / 'resultados/deck/project/slides/*.html'))):
    nome = f.split('/')[-1]
    o = conferir(nome, pre_limpar(limpar_html(open(f, encoding='utf-8').read())))
    if o:
        falhas += len(o)
        print(f'  {nome:24} ORFAOS: {", ".join(sorted(o))}')
    else:
        print(f'  {nome:24} ok')

# ── relatorio ──
print('\n[RELATORIO]')
md = subprocess.run(['pandoc', '-t', 'plain',
                     f'{OUT}/Relatorio_Fraude_Entregas_Last_Mile_2023.docx'],
                    capture_output=True, text=True).stdout
o = conferir('relatorio', pre_limpar(md))
if o:
    falhas += len(o)
    print(f'  ORFAOS: {", ".join(sorted(o))}')
else:
    print('  ok: todo numero do relatorio consta no pipeline')

# ── readme ──
print('\n[README]')
rm = (RAIZ / 'README.md')
if rm.exists():
    txt = re.sub(r'```.*?```', ' ', rm.read_text(encoding='utf-8'), flags=re.S)  # blocos de codigo
    txt = re.sub(r'!?\[[^\]]*\]\([^)]*\)', ' ', txt)                            # links e imagens
    o = conferir('README', pre_limpar(txt))
    if o:
        falhas += len(o)
        print(f'  ORFAOS: {", ".join(sorted(o))}')
    else:
        print('  ok: todo numero do README consta no pipeline')
    if 'sintétic' not in rm.read_text(encoding='utf-8')[:1200].lower():
        falhas += 1
        print('  FALHA: a natureza sintetica da base nao esta declarada na abertura')
    else:
        print('  ok: base declarada como sintetica na abertura')
else:
    falhas += 1
    print('  FALHA: README.md ausente')

# ── marca ──
print('\n[MARCA]')
alvos = list((RAIZ / 'resultados/deck/project/slides').glob('*.html')) + [RAIZ / 'README.md']
vaz = [p.name for p in alvos
       if re.search(r'walmart', p.read_text(encoding='utf-8'), re.I)]
if vaz:
    falhas += len(vaz)
    print(f'  FALHA: marca ainda citada em {", ".join(vaz)}')
else:
    print('  ok: nenhuma marca de empresa real citada no deck nem no README')

# ── travessoes ──
print('\n[TIPOGRAFIA]')
import openpyxl
EM, EN = '—', '–'   # escapes: o arquivo nao deve conter o caractere


def texto_do_xlsx(caminho):
    wb_ = openpyxl.load_workbook(caminho, data_only=True)
    partes = []
    for ws_ in wb_.worksheets:
        partes.append(ws_.title)
        for linha in ws_.iter_rows(values_only=True):
            partes += [str(c) for c in linha if isinstance(c, str)]
    return '\n'.join(partes)


fontes = {}
for p in sorted((RAIZ / 'resultados/deck/project/slides').glob('*.html')):
    fontes['deck/' + p.name] = p.read_text(encoding='utf-8')
fontes['README.md'] = (RAIZ / 'README.md').read_text(encoding='utf-8')
fontes['dados_brutos/LEIA-ME.md'] = (RAIZ / 'dados_brutos/LEIA-ME.md').read_text(encoding='utf-8')
fontes['relatorio.docx'] = md
fontes['analise.xlsx'] = texto_do_xlsx(
    f'{OUT}/Analise_Fraude_Entregas_Last_Mile_2023.xlsx')
fontes['drivers.csv'] = open(f'{OUT}/drivers_ranking_acompanhamento.csv',
                             encoding='utf-8').read()

sujos = {n: (t.count(EM), t.count(EN)) for n, t in fontes.items()
         if EM in t or EN in t}
if sujos:
    falhas += len(sujos)
    for n, (a, b) in sujos.items():
        print(f'  FALHA: {n} tem {a} travessao(es) e {b} meia-risca(s)')
else:
    print(f'  ok: nenhum travessao nos {len(fontes)} arquivos de texto gerados')

# ── estrutura de pastas ──
print('\n[ESTRUTURA]')
esperado = {
    'dados_brutos/entregas_2023.xlsx': 'base original',
    'dados_brutos/LEIA-ME.md': 'dicionario de dados',
    'resultados/metricas.json': 'fonte de verdade dos numeros',
    'resultados/graficos': 'figuras',
    'resultados/tabelas': 'agregacoes intermediarias',
    'resultados/deck': 'slides',
}
for rel, desc_ in esperado.items():
    if not (RAIZ / rel).exists():
        falhas += 1
        print(f'  FALHA: falta {rel} ({desc_})')
# nada gerado pode cair dentro de dados_brutos/
intrusos = [p.name for p in (RAIZ / 'dados_brutos').iterdir()
            if p.name not in ('entregas_2023.xlsx', 'LEIA-ME.md')]
if intrusos:
    falhas += len(intrusos)
    print(f'  FALHA: dados_brutos/ contem arquivo gerado: {", ".join(intrusos)}')
else:
    print('  ok: dados brutos e resultados em pastas separadas, sem mistura')

# ── excel: KPIs calculados vs pipeline ──
print('\n[EXCEL]')
wb = openpyxl.load_workbook(f'{OUT}/Analise_Fraude_Entregas_Last_Mile_2023.xlsx', data_only=True)
ws = wb['Overview']
vals = {}
for r in range(1, 60):
    k, v = ws.cell(row=r, column=2).value, ws.cell(row=r, column=3).value
    if k and v is not None:
        vals[k] = v
checks = [
    ('Pedidos analisados', M['kpis']['pedidos']),
    ('Itens transportados', M['kpis']['itens']),
    ('Motoristas', M['kpis']['motoristas']),
    ('Faturamento (US$)', M['kpis']['faturamento']),
    ('Pedidos com ao menos 1 falta', M['kpis']['pedidos_com_falta']),
    ('Itens faltantes', M['kpis']['itens_faltantes']),
    ('>> Incidencia por pedido  (KPI PRIMARIO)', M['kpis']['incidencia_por_pedido']),
    ('Taxa agregada de itens  (KPI secundario)', M['kpis']['taxa_item_agregada']),
    ('Valor dos itens faltantes (US$)', M['kpis']['valor_em_risco']),
    ('% do faturamento', M['kpis']['valor_em_risco_pct_faturamento']),
    ('Media simples das razoes por pedido', M['kpis']['media_razoes_INCORRETA']),
    ('Inflacao da metrica incorreta', M['kpis']['inflacao_da_metrica_incorreta']),
    ('Diferenca vs benchmark (p.p.)', M['kpis']['diferenca_vs_benchmark_pp']),
]
for nome, esp in checks:
    got = vals.get(nome)
    ok = got is not None and abs(float(got) - float(esp)) < max(1e-6, abs(esp) * 1e-6)
    if not ok:
        falhas += 1
        print(f'  DIVERGE  {nome}: excel={got} pipeline={esp}')
print(f'  {len(checks)} formulas vivas conferidas contra o pipeline'
      f'{": todas batem" if falhas == 0 else ""}')

# ── CSV ──
print('\n[CSV]')
linhas = open(f'{OUT}/drivers_ranking_acompanhamento.csv', encoding='utf-8').read().strip().split('\n')
cab = linhas[0].split(',')
sig = [l.split(',')[cab.index('significativo_apos_correcao')] for l in linhas[1:]]
if any(s.strip().lower() == 'true' for s in sig):
    falhas += 1
    print('  FALHA: ha motorista marcado como significativo, mas o pipeline diz 0')
else:
    print(f'  ok: {len(sig)} motoristas listados, nenhum marcado como significativo')
if 'suspect' in open(f'{OUT}/drivers_ranking_acompanhamento.csv', encoding='utf-8').read().lower():
    falhas += 1
    print('  FALHA: o arquivo ainda usa linguagem de acusacao')

# ── coerencia interna de conclusoes ──
print('\n[CONCLUSOES]')
c = M['conclusao']
regras = [
    (not c['sinal_de_fraude_detectado'], 'nenhum sinal de fraude declarado'),
    (not c['variacao_regional_significativa'], 'regiao sem variacao significativa'),
    (not c['variacao_horaria_significativa'], 'hora sem variacao significativa'),
    (not c['estudo_tem_poder_para_deteccao_individual'], 'estudo declarado subdimensionado'),
    (not c['existe_variacao_individual_entre_motoristas'], 'base sem variacao individual'),
    (c['operacao_vs_benchmark'] == 'indistinguivel', 'benchmark dentro do IC'),
]
for ok, desc in regras:
    print(f'  {"ok  " if ok else "FALHA"} {desc}')
    if not ok:
        falhas += 1

print('\n' + '=' * 72)
print('CONSISTENTE: nenhum numero orfao' if falhas == 0 else f'{falhas} PROBLEMA(S)')
print('=' * 72)
sys.exit(1 if falhas else 0)

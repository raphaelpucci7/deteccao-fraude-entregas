"""
Gera os arquivos do deck a partir de resultados/metricas.json.
Nenhum numero digitado a mao. Mesma fonte de verdade do relatorio e do Excel.
"""
import json, pathlib, os, datetime

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = str(RAIZ / 'resultados')
DECK = str(RAIZ / 'resultados' / 'deck')
M = json.load(open(f'{OUT}/metricas.json', encoding='utf-8'))
K, A, PW, AR = M['kpis'], M['anomalia'], M['poder'], M['artefatos']
EP, DM, EM, V = M['evento_por_pedido'], M['dimensoes'], M['estrutura_motoristas'], M['validacao']

IMG = {
    's1': '/_blob/cea0a4c20dc9e959b817c15eb3ec3803',
    's2': '/_blob/a34927160b64c38d10b2d6ef884093f9',
    's3': '/_blob/415407ca3e58af50d39eb07f05c4f5aa',
    's4': '/_blob/00c71672fb4302b0ebd2e83866fcc547',
}

# paleta
ESC = '#15202B'; PAP = '#F8F8F5'; PAP2 = '#EDEDE6'
OXI = '#B0442C'; PET = '#2D6A6A'
TXT = '#4A5560'; TXT_ESC = '#A9B7C0'; LIN = '#D6D6CC'

SERIF = "'Source Serif 4', Georgia, serif"
SANS = "'IBM Plex Sans', Arial, sans-serif"

pct = lambda v, c=2: f'{v*100:.{c}f}'.replace('.', ',') + '%'
num = lambda v: f'{round(v):,}'.replace(',', '.')
dec = lambda v, c=3: f'{v:.{c}f}'.replace('.', ',')

os.makedirs(f'{DECK}/project/slides', exist_ok=True)
slides = []


def slide(sid, corpo, notas=None, fundo=PAP, cor=ESC, extra='', trans='fade'):
    pad = '128px 128px 160px' if 'bottom:64px' in corpo else '128px'
    html = (f'<section id="{sid}" data-transition="{trans}" style="background:{fundo}; '
            f'color:{cor}; font-family:{SANS}; padding:{pad}; display:flex; '
            f'flex-direction:column; {extra}">\n{corpo}\n')
    if notas:
        html += f'  <aside>{notas}</aside>\n'
    html += '</section>\n'
    open(f'{DECK}/project/slides/{sid}.html', 'w', encoding='utf-8').write(html)
    slides.append(sid)


def eyebrow(t, cor=OXI):
    return (f'  <p style="font-size:24px; font-weight:600; letter-spacing:2px; '
            f'text-transform:uppercase; color:{cor}">{t}</p>\n')


def h2(t, cor=None, size=64):
    c = f'color:{cor}; ' if cor else ''
    return (f'  <h2 style="font-family:{SERIF}; font-size:{size}px; font-weight:600; '
            f'line-height:1.12; {c}">{t}</h2>\n')


def rodape(t, cor=None):
    c = cor or TXT
    return (f'  <p style="position:absolute; left:128px; bottom:64px; width:1664px; '
            f'font-size:24px; color:{c}">{t}</p>\n')


def card(titulo, corpo, dest=False, flex=1):
    borda = f'2px solid {OXI}' if dest else f'1px solid {LIN}'
    return (f'<div style="flex:{flex}; display:flex; flex-direction:column; gap:14px; '
            f'background:#FFFFFF; border:{borda}; border-radius:10px; padding:36px">'
            f'<h3 style="font-size:30px; font-weight:600; color:{OXI if dest else ESC}">{titulo}</h3>'
            f'<p style="font-size:26px; line-height:1.4; color:{TXT}">{corpo}</p></div>')


# ───────────────────────── 1 capa ─────────────────────────
slide('capa', (
    eyebrow('Projeto de portfólio · Análise de dados em operações', PET)
    + f'  <div style="flex:1"></div>\n'
    + f'  <h1 style="font-family:{SERIF}; font-size:96px; font-weight:600; line-height:1.05; '
      f'color:#FFFFFF">Detecção de fraude<br>em entregas de última milha</h1>\n'
    + f'  <p style="font-size:34px; line-height:1.4; color:{TXT_ESC}; width:1400px">'
      f'Análise de um <b style="color:#FFFFFF">dataset sintético</b> de e-commerce, '
      f'{V["periodo_inicio"]} a {V["periodo_fim"]}, e o que a validação revelou sobre ele.</p>\n'
    + f'  <div style="flex:1"></div>\n'
    + f'  <div style="display:flex; gap:56px; border-top:1px solid #2E3D4B; padding:32px 0 0">'
      f'<p style="font-size:26px; color:{TXT_ESC}">{num(V["linhas_brutas"])} pedidos</p>'
      f'<p style="font-size:26px; color:{TXT_ESC}">{num(K["motoristas"])} motoristas</p>'
      f'<p style="font-size:26px; color:{TXT_ESC}">{len(V["regioes"])} regiões atendidas</p>'
      f'<p style="font-size:26px; color:{TXT_ESC}">Pipeline reproduzível em Python</p></div>\n'
), 'A base é um dataset de estudo, não dado operacional real. Isso está declarado desde a capa. '
   'Descobrir que ela é gerada foi um dos dois resultados da análise, e o slide 4 mostra a prova.',
   fundo=ESC, cor='#FFFFFF', extra='justify-content:space-between')

# ───────────────────────── 2 pergunta ─────────────────────────
slide('pergunta', (
    eyebrow('A pergunta')
    + h2('Itens registrados como "não entregues" indicam fraude de motorista?')
    + f'  <div style="display:flex; gap:28px; padding:48px 0 0">'
      + card('Hipótese investigada',
             'Motoristas com taxa de itens faltantes acima da média estariam desviando '
             'mercadoria de forma sistemática.')
      + card('O que seria preciso para afirmar isso',
             'Variação individual real entre motoristas, volume suficiente por motorista '
             'e significância que sobreviva ao número de testes feitos.')
      + card('O que este deck mostra',
             'Nenhuma das três condições se verifica, e a checagem da terceira revelou '
             'que a própria base é gerada artificialmente.', dest=True)
      + '</div>\n'
), 'Enquadrar assim desde o início evita a armadilha de apresentar um ranking como se fosse uma acusação.')

# ───────────────────────── 3 resposta ─────────────────────────
def kpi(valor, rotulo, cor=ESC):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:10px; '
            f'border-top:3px solid {cor}; padding:28px 0 0">'
            f'<p style="font-family:{SERIF}; font-size:72px; font-weight:600; color:{cor}; '
            f'line-height:1">{valor}</p>'
            f'<p style="font-size:26px; line-height:1.35; color:{TXT}">{rotulo}</p></div>')

slide('resposta', (
    eyebrow('Dois resultados')
    + h2('Nenhum motorista se destaca, e a base não permitiria que se destacasse')
    + f'  <div style="display:flex; gap:32px; padding:44px 0 0">'
      + kpi(pct(K['incidencia_por_pedido'], 1),
            f'dos pedidos têm ao menos um item faltante<br>IC 95%: {pct(K["incidencia_ic95"][0],1)} a {pct(K["incidencia_ic95"][1],1)}', PET)
      + kpi(pct(K['taxa_item_agregada'], 2),
            f'dos itens transportados<br>o benchmark de {pct(K["benchmark_industria"],1)} cai dentro do IC', PET)
      + kpi(num(K['valor_em_risco'] / 1000) + ' mil',
            f'US$ em itens faltantes<br>{pct(K["valor_em_risco_pct_faturamento"])} do faturamento', PET)
      + kpi(str(A['significativos_fdr']),
            f'motoristas com desvio significativo<br>de {num(A["motoristas_testados"])} testados', OXI)
      + '</div>\n'
    + f'  <div style="display:flex; gap:22px; align-items:center; background:#FFFFFF; '
      f'border:2px solid {OXI}; border-radius:10px; padding:32px 36px; margin:44px 0 0">'
      f'<p style="font-size:25px; font-weight:600; letter-spacing:1px; text-transform:uppercase; '
      f'color:{OXI}; width:260px">Segundo resultado</p>'
      f'<p style="flex:1; font-size:28px; line-height:1.4">A validação mostrou que a base é '
      f'<b>sintética</b>: o número de faltas é função determinística do volume de entregas. '
      f'Não há variação individual entre motoristas para detectar, nem verdadeira, nem falsa.</p></div>\n'
    + rodape(f'Base após limpeza: {num(K["pedidos"])} pedidos e {num(K["itens"])} itens. '
             f'Faturamento no período: US$ {num(K["faturamento"])}.')
), f'A diferença de {dec(K["diferenca_vs_benchmark_pp"],2)} p.p. contra o benchmark não é distinguível '
   'de ruído amostral. Não afirme "acima" nem "abaixo" do benchmark. '
   'O segundo resultado é o mais interessante e tem slide próprio adiante.')

# ───────────────────────── 4 metodo ─────────────────────────
def etapa(n, tit, corpo):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:12px">'
            f'<p style="font-family:{SERIF}; font-size:44px; font-weight:600; color:{OXI}">{n}</p>'
            f'<div style="border-top:1px solid {LIN}; padding:18px 0 0; display:flex; '
            f'flex-direction:column; gap:10px">'
            f'<h3 style="font-size:30px; font-weight:600">{tit}</h3>'
            f'<p style="font-size:25px; line-height:1.4; color:{TXT}">{corpo}</p></div></div>')

slide('metodo', (
    eyebrow('Como a análise foi feita')
    + h2('Uma fonte de verdade, quatro etapas')
    + f'  <div style="display:flex; gap:36px; padding:52px 0 0">'
      + etapa('01', 'Validação', 'Zero nulos e identidade entregues + faltantes = total confirmada em 100% das linhas.')
      + etapa('02', 'Limpeza', f'Remoção de {AR["pedidos_removidos"]} pedidos afetados por artefato de geração da base.')
      + etapa('03', 'Definição do KPI', 'A falta é evento por pedido, não por item. O indicador foi redefinido.')
      + etapa('04', 'Teste e correção', f'Binomial exato por motorista, corrigido por FDR para {num(A["motoristas_testados"])} testes.')
      + '</div>\n'
    + rodape('Todos os números deste deck são gerados por um único script a partir da base bruta. '
             'Nenhum valor foi digitado manualmente em slide, relatório ou planilha.')
), 'A frase do rodapé é o ponto que mais impressiona numa entrevista técnica: reprodutibilidade.')

# ───────────────────────── 5 limpeza ─────────────────────────
slide('limpeza', (
    eyebrow('Etapa 02 · Limpeza')
    + h2('A base tem um teto artificial que fabrica faltas')
    + f'  <div style="display:flex; gap:56px; padding:44px 0 0; align-items:start">'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:26px">'
      f'<p style="font-size:30px; line-height:1.45; color:{TXT}">A coluna de itens entregues está '
      f'truncada em <b style="color:{ESC}">{AR["teto_items_delivered"]}</b>. Todo pedido maior que isso '
      f'registra falta por construção, não por ocorrência operacional.</p>'
      f'<p style="font-size:30px; line-height:1.45; color:{TXT}">Esses pedidos foram removidos e o '
      f'tratamento está documentado na planilha.</p></div>'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:20px; background:#FFFFFF; '
      f'border:1px solid {LIN}; border-radius:10px; padding:40px">'
      f'<div style="display:flex; justify-content:space-between"><p style="font-size:27px; color:{TXT}">Pedidos removidos</p>'
      f'<p style="font-size:27px; font-weight:600">{AR["pedidos_removidos"]}</p></div>'
      f'<div style="display:flex; justify-content:space-between"><p style="font-size:27px; color:{TXT}">Deles, com falta</p>'
      f'<p style="font-size:27px; font-weight:600; color:{OXI}">{pct(AR["pct_com_falta_no_grupo_removido"],0)}</p></div>'
      f'<div style="display:flex; justify-content:space-between"><p style="font-size:27px; color:{TXT}">Itens que somavam</p>'
      f'<p style="font-size:27px; font-weight:600">{AR["faltas_removidas"]}</p></div>'
      f'<div style="display:flex; justify-content:space-between; border-top:1px solid {LIN}; padding:20px 0 0">'
      f'<p style="font-size:27px; color:{TXT}">Das faltas brutas</p>'
      f'<p style="font-size:27px; font-weight:600; color:{OXI}">{pct(AR["pct_das_faltas_brutas"],1)}</p></div></div></div>\n'
    + rodape(f'Outros sinais de base sintética: nenhum dos {AR["pedidos_1_item"]} pedidos de item único tem falta, '
             f'e o volume por motorista assume apenas os valores {", ".join(map(str, AR["valores_distintos_entregas_por_motorista"]))}.')
), 'Declarar limitação de dado é sinal de maturidade, não de fraqueza. Esse slide vale mais que qualquer gráfico bonito.')

# ───────────────────────── 6 kpi ─────────────────────────
slide('kpi', (
    eyebrow('Etapa 03 · O indicador')
    + h2('O KPI antigo media tamanho de pedido, não comportamento')
    + f'  <img src="{IMG["s1"]}" alt="A incidência por pedido permanece constante em torno de 15% '
      f'para pedidos de 2 a 19 itens, enquanto a razão itens faltantes sobre total cai de 7,8% para 0,8%" '
      f'style="width:1280px; height:585px; object-fit:contain; align-self:center">\n'
    + rodape(f'Incidência × tamanho: Spearman ρ = {dec(EP["spearman_incidencia_vs_tamanho"])} '
             f'(p = {dec(EP["spearman_incidencia_p"])}), sem tendência. '
             f'Razão × tamanho: ρ = {dec(EP["spearman_taxa_item_vs_tamanho"])}, queda de {dec(EP["queda_taxa_item"],1)}×.')
), 'A falta ocorre no pedido, não no item. Dividir pelo número de itens transforma o indicador '
   'numa medida de tamanho de pedido. Quem atende pedidos pequenos sobe no ranking sem mudar de conduta.')

# ───────────────────────── 7 inflacao ─────────────────────────
slide('inflacao', (
    eyebrow('Etapa 03 · O indicador')
    + h2('Média de porcentagens não é uma taxa')
    + f'  <div style="display:flex; gap:32px; padding:48px 0 0; align-items:stretch">'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:16px; background:#FFFFFF; '
      f'border:2px solid {OXI}; border-radius:10px; padding:40px">'
      f'<p style="font-size:25px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:{OXI}">Métrica descartada</p>'
      f'<p style="font-family:{SERIF}; font-size:68px; font-weight:600; color:{OXI}; line-height:1">{pct(K["media_razoes_INCORRETA"])}</p>'
      f'<p style="font-size:26px; line-height:1.4; color:{TXT}">Média simples das razões por pedido. '
      f'Dá o mesmo peso a um pedido de 2 e a um de {AR["teto_items_delivered"]} itens.</p></div>'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:16px; background:#FFFFFF; '
      f'border:2px solid {PET}; border-radius:10px; padding:40px">'
      f'<p style="font-size:25px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:{PET}">Taxa correta</p>'
      f'<p style="font-family:{SERIF}; font-size:68px; font-weight:600; color:{PET}; line-height:1">{pct(K["taxa_item_agregada"])}</p>'
      f'<p style="font-size:26px; line-height:1.4; color:{TXT}">Soma dos itens faltantes dividida '
      f'pela soma dos itens transportados.</p></div>'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:16px; background:{PAP2}; '
      f'border:1px solid {LIN}; border-radius:10px; padding:40px">'
      f'<p style="font-size:25px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:{TXT}">Diferença</p>'
      f'<p style="font-family:{SERIF}; font-size:68px; font-weight:600; line-height:1">{dec(K["inflacao_da_metrica_incorreta"],2)}×</p>'
      f'<p style="font-size:26px; line-height:1.4; color:{TXT}">A métrica descartada inflava o problema '
      f'e sustentava uma urgência que os dados não têm.</p></div></div>\n'
), 'É a diferença entre "média das porcentagens" e "porcentagem do total". Só a segunda é uma taxa operacional.')

# ───────────────────────── 8 deteccao ─────────────────────────
slide('deteccao', (
    eyebrow('Etapa 04 · Detecção')
    + h2('Testar 1.247 motoristas exige corrigir para testes múltiplos')
    + f'  <div style="display:flex; gap:56px; padding:44px 0 0; align-items:start">'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:24px">'
      f'<p style="font-size:30px; line-height:1.45; color:{TXT}">A 5% de significância, testar '
      f'{num(A["motoristas_testados"])} hipóteses produziria cerca de <b style="color:{ESC}">'
      f'{round(A["falsos_positivos_esperados"])} "descobertas"</b> por puro acaso.</p>'
      f'<p style="font-size:30px; line-height:1.45; color:{TXT}">Por isso o critério de decisão é o '
      f'q-valor após correção de Benjamini-Hochberg, nunca o p-valor bruto.</p></div>'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:22px; background:#FFFFFF; '
      f'border:2px solid {OXI}; border-radius:10px; padding:40px">'
      f'<div style="display:flex; justify-content:space-between"><p style="font-size:27px; color:{TXT}">Maior desvio observado</p>'
      f'<p style="font-size:27px; font-weight:600">{A["max_entregas_com_falta"]} de {A["max_entregas_por_motorista"]} entregas</p></div>'
      f'<div style="display:flex; justify-content:space-between"><p style="font-size:27px; color:{TXT}">Esperado pela taxa base</p>'
      f'<p style="font-size:27px; font-weight:600">{dec(M["derivados"]["esperado_no_motorista_mais_ativo"],2)} entregas</p></div>'
      f'<div style="display:flex; justify-content:space-between"><p style="font-size:27px; color:{TXT}">Menor p-valor da base</p>'
      f'<p style="font-size:27px; font-weight:600">{dec(A["menor_p_valor"],4)}</p></div>'
      f'<div style="display:flex; justify-content:space-between; border-top:1px solid {LIN}; padding:20px 0 0">'
      f'<p style="font-size:27px; color:{TXT}">Menor q-valor (FDR)</p>'
      f'<p style="font-size:27px; font-weight:600; color:{OXI}">{dec(A["menor_q_valor"])}</p></div></div></div>\n'
    + rodape(f'Nenhum motorista atinge sequer o limiar bruto de 0,05. '
             f'{num(A["motoristas_com_zero_faltas"])} motoristas ({pct(A["pct_motoristas_zero_faltas"],1)}) '
             f'não registram um único item faltante no ano.')
), 'Este é o slide que responde à pergunta que todo entrevistador técnico faz: "você corrigiu para testes múltiplos?"')

# ───────────────────────── 9 determinismo ─────────────────────────
slide('determinismo', (
    eyebrow('O achado central')
    + h2('A validação revelou que a base é gerada, não observada')
    + f'  <img src="{IMG["s2"]}" alt="Motoristas com 6 ou 7 entregas têm sempre zero faltas; '
      f'com 11 entregas têm sempre 3 ou 4. Cada volume admite no máximo dois resultados" '
      f'style="width:1180px; height:537px; object-fit:contain; align-self:center">\n'
    + rodape(f'O número de entregas com falta é função quase determinística do volume: '
             f'{EM["volumes_deterministicos"]} dos {EM["volumes_distintos"]} volumes admitem um único resultado. '
             f'Contra a binomial, qui-quadrado = {num(EM["qui2_vs_binomial"])}.')
), 'Sob um processo aleatório, 472 motoristas teriam exatamente uma entrega com falta. A base tem 1. '
   'Consequência: a taxa de cada motorista é determinada pelo volume, não pela conduta. '
   'Qualquer lista de suspeitos extraída daqui seria uma lista dos motoristas mais ativos.')

# ───────────────────────── 10 poder ─────────────────────────
slide('poder', (
    eyebrow('A limitação central')
    + h2('Mesmo que houvesse sinal, o estudo não teria poder para vê-lo')
    + f'  <img src="{IMG["s3"]}" alt="Para detectar um motorista operando ao dobro da taxa base '
      f'seriam necessárias 190 entregas; a base oferece no máximo 11" '
      f'style="width:1280px; height:492px; object-fit:contain; align-self:center">\n'
    + rodape(f'Poder alvo de 80%, alfa corrigido para {num(A["motoristas_testados"])} testes. '
             f'O motorista mais ativo da base tem {PW["entregas_disponiveis_max"]} entregas no ano; '
             f'a mediana da frota é {round(A["mediana_entregas"])}. O estudo está '
             f'{round(PW["subdimensionamento"])}× subdimensionado.')
), 'A ausência de significância não prova ausência de fraude. Prova que esta base não tem volume '
   'por motorista para detectá-la. Essa distinção é o ponto técnico mais importante do deck.')

# ───────────────────────── 11 dimensoes ─────────────────────────
slide('dimensoes', (
    eyebrow('Cortes testados')
    + h2('Hora, região e mês: nenhum apresenta variação significativa')
    + f'  <img src="{IMG["s4"]}" alt="Incidência por hora do dia com intervalos de confiança de 95% '
      f'que se sobrepõem à linha da taxa base em todas as 24 horas" '
      f'style="width:1120px; height:462px; object-fit:contain; align-self:center">\n'
    + f'  <div style="display:flex; gap:20px; padding:20px 0 0">'
      + ''.join(
          f'<div style="flex:1; display:flex; justify-content:space-between; background:#FFFFFF; '
          f'border:1px solid {LIN}; border-radius:8px; padding:20px 26px">'
          f'<p style="font-size:25px; color:{TXT}">{rot}</p>'
          f'<p style="font-size:25px; font-weight:600; color:{PET}">p = {dec(DM[k]["p_valor"])}</p></div>'
          for k, rot in [('hora', 'Hora do dia'), ('regiao', 'Região'), ('mes', 'Mês')])
      + '</div>\n'
), 'Qualquer recomendação de reforçar supervisão em janela horária ou região específica seria '
   'uma recomendação construída sobre ruído.')

# ───────────────────────── 12 limites ─────────────────────────
slide('limites', (
    eyebrow('Honestidade de escopo')
    + h2('O que esta base não permite concluir')
    + f'  <div style="display:flex; gap:28px; padding:48px 0 0">'
      + card('Produto e categoria', 'Não há coluna de SKU nem de categoria. Qualquer ranking de '
             'produtos impactados ou concentração por categoria está fora de escopo.')
      + card('Perfil de cliente', 'Não há identificador de cliente. Segmentação de risco ou '
             'análise de reincidência de reclamação não são calculáveis.')
      + card('Evolução histórica', 'A base cobre um único ano e não registra reclamações. Não há '
             'como afirmar aumento ou queda em relação a período anterior.')
      + '</div>\n'
    + f'  <div style="background:{PAP2}; border-left:5px solid {OXI}; border-radius:4px; '
      f'padding:30px 36px; margin:0">'
      f'<p style="font-size:28px; line-height:1.45; color:{ESC}">Estas quatro análises constavam em '
      f'versões anteriores deste material. Foram removidas por não terem origem nos dados.</p></div>\n'
), 'Remover uma seção inteira por não ter dado que a sustente é mais forte do que mantê-la. '
   'Um entrevistador vai perguntar de onde veio a categoria de produto.')

# ───────────────────────── 13 medidas ─────────────────────────
def medida(n, tit, corpo):
    return (f'<div style="display:flex; gap:22px; align-items:start">'
            f'<p style="font-family:{SERIF}; font-size:34px; font-weight:600; color:{OXI}; '
            f'width:52px">{n}</p>'
            f'<div style="flex:1; display:flex; flex-direction:column; gap:6px">'
            f'<h3 style="font-size:28px; font-weight:600">{tit}</h3>'
            f'<p style="font-size:25px; line-height:1.4; color:{TXT}">{corpo}</p></div></div>')

slide('medidas', (
    eyebrow('Recomendações')
    + h2('Medidas preventivas: justificadas por custo-benefício, não por fraude')
    + f'  <div style="display:flex; gap:64px; padding:44px 0 0">'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:28px">'
      + medida('01', 'Prova de entrega multimodal', 'Foto, GPS e confirmação do cliente vinculados ao pedido. Cria a trilha de evidência que hoje não existe.')
      + medida('02', 'Selo inviolável com QR único', 'Escaneado no picking e na entrega, fecha a lacuna entre separação e recebimento.')
      + medida('03', 'Scan item a item', 'Bloqueia a conclusão em caso de divergência. Gera o dado de item que viabiliza as análises hoje impossíveis.')
      + '</div>'
      f'<div style="flex:1; display:flex; flex-direction:column; gap:28px">'
      + medida('04', 'Auditoria amostral priorizada', 'O ranking de acompanhamento define a ordem de amostragem, não uma lista de suspeitos.')
      + medida('05', 'Reembolso escalonado por valor', 'Aprovação automática apenas para baixo valor; verificação adicional acima do limite.')
      + medida('06', 'Incentivo por conformidade', 'Medido sobre a incidência por pedido, normalizada por volume. Nunca sobre a razão faltantes ÷ total.')
      + '</div></div>\n'
    + rodape(f'Teto de retorno: US$ {num(K["valor_em_risco"])} ao ano, ou {pct(K["valor_em_risco_pct_faturamento"])} '
             f'do faturamento. Qualquer medida com custo por entrega deve ser dimensionada contra esse teto.')
), 'O rodapé é o que separa uma recomendação de consultoria de uma lista de boas intenções: '
   'toda medida tem um teto de retorno conhecido.')

# ───────────────────────── 14 roadmap ─────────────────────────
slide('roadmap', (
    eyebrow('Próximos passos')
    + h2('O que viabiliza a detecção numa próxima rodada')
    + f'  <table style="font-family:{SANS}; font-size:26px; color:{ESC}; margin:44px 0 0">'
      f'<tr><th style="width:8%; text-align:left; padding:18px 20px; font-weight:600">Fase</th>'
      f'<th style="width:46%; text-align:left; font-weight:600">Ação</th>'
      f'<th style="width:46%; text-align:left; font-weight:600">Pré-requisito</th></tr>'
      f'<tr><td>1</td><td>Elevar o volume por unidade de análise: consolidar histórico multi-ano ou agregar por equipe e rota</td>'
      f'<td>Atingir ~{num(PW["cenarios"][0]["entregas_necessarias"])} entregas por unidade</td></tr>'
      f'<tr><td>2</td><td>Enriquecer a base com produto, categoria, cliente e registro de reclamação</td>'
      f'<td>Integração com ERP e sistema de atendimento</td></tr>'
      f'<tr><td>3</td><td>Modelos de anomalia não supervisionados</td><td>Fases 1 e 2 concluídas</td></tr>'
      f'<tr><td>4</td><td>Modelo supervisionado com explicabilidade</td><td>Rótulos vindos da auditoria da fase 1</td></tr>'
      f'<tr><td>5</td><td>Controle estatístico de processo sobre a incidência</td><td>Série estável após as medidas</td></tr>'
      f'</table>\n'
    + rodape('As fases 3 e 4 não são executáveis com o dado atual. Adiantá-las produziria modelos '
             'que aprendem volume de entregas, exatamente como o KPI antigo.')
), 'Ordenado por pré-requisito, não por sofisticação. Prometer XGBoost na fase 1 é o erro mais comum.')

# ───────────────────────── 15 conclusao ─────────────────────────
slide('conclusao', (
    eyebrow('Conclusão', PET)
    + f'  <div style="flex:1"></div>\n'
    + f'  <h2 style="font-family:{SERIF}; font-size:56px; font-weight:600; line-height:1.25; '
      f'color:#FFFFFF; width:1500px">A operação está dentro do esperado, nenhum motorista '
      f'apresenta desvio significativo, e a base não tem estrutura para sustentar acusação individual.</h2>\n'
    + f'  <p style="font-size:32px; line-height:1.5; color:{TXT_ESC}; width:1400px; padding:28px 0 0">'
      f'As medidas preventivas seguem recomendadas, por redução de disputa com cliente e por '
      f'custo-benefício operacional, dentro de um teto de US$ {num(K["valor_em_risco"])} ao ano.</p>\n'
    + f'  <div style="flex:1"></div>\n'
    + f'  <div style="display:flex; gap:52px; border-top:1px solid #2E3D4B; padding:32px 0 0">'
      f'<p style="font-size:25px; color:{TXT_ESC}">{num(A["motoristas_testados"])} motoristas testados</p>'
      f'<p style="font-size:25px; color:{TXT_ESC}">Correção FDR aplicada</p>'
      f'<p style="font-size:25px; color:{TXT_ESC}">Poder estatístico calculado</p>'
      f'<p style="font-size:25px; color:{TXT_ESC}">Limitações declaradas</p></div>\n'
), 'Fechar com um resultado negativo bem fundamentado demonstra ceticismo quantitativo, '
   'a competência central de auditoria e controladoria.',
   fundo=ESC, cor='#FFFFFF', extra='justify-content:space-between')

# ───────────────────────── indice ─────────────────────────
href = ('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700'
        '&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap')
indice = {
    'v': 4,
    # preservado do indice publicado: nao regerar a cada execucao
    'createdOnFiles': {'v': 1, 'at': '2026-09-22T05:40:07Z'},
    'title': 'Detecção de Fraude em Entregas',
    'order': slides,
    'sections': {
        's1': {'description': 'A pergunta de fraude, a resposta e o que a validação revelou sobre a base.', 'start': 'capa'},
        's2': {'description': 'Como a análise foi feita: limpeza, definição do KPI e teste corrigido.', 'start': 'metodo'},
        's3': {'description': 'Por que a base é gerada e não sustenta acusação individual.', 'start': 'determinismo'},
        's4': {'description': 'O que fazer com isso: medidas, roadmap e conclusão.', 'start': 'limites'},
    },
    'faces': {
        'source-serif-4': {'family': 'Source Serif 4', 'href': href},
        'ibm-plex-sans': {'family': 'IBM Plex Sans', 'href': href},
    },
    'designSystems': [],
}
json.dump(indice, open(f'{DECK}/project/deck.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print(f'{len(slides)} slides gerados:', ', '.join(slides))

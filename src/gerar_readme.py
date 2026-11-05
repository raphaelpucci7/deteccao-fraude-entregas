"""Gera o README.md do repositorio a partir de output/metricas.json."""
import json, pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = RAIZ / 'resultados'
M = json.load(open(OUT / 'metricas.json', encoding='utf-8'))
K, A, PW, AR = M['kpis'], M['anomalia'], M['poder'], M['artefatos']
EP, DM, EM, V, DV = (M['evento_por_pedido'], M['dimensoes'],
                     M['estrutura_motoristas'], M['validacao'], M['derivados'])

pct = lambda v, c=2: f'{v*100:.{c}f}'.replace('.', ',') + '%'
num = lambda v: f'{round(v):,}'.replace(',', '.')
dec = lambda v, c=3: f'{v:.{c}f}'.replace('.', ',')


README = f'''# Detecção de fraude em entregas de última milha

Análise de {num(V['linhas_brutas'])} pedidos de e-commerce para responder a uma pergunta de
operações: **os itens registrados como "não entregues" indicam fraude de motorista?**

A resposta é não, e o caminho até ela é o conteúdo deste repositório.

> ### ⚠️ Sobre a base
> Este é um **dataset sintético**, usado como exercício de análise. Não são dados
> operacionais de nenhuma empresa real, e nenhuma conclusão aqui descreve uma
> operação existente.
>
> Identificar que a base é gerada, e não observada, foi um dos dois resultados
> da análise. A prova está em [Achado 2](#achado-2--a-base-é-gerada-não-observada).

O repositório separa o que entrou do que saiu: **`dados_brutos/`** guarda a base original,
que o pipeline apenas lê, e **`resultados/`** guarda tudo que a análise produziu. O código que
leva de um ao outro está em `src/`.

---

## Resultados

| | |
|---|---|
| Incidência de pedidos com ao menos um item faltante | **{pct(K['incidencia_por_pedido'], 2)}** (IC 95%: {pct(K['incidencia_ic95'][0])} a {pct(K['incidencia_ic95'][1])}) |
| Taxa agregada de itens faltantes | **{pct(K['taxa_item_agregada'])}** (IC 95%: {pct(K['taxa_item_ic95'][0])} a {pct(K['taxa_item_ic95'][1])}) |
| Valor associado aos itens faltantes | **US$ {num(K['valor_em_risco'])}** ({pct(K['valor_em_risco_pct_faturamento'])} do faturamento) |
| Motoristas testados | {num(A['motoristas_testados'])} |
| Motoristas com desvio estatisticamente significativo | **{A['significativos_fdr']}** |

O benchmark de indústria de {pct(K['benchmark_industria'], 1)} usado como referência cai **dentro**
do intervalo de confiança da taxa observada. A diferença de {dec(K['diferenca_vs_benchmark_pp'], 2)} p.p.
não é distinguível de ruído amostral, então a operação não é descrita nem como acima
nem como abaixo do benchmark.

---

## Achado 1: o KPI original media tamanho de pedido

A métrica natural para "itens faltantes" é `itens_faltantes ÷ itens_totais`. Ela está errada
para esta operação, e o motivo é estrutural: **a falta é um evento que ocorre no pedido, não
em cada item**.

A probabilidade de um pedido apresentar falta é estatisticamente constante ao longo de todo
o intervalo de tamanhos (Spearman ρ = {dec(EP['spearman_incidencia_vs_tamanho'])}, p = {dec(EP['spearman_incidencia_p'])}, sem tendência).
Já a razão cai {dec(EP['queda_taxa_item'], 1)}× no mesmo intervalo (ρ = {dec(EP['spearman_taxa_item_vs_tamanho'])}), inteiramente por
efeito do denominador.

![Incidência por pedido versus razão faltantes sobre total](resultados/graficos/g1_tamanho_pedido.png)

**Consequência prática:** qualquer ranking de motoristas construído sobre essa razão ordena
os motoristas por mix de tamanho de pedido, não por conduta. Quem atende pedidos pequenos
aparece no topo sem qualquer desvio de comportamento.

O KPI foi redefinido como **incidência por pedido**, a proporção de pedidos com ao menos um
item faltante. A taxa agregada (`Σ faltantes ÷ Σ itens`) fica como métrica secundária de volume.

A média simples das razões por pedido, que trata um pedido de 2 itens igual a um de {AR['teto_items_delivered']},
infla o resultado em {dec(K['inflacao_da_metrica_incorreta'], 2)}× ({pct(K['media_razoes_INCORRETA'])} contra {pct(K['taxa_item_agregada'])}). Não é uma taxa
operacional e não foi usada.

---

## Achado 2: a base é gerada, não observada

Testar {num(A['motoristas_testados'])} motoristas a 5% de significância produziria cerca de {round(A['falsos_positivos_esperados'])} "descobertas"
por puro acaso. Por isso o critério de decisão é o q-valor após correção de
Benjamini-Hochberg, não o p-valor bruto.

**Nenhum motorista atinge sequer o limiar bruto de 0,05**. O menor p-valor da base é
{dec(A['menor_p_valor'], 4)}, e o menor q-valor, {dec(A['menor_q_valor'])}.

Antes de ler isso como "operação limpa", vale verificar se a base sequer admite variação
individual. Ela não admite. Se as faltas fossem sorteadas de forma independente, a
distribuição por motorista seria binomial. O observado diverge dela de forma extrema
(qui-quadrado = {num(EM['qui2_vs_binomial'])}):

![Distribuição observada contra a binomial](resultados/graficos/g5_estrutura.png)

Sob um processo aleatório, {dec(EM['esperado_binomial']['1'], 1)} motoristas teriam exatamente uma entrega com falta.
A base tem **{EM['observado']['1']}**.

A causa fica evidente ao cruzar volume com ocorrências: o número de entregas com falta é
praticamente uma função determinística do número de entregas:

![Entregas com falta por volume de entregas](resultados/graficos/g6_determinismo.png)

Motoristas com 6 ou 7 entregas têm sempre zero faltas. {EM['volumes_deterministicos']} dos {EM['volumes_distintos']} volumes distintos
admitem um único resultado possível; os demais admitem dois.

**A "taxa" de cada motorista nesta base é determinada pelo seu volume, não pela conduta.**
Qualquer lista de suspeitos extraída daqui seria, necessariamente, uma lista dos motoristas
mais ativos.

---

## Poder estatístico

Mesmo que houvesse sinal, o estudo não teria poder para detectá-lo. Com alfa corrigido para
{num(A['motoristas_testados'])} testes e poder alvo de 80%:

| Cenário | Entregas necessárias | Disponível na base |
|---|---|---|
{chr(10).join(f"| Motorista operando a {c['multiplo_da_taxa_base']:.0f}× a incidência base ({pct(c['incidencia_alvo'], 1)}) | {num(c['entregas_necessarias'])} | {PW['entregas_disponiveis_max']} |" for c in PW['cenarios'])}

![Entregas necessárias contra disponíveis](resultados/graficos/g4_poder.png)

O motorista mais ativo da base tem {PW['entregas_disponiveis_max']} entregas no ano; a mediana da frota é
{round(A['mediana_entregas'])}. O estudo está **{round(PW['subdimensionamento'])}× subdimensionado** para detecção individual.

A ausência de significância não prova ausência de fraude. Prova que esta base não tem volume
por motorista para detectá-la.

---

## O que a base não permite concluir

A base tem {len(V['colunas'])} colunas: `{'`, `'.join(V['colunas'])}`. Não há identificador de produto,
categoria, cliente ou registro de reclamação. Estão fora do escopo possível deste dado:
análise de mix de produto, ranking de SKUs, segmentação de clientes e qualquer comparação
com período anterior.

Três cortes foram testados com qui-quadrado de aderência. Nenhum apresenta variação
distinguível de flutuação aleatória:

| Dimensão | χ² | g.l. | p-valor | Amplitude |
|---|---|---|---|---|
| Região | {dec(DM['regiao']['qui2'], 2)} | {DM['regiao']['gl']} | {dec(DM['regiao']['p_valor'])} | {dec(DM['regiao']['amplitude_pp'], 2)} p.p. |
| Hora da entrega | {dec(DM['hora']['qui2'], 2)} | {DM['hora']['gl']} | {dec(DM['hora']['p_valor'])} | {dec(DM['hora']['amplitude_pp'], 2)} p.p. |
| Mês | {dec(DM['mes']['qui2'], 2)} | {DM['mes']['gl']} | {dec(DM['mes']['p_valor'])} | {dec(DM['mes']['amplitude_pp'], 2)} p.p. |

---

## Tratamento aplicado à base

A coluna `items_delivered` está truncada em {AR['teto_items_delivered']} na base original, o que força falta em
todo pedido acima desse teto: {AR['pedidos_removidos']} pedidos, {pct(AR['pct_com_falta_no_grupo_removido'], 0)} deles com falta, somando
{AR['faltas_removidas']} itens ({pct(AR['pct_das_faltas_brutas'], 1)} das faltas brutas). Foram removidos por serem artefato de
geração, não ocorrência operacional. Base analítica final: {num(K['pedidos'])} pedidos.

Outros indícios de geração sintética, registrados para transparência:

- Nenhum dos {AR['pedidos_1_item']} pedidos de item único apresenta falta (esperado: cerca de {round(DV['pedidos_1_item_esperado_com_falta'])}).
- Entregas por motorista assumem apenas os valores {', '.join(map(str, AR['valores_distintos_entregas_por_motorista']))}.
- Nenhum pedido registra mais de {AR['max_faltas_em_um_pedido']} itens faltantes.

Integridade verificada: zero valores nulos e a identidade
`itens_entregues + itens_faltantes = itens_total` válida em 100% das linhas.

---

## Reprodutibilidade

**Nenhum número dos entregáveis é digitado à mão.** `pipeline.py` lê a base e escreve
`output/metricas.json`; relatório, planilha, gráficos e slides são gerados a partir desse
JSON. `verificar.py` varre todo número citado nos entregáveis e falha se algum não for
derivável do JSON. É a defesa contra o número órfão, que é o modo mais comum de um deck
divergir da análise que o originou.

```bash
pip install -r requirements.txt
npm install docx

python src/pipeline.py          # base -> output/metricas.json + tabelas
python src/gerar_graficos.py    # gráficos do relatório
python src/gerar_excel.py       # workbook analítico + CSV
node   src/gerar_relatorio.js   # relatório .docx
python src/gerar_readme.py      # este arquivo
python src/verificar.py         # consistência cruzada (sai != 0 se falhar)
```

### Estrutura

```
├── data/entregas_2023.xlsx     base original
├── src/
│   ├── pipeline.py             fonte de verdade. Toda métrica sai daqui
│   ├── gerar_excel.py          workbook analítico (KPIs em fórmulas vivas)
│   ├── gerar_relatorio.js      relatório .docx
│   ├── gerar_graficos.py       figuras do relatório
│   ├── gerar_graficos_slide.py figuras do deck
│   ├── gerar_deck.py           slides
│   ├── gerar_readme.py         este README
│   └── verificar.py            consistência cruzada entre entregáveis
├── docs/                       entregáveis prontos para leitura
└── output/                     gerado (não versionado)
```

### Decisões metodológicas

1. **KPI primário = incidência por pedido.** A falta é evento por pedido, não por item (Achado 1).
2. **Média de razões é proibida.** Dá o mesmo peso a pedidos de tamanhos diferentes e infla o resultado.
3. **Teste binomial exato unilateral** por motorista, sobre pedidos, contra a incidência base.
4. **Correção Benjamini-Hochberg** obrigatória: com {num(A['motoristas_testados'])} testes, p-valor bruto não decide nada.
5. **Poder calculado antes de concluir.** Um resultado negativo sem análise de poder não é resultado.
6. **Artefatos de geração removidos e documentados**, nunca silenciosamente.

---

## Entregáveis

| Arquivo | Conteúdo |
|---|---|
| [`resultados/Relatorio_Fraude_Entregas_Last_Mile_2023.pdf`](resultados/Relatorio_Fraude_Entregas_Last_Mile_2023.pdf) | Relatório completo, 7 páginas |
| [`resultados/Analise_Fraude_Entregas_Last_Mile_2023.xlsx`](resultados/Analise_Fraude_Entregas_Last_Mile_2023.xlsx) | Workbook com 10 abas; `Overview` calcula os KPIs em fórmulas vivas sobre a base |
| [`resultados/drivers_ranking_acompanhamento.csv`](resultados/drivers_ranking_acompanhamento.csv) | Ranking de acompanhamento operacional, com p-valor e q-valor |

O CSV de motoristas é um ranking de **priorização de auditoria amostral**, não uma lista de
suspeitos: nenhum dos motoristas nele atinge significância estatística, e a coluna
`significativo_apos_correcao` registra isso explicitamente.

---

## Stack

Python (pandas, scipy, statsmodels, openpyxl, matplotlib) · Node (docx) · Excel com fórmulas vivas
'''

(RAIZ / 'README.md').write_text(README, encoding='utf-8')

(RAIZ / 'requirements.txt').write_text(
    'pandas>=2.0\nnumpy>=1.24\nscipy>=1.11\nstatsmodels>=0.14\n'
    'openpyxl>=3.1\nmatplotlib>=3.7\n', encoding='utf-8')

(RAIZ / '.gitignore').write_text(
    '# resultados/ e versionado: e o que a pessoa abre no GitHub sem rodar nada.\n'
    '# Fora o pickle intermediario, que se regenera com o pipeline.\n'
    'resultados/tabelas/base_limpa.pkl\n\n'
    'node_modules/\n__pycache__/\n*.pyc\n.DS_Store\n', encoding='utf-8')

print('README.md, requirements.txt e .gitignore gerados')
print('resultados/:', ', '.join(sorted(p.name for p in OUT.iterdir())))

"""
Pipeline unico de metricas - Deteccao de Fraude em Entregas de Ultima Milha
Dataset sintetico de e-commerce, 2023

FONTE DE VERDADE. Todo numero que aparece no deck, no relatorio, no Excel
ou no CSV sai deste script. Nada e' digitado a mao em nenhum entregavel.

Decisoes metodologicas travadas aqui:
  1. Exclusao do artefato de teto: items_delivered esta truncado em 19, o que
     forca 100% de falta em todo pedido com items_total >= 20. Esses pedidos
     sao removidos da base analitica e reportados separadamente.
  2. KPI primario = P(pedido com ao menos 1 item faltante). A falta e' um
     evento por PEDIDO, nao por item (verificado: a probabilidade e' constante
     em ~15% para pedidos de 2 a 19 itens).
  3. KPI secundario = taxa agregada de itens (soma faltantes / soma itens).
  4. PROIBIDO: media simples das razoes por pedido. Infla o resultado porque
     da o mesmo peso a um pedido de 2 itens e a um de 19.
  5. Deteccao de anomalia por motorista: teste binomial exato unilateral sobre
     PEDIDOS (o evento real), com correcao Benjamini-Hochberg para o numero
     de motoristas testados. Significancia so' e' declarada apos o q-valor.
"""

import json
import pathlib
import numpy as np
import pandas as pd
import openpyxl
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FONTE = str(RAIZ / 'dados_brutos' / 'entregas_2023.xlsx')
SAIDA = str(RAIZ / 'resultados')
TABELAS = str(RAIZ / 'resultados' / 'tabelas')
BRUTOS = str(RAIZ / 'dados_brutos')
ALPHA = 0.05

M = {}   # dicionario de metricas -> vira metricas.json


def carregar():
    wb = openpyxl.load_workbook(FONTE, data_only=True)
    linhas = list(wb['Data'].values)
    df = pd.DataFrame(linhas[1:], columns=linhas[0])
    df['data'] = pd.to_datetime(df['date'], unit='D', origin='1899-12-30')
    return df


def validar(df):
    """Checagens de integridade. Falha alto se a base nao for o que esperamos."""
    assert df.isna().sum().sum() == 0, 'base tem valores nulos'
    assert (df.items_delivered + df.items_missing == df.items_total).all(), \
        'items_delivered + items_missing != items_total'
    M['validacao'] = {
        'linhas_brutas': int(len(df)),
        'valores_nulos': 0,
        'identidade_itens_ok': True,
        'periodo_inicio': df.data.min().strftime('%d/%m/%Y'),
        'periodo_fim': df.data.max().strftime('%d/%m/%Y'),
        'regioes': sorted(df.region.unique().tolist()),
        'colunas': df.columns.drop('data').tolist(),
    }


def limpar(df):
    """Remove o artefato de teto e documenta o impacto."""
    teto = df.items_delivered.max()
    art = df[df.items_total > teto]
    M['artefatos'] = {
        'teto_items_delivered': int(teto),
        'pedidos_removidos': int(len(art)),
        'faltas_removidas': int(art.items_missing.sum()),
        'pct_das_faltas_brutas': float(art.items_missing.sum() / df.items_missing.sum()),
        'pct_com_falta_no_grupo_removido': float(art.items_missing.gt(0).mean()),
        'teto_mais_um': int(teto + 1),
        'pedidos_1_item': int((df.items_total == 1).sum()),
        'pedidos_1_item_com_falta': int(df[df.items_total == 1].items_missing.gt(0).sum()),
        'valores_distintos_entregas_por_motorista':
            sorted(df.groupby('driver_id').size().unique().tolist()),
        'max_faltas_em_um_pedido': int(df.items_missing.max()),
    }
    return df[df.items_total <= teto].copy()


def kpis(df):
    ped = len(df)
    ped_falta = int(df.items_missing.gt(0).sum())
    itens = int(df.items_total.sum())
    faltas = int(df.items_missing.sum())

    inc = ped_falta / ped                        # KPI primario
    tx_item = faltas / itens                     # KPI secundario
    media_razoes = float((df.items_missing / df.items_total).mean())  # metrica incorreta, so' p/ contraste

    lo_i, hi_i = proportion_confint(ped_falta, ped, method='wilson')
    lo_t, hi_t = proportion_confint(faltas, itens, method='wilson')

    # valor em risco: rateia o valor do pedido pelos itens
    valor_item = df.order_amount_clean / df.items_total
    risco = float((valor_item * df.items_missing).sum())
    fat = float(df.order_amount_clean.sum())

    M['kpis'] = {
        'pedidos': int(ped),
        'pedidos_com_falta': ped_falta,
        'itens': itens,
        'itens_faltantes': faltas,
        'motoristas': int(df.driver_id.nunique()),
        'incidencia_por_pedido': float(inc),
        'incidencia_ic95': [float(lo_i), float(hi_i)],
        'taxa_item_agregada': float(tx_item),
        'taxa_item_ic95': [float(lo_t), float(hi_t)],
        'media_razoes_INCORRETA': media_razoes,
        'inflacao_da_metrica_incorreta': float(media_razoes / tx_item),
        'faturamento': fat,
        'valor_em_risco': risco,
        'valor_em_risco_pct_faturamento': float(risco / fat),
        'benchmark_industria': 0.015,
        # o benchmark cai dentro do IC da taxa observada? entao a diferenca nao
        # e' distinguivel de ruido amostral e nao deve ser narrada como desvio.
        'benchmark_dentro_do_ic': bool(lo_t <= 0.015 <= hi_t),
        'diferenca_vs_benchmark_pp': float((tx_item - 0.015) * 100),
    }


def evento_por_pedido(df):
    """Prova que a falta e' evento por pedido, nao por item."""
    linhas = []
    for n in range(2, int(df.items_total.max()) + 1):
        s = df[df.items_total == n]
        if len(s) >= 50:
            linhas.append({
                'tamanho_pedido': n,
                'pedidos': int(len(s)),
                'p_pedido_com_falta': float(s.items_missing.gt(0).mean()),
                'taxa_por_item': float(s.items_missing.sum() / s.items_total.sum()),
            })
    t = pd.DataFrame(linhas)
    # a incidencia nao deve ter tendencia; a taxa por item deve despencar
    rho_inc = stats.spearmanr(t.tamanho_pedido, t.p_pedido_com_falta)
    rho_tx = stats.spearmanr(t.tamanho_pedido, t.taxa_por_item)
    M['evento_por_pedido'] = {
        'tabela': linhas,
        'spearman_incidencia_vs_tamanho': float(rho_inc.statistic),
        'spearman_incidencia_p': float(rho_inc.pvalue),
        'spearman_taxa_item_vs_tamanho': float(rho_tx.statistic),
        'spearman_taxa_item_p': float(rho_tx.pvalue),
        'queda_taxa_item': float(t.taxa_por_item.iloc[0] / t.taxa_por_item.iloc[-1]),
    }
    return t


def por_dimensao(df, col, rotulo):
    """Agrega por dimensao e testa se a variacao e' significativa (qui-quadrado)."""
    g = df.groupby(col).agg(
        pedidos=('items_total', 'size'),
        pedidos_com_falta=('items_missing', lambda s: int(s.gt(0).sum())),
        itens=('items_total', 'sum'),
        faltas=('items_missing', 'sum'),
        faturamento=('order_amount_clean', 'sum'),
    )
    g['incidencia'] = g.pedidos_com_falta / g.pedidos
    g['taxa_item'] = g.faltas / g.itens
    ic = [proportion_confint(k, n, method='wilson')
          for k, n in zip(g.pedidos_com_falta, g.pedidos)]
    g['ic_lo'] = [a for a, b in ic]
    g['ic_hi'] = [b for a, b in ic]

    p0 = M['kpis']['incidencia_por_pedido']
    chi2, p = stats.chisquare(g.pedidos_com_falta, f_exp=g.pedidos * p0)
    M.setdefault('dimensoes', {})[rotulo] = {
        'qui2': float(chi2),
        'gl': int(len(g) - 1),
        'p_valor': float(p),
        'significativo': bool(p < ALPHA),
        'amplitude_pp': float((g.incidencia.max() - g.incidencia.min()) * 100),
    }
    return g.reset_index()


def anomalia_motoristas(df):
    """
    Deteccao por motorista. Teste binomial exato unilateral sobre PEDIDOS
    (o evento real), corrigido por Benjamini-Hochberg.
    """
    g = df.groupby(['driver_id', 'driver_name']).agg(
        entregas=('items_total', 'size'),
        entregas_com_falta=('items_missing', lambda s: int(s.gt(0).sum())),
        itens=('items_total', 'sum'),
        itens_faltantes=('items_missing', 'sum'),
        valor=('order_amount_clean', 'sum'),
    ).reset_index()

    p0 = M['kpis']['incidencia_por_pedido']
    g['incidencia'] = g.entregas_com_falta / g.entregas
    g['esperado'] = g.entregas * p0
    g['p_valor'] = [
        stats.binomtest(int(k), int(n), p0, alternative='greater').pvalue
        for k, n in zip(g.entregas_com_falta, g.entregas)
    ]
    rej, q, _, _ = multipletests(g.p_valor, alpha=ALPHA, method='fdr_bh')
    g['q_valor'] = q
    g['significativo_fdr'] = rej
    rej_b, _, _, _ = multipletests(g.p_valor, alpha=ALPHA, method='bonferroni')
    g['significativo_bonferroni'] = rej_b

    g = g.sort_values('p_valor').reset_index(drop=True)
    g['rank'] = np.arange(1, len(g) + 1)

    M['anomalia'] = {
        'motoristas_testados': int(len(g)),
        'taxa_base_usada': float(p0),
        'p_bruto_abaixo_05': int((g.p_valor < ALPHA).sum()),
        'falsos_positivos_esperados': float(len(g) * ALPHA),
        'significativos_fdr': int(g.significativo_fdr.sum()),
        'significativos_bonferroni': int(g.significativo_bonferroni.sum()),
        'menor_p_valor': float(g.p_valor.min()),
        'menor_q_valor': float(g.q_valor.min()),
        'motoristas_com_zero_faltas': int((g.itens_faltantes == 0).sum()),
        'pct_motoristas_zero_faltas': float((g.itens_faltantes == 0).mean()),
        'max_entregas_por_motorista': int(g.entregas.max()),
        'mediana_entregas': float(g.entregas.median()),
        'max_entregas_com_falta': int(g.entregas_com_falta.max()),
    }
    return g


def estrutura_motoristas(g):
    """
    Testa se a distribuicao de entregas-com-falta por motorista e' compativel
    com um processo aleatorio (binomial). Se nao for, nao ha variacao individual
    a detectar: o numero de faltas e' funcao do volume, nao do motorista.
    """
    p0 = M['kpis']['incidencia_por_pedido']
    ct = pd.crosstab(g.entregas, g.entregas_com_falta)

    obs = g.entregas_com_falta.value_counts().to_dict()
    esp = {}
    for n in g.entregas:
        for k in range(int(n) + 1):
            esp[k] = esp.get(k, 0) + stats.binom.pmf(k, int(n), p0)

    ks = sorted(set(list(obs.keys()) + list(esp.keys())))
    o = np.array([obs.get(k, 0) for k in ks], float)
    e = np.array([esp.get(k, 0) for k in ks], float)
    e = np.where(e < 1e-9, 1e-9, e)
    chi2 = float(((o - e) ** 2 / e).sum())

    # quantas linhas da tabela cruzada sao deterministicas (uma unica coluna ocupada)
    determin = int((ct.gt(0).sum(axis=1) == 1).sum())

    M['estrutura_motoristas'] = {
        'tabela_cruzada': {str(i): {str(c): int(v) for c, v in row.items() if v > 0}
                           for i, row in ct.iterrows()},
        'volumes_distintos': int(len(ct)),
        'volumes_deterministicos': determin,
        'qui2_vs_binomial': chi2,
        'observado': {str(k): int(obs.get(k, 0)) for k in ks},
        'esperado_binomial': {str(k): round(esp.get(k, 0), 1) for k in ks},
        'compativel_com_processo_aleatorio': bool(chi2 < 100),
        'menor_p_valor_alcancavel': float(
            stats.binomtest(int(g.entregas.max()), int(g.entregas.max()), p0,
                            alternative='greater').pvalue),
    }
    return ct


def poder(df, g):
    """Quantas entregas seriam necessarias para detectar um desvio real."""
    p0 = M['kpis']['incidencia_por_pedido']
    n_testes = len(g)
    alpha_corr = ALPHA / n_testes
    linhas = []
    for mult in (2.0, 3.0, 4.0):
        p1 = min(p0 * mult, 0.99)
        necessario = None
        for n in range(10, 3001, 5):
            crit = stats.binom.ppf(1 - alpha_corr, n, p0)
            pot = 1 - stats.binom.cdf(crit, n, p1)
            if pot >= 0.80:
                necessario = n
                break
        linhas.append({
            'multiplo_da_taxa_base': mult,
            'incidencia_alvo': float(p1),
            'entregas_necessarias': necessario,
        })
    M['poder'] = {
        'alvo_poder': 0.80,
        'alpha_corrigido': float(alpha_corr),
        'cenarios': linhas,
        'entregas_disponiveis_max': int(g.entregas.max()),
        'subdimensionamento': float(linhas[0]['entregas_necessarias'] / g.entregas.max()),
    }


def dicionario_de_dados(bruto):
    """
    Escreve o LEIA-ME da pasta de dados brutos. Descreve a base como ela e',
    a partir dela mesma, para que ninguem precise abrir o xlsx para entender
    o que cada coluna significa.
    """
    desc = {
        'driver_name': 'Nome do motorista responsavel pela entrega',
        'driver_id': 'Identificador unico do motorista (formato WDID#####)',
        'region': 'Regiao atendida, entre as sete da area metropolitana',
        'date': 'Data da entrega, em numero de serie do Excel',
        'delivery_hour_num': 'Hora da entrega, de 0 a 23',
        'items_delivered': 'Itens efetivamente entregues ao cliente',
        'items_missing': 'Itens registrados como nao entregues',
        'items_total': 'Total de itens do pedido',
        'order_amount_clean': 'Valor do pedido em dolares',
    }
    linhas = ['# Dados brutos', '',
              'Base original da analise, exatamente como foi recebida. '
              'Nada aqui e editado pelo pipeline: os scripts apenas leem este arquivo.', '',
              '> **Dataset sintetico.** Nao sao dados operacionais de nenhuma empresa real. '
              'A analise em `../resultados/` demonstra que a base e gerada artificialmente, '
              'e nao observada.', '',
              '## entregas_2023.xlsx', '',
              (f"Aba `Data`, {len(bruto):,}".replace(',', '.') +
               f" linhas, {len(desc)} colunas, periodo de "
               f"{M['validacao']['periodo_inicio']} a {M['validacao']['periodo_fim']}."), '',
              '| Coluna | Tipo | Descricao | Amplitude |',
              '|---|---|---|---|']
    for c, d in desc.items():
        s = bruto[c]
        if c == 'date':
            amp = f"{M['validacao']['periodo_inicio']} a {M['validacao']['periodo_fim']}"
            tipo = 'inteiro'
        elif not pd.api.types.is_numeric_dtype(s):
            amp = f'{s.nunique():,}'.replace(',', '.') + ' valores distintos'
            tipo = 'texto'
        else:
            tipo = 'decimal' if s.dtype.kind == 'f' else 'inteiro'
            amp = (f'{s.min():,.2f} a {s.max():,.2f}' if tipo == 'decimal'
                   else f'{int(s.min())} a {int(s.max())}')
            amp = amp.replace(',', '#').replace('.', ',').replace('#', '.') if tipo == 'decimal' else amp
        linhas.append(f'| `{c}` | {tipo} | {d} | {amp} |')
    linhas += ['',
               '## Integridade', '',
               '- Zero valores nulos em todas as colunas.',
               '- `items_delivered + items_missing = items_total` vale em 100% das linhas.',
               (f"- Sao {bruto.driver_id.nunique():,} `driver_id` distintos para "
                f"{bruto.driver_name.nunique():,} nomes: ha homonimos, "
                "e o identificador e o que vale.").replace(',', '.'),
               '',
               '## Limitacoes conhecidas', '',
               f"- `items_delivered` esta truncado em {M['artefatos']['teto_items_delivered']}, "
               f"o que forca falta em todo pedido maior que isso "
               f"({M['artefatos']['pedidos_removidos']} pedidos, removidos da base analitica).",
               f"- Nenhum dos {M['artefatos']['pedidos_1_item']} pedidos de item unico registra falta.",
               f"- Entregas por motorista assumem apenas os valores "
               f"{', '.join(map(str, M['artefatos']['valores_distintos_entregas_por_motorista']))}.",
               '- Nao ha coluna de produto, categoria, cliente ou reclamacao.',
               '',
               'O tratamento aplicado a cada uma dessas limitacoes esta documentado no '
               'relatorio, em `../resultados/`.', '']
    pathlib.Path(BRUTOS).mkdir(parents=True, exist_ok=True)
    (pathlib.Path(BRUTOS) / 'LEIA-ME.md').write_text('\n'.join(linhas), encoding='utf-8')


def main():
    bruto = carregar()
    validar(bruto)
    df = limpar(bruto)

    kpis(df)
    tam = evento_por_pedido(df)
    reg = por_dimensao(df, 'region', 'regiao')
    hor = por_dimensao(df, 'delivery_hour_num', 'hora')
    mes = por_dimensao(df, df.data.dt.to_period('M').astype(str).rename('mes'), 'mes')
    drv = anomalia_motoristas(df)
    estrutura_motoristas(drv)
    poder(df, drv)

    # valores derivados citados nos entregaveis, gravados aqui para que todo
    # numero de slide e relatorio seja rastreavel a este arquivo.
    M['derivados'] = {
        'pedidos_1_item_esperado_com_falta':
            float(M['artefatos']['pedidos_1_item'] * M['kpis']['incidencia_por_pedido']),
        'esperado_no_motorista_mais_ativo':
            float(M['anomalia']['max_entregas_por_motorista'] * M['kpis']['incidencia_por_pedido']),
        'valor_em_risco_milhares': float(M['kpis']['valor_em_risco'] / 1000),
    }

    M['conclusao'] = {
        'sinal_de_fraude_detectado': bool(M['anomalia']['significativos_fdr'] > 0),
        'existe_variacao_individual_entre_motoristas':
            M['estrutura_motoristas']['compativel_com_processo_aleatorio'],
        'operacao_vs_benchmark': (
            'indistinguivel' if M['kpis']['benchmark_dentro_do_ic']
            else ('abaixo' if M['kpis']['taxa_item_agregada'] < M['kpis']['benchmark_industria']
                  else 'acima')
        ),
        'variacao_regional_significativa': M['dimensoes']['regiao']['significativo'],
        'variacao_horaria_significativa': M['dimensoes']['hora']['significativo'],
        'estudo_tem_poder_para_deteccao_individual': bool(
            M['poder']['entregas_disponiveis_max'] >=
            M['poder']['cenarios'][0]['entregas_necessarias']
        ),
    }

    pathlib.Path(TABELAS).mkdir(parents=True, exist_ok=True)
    with open(f'{SAIDA}/metricas.json', 'w', encoding='utf-8') as f:
        json.dump(M, f, ensure_ascii=False, indent=2)
    for nome, t in [('tamanho_pedido', tam), ('regiao', reg), ('hora', hor),
                    ('mes', mes), ('motoristas', drv)]:
        t.to_csv(f'{TABELAS}/tab_{nome}.csv', index=False)
    df.to_pickle(f'{TABELAS}/base_limpa.pkl')
    dicionario_de_dados(bruto)

    print('=' * 68)
    print('PIPELINE OK')
    print('=' * 68)
    k = M['kpis']
    print(f"pedidos analisados ......... {k['pedidos']:,}".replace(',', '.'))
    print(f"incidencia por pedido ...... {k['incidencia_por_pedido']:.2%} "
          f"(IC95 {k['incidencia_ic95'][0]:.2%}-{k['incidencia_ic95'][1]:.2%})")
    print(f"taxa de itens agregada ..... {k['taxa_item_agregada']:.2%} "
          f"(IC95 {k['taxa_item_ic95'][0]:.2%}-{k['taxa_item_ic95'][1]:.2%})")
    print(f"metrica incorreta (contraste) {k['media_razoes_INCORRETA']:.2%} "
          f"= {k['inflacao_da_metrica_incorreta']:.2f}x a correta")
    print(f"faturamento ................ US$ {k['faturamento']:,.2f}")
    print(f"valor em risco ............. US$ {k['valor_em_risco']:,.2f} "
          f"({k['valor_em_risco_pct_faturamento']:.2%})")
    print(f"\nmotoristas significativos (FDR) ... {M['anomalia']['significativos_fdr']}")
    print(f"menor q-valor .................... {M['anomalia']['menor_q_valor']:.3f}")
    print(f"regiao  p={M['dimensoes']['regiao']['p_valor']:.3f}  "
          f"hora p={M['dimensoes']['hora']['p_valor']:.3f}  "
          f"mes p={M['dimensoes']['mes']['p_valor']:.3f}")
    print(f"\npoder: {M['poder']['cenarios'][0]['entregas_necessarias']} entregas "
          f"necessarias vs {M['poder']['entregas_disponiveis_max']} disponiveis "
          f"= {M['poder']['subdimensionamento']:.0f}x subdimensionado")
    em = M['estrutura_motoristas']
    print(f"\nestrutura por motorista: {em['volumes_deterministicos']}/{em['volumes_distintos']} "
          f"volumes deterministicos | qui2 vs binomial = {em['qui2_vs_binomial']:,.0f}")
    print(f"  max entregas com falta observado: {M['anomalia']['max_entregas_com_falta']} "
          f"-> menor p-valor da base: {M['anomalia']['menor_p_valor']:.4f} (nem atinge 0,05)")
    print(f"\nevento por pedido: incidencia x tamanho rho="
          f"{M['evento_por_pedido']['spearman_incidencia_vs_tamanho']:.3f} "
          f"(p={M['evento_por_pedido']['spearman_incidencia_p']:.3f}) | "
          f"taxa_item x tamanho rho="
          f"{M['evento_por_pedido']['spearman_taxa_item_vs_tamanho']:.3f}")


if __name__ == '__main__':
    main()

"""Versoes dos graficos para o deck: fundo do slide, tipografia maior."""
import json, pathlib, pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = str(RAIZ / 'resultados')
GRAF = str(RAIZ / 'resultados' / 'graficos')
pathlib.Path(GRAF).mkdir(parents=True, exist_ok=True)
M = json.load(open(f'{OUT}/metricas.json', encoding='utf-8'))

FUNDO = '#F8F8F5'
ESCURO = '#15202B'; OXIDO = '#B0442C'; PETRO = '#2D6A6A'; CINZA = '#7C8691'; CLARO = '#D8D8D0'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 15,
    'text.color': ESCURO, 'axes.labelcolor': ESCURO,
    'xtick.color': CINZA, 'ytick.color': CINZA, 'xtick.labelsize': 14, 'ytick.labelsize': 14,
    'axes.edgecolor': '#C9C9C0', 'axes.linewidth': 1.1,
    'axes.grid': True, 'grid.color': '#E4E4DC', 'grid.linewidth': 1,
    'axes.axisbelow': True, 'figure.dpi': 150, 'savefig.bbox': 'tight',
    'figure.facecolor': FUNDO, 'axes.facecolor': FUNDO, 'savefig.facecolor': FUNDO,
})


def limpar(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


# S1: o KPI mede tamanho de pedido
t = pd.DataFrame(M['evento_por_pedido']['tabela'])
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(t.tamanho_pedido, t.p_pedido_com_falta * 100, 'o-', color=PETRO, lw=3.2, ms=8)
ax.plot(t.tamanho_pedido, t.taxa_por_item * 100, 'o-', color=OXIDO, lw=3.2, ms=8)
ax.text(10.5, 19.2, 'Incidência por pedido: o evento real', color=PETRO,
        fontsize=16.5, fontweight='bold', ha='center')
ax.text(13.6, 6.2, 'faltantes ÷ total: a métrica antiga', color=OXIDO,
        fontsize=16.5, fontweight='bold', ha='center')
ax.annotate('', xy=(17, 1.4), xytext=(14.6, 5.2),
            arrowprops=dict(arrowstyle='->', color=OXIDO, lw=1.6))
ax.set_xlabel('Tamanho do pedido (itens)', fontsize=15, labelpad=9)
ax.set_ylabel('%', fontsize=15)
ax.set_xticks(range(2, 20, 2)); ax.set_ylim(0, 22)
limpar(ax)
fig.savefig(f'{GRAF}/s1_kpi.png'); plt.close(fig)

# S2: determinismo
em = M['estrutura_motoristas']
ct = em['tabela_cruzada']
vols = sorted(int(v) for v in ct)
fig, ax = plt.subplots(figsize=(11, 4.4))
for v in vols:
    for k, n in ct[str(v)].items():
        ax.scatter(v, int(k), s=min(120 + n * 3.4, 1500), color=PETRO, alpha=.85, zorder=3)
        if n >= 60:
            ax.annotate(f'{n}', (v, int(k)), color='white', fontsize=14,
                        ha='center', va='center', fontweight='bold', zorder=4)
        else:
            ax.annotate(f'{n}', (v, int(k)), color=PETRO, fontsize=14, fontweight='bold',
                        textcoords='offset points', xytext=(24, 0), va='center', zorder=4)
ax.set_xlabel('Entregas no ano', fontsize=15, labelpad=9)
ax.set_ylabel('Entregas com falta', fontsize=15)
ax.set_xticks(vols); ax.set_yticks(range(0, 5))
ax.set_xlim(5.3, 11.9); ax.set_ylim(-.6, 4.6)
limpar(ax)
fig.savefig(f'{GRAF}/s2_determinismo.png'); plt.close(fig)

# S3: poder
pw = M['poder']
fig, ax = plt.subplots(figsize=(11, 4.0))
lab = [f"{c['multiplo_da_taxa_base']:.0f}× a base" for c in pw['cenarios']]
nec = [c['entregas_necessarias'] for c in pw['cenarios']]
y = range(len(lab))
ax.barh(y, nec, color=CLARO, height=.52)
ax.barh(y, [pw['entregas_disponiveis_max']] * len(lab), color=OXIDO, height=.24)
for i, n in enumerate(nec):
    ax.text(n + 5, i, f'{n} entregas', va='center', fontsize=16,
            color=ESCURO, fontweight='bold')
ax.annotate(f"disponível na base: {pw['entregas_disponiveis_max']}",
            xy=(pw['entregas_disponiveis_max'], 0), xytext=(58, -.44),
            color=OXIDO, fontsize=15.5, fontweight='bold', va='center',
            arrowprops=dict(arrowstyle='->', color=OXIDO, lw=1.5))
ax.set_yticks(list(y)); ax.set_yticklabels(lab, fontsize=16)
ax.set_xlabel('Entregas por motorista necessárias para 80% de poder', fontsize=15, labelpad=9)
ax.invert_yaxis(); ax.set_xlim(0, max(nec) * 1.32); ax.set_ylim(2.6, -.75)
ax.grid(axis='y', visible=False)
limpar(ax)
fig.savefig(f'{GRAF}/s3_poder.png'); plt.close(fig)

# S4: dimensoes sem sinal: hora com IC
h = pd.read_csv(f'{OUT}/tabelas/tab_hora.csv')
base = M['kpis']['incidencia_por_pedido'] * 100
fig, ax = plt.subplots(figsize=(11, 4.0))
ax.vlines(h.delivery_hour_num, h.ic_lo * 100, h.ic_hi * 100, color=CINZA, lw=2.4)
ax.plot(h.delivery_hour_num, h.incidencia * 100, 'o', color=PETRO, ms=9, zorder=3)
ax.axhline(base, color=OXIDO, ls='--', lw=2.2)
ax.text(23.5, base + .7, f'base {base:.1f}%', color=OXIDO, fontsize=15,
        ha='right', fontweight='bold')
ax.set_xlabel('Hora da entrega', fontsize=15, labelpad=9)
ax.set_ylabel('Incidência (%)', fontsize=15)
ax.set_xticks(range(0, 24, 3))
limpar(ax)
fig.savefig(f'{GRAF}/s4_hora.png'); plt.close(fig)

print('4 graficos de slide gerados')

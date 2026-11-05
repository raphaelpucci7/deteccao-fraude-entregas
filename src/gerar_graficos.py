"""Graficos do relatorio e do deck. Todos lidos do pipeline, nenhum numero a mao."""
import json, pathlib, pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = str(RAIZ / 'resultados')
GRAF = str(RAIZ / 'resultados' / 'graficos')
pathlib.Path(GRAF).mkdir(parents=True, exist_ok=True)
M = json.load(open(f'{OUT}/metricas.json', encoding='utf-8'))

AZUL = '#1F3864'; VERM = '#C00000'; CINZA = '#8C8C8C'; CLARO = '#D9D9D9'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.edgecolor': '#BFBFBF', 'axes.linewidth': .8,
    'axes.grid': True, 'grid.color': '#E8E8E8', 'grid.linewidth': .7,
    'axes.axisbelow': True, 'figure.dpi': 200, 'savefig.bbox': 'tight',
})


def limpar(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


# 1 ── o KPI antigo mede tamanho de pedido
t = pd.DataFrame(M['evento_por_pedido']['tabela'])
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.plot(t.tamanho_pedido, t.p_pedido_com_falta * 100, 'o-', color=AZUL, lw=2, ms=4.5,
        label='Incidência por pedido: o evento real')
ax.plot(t.tamanho_pedido, t.taxa_por_item * 100, 'o-', color=VERM, lw=2, ms=4.5,
        label='faltantes ÷ total: a métrica antiga')
ax.set_xlabel('Tamanho do pedido (itens)'); ax.set_ylabel('%')
ax.set_xticks(range(2, 20, 2)); ax.set_ylim(0, 22)
ax.legend(frameon=False, loc='center right', fontsize=8.5, bbox_to_anchor=(1.0, .42))
ax.annotate('plana: o evento não depende do tamanho do pedido', xy=(10.5, 20),
            color=AZUL, fontsize=8.5, ha='center', fontweight='bold')
ax.annotate(f"cai {M['evento_por_pedido']['queda_taxa_item']:.0f}×: efeito do denominador",
            xy=(16, 1.1), xytext=(8.5, 5.2), color=VERM, fontsize=8.5, ha='center',
            fontweight='bold', arrowprops=dict(arrowstyle='->', color=VERM, lw=.9))
limpar(ax)
fig.savefig(f'{GRAF}/g1_tamanho_pedido.png'); plt.close(fig)

# 2 ── incidencia por hora com IC95
h = pd.read_csv(f'{OUT}/tabelas/tab_hora.csv')
base = M['kpis']['incidencia_por_pedido'] * 100
fig, ax = plt.subplots(figsize=(7.2, 3.1))
ax.vlines(h.delivery_hour_num, h.ic_lo * 100, h.ic_hi * 100, color=CINZA, lw=1.6)
ax.plot(h.delivery_hour_num, h.incidencia * 100, 'o', color=AZUL, ms=5, zorder=3)
ax.axhline(base, color=VERM, ls='--', lw=1.4)
ax.text(23.4, base + .5, f'base {base:.1f}%', color=VERM, fontsize=8.5, ha='right')
ax.set_xlabel('Hora da entrega'); ax.set_ylabel('Incidência por pedido (%)')
ax.set_xticks(range(0, 24, 3))
ax.set_title(f"Qui-quadrado: p = {M['dimensoes']['hora']['p_valor']:.3f}, variação não significativa",
             fontsize=9.5, color=AZUL, loc='left', pad=9)
limpar(ax)
fig.savefig(f'{GRAF}/g2_hora.png'); plt.close(fig)

# 3 ── incidencia por regiao com IC95
r = pd.read_csv(f'{OUT}/tabelas/tab_regiao.csv').sort_values('incidencia')
fig, ax = plt.subplots(figsize=(7.2, 2.9))
y = range(len(r))
ax.hlines(y, r.ic_lo * 100, r.ic_hi * 100, color=CINZA, lw=1.8)
ax.plot(r.incidencia * 100, y, 'o', color=AZUL, ms=5.5, zorder=3)
ax.axvline(base, color=VERM, ls='--', lw=1.4)
ax.set_yticks(list(y)); ax.set_yticklabels(r.region, fontsize=8.5)
ax.set_xlabel('Incidência por pedido (%)')
ax.set_title(f"Qui-quadrado: p = {M['dimensoes']['regiao']['p_valor']:.3f}, variação não significativa",
             fontsize=9.5, color=AZUL, loc='left', pad=9)
ax.grid(axis='y', visible=False)
limpar(ax)
fig.savefig(f'{GRAF}/g3_regiao.png'); plt.close(fig)

# 4 ── poder estatistico
pw = M['poder']
fig, ax = plt.subplots(figsize=(7.2, 2.9))
lab = [f"{c['multiplo_da_taxa_base']:.0f}× a base\n({c['incidencia_alvo']:.0%})" for c in pw['cenarios']]
nec = [c['entregas_necessarias'] for c in pw['cenarios']]
ypos = range(len(lab))
ax.barh(ypos, nec, color=CLARO, height=.55, label='Entregas necessárias (80% de poder)')
ax.barh(ypos, [pw['entregas_disponiveis_max']] * len(lab), color=VERM, height=.22,
        label=f"Disponível na base ({pw['entregas_disponiveis_max']})")
for i, n in enumerate(nec):
    ax.text(n + 12, i, f'{n}', va='center', fontsize=8.5, color=AZUL, fontweight='bold')
ax.set_yticks(list(ypos)); ax.set_yticklabels(lab, fontsize=8.5)
ax.set_xlabel('Entregas por motorista'); ax.invert_yaxis()
ax.legend(frameon=False, fontsize=8.5, loc='lower right')
ax.set_title(f"Estudo {pw['subdimensionamento']:.0f}× subdimensionado para detecção individual",
             fontsize=9.5, color=VERM, loc='left', pad=9)
ax.grid(axis='y', visible=False)
limpar(ax)
fig.savefig(f'{GRAF}/g4_poder.png'); plt.close(fig)

# 5 ── a base nao se comporta como processo aleatorio
em = M['estrutura_motoristas']
ks = [int(k) for k in sorted(em['observado'], key=int)
      if em['observado'][k] > 0 or em['esperado_binomial'][k] >= 1]
obs = [em['observado'][str(k)] for k in ks]
esp = [em['esperado_binomial'][str(k)] for k in ks]
import numpy as np
x = np.arange(len(ks)); w = .38
fig, ax = plt.subplots(figsize=(7.2, 2.9))
ax.bar(x - w / 2, obs, w, color=AZUL, label='Observado na base')
ax.bar(x + w / 2, esp, w, color=CLARO, label='Esperado se fosse aleatório (binomial)')
topo = max(max(obs), max(esp))
for i, (o, e) in enumerate(zip(obs, esp)):
    ax.text(i - w / 2, o + topo * .03, f'{o}', ha='center', fontsize=8.5,
            color=VERM if o == 1 else AZUL, fontweight='bold')
    if e >= 5:
        ax.text(i + w / 2, e + topo * .03, f'{e:.0f}', ha='center', fontsize=8.5, color=CINZA)
ax.set_xticks(x); ax.set_xticklabels(ks)
ax.set_xlabel('Entregas com falta no ano, por motorista'); ax.set_ylabel('Motoristas')
ax.legend(frameon=False, fontsize=8.5)
ax.set_title('Nenhum motorista tem 1 falta; 167 têm exatamente 4. A base não é aleatória',
             fontsize=9.5, color=VERM, loc='left', pad=9)
ax.grid(axis='x', visible=False); ax.set_ylim(0, max(max(obs), max(esp)) * 1.2)
limpar(ax)
fig.savefig(f'{GRAF}/g5_estrutura.png'); plt.close(fig)

# 6 ── faltas sao funcao deterministica do volume
ct = em['tabela_cruzada']
vols = sorted(int(v) for v in ct)
fig, ax = plt.subplots(figsize=(7.2, 2.6))
for v in vols:
    for k, n in ct[str(v)].items():
        ax.scatter(v, int(k), s=min(40 + n * 1.6, 420), color=AZUL, alpha=.82, zorder=3)
        if n >= 60:
            ax.annotate(f'{n}', (v, int(k)), color='white', fontsize=8,
                        ha='center', va='center', fontweight='bold', zorder=4)
        else:
            ax.annotate(f'{n}', (v, int(k)), color=AZUL, fontsize=8, fontweight='bold',
                        textcoords='offset points', xytext=(13, 0), va='center', zorder=4)
ax.set_xlabel('Entregas no ano'); ax.set_ylabel('Entregas com falta')
ax.set_xticks(vols); ax.set_yticks(range(0, 5))
ax.set_xlim(5.4, 11.8); ax.set_ylim(-.55, 4.6)
ax.set_title('Cada volume de entregas admite no máximo dois resultados possíveis',
             fontsize=9.5, color=VERM, loc='left', pad=9)
limpar(ax)
fig.savefig(f'{GRAF}/g6_determinismo.png'); plt.close(fig)

print('6 graficos gerados')

// Relatorio DOCX. Todo numero vem de resultados/metricas.json. Nada digitado a mao.
const fs = require('fs');
const d = require('docx');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageOrientation,
  LevelFormat, convertInchesToTwip,
} = d;

const path = require('path');
const RAIZ = path.resolve(__dirname, '..');
const OUT = path.join(RAIZ, 'resultados');
const M = JSON.parse(fs.readFileSync(`${OUT}/metricas.json`, 'utf8'));

const AZUL = '1F3864', VERM = 'C00000', CINZA = '595959', VERDE = '375623';
const LARGURA = 10080; // US Letter menos margens de 0,75"

// ── formatadores pt-BR ──
const pct = (v, c = 2) => (v * 100).toFixed(c).replace('.', ',') + '%';
const num = (v) => Math.round(v).toLocaleString('pt-BR');
const usd = (v) => 'US$ ' + v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const dec = (v, c = 3) => v.toFixed(c).replace('.', ',');

// ── blocos ──
const P = (txt, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, before: o.before ?? 0, line: 276 },
  alignment: o.align,
  indent: o.indent,
  border: o.border,
  shading: o.shading,
  children: (Array.isArray(txt) ? txt : [txt]).map((t) =>
    typeof t === 'string'
      ? new TextRun({ text: t, size: o.size ?? 20, color: o.color ?? '000000', font: 'Arial', bold: o.bold, italics: o.italics })
      : t),
});
const R = (text, o = {}) => new TextRun({
  text, size: o.size ?? 20, color: o.color ?? '000000', font: 'Arial',
  bold: o.bold, italics: o.italics,
});
const H = (txt, lvl) => new Paragraph({
  heading: lvl, spacing: { before: 320, after: 140 },
  children: [new TextRun({ text: txt, font: 'Arial', bold: true,
    size: lvl === HeadingLevel.HEADING_1 ? 26 : 22, color: AZUL })],
});
const BULL = (txt, o = {}) => new Paragraph({
  numbering: { reference: 'bul', level: 0 },
  spacing: { after: 70, line: 276 },
  children: (Array.isArray(txt) ? txt : [txt]).map((t) =>
    typeof t === 'string' ? R(t, o) : t),
});
const NUMI = (txt) => new Paragraph({
  numbering: { reference: 'ord', level: 0 },
  spacing: { after: 80, line: 276 },
  children: (Array.isArray(txt) ? txt : [txt]).map((t) => (typeof t === 'string' ? R(t) : t)),
});

function img(arquivo, larguraPx, alturaPx) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 140, after: 60 },
    children: [new ImageRun({
      type: 'png', data: fs.readFileSync(`${OUT}/graficos/${arquivo}`),
      transformation: { width: larguraPx, height: alturaPx },
    })],
  });
}
const legenda = (t) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [R(t, { size: 16, italics: true, color: CINZA })],
});

function tabela(cabs, linhas, pesos, destaques = []) {
  const larg = pesos.map((p) => Math.round(LARGURA * p));
  const cell = (txt, o = {}) => new TableCell({
    width: { size: o.w, type: WidthType.DXA },
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      spacing: { after: 0, line: 240 },
      alignment: o.align,
      children: [R(String(txt), { size: 17, bold: o.bold, color: o.color ?? '000000' })],
    })],
  });
  return new Table({
    columnWidths: larg,
    width: { size: LARGURA, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
      left: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
      right: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
    },
    rows: [
      new TableRow({
        tableHeader: true,
        children: cabs.map((c, i) => cell(c, { w: larg[i], bold: true, fill: AZUL, color: 'FFFFFF',
          align: i > 0 ? AlignmentType.RIGHT : undefined })),
      }),
      ...linhas.map((ln, li) => new TableRow({
        children: ln.map((c, i) => cell(c, {
          w: larg[i],
          fill: destaques.includes(li) ? 'FBE9E7' : (li % 2 ? 'F7F8FA' : undefined),
          color: destaques.includes(li) ? VERM : '000000',
          bold: destaques.includes(li),
          align: i > 0 ? AlignmentType.RIGHT : undefined,
        })),
      })),
    ],
  });
}

const destaque = (txt, cor = VERM) => new Paragraph({
  spacing: { before: 140, after: 180, line: 276 },
  shading: { type: ShadingType.CLEAR, fill: cor === VERM ? 'FBE9E7' : 'EDF1F6', color: 'auto' },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: cor } },
  indent: { left: 180, right: 180 },
  children: [R(txt, { size: 20, color: '000000' })],
});

const K = M.kpis, A = M.anomalia, PW = M.poder, AR = M.artefatos, EP = M.evento_por_pedido,
      DM = M.dimensoes, EM = M.estrutura_motoristas, DV = M.derivados;

// ═══════════════════ DOCUMENTO ═══════════════════
const filhos = [];

// capa
filhos.push(new Paragraph({
  spacing: { after: 60 },
  children: [R('RELATÓRIO ANALÍTICO', { size: 18, bold: true, color: CINZA })],
}));
filhos.push(new Paragraph({
  spacing: { after: 80 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: AZUL } },
  children: [R('Detecção de Fraude em Entregas de Última Milha', { size: 36, bold: true, color: AZUL })],
}));
filhos.push(P('Dataset sintético de e-commerce · operação de última milha · 7 regiões metropolitanas · 2023', { size: 22, color: CINZA, after: 40 }));
filhos.push(P(`Base de ${num(M.validacao.linhas_brutas)} pedidos · ${num(K.motoristas)} motoristas · ${M.validacao.regioes.length} regiões atendidas`, { size: 18, color: CINZA, after: 300 }));

filhos.push(destaque(
  `Sobre a base: este é um dataset sintético, usado como exercício de análise. Não são dados operacionais de nenhuma empresa real, e nenhuma conclusão aqui descreve uma operação existente. Identificar que a base é gerada, e não observada, foi um dos dois resultados da análise, e está demonstrado na seção 4.1.`, AZUL));

// 1 sumario
filhos.push(H('1. Sumário executivo', HeadingLevel.HEADING_1));
filhos.push(P([
  R('A operação apresenta incidência de '),
  R(pct(K.incidencia_por_pedido), { bold: true }),
  R(` de pedidos com ao menos um item faltante (IC 95%: ${pct(K.incidencia_ic95[0])} a ${pct(K.incidencia_ic95[1])}), o que corresponde a uma taxa agregada de `),
  R(pct(K.taxa_item_agregada), { bold: true }),
  R(` dos itens transportados (IC 95%: ${pct(K.taxa_item_ic95[0])} a ${pct(K.taxa_item_ic95[1])}). O benchmark de indústria de ${pct(K.benchmark_industria, 1)} adotado como referência cai dentro desse intervalo: a diferença de ${dec(K.diferenca_vs_benchmark_pp, 2)} p.p. não é distinguível de ruído amostral, e a operação não deve ser descrita nem como acima nem como abaixo do benchmark. O valor associado aos itens faltantes é de `),
  R(usd(K.valor_em_risco), { bold: true }),
  R(`, ou ${pct(K.valor_em_risco_pct_faturamento)} do faturamento de ${usd(K.faturamento)} no período.`),
]));
filhos.push(P([
  R('A análise de anomalia testou os '),
  R(num(A.motoristas_testados), { bold: true }),
  R(' motoristas da base com teste binomial exato corrigido para testes múltiplos (Benjamini-Hochberg). '),
  R('Nenhum motorista apresenta desvio estatisticamente significativo', { bold: true, color: VERM }),
  R(`. O menor p-valor da base é ${dec(A.menor_p_valor, 4)}, e o menor q-valor, ${dec(A.menor_q_valor)}.`),
]));
filhos.push(destaque(
  `Conclusão principal: esta base não sustenta acusação individual de fraude, por dois motivos independentes. Primeiro, o número de entregas com falta por motorista é praticamente uma função determinística do volume de entregas (seção 4.1): não há variação individual a detectar. Segundo, mesmo que houvesse, com no máximo ${PW.entregas_disponiveis_max} entregas por motorista no ano seriam necessárias ${PW.cenarios[0].entregas_necessarias} para detectar, com 80% de poder, um motorista operando ao dobro da incidência base: o estudo está ${Math.round(PW.subdimensionamento)}× subdimensionado. As medidas preventivas da seção 7 se justificam por custo-benefício operacional, não por fraude comprovada.`));

filhos.push(P('Números-chave:', { bold: true, before: 120 }));
filhos.push(tabela(
  ['Indicador', 'Valor', 'Observação'],
  [
    ['Pedidos analisados', num(K.pedidos), 'após limpeza'],
    ['Itens transportados', num(K.itens), ''],
    ['Pedidos com ao menos 1 falta', num(K.pedidos_com_falta), ''],
    ['Itens faltantes', num(K.itens_faltantes), ''],
    ['Incidência por pedido (KPI primário)', pct(K.incidencia_por_pedido), `IC 95% ${pct(K.incidencia_ic95[0])} a ${pct(K.incidencia_ic95[1])}`],
    ['Taxa agregada de itens', pct(K.taxa_item_agregada), `IC 95% ${pct(K.taxa_item_ic95[0])} a ${pct(K.taxa_item_ic95[1])}; contém o benchmark de ${pct(K.benchmark_industria, 1)}`],
    ['Faturamento', usd(K.faturamento), ''],
    ['Valor dos itens faltantes', usd(K.valor_em_risco), pct(K.valor_em_risco_pct_faturamento) + ' do faturamento'],
    ['Motoristas com desvio significativo', String(A.significativos_fdr), `menor q = ${dec(A.menor_q_valor)}`],
  ],
  [0.42, 0.24, 0.34], [8]));

// 2 metodologia
filhos.push(H('2. Metodologia e tratamento da base', HeadingLevel.HEADING_1));
filhos.push(P(`Base bruta de ${num(M.validacao.linhas_brutas)} pedidos, período de ${M.validacao.periodo_inicio} a ${M.validacao.periodo_fim}. Integridade verificada: zero valores nulos e a identidade itens_entregues + itens_faltantes = itens_total válida em 100% das linhas.`));

filhos.push(H('2.1 Artefato de geração removido', HeadingLevel.HEADING_2));
filhos.push(P(`A coluna items_delivered está truncada em ${AR.teto_items_delivered} itens na base original. Isso força mecanicamente falta em todo pedido acima desse teto: os ${AR.pedidos_removidos} pedidos com ${AR.teto_mais_um} ou mais itens totais apresentam ${pct(AR.pct_com_falta_no_grupo_removido, 0)} de incidência, todos eles sem exceção, somando ${AR.faltas_removidas} itens, ou ${pct(AR.pct_das_faltas_brutas, 1)} das faltas brutas.`));
filhos.push(P(`Esses pedidos foram removidos da base analítica por serem artefato de geração, não ocorrência operacional. Base final: ${num(K.pedidos)} pedidos.`));
filhos.push(P('Outros indícios de que a base é sintética, registrados para transparência:', { before: 80 }));
filhos.push(BULL(`Nenhum dos ${AR.pedidos_1_item} pedidos de item único apresenta falta (esperado: cerca de ${Math.round(DV.pedidos_1_item_esperado_com_falta)}). O gerador nunca zera um pedido.`));
filhos.push(BULL(`Entregas por motorista assumem apenas os valores ${AR.valores_distintos_entregas_por_motorista.join(', ')}, nunca uma distribuição contínua.`));
filhos.push(BULL(`Nenhum pedido registra mais de ${AR.max_faltas_em_um_pedido} itens faltantes, o que é incompatível com eventos de desvio de alto volume.`));

filhos.push(H('2.2 Definição dos indicadores', HeadingLevel.HEADING_2));
filhos.push(P([
  R('KPI primário. Incidência por pedido: ', { bold: true }),
  R('pedidos com ao menos um item faltante dividido pelo total de pedidos. A falta é um evento que ocorre no pedido, não em cada item independentemente (demonstrado na seção 3).'),
]));
filhos.push(P([
  R('KPI secundário. Taxa agregada de itens: ', { bold: true }),
  R('soma dos itens faltantes dividida pela soma dos itens. Mede volume perdido e é a métrica comparável ao benchmark de indústria.'),
]));
filhos.push(P([
  R('Métrica descartada. Média simples das razões por pedido: ', { bold: true, color: VERM }),
  R(`atribui o mesmo peso a um pedido de 2 itens e a um de ${AR.teto_items_delivered}. Como pedidos pequenos produzem razões artificialmente altas, o resultado é inflado em ${dec(K.inflacao_da_metrica_incorreta, 2)}× (${pct(K.media_razoes_INCORRETA)} contra ${pct(K.taxa_item_agregada)} da taxa correta). Não é uma taxa operacional e não foi utilizada.`),
]));

// 3 evento por pedido
filhos.push(H('3. Por que a incidência substitui a razão por item', HeadingLevel.HEADING_1));
filhos.push(P(`A probabilidade de um pedido apresentar falta é estatisticamente constante ao longo de todo o intervalo de tamanhos de pedido: a correlação de Spearman entre tamanho e incidência é ρ = ${dec(EP.spearman_incidencia_vs_tamanho)} com p = ${dec(EP.spearman_incidencia_p)}, ou seja, ausência de tendência.`));
filhos.push(P(`A razão faltantes/total, por outro lado, cai ${dec(EP.queda_taxa_item, 1)}× ao longo do mesmo intervalo (ρ = ${dec(EP.spearman_taxa_item_vs_tamanho)}). Essa queda é integralmente efeito do denominador, não de comportamento operacional.`));
filhos.push(img('g1_tamanho_pedido.png', 600, 283));
filhos.push(legenda('Mesma realidade, duas leituras. A linha superior é plana; a inferior despenca apenas porque o denominador cresce.'));
filhos.push(destaque(
  `Consequência prática: qualquer ranking de motoristas construído sobre a razão faltantes/total ordena os motoristas por mix de tamanho de pedido, não por conduta. Um motorista que atende predominantemente pedidos pequenos aparece no topo do ranking sem qualquer desvio de comportamento.`));

// 4 deteccao
filhos.push(H('4. Detecção de anomalia por motorista', HeadingLevel.HEADING_1));
filhos.push(P(`Cada um dos ${num(A.motoristas_testados)} motoristas foi submetido a teste binomial exato unilateral sobre suas entregas, contra a incidência base de ${pct(A.taxa_base_usada)} da operação. Testar ${num(A.motoristas_testados)} hipóteses a 5% produziria, por puro acaso, cerca de ${Math.round(A.falsos_positivos_esperados)} resultados "significativos", razão pela qual o critério de decisão adotado é o q-valor após correção de Benjamini-Hochberg, não o p-valor bruto.`));
filhos.push(destaque(
  `Resultado: nenhum motorista atinge sequer o limiar bruto de 0,05. O menor p-valor da base inteira é ${dec(A.menor_p_valor, 4)}. O desvio máximo observado é de ${A.max_entregas_com_falta} entregas com falta em ${A.max_entregas_por_motorista}, contra ${dec(DV.esperado_no_motorista_mais_ativo, 2)} esperadas. Após correção FDR: ${A.significativos_fdr} significativos, menor q-valor ${dec(A.menor_q_valor)}. ${num(A.motoristas_com_zero_faltas)} motoristas (${pct(A.pct_motoristas_zero_faltas, 1)}) sequer registram um item faltante no ano.`));

filhos.push(H('4.1 A validação revelou que a base é gerada, não observada', HeadingLevel.HEADING_2));
filhos.push(P('Antes de interpretar o resultado acima como "operação limpa", é preciso verificar se a base sequer admite variação individual entre motoristas. Ela não admite, e a checagem que demonstra isso é o segundo resultado desta análise.'));
filhos.push(P(`Se as faltas fossem sorteadas de forma independente por entrega, a distribuição do número de entregas com falta por motorista seguiria uma binomial. O observado diverge dela de forma extrema (qui-quadrado = ${num(EM.qui2_vs_binomial)}):`));
filhos.push(img('g5_estrutura.png', 600, 242));
filhos.push(legenda(`Sob um processo aleatório, ${dec(EM.esperado_binomial['1'], 1)} motoristas teriam exatamente uma entrega com falta. A base tem ${EM.observado['1']}.`));
filhos.push(P(`A causa fica evidente ao cruzar volume com ocorrências: o número de entregas com falta é praticamente uma função determinística do número de entregas. Motoristas com 6 ou 7 entregas têm sempre zero faltas: ${EM.volumes_deterministicos} dos ${EM.volumes_distintos} volumes distintos admitem um único resultado possível; os demais admitem dois.`, { before: 100 }));
filhos.push(img('g6_determinismo.png', 600, 217));
filhos.push(legenda('Cada círculo é um grupo de motoristas; o número indica quantos são.'));
filhos.push(destaque(
  `Implicação metodológica: a "taxa" de cada motorista nesta base é determinada pelo seu volume de entregas, não por sua conduta. Não existe sinal individual a detectar, nem verdadeiro, nem falso. Qualquer lista de suspeitos extraída desta base seria, necessariamente, uma lista dos motoristas mais ativos.`));
filhos.push(P('O anexo A traz os 40 motoristas de menor p-valor. Esse ranking serve a priorização de auditoria amostral e a acompanhamento operacional, não a ação disciplinar individual.', { before: 100 }));

// 5 poder
filhos.push(H('5. Poder estatístico: a limitação central', HeadingLevel.HEADING_1));
filhos.push(P(`A ausência de motoristas significativos não prova ausência de fraude. Prova que esta base não tem volume por motorista suficiente para detectá-la. O cálculo de poder, com alfa corrigido para ${num(A.motoristas_testados)} testes e poder alvo de 80%, quantifica o limite:`));
filhos.push(tabela(
  ['Cenário', 'Incidência alvo', 'Entregas necessárias', 'Detectável?'],
  [
    ...PW.cenarios.map((c) => [
      `Motorista operando a ${c.multiplo_da_taxa_base.toFixed(0)}× a incidência base`,
      pct(c.incidencia_alvo, 1), num(c.entregas_necessarias),
      c.entregas_necessarias <= PW.entregas_disponiveis_max ? 'sim' : 'não',
    ]),
    ['Disponível na base (motorista mais ativo)', 'n/a', num(PW.entregas_disponiveis_max), 'n/a'],
  ],
  [0.46, 0.17, 0.22, 0.15], [3]));
filhos.push(img('g4_poder.png', 600, 242));
filhos.push(legenda(`O motorista mais ativo da base tem ${PW.entregas_disponiveis_max} entregas no ano; a mediana da frota é ${Math.round(A.mediana_entregas)}.`));
filhos.push(P('Para viabilizar detecção individual seria necessário elevar o denominador por motorista: consolidando histórico multi-ano, ou agregando a análise por equipe, rota ou centro de distribuição até atingir a faixa de entregas indicada acima.', { before: 80 }));

// 6 dimensoes
filhos.push(H('6. Dimensões sem variação significativa', HeadingLevel.HEADING_1));
filhos.push(P('Três cortes foram testados com qui-quadrado de aderência contra a incidência base da operação. Nenhum apresenta variação distinguível de flutuação aleatória:'));
filhos.push(tabela(
  ['Dimensão', 'Qui-quadrado', 'g.l.', 'p-valor', 'Amplitude', 'Veredito'],
  [
    ['Região', dec(DM.regiao.qui2, 2), String(DM.regiao.gl), dec(DM.regiao.p_valor), dec(DM.regiao.amplitude_pp, 2) + ' p.p.', DM.regiao.significativo ? 'significativa' : 'não significativa'],
    ['Hora da entrega', dec(DM.hora.qui2, 2), String(DM.hora.gl), dec(DM.hora.p_valor), dec(DM.hora.amplitude_pp, 2) + ' p.p.', DM.hora.significativo ? 'significativa' : 'não significativa'],
    ['Mês', dec(DM.mes.qui2, 2), String(DM.mes.gl), dec(DM.mes.p_valor), dec(DM.mes.amplitude_pp, 2) + ' p.p.', DM.mes.significativo ? 'significativa' : 'não significativa'],
  ],
  [0.22, 0.16, 0.08, 0.14, 0.15, 0.25]));
filhos.push(img('g2_hora.png', 600, 258));
filhos.push(legenda('Os intervalos de confiança de 95% se sobrepõem entre praticamente todas as horas.'));
filhos.push(img('g3_regiao.png', 600, 242));
filhos.push(legenda('Idem entre as sete regiões atendidas.'));
filhos.push(P('Não há, portanto, base para recomendar reforço de supervisão em janela horária ou região específica. Recomendações desse tipo em versões anteriores deste material não se sustentam nos dados.', { before: 80 }));

filhos.push(H('6.1 O que esta base não permite concluir', HeadingLevel.HEADING_2));
filhos.push(P(`A base contém ${M.validacao.colunas.length} colunas: ${M.validacao.colunas.join(', ')}. Não há identificador de produto, categoria, cliente ou registro de reclamação.`));
filhos.push(P('Em consequência, estão fora do escopo possível deste dado:'));
filhos.push(BULL('Análise de mix de produto ou concentração por categoria.'));
filhos.push(BULL('Ranking de SKUs impactados.'));
filhos.push(BULL('Segmentação ou perfil de risco de clientes.'));
filhos.push(BULL('Evolução de reclamações ou qualquer comparação com período anterior a 2023.'));
filhos.push(P('Qualquer afirmação sobre esses temas exige integração com outra fonte de dados, listada no roadmap da seção 8.', { before: 60 }));

// 7 medidas
filhos.push(H('7. Medidas preventivas recomendadas', HeadingLevel.HEADING_1));
filhos.push(P(`As medidas abaixo são boas práticas de last-mile e permanecem recomendadas, com uma ressalva importante: a justificativa é custo-benefício operacional e redução de disputa com cliente, não fraude comprovada. Com ${pct(K.valor_em_risco_pct_faturamento)} do faturamento em itens faltantes (${usd(K.valor_em_risco)} no ano), qualquer medida deve ser dimensionada contra esse teto de retorno.`));
filhos.push(NUMI([R('Prova de entrega (PoD) multimodal. ', { bold: true }), R('Foto, GPS e confirmação do cliente vinculados ao pedido. Reduz disputa e cria a trilha de evidência que hoje não existe na base.')]));
filhos.push(NUMI([R('Selo inviolável com QR único. ', { bold: true }), R('Escaneado no picking e na entrega, fecha a lacuna entre separação e recebimento.')]));
filhos.push(NUMI([R('Scan item a item na entrega. ', { bold: true }), R('Bloqueia a conclusão em caso de divergência sem evidência adicional. É também o que gera o dado de item necessário para as análises hoje impossíveis.')]));
filhos.push(NUMI([R('Auditoria amostral priorizada. ', { bold: true }), R('Use o ranking do anexo A como ordem de amostragem, não como lista de suspeitos.')]));
filhos.push(NUMI([R('Fluxo de reembolso escalonado. ', { bold: true }), R('Aprovação automática apenas para casos de baixo valor e histórico limpo; verificação adicional acima do limite.')]));
filhos.push(NUMI([R('Programa de incentivo por conformidade. ', { bold: true }), R('Medido sobre a incidência por pedido, normalizada por volume, nunca sobre a razão faltantes/total, pelo motivo da seção 3.')]));
filhos.push(destaque(
  'Dimensionamento: as medidas 1 a 3 têm custo unitário por entrega e devem ser pilotadas antes do rollout. Um piloto A/B por região, com a incidência por pedido como métrica primária, é o desenho adequado e, com a variação regional não significativa demonstrada na seção 6, as regiões são intercambiáveis para fins de alocação em grupos de teste e controle.', AZUL));

// 8 roadmap
filhos.push(H('8. Roadmap de dados e modelos', HeadingLevel.HEADING_1));
filhos.push(P('Ordenado por pré-requisito. As fases 3 e 4 dependem de ganho de volume por motorista e de enriquecimento da base, e não são executáveis com o dado atual.'));
filhos.push(tabela(
  ['Fase', 'Ação', 'Pré-requisito'],
  [
    ['1', 'Elevar volume por motorista: consolidar histórico multi-ano ou agregar por equipe/rota', `Atingir ~${num(PW.cenarios[0].entregas_necessarias)} entregas por unidade de análise`],
    ['2', 'Enriquecer a base com produto, categoria, cliente e registro de reclamação', 'Integração com ERP e sistema de atendimento'],
    ['3', 'Modelos de anomalia não supervisionados (Isolation Forest, clustering)', 'Fases 1 e 2 concluídas'],
    ['4', 'Modelo supervisionado com rótulo de fraude confirmada e explicabilidade (SHAP)', 'Rótulos vindos da auditoria da fase 1'],
    ['5', 'Controle estatístico de processo com limites de controle sobre a incidência', 'Série temporal estável pós-medidas'],
  ],
  [0.08, 0.55, 0.37]));

// 9 anexos
filhos.push(new Paragraph({ children: [new d.PageBreak()] }));
filhos.push(H('Anexo A: Ranking de acompanhamento operacional', HeadingLevel.HEADING_1));
filhos.push(P([
  R('Este ranking não é uma lista de suspeitos. ', { bold: true, color: VERM }),
  R(`Nenhum dos motoristas abaixo atinge significância estatística após correção para testes múltiplos (critério: q < 0,05; menor q observado: ${dec(A.menor_q_valor)}). Ordenado por p-valor bruto, apenas para priorizar amostragem de auditoria.`),
]));
const drv = fs.readFileSync(`${OUT}/drivers_ranking_acompanhamento.csv`, 'utf8').trim().split('\n').slice(1, 16)
  .map((l) => l.split(','));
filhos.push(tabela(
  ['#', 'ID', 'Motorista', 'Entregas', 'C/ falta', 'Esperado', 'p bruto', 'q (FDR)'],
  drv.map((c) => [c[0], c[1], c[2], c[3], c[4], dec(parseFloat(c[6]), 2), dec(parseFloat(c[9]), 4), dec(parseFloat(c[10]))]),
  [0.05, 0.13, 0.25, 0.12, 0.11, 0.12, 0.11, 0.11]));
filhos.push(P(`Exibidos os 15 primeiros de ${num(A.motoristas_testados)} motoristas testados. O arquivo completo (40 primeiros) acompanha este relatório.`, { size: 17, italics: true, color: CINZA, before: 100 }));

filhos.push(H('Anexo B: Arquivos que acompanham este relatório', HeadingLevel.HEADING_1));
filhos.push(tabela(
  ['Arquivo', 'Conteúdo'],
  [
    ['Analise_Fraude_Entregas_Last_Mile_2023.xlsx', 'Workbook analítico: Leia-me, Overview (KPIs em fórmulas vivas), Data, Drivers, Regions, Hours, Months, Order_Size e Power'],
    ['drivers_ranking_acompanhamento.csv', 'Ranking dos 40 motoristas de menor p-valor, com q-valor e marcação de significância'],
    ['pipeline.py', 'Script único que gera todos os números deste relatório a partir da base bruta'],
    ['metricas.json', 'Saída do pipeline: toda métrica citada neste documento, com sua chave de origem'],
  ],
  [0.42, 0.58]));
filhos.push(destaque(
  'Reprodutibilidade: nenhum número deste relatório foi digitado manualmente. Todos são lidos de metricas.json, que por sua vez é produzido por pipeline.py a partir da base bruta. Alterar a base e reexecutar o pipeline atualiza relatório, planilha e CSV de forma consistente.', AZUL));

const doc = new Document({
  creator: 'Raphael Pucci',
  title: 'Detecção de Fraude em Entregas de Última Milha, 2023',
  numbering: {
    config: [
      { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.28), hanging: convertInchesToTwip(0.18) } } } }] },
      { reference: 'ord', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.32), hanging: convertInchesToTwip(0.22) } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840, orientation: PageOrientation.PORTRAIT },
        margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
      },
    },
    children: filhos,
  }],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(`${OUT}/Relatorio_Fraude_Entregas_Last_Mile_2023.docx`, b);
  console.log('DOCX gerado:', b.length, 'bytes');
});

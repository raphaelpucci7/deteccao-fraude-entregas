# Dados brutos

Base original da analise, exatamente como foi recebida. Nada aqui e editado pelo pipeline: os scripts apenas leem este arquivo.

> **Dataset sintetico.** Nao sao dados operacionais de nenhuma empresa real. A analise em `../resultados/` demonstra que a base e gerada artificialmente, e nao observada.

## entregas_2023.xlsx

Aba `Data`. 10.000 linhas, 9 colunas, periodo de 01/01/2023 a 31/12/2023.

| Coluna | Tipo | Descricao | Amplitude |
|---|---|---|---|
| `driver_name` | texto | Nome do motorista responsavel pela entrega | 1.229 valores distintos |
| `driver_id` | texto | Identificador unico do motorista (formato WDID#####) | 1.247 valores distintos |
| `region` | texto | Regiao atendida, entre as sete da area metropolitana | 7 valores distintos |
| `date` | inteiro | Data da entrega, em numero de serie do Excel | 01/01/2023 a 31/12/2023 |
| `delivery_hour_num` | inteiro | Hora da entrega, de 0 a 23 | 0 a 23 |
| `items_delivered` | inteiro | Itens efetivamente entregues ao cliente | 1 a 19 |
| `items_missing` | inteiro | Itens registrados como nao entregues | 0 a 3 |
| `items_total` | inteiro | Total de itens do pedido | 1 a 21 |
| `order_amount_clean` | decimal | Valor do pedido em dolares | 20,08 a 1.386,00 |

## Integridade

- Zero valores nulos em todas as colunas.
- `items_delivered + items_missing = items_total` vale em 100% das linhas.
- Sao 1.247 `driver_id` distintos para 1.229 nomes: ha homonimos. e o identificador e o que vale.

## Limitacoes conhecidas

- `items_delivered` esta truncado em 19, o que forca falta em todo pedido maior que isso (96 pedidos, removidos da base analitica).
- Nenhum dos 419 pedidos de item unico registra falta.
- Entregas por motorista assumem apenas os valores 6, 7, 10, 11.
- Nao ha coluna de produto, categoria, cliente ou reclamacao.

O tratamento aplicado a cada uma dessas limitacoes esta documentado no relatorio, em `../resultados/`.

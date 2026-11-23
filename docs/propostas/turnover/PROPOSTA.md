# Proposta: tela de Turnover

Aberta em 22-23/11/2026. Pedido recorrente do Gabriel (tester): "não tem um relatório de
turnover decente no Sharpen". Hoje o turnover aparece em várias telas, mas só como coluna
ou KPI solto. Nenhuma tela tem o turnover como eixo.

Protótipo: [`turnover_v3.html`](turnover_v3.html). Abra pelo navegador com o repositório
local: ele carrega o CSS e o Chart.js reais do dash por caminho relativo. Os dados são
fictícios.

## O que a tela tem (v3)

- Filtros: Período (os mesmos botões do dash), Comparar com (mês anterior nos mesmos dias,
  média de 3 meses, ano anterior), Data (da aposta / do evento).
- KPIs: Turnover (com variação contra o mesmo trecho), Média por Dia, Projeção do Mês,
  Apostas, Stake Média, ROI.
- Turnover Diário: barras do dia, acumulado do mês contra o mês anterior, projeção
  tracejada. Botão Turnover / Apostas.
- Turnover por Dia da Semana: MÉDIA por ocorrência do dia, contra o período de comparação.
- Turnover por Casa / Tipster / Conta / Esporte / Fornecedor: tabela que funciona como
  legenda de um gráfico de linhas (marque até 4). Botão Valor / % do total.
  Em Casa e Conta: Saldo hoje, Saldo sugerido, Acima do sugerido.
- Turnover e ROI por Mês.

## Decisões do Feca (23/11/2026)

1. A tela usa **ROI**, não "lucro por R$ 1.000" (é o mesmo número, e o app inteiro fala ROI).
2. Projeção do mês: **já apostado + média dos últimos 7 dias × dias que faltam**.
3. O nome é **Saldo sugerido** (e "Acima do sugerido").

Escolhas do protótipo, ainda sem confirmação:
- Dia da semana é média por ocorrência, com dia sem aposta contando como zero.
- Saldo hoje sai com 2 casas (`fmtSaldo`). Saldo sugerido e Acima do sugerido saem
  inteiros (`fmtR`).

## Em aberto

- **Qual data conta: a da aposta ou a do evento.** `bilhetes.data` é a data do EVENTO e
  `calcTurnover` só soma aposta liquidada. A data da aposta só existe exata na Bet365
  (`aposta_em`, sem conversão de fuso). Nas outras casas, a referência possível é o
  `criado_em`, que só vale para casa capturada pelo robô.
- **Prazo das apostas (ideia do Feca).** Separar as apostas em: mesmo dia, dia seguinte,
  2 dias, 3 dias ou mais. Isso define o Saldo sugerido: dinheiro médio em aberto ≈
  turnover por dia × dias que a aposta fica presa. O evento só tem DIA (sem hora) e não
  existe carimbo de liquidação, por isso as faixas são em dias, não em horas.

## Próximo passo

Medição **só de leitura** na base do Gabriel, por casa:
1. distribuição das apostas nas 4 faixas de prazo (quantidade e turnover);
2. na Bet365, diferença entre `aposta_em` e `criado_em` (o quanto o `criado_em` atrasa);
3. quanto do histórico vem de captura e quanto de print ou import.

Falta o Feca passar o **username** do Gabriel e dar o ok para consultar produção.

# 02 · Casas em uso em outubro (Feca e Gabriel)

> Medido no banco de produção, só leitura, em 11/10/2026, janela 01/10 a 11/10.
> Consultas no fim do arquivo. Bet365 aparece na tabela mas **está fora do projeto por enquanto**
> (decisão do Feca).

## 1. A tabela

| # | Casa | Família | Apostas criadas (Feca / Gabriel) | Extrações | Custo IA (US$) | Leituras por aposta | Fixture na bancada |
|---|---|---|---|---|---|---|---|
| 1 | **DEX Sport** | `dx_inject` | 246 (108 / 138) | 40 | **30,11** | **6,44** | `dexsport.tickets.json` |
| 2 | **Megapari** | `x1_inject` (1xBet) | 243 (39 / 204) | 33 | 18,54 | 1,92 | `megapari.bethistory.json` |
| 3 | **MyStake** | `tv_inject` (BetConstruct) | 206 (136 / 70) | 19 | 6,95 | 1,42 | `mystake.gethistory.json` |
| 4 | **Shuffle** | `shf_inject` | 78 (67 / 11) | 10 | 6,27 | **4,45** | `shuffle.sportsbets.json` |
| 5 | **Betrebels** | `vb_inject` (Altenar) | 75 (44 / 31) | 14 | 5,42 | 2,15 | família: `vaidebet`, `esportiva`, `estrelabet`... |
| 6 | **Duel** | `jb_inject` (BetBy) | 126 (54 / 72) | 21 | 5,29 | 1,78 | família: `jonbet`, `blaze`, `betpanda`... |
| 7 | **Betpanda** | `jb_inject` (BetBy) | 160 (160 / 0) | 10 | 4,13 | 1,49 | `betpanda.my_bets.json` |
| 8 | **BetMartini** | `vb_inject` (Altenar) | 84 (84 / 0) | 6 | 3,18 | 1,52 | família Altenar |
| 9 | **Betfury** | `jb_inject` (BetBy) | 46 (0 / 46) | 15 | 2,41 | 1,87 | família BetBy |
| 10 | **Vavada** | `vb_inject` (Altenar) | 39 (39 / 0) | 3 | 1,39 | 1,41 | família Altenar |
| 11 | **Betcoin** | `jb_inject` (BetBy) | 20 (0 / 20) | 9 | 1,23 | 2,00 | família BetBy |
| 12 | **PariPesa** | `x1_inject` (1xBet) | 37 (37 / 0) | 2 | 1,10 | 1,03 | `paripesa.bethistory.json` |
| 13 | **SapphireBet** | `x1_inject` (1xBet) | 36 (36 / 0) | 2 | 1,05 | 1,14 | `sapphirebet.bethistory.json` |
| 14 | **1xBit** | `x1_inject` (1xBet) | 8 (8 / 0) | 1 | 0,41 | 1,00 | `1xbit.bethistory.json` |
| 15 | **Kikobet** | `vb_inject` (Altenar) | 0 | 1 | 0,03 | — | família Altenar |
| — | Polymarket | sync | 53 (53 / 0) | 0 | 0 | — | **já é determinística** (`app/polymarket.py`) |
| — | Bet365 | `b3_inject` | 118 (0 / 118) | 15 | 6,93 | 2,33 | **fora por decisão do Feca** |

**Total das 15 casas do projeto:** cerca de US$ 87,5 em 11 dias, cerca de **US$ 240/mês** no ritmo atual,
só para Feca e Gabriel.

## 2. A ordem e por quê

Seis famílias cobrem as 15 casas. Um adaptador por família, não um por casa.

| Ordem | Família | Casas | Por quê primeiro |
|---|---|---|---|
| 1 | DEX Sport | 1 | maior custo (32%), maior releitura (6,44), casa nova sem legado, fixture pronta |
| 2 | 1xBet | 4 | 2º maior custo; um adaptador leva 4 casas; mercado misturado é o teste mais duro do dicionário |
| 3 | BetConstruct | MyStake | 3º custo; formato limpo (mercado em campo próprio) |
| 4 | BetBy | 4 | volume alto somado (352 apostas); moeda já tratada |
| 5 | Altenar | 4 | precisa resolver moeda ausente (Betrebels em USDT) |
| 6 | Shuffle | 1 | custo menor; correção do porteiro já em curso em outra frente |

## 3. Consultas usadas

```sql
-- custo e extrações por casa
SELECT casa, count(*) extracoes, sum(chunks) pedacos, round(sum(custo_usd)::numeric,2) usd,
       string_agg(DISTINCT dono, ',') donos, max(criado_em)::date ultima
FROM uso_tokens WHERE criado_em >= '2026-10-01' AND dono IN ('Feca','Gabriel')
GROUP BY 1 ORDER BY 4 DESC;

-- apostas criadas por casa e origem
SELECT casa, count(*), count(*) FILTER (WHERE dono='Feca'), count(*) FILTER (WHERE dono='Gabriel'),
       count(*) FILTER (WHERE origem='extracao'), count(*) FILTER (WHERE origem='sync')
FROM bilhetes WHERE criado_em >= '2026-10-01' AND dono IN ('Feca','Gabriel')
GROUP BY 1 ORDER BY 2 DESC;

-- leituras pagas por aposta
SELECT casa, count(*) leituras, count(DISTINCT codigo) bilhetes,
       round(count(*)::numeric/nullif(count(DISTINCT codigo),0),2)
FROM sombra_rotulos WHERE criado_em >= '2026-10-01' AND dono IN ('Feca','Gabriel')
GROUP BY 1 ORDER BY 2 DESC;
```

Família por casa: frente F6 do mapa (`Auditorias\mapa_2026-10\claude\frentes\F6\F6.md`). Fixtures:
`extensor/harness/fixtures/`.

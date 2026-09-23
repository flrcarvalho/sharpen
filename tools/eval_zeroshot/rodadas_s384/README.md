# Rodadas da s384 — a evidência por trás da tabela do `../README.md`

18 rodadas de 2026-09-23, gabarito `../pares_v2.json` (282 pares, 33 casas com mercado confirmado, 35 categorias).

- `preds_<modelo>_n<1..5>.tsv` · `RESULTADO_<modelo>_n<1..5>.txt` — N=5 por modelo,
  **`thinking` desligado**, sem `temperature`.
- `preds_ctrl_temp0_n<1..3>.tsv` — o controle: Sonnet 4.6 com `temperature=0`.
- `rodadas.json` — o consolidado (acertos, silenciosos, seguras, alucinações, US$ por rodada).

> **Por que 15 arquivos e não um.** A versão anterior deste harness guardava **uma** `preds.tsv`
> e o README a citava como métrica. Era tirada única apresentada como medida, e foi isso que
> deixou `97,3%` parado por dois meses como se fosse estável. Aqui a dispersão é o dado: quem
> quiser conferir a média e o desvio da tabela refaz a conta a partir destes arquivos.

**O controle prova que `temperature=0` não determina** (e ele nem existe mais no Sonnet 5 / Opus 5):
as três rodadas deram 257 / 256 / 257, com 2 a 3 predições diferentes entre si — os índices
`161`, `173` e `279` trocaram de categoria entre rodadas idênticas no parâmetro.

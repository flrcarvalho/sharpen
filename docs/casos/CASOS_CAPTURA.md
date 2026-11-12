# Casos de captura que não chega ao banco

> Partição de [`../CASOS.md`](../CASOS.md) por assunto, aberta na s448 com ele perto do teto
> de 60 KB do `check_docs.py`. **Caso não se apaga:** caso novo em que a casa mostra uma coisa,
> a captura leu e o banco ficou com outra entra AQUI.

> ⚠️ Daqui de dentro, todo caminho relativo sobe um nível: `../CASOS.md`, `../../app/`.

> A **regra** vive no [`../../CLAUDE.md`](../../CLAUDE.md) § *"Fonte determinística manda;
> extração por IA congela"* (a exceção da reliquidação).

---

## A aposta que a casa reliquidou e o Sharpen nunca soube — 1win, s448

**Sintoma:** a Caixa da 1win (Ellen [Eu], Feca, 11/11/2026) projetava **685,60 USDT** com
**492,00** na casa. Nenhum erro, nenhuma aposta faltando: as 104 do texto da captura eram as
104 do banco.

**Como se achou:** somando o texto que a extensão mandou (stake 3.982,70, retorno 3.274,70) o
resultado da casa era **−708,00**; o Sharpen dizia **−594,40**. A diferença, **113,60**, é
exatamente `40 × 2,84`, e 2,84 era a odd da perna GANHA de uma única aposta perdida, a
`381894004` (Kristiansund × Volos). O jogo foi em 07/11 e o `Liquidado em` dizia **09/11
16:55**: a casa pagou primeiro como ganha a 2,84 (perna do Kristiansund anulada) e refez como
**perdida** dois dias depois. Na grade do Sharpen: W, odd 2,84, +73,60 USDT.

**Causa:** o pré-dedup (`get_codigos_resolvidos`, `main._dedup_superbet_text`) descarta,
ANTES da leitura, todo código que já está `resolvida` no banco, e a Ficha faz o mesmo
(`virada._liquidados`, D10). As duas economias foram desenhadas para a recaptura do que não
muda. Liquidado nunca voltava a ser lido, então a reliquidação da casa nunca chegava, por
nenhuma das duas rotas.

**Conserto (s448):**
- O bloco da extensão já traz o veredito (`Status: … → X`). Liquidado cujo veredito é de
  outra **classe** (ganhou, perdeu, devolveu) que o resultado gravado deixa de ser "já
  resolvido" e vai à leitura. A Ficha faz o mesmo com o resultado do cru final
  (`virada._reliquidados`). Mesma classe (W × HW) não reabre: o texto escreve W também para
  meia vitória.
- **Correção humana manda:** linha com `correcoes.origem` NULL em `resultado` segue pulada.
- O UPSERT leva a **odd junto** quando a classe troca. Só o resultado trocar (ele nunca foi
  congelado) deixaria L → W com a odd velha: o UPSERT meio-atualizado de sempre.

**Provado por mutação:** 10 de 10 detectadas (`tests/test_barreira_recaptura.py`, o
`test_predup_escopo_conta.py` e os `test_s448_*` do `test_repository_db.py`).

> **Sintoma para reconhecer isto noutro campo:** Caixa acima da casa por um valor que é
> `stake × odd` de UMA aposta, ou um `Liquidado em` dias depois do evento. Qualquer
> economia que pula "o que já está resolvido" assume que resolvido não muda; a casa
> discorda. Antes de pular, compare o que a fonte diz AGORA com o que está gravado,
> quando a comparação é de graça.

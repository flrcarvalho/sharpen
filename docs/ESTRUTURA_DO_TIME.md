# Estrutura do time — duas equipes, dois terminais, um repo

Decisão do Feca em 19/09/2026. O trabalho do lançamento foi partido em duas frentes que
rodam **ao mesmo tempo, em terminais separados, no mesmo repositório**. Este arquivo diz
quem faz o quê, quem é dono de qual arquivo e como as duas convivem no git.

## As duas equipes

| | **Equipe 1 — Lançamento** | **Equipe 2 — Marketing** |
|---|---|---|
| O que faz | Arquitetura, segurança, confiabilidade, onboarding, gates, deploy, rollback, runbook de incidente | Depoimentos, roteiro e vídeo, landing, material do X, prova social |
| Natureza | Execução técnica em lote | Conversa contínua com o Feca (ele manda áudio, a frente processa) |
| Dona de | `app/**` (menos os dois abaixo), `tests/**`, `extensor/**`, `scripts/**` (menos `demo/`), `tools/**`, infra e Railway | `app/static/landing.html`, `app/static/landing/**`, `docs/marketing/**`, `scripts/demo/**` |
| Compartilhados | `STATUS.md`, `BACKLOG.md`, `CLAUDE.md`, `app/main.py` — **avisar antes de tocar** | idem |

**Por que o marketing ficou com a landing e com `scripts/demo/`:** a landing é peça de
venda, e o `scripts/demo/` existe para gravar o produto rodando. Os dois são material de
comunicação que por acaso mora em código.

## A regra de git, e por que ela existe

O index do git é **compartilhado entre as duas sessões**. Arquivo que fica esperando
entre um `add` e um `commit` é levado por quem commitar primeiro.

1. **`git add <arquivos por nome>` e `git commit` no MESMO comando.** Nunca `git add -A`,
   nunca `git add .` — nem no `/encerrar`, que pede `-A` no texto genérico dele.
2. **`git show --stat` depois de commitar.** Se levou arquivo alheio, **não reescreva
   histórico já pushado**: registre e siga.
3. **Arquivo compartilhado se avisa antes.** E há uma armadilha mais fina, já medida: o
   `git show --stat` **não pega trecho alheio dentro de arquivo que também é seu**. Ali
   vale `git show <sha> -- <arquivo>`.
4. **Ninguém edita o `STATUS.md` da outra frente.** Este arquivo nasceu de um caso real:
   no encerramento de 29/09 a Equipe 2 começou a mover um bloco do `STATUS.md` e a Equipe 1
   estava escrevendo nele **no mesmo minuto**. Os índices de linha deslizaram no meio da
   edição e a remoção saiu errada; foi desfeita a partir do `git show HEAD:STATUS.md`. A
   conclusão ficou como regra: **com duas sessões vivas, o `STATUS.md` é de UMA por vez.**

> O caso original das duas sessões commitando ao mesmo tempo está em
> [`CASOS.md`](CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026).

## Coordenação

Quem coordena é o Feca. As equipes não conversam entre si: cada uma reporta a ele, e ele
decide. Achado de uma frente que pertence à outra **vira item no `BACKLOG.md`, com a
medição junto**, em vez de correção atravessada. Foi assim com o `BACKLOG 4.6` (a tela de
Custos abrindo vazia por F5), achado pelo marketing e deixado para a Equipe 1.

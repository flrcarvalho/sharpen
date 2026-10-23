---
description: Implementa a captura de uma casa nova no SharpenUp (harness, inject, content, 12 registros, gates)
argument-hint: "<NomeCanonico>  (ex.: Novibet) - exige /sharpenup-recon feito"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(node:*), Bash(python:*), Bash(git:*), Bash(cp:*), Bash(mkdir:*)
---

# Casa nova no SharpenUp: $ARGUMENTS

Segue `docs/GUIA_CASA_SHARPENUP.md` (Fases 2 a 7). Uma fase por vez:
**propor -> aguardar confirmacao -> executar**. Tudo em pt-BR. Terminal = PowerShell
(sem heredoc bash, sem `&&`).

**Pre-requisitos (se faltar, pare e peca):**
- `/sharpenup-recon` feito: modo decidido + tabela de campos respondida;
- `extensor/harness/fixtures/<casa>.*.json` com payload REAL (aberta, perdida, ganha,
  boost, multipla).

Leia antes de escrever qualquer linha: `docs/GUIA_CASA_SHARPENUP.md`,
`docs/SHARPENUP_ARQUITETURA.md` (§3 contrato e §5 registro) e o inject espelho escolhido.

## Fase 2 — Harness ANTES do codigo

- Escreva `extensor/harness/casos/<casa>.mjs` espelhando `casos/kto.mjs`.
- Cada valor esperado vem do **card da casa**, nunca do que o codigo produz.
- Rode `node extensor/harness/run.mjs <casa>`. **Vermelho aqui e o estado correto.**
- Mostre ao Feca a lista do que sera travado e confirme antes de seguir.

## Fase 3 — Inject (`extensor/<xx>_inject.js`)

- Copie o inject do mesmo modo e troque: `RX`, chave do bilhete, nome da mensagem,
  normalizacao, avanco de pagina.
- Cheque o contrato item a item (`ARQUITETURA §3`): `hook:true` + `respostas` sempre;
  re-enviar sob demanda; `const of = window.fetch` guardado para o replay; hook em fetch
  **e** XHR; `credentials:"include"`; avancar pelo tamanho que VOLTOU; teto de paginas;
  **normalizar, nunca decidir** (status desconhecido sobe cru).

## Fase 4 — content.js

Quatro pecas, espelhando a KTO (a mais recente e completa):
ouvinte (resolvida vence aberta) · `formatTicket<XX>` · `robo<XX>Passive` · ramo no
`iniciarRobo` + entrada no mapa de autodiagnostico.

No formatador, checar um a um: 1a linha `[Codigo: <id>]`; aberta com o texto padrao
"em aberto (aguardando resultado — NAO liquidar; sem resultado)"; retorno de aberta e
**potencial**; status desconhecido "(a conferir — nao liquidar automaticamente)";
**odd nunca truncada**, decimal com virgula; W = `retorno / stake`.

Rode o harness ate ficar verde. Se um valor esperado estiver errado, **corrija contra a
tela da casa**, nunca afrouxe o teste para o codigo passar.

## Fase 5 — Registro (12 pontos)

**ANTES de escrever a grafia em qualquer ponto, rode `python tools/audit_grafias.py` e procure
a casa na base sem caixa e sem espaco.** Se ela ja existe, a grafia registrada e a DA BASE,
nao a da marca. O registro manda em toda gravacao (`main.casa_oficial`), entao registrar uma
grafia que a base nao usa grava a captura numa casa que a conta nao enxerga (s391: a Megapari
registrada como `MegaPari`, 20 bilhetes invisiveis; o mesmo bug da s249).

Percorra a tabela de `ARQUITETURA §5`. Depois **prove**:

```
python tools/audit_sharpenup.py <CASA>
```

Cadastre o codigo real em `CODIGO_EXEMPLO` (`tools/audit_sharpenup.py`) — e o que liga a
conferencia de cobertura. Os dois que mais somem: `CASAS_CONECTAVEIS` (botao Conectar
nasce morto) e a regex de codigo em `repository.py` (perda silenciosa de chunk).

## Fase 6 — Gates

Backup em `Backups/<nome-descritivo>/` **so dos arquivos que serao editados** (nunca
`docs/HISTORICO.md`, nunca diretorio inteiro) ANTES de editar. Depois rode `/sharpenup-validar`.

## Fase 6b — Ficha Sharpen: a casa NASCE fora da IA (obrigatorio, s427)

**Casa de captura sem adaptador da Ficha e casa pela metade.** O cru chega, nenhum vira Ficha e
cada bilhete vai a IA: exportacao lenta e cara. Foi assim com a Thunderpick (s426) e a Vave
(s425), e o Feca: *"TODAS AS CASAS PRECISAM ESTAR ASSIM"*. O `audit_sharpenup` da **FAIL** em
casa de captura cuja familia nao tem adaptador (lista de excecao com data:
`FAMILIAS_SEM_ADAPTADOR`, hoje so as .bet.br em banho-maria).

1. **O inject manda o cru** (`_montarCru` / `_crus`, campo `cru` da mensagem), e o cru precisa
   bastar sozinho para montar a Ficha. Se a casa normaliza (ids + tabelas irmas, dicionario de
   mercado a parte, como a Vave), o cru leva as linhas que o bilhete usa, **verbatim**. Trave no
   harness que o cru tem tudo (Vave: o dicionario de cada perna, igual ao da casa).
2. **Familia ja tem adaptador** (espelho: `jb`, `tv`, `vb`, `x1`...)? Rode o adaptador nos crus
   da fixture e confira contra o card. **Familia nova:** `app/adaptadores/<xx>.py` no molde do
   `thp.py`/`vv.py` (`adaptar`, `bilhetes_da_resposta`, `codigo` se o id nao mora em `cru.id`),
   registrado em `ADAPTADORES`, fixture em `tests/test_cru.py::FIXTURES_POR_FAMILIA`.
   - **O adaptador COPIA.** Status pelo DINHEIRO (retorno = stake → anulada; ganha so se o
     retorno fecha com stake × odd); o que nao tem amostra, `Recusa` (o texto leva a IA).
   - **Codigo IGUAL ao do `[Codigo: …]` do texto**, senao Ficha e IA gravam dois bilhetes.
   - **Nome dentro do mercado** (jogador, time) atrapalha a chave do dicionario: confira que
     `dicionario.chaves(f)` generaliza (`{jogador}` s415, `{time}` s427).
3. **Testes** `tests/test_adaptador_<xx>.py`: valor esperado do CARD, nunca do codigo; prove por
   mutacao (liste no cabecalho, e o que NAO cobre).
4. **Medir nos crus reais** (banco, so leitura): quantos aceitos/recusados e por que; e,
   quando ja ha linha da IA, resultado, data e odd Ficha × IA. Divergencia se explica caso a
   caso antes de virar (data: a Ficha segue o MASTER; odd: a da casa).
5. **Virada** (depois do deploy): a casa entra em `FICHA_SOMBRA_CASAS`, `FICHA_CASAS_VIRADAS` e
   `EXTRACAO_SEM_PENSAMENTO` (Railway, servico `extrator`). A CLI e bloqueada para o Claude:
   entregue ao Feca o comando COMPLETO, numa linha, com os valores atuais + a casa
   (`railway variables --service extrator --kv` para ler). Depois do redeploy,
   `python scripts/semear_dicionario.py --aplicar`.
6. **1a captura virada** conferida no `virada_log` (pela_ficha × para_ia). `DIARIO.md` do
   projeto Ficha com a entrada da etapa.

## Fase 7 — Soltar

- **Bump da `version` no `manifest.json`** (obrigatorio: e o sinal de versao nova).
- `casas/CASA_<X>.md`: §2.5 com os campos da API e §5 com o de-para de status.
- `STATUS.md` + commit + push (Conventional Commits, multiplos `-m`).
- Marque explicitamente o que **nao** foi validado ao vivo.

### 7.1 LIBERAR O BOTAO PRA GALERA — passo proprio, e nao e o `CASAS_CONECTAVEIS`

**Registrar a casa NAO libera o botao de quem ja esta com o painel aberto.** Este passo
existe porque ele foi esquecido vezes suficientes para o Feca pedir que virasse processo
(s372), e porque o sintoma e indistinguivel de registro faltando.

1. **Depois do deploy, PROVE em producao** — leitura de codigo nao vale, o gate do
   `audit_sharpenup` confere a LISTA e nao o runtime:

   ```js
   // no console de https://www.sharpen.bet/app, logado:
   const w = document.getElementById('fr-plan').contentWindow;
   [w._casaConectavel('<Casa>'), w._casaConectavel('CasaQueNaoExiste')]   // [true, false]
   await (await fetch('/casas')).json()                                    // <Casa> em `captura`
   ```

   O controle negativo e obrigatorio: `true` sozinho tambem sai de uma funcao que devolve
   `true` para tudo.

2. **O aviso ao grupo tem de mandar recarregar o PAINEL, nao so a aba da casa.** Sao dois
   Ctrl+Shift+R diferentes e por motivos diferentes:

   | Onde | Por que | O que fica quebrado sem isso |
   |---|---|---|
   | aba da **casa** | recarregar a extensao **nao** re-injeta em aba ja aberta | a captura nao arranca |
   | aba do **painel** | `CASAS_CONECTAVEIS` e `carregarCasas()` rodam **uma vez, no load** | **o botao Conectar nasce desabilitado** e a casa nao aparece em "Nova conta" |

   O painel e servido com `no-cache`, mas `no-cache` obriga a revalidar **no carregamento**:
   aba aberta desde ontem segue rodando o JS antigo em memoria.

3. **Se alguem disser que o botao esta travado, meca o SERVIDOR antes de mexer no
   registro.** `GET /casas` na sessao dele responde se a casa esta la. Se estiver, o defeito
   e a aba, e a acao e um F5 — nao ha nada para corrigir no codigo.
   → [o caso da Novibet](../../docs/GUIA_CASA_SHARPENUP.md#fase-7--soltar-e-validar-ao-vivo) (s272: o botao
   estava liberado havia 16 horas) e o do seletor de contas (s298, com os 12 pontos verdes).

## Ao final

Uma linha: casa X no modo Y, harness com N bilhetes verdes, audit sem FAIL,
adaptador <xx> (N testes, M mutacoes, crus reais aceitos), virada pedida ao Feca,
manifest 0.a.b -> 0.a.c, commit <hash> enviado, pendente = validacao ao vivo.

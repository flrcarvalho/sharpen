# CLAUDE.md — Planilhador (FDC Capital)

> Regras operacionais obrigatórias para este projeto.
> A bíblia de marca e design está em [`../pack/CLAUDE.md`](../pack/CLAUDE.md).
> O ponteiro de navegação do projeto pai está em [`../CLAUDE.md`](../CLAUDE.md).

---

## Estrutura do projeto

```
Planilhador/
├── global/          ← 6 masters globais (fonte única de verdade)
├── casas/           ← 1 arquivo por casa (traduz; nunca redefine)
├── golden_set/      ← bilhetes reais + TSV esperado (validação)
├── extensor/        ← SharpenUp (extensão de captura) + harness/ de regressão
├── Backups/         ← snapshots antes de cada edição
└── STATUS.md        ← estado atual; ler antes de qualquer sessão
```

---

## ⚠️ CASA NOVA — leia antes de começar

Casa tem **duas camadas independentes**. Confira qual você vai mexer:

| Camada | O que é | Guia | Gate |
|---|---|---|---|
| **Leitura** | `casas/CASA_*.md` + registro no seletor/favicon. Já funciona por **print**. | [`docs/GUIA_NOVA_CASA.md`](docs/GUIA_NOVA_CASA.md) | `python tools/audit_casas.py` |
| **Captura** | robô do SharpenUp lendo a API da casa. **12 pontos de registro** em 4 camadas. | [`docs/GUIA_CASA_SHARPENUP.md`](docs/GUIA_CASA_SHARPENUP.md) | `python tools/audit_sharpenup.py` |

Mapa do sistema: [`docs/SHARPENUP_ARQUITETURA.md`](docs/SHARPENUP_ARQUITETURA.md).
Regressão da captura: `node extensor/harness/run.mjs` — **rode antes de todo commit que
toque `extensor/`**. Skills: `/sharpenup-recon` → `/sharpenup-casa` → `/sharpenup-validar`;
casa que parou → `/sharpenup-diagnostico`.

> **Nunca escolha o modo TEXTO sem provar que há linha em branco entre bilhetes no
> `innerText`.** Sem isso a lista vira um bloco só e a IA perde o resto **em silêncio**
> (s192: KTO, ~90 % dos bilhetes). Na dúvida, vá por trás — F12 → Network → a API da casa.

---

## Invariantes (nunca quebrar)

1. O app **lê** os masters, **nunca escreve**. Mudança = diff revisado + aprovação humana.
2. Arquivo de casa **traduz**; nunca redefine regra global.
3. **Cálculo é global, localização é da casa.**
4. Backup em `Planilhador/Backups/<nome-descritivo>/` antes de qualquer edição. Nunca usar `FDC Capital/Backups/`. **Retenção (#25 auditoria):** copiar para o backup **só os arquivos que serão editados** — nunca `docs/HISTORICO.md` (500KB, já versionado no git) nem diretórios inteiros. `Backups/` é gitignored/manual; podar snapshots além de ~últimas sessões / 90 dias quando incomodar (o git cobre o histórico versionado).
5. Arquivos completos, nunca diffs parciais.
6. Uma mudança por vez. Propor → aguardar confirmação → executar.
7. Atualizar `STATUS.md` ao fim de cada mudança aplicada.
8. **Commit e push sempre juntos.** Após cada mudança aprovada: `git add` → `git commit` → `git push`. Deploy automático via Railway. Nunca deixar commit sem push.

---

## Conta de usuário nova = duas metades, e a segunda é humana

Criar login é 1 linha em `USUARIOS` (`app/auth.py`) + a env var `SENHA_<USER>_HASH` no
Railway. **Não existe migration, seed nem import:** o isolamento é a coluna `dono` no
Postgres, então a base nasce vazia e o primeiro bilhete capturado cria as linhas.

O código sobe no push. A senha depende de alguém colar a variável no Railway — e
**enquanto ela falta o login diz "usuário ou senha inválidos"**, igualzinho a senha
errada (`USUARIOS[x] == ""` nunca autentica; fail-closed por desenho).

**Antes de suspeitar do código, separe código de configuração medindo:** um asset que
só existe no deploy novo responde 200 → o usuário está em `USUARIOS`; `POST /login`
devolvendo **401** tem origem única (`verificar_credenciais` falso) — 429 é rate-limit,
500 é erro do app. Usuário existindo + 401 = **env var ausente ou truncada**.

**O `$` do hash bcrypt é a armadilha de transporte:** `$2b$12$…` passa mutilado por
qualquer shell que interpole variável (PowerShell inclusive). Cole na caixa de Variables
do Railway, confira **60 caracteres** e nenhum espaço nas pontas. Hash nunca vai para o
git. Decidir também se a conta é **dono solo** ou entra em `OPERADORES` — solo é o
default; operador significa que o supervisor vê a base dele e que a dedup cruzada passa
a valer entre os dois.

---

## `DADOS` só tem aposta LIQUIDADA. Quem existe antes da 1ª aposta vem do cadastro.

`aplicarFeed` (`dash/assets/js/app.js`) parte o feed em dois: `DADOS` recebe só
`W/L/V/HW/HL` e `DADOS_ABERTAS` recebe o resto. Toda tela que deriva de `DADOS` herda
o mesmo ponto cego: **usuário novo, que só tem aposta em aberto, chega com `DADOS`
vazio.** O sintoma não é erro, é tela parada num "aguardando" que nunca resolve (s239:
o Diogo cadastrou 16 contas, tinha 12 bilhetes, todos em aberto, e a aba Custos de
Contas ficou em branco).

A regra de fundo: **a existência de uma entidade não vem do bilhete.** Conta comprada
tem custo antes de apostar; o cadastro (`parceiros`) é a fonte de quem existe, e o
bilhete só acrescenta o que nunca foi cadastrado. Onde os dois valem, use a **união** —
na base do Feca são 130 contas que só existem em bilhete e sumiriam se você trocasse
uma fonte pela outra em vez de somar.

Antes de unir cadastro e bilhete, **meça as duas divergências que duplicam linha**:
grafia de casa (`Bet365` × `BET365`) e fornecedor divergente para a mesma conta. As
duas deram zero em todos os donos na s239, mas isso é medição datada, não garantia.

> Separe **existir** de **contar no P/L**. Conta sem aposta aparece na tela para
> receber o custo, e continua fora de qualquer janela de P/L (`calcCostFiltered` usa
> a data da 1ª aposta). Misturar os dois é como o UPSERT meio-atualizado: vira lucro
> fantasma.

**Nem toda entidade tem cadastro. Esporte e mercado têm MASTER.** Para eles a fonte de
"o que existe" é a taxonomia canônica — `app/taxonomia.py` **lê** o `MASTER_ESPORTES §7`
e o `MASTER_APOSTAS §3`, e a rota `/taxonomia` serve as listas (s241). A tela usa a
**união** com a base do dono, e os dois lados são load-bearing: o canônico oferece o que
ele ainda não apostou, a base preserva a grafia herdada de import (`Fórmula 1`, `Esoccer`,
`Tênis de Mesa`) que o canônico não tem e que **é a que o matcher compara**.

Ler o MASTER em vez de copiá-lo tira uma linha da regra de propagação acima, e o preço é
um parse que **falha em silêncio**: seção renumerada, tabela virando lista, e a extração
devolve `[]` sem erro nenhum — menu vazio para o usuário. Quem lê MASTER em código paga
o gate junto: `tests/test_taxonomia.py` trava âncoras e piso de tamanho, para MASTER
reformatado quebrar o CI em vez da tela.

---

## "Sugerir tipsters" parou? O suspeito é um perfil novo, não o código.

O matcher (`_sugParaBilhete`, inline no `app/static/index.html`) só sugere com **folga ≥ 7**
entre o 1º e o 2º colocado. Em empate ele fica **vazio de propósito** — não chuta.

A consequência é o modo de falha: **um perfil novo pode matar um perfil antigo em silêncio.**
Nada aparece no rail nem no console, só a coluna vazia. Foi a s221: `MultiLBB` nasceu com a
dica `49, 99`, o parser deriva o final de todo valor não-redondo (`49 → 9`, `99 → 9`), ele
virou dono do final 9 inteiro e empatou com o `199` do LBB (28 × 27) — os dois se anularam.

**Diagnóstico, nesta ordem:**

1. `select nome, criado_em from tipsters where dono = '<dono>' order by criado_em desc limit 5`
   — perfil criado ou editado nos últimos dias é o primeiro suspeito.
2. **Prove por remoção, não por dedução.** Extraia o bloco JS do `index.html`, rode em node
   contra os perfis e bilhetes **reais** do banco, e compare com e sem o perfil suspeito.
   Isola a causa sem editar nada.
3. Só então mexa no peso. E **meça**: backtest contra bilhetes já rotulados, antes e depois.

**Ao calibrar peso de stake, dois cortes são load-bearing** (tirar qualquer um já quebrou o
matcher em produção): valor **redondo** (50/100/250/800) não é digital, é valor comum — sem
esse corte o M&M rouba os 50/100 do Peixe; e `valores.size === 1` separa "este valor É minha
assinatura única" de "é um dos vários que aposto".

> **Assinatura tem ERA.** O `199` foi do SóTudo até junho e virou do LBB em julho. Backtest
> in-sample pune o acerto de hoje com bilhete velho — leia o placar sabendo disso, e use
> holdout **temporal** para qualquer regra que aprenda da base.

---

## ⚠️ REGRA DE UI / MARCA OBRIGATÓRIA (antes de criar QUALQUER visual novo)

> **Motivo:** na sessão 83, cards de KPI foram criados com formatadores caseiros que abreviavam (`1,4k`) e coloriam o valor inteiro — violando 4 regras do padrão monetário. O Feca teve que voltar em detalhe já documentado. A causa: **regra escrita sem hábito de conferir = pulada.** Esta seção torna a conferência obrigatória.

**Antes de escrever qualquer render de número, dinheiro, cor, tipografia ou componente visual, NESTA ordem:**

1. **Ler** `docs/UI_REFERENCE.md` (§5 = padrão monetário) e, se tocar na casca, `docs/SHELL_SPEC.md`. A bíblia de marca é [`../pack/CLAUDE.md`](../pack/CLAUDE.md); tokens em [`../pack/tokens/tokens.css`](../pack/tokens/tokens.css).
2. **Reusar helper existente, nunca criar formatador.** `grep` por `fmtPL`/`fmtR`/`moneyStake`/`.money` no arquivo e reusar. Todo R$ usa o componente `.money`; só muda as casas por contexto (ver `UI_REFERENCE §5`): **P/L → `fmtPL` (2 casas**, `R$` menor `--ink-soft`, cor SÓ no número, minus U+2212, zero neutro); **agregado/KPI/turnover/custo → `fmtR` (inteiro)**. **Nunca abreviar milhar (`k`/`M`) — barrado pelo `check-tokens §d`.** `.toFixed`/`.replace` só nas exceções documentadas (odd/USD), nunca em R$.
3. **Cor sempre de token** (`var(--…)`), nunca literal. `.money-sign`/sinal ficam neutros.
4. **Auto-auditar item a item contra §5 ANTES do commit** + rodar `node scripts/tokens/check-tokens.mjs`.

> Dúvida de qual convenção (tabela vs card)? Pergunte ao Feca — não invente uma terceira. Use `/nova-ui` para rodar este checklist guiado.

---

## Escada de Tinta — a cor do texto vem do PAPEL, não do espaço

> **Motivo:** o cabeçalho de grupo do Painel de Contas usava `--ink-mute` em 9,5px caixa
> alta com tracking .16em sobre fundo efetivo `#1A1F26` — **2,9:1**. Reprova AA (4,5:1) e
> reprova até o piso de texto grande (3:1). O feedback que abriu o caso foi de uso, não de
> auditoria: *"essas letras nesse cinza claro fica muito claro"*.

Três causas somaram: tom baixo, corpo minúsculo e tracking largo em caixa alta. Junto
veio **inversão de hierarquia** — o e-mail da conta (13,5px/700/`--ink`) pesava mais que o
nome da casa, então a varredura da lista lia endereços em vez de casas.

A regra que faltava: **`--ink-mute` nunca teve piso de tamanho.** Ele é legítimo em 12px
sobre `--surface`; em 9,5px caixa alta sobre `--surface-2` deixa de ser texto e vira
textura.

**Contraste sempre medido sobre o FUNDO EFETIVO** — somando os overlays de
`rgba(255,255,255,…)`, não sobre o token de superfície que está no CSS. Foi o overlay de
`.025` que escondeu o problema.

| Papel | Exemplo | Cor | Corpo mín. | Contraste mín. |
|---|---|---|---|---|
| Identidade / nome próprio | casa, tipster, operador, e-mail | `--ink` | 13px | 12:1 |
| Valor numérico | KPI, odd, saldo, P/L | `--ink` | 13px | 12:1 |
| Label / eyebrow / `thead` | CONTAS, PERÍODO, ESPORTE | `--ink-soft` | 9,5px | 4,5:1 |
| Metadado secundário | contador, unidade, timestamp | `--ink-mute` | 10px | 3:1 |
| Desabilitado / placeholder | input vazio, ícone off | `--ink-mute` | 12px | — |

Medido no tema escuro (o app é dark, sem toggle), sobre `--surface-2` com overlay:
`--ink` **14,7:1** · `--ink-soft` **6,3:1** · `--ink-mute` **3,0:1**.

**Faça**

- Um único elemento `--ink-mute` por linha ou cabeçalho. Se houver dois, um deles é
  conteúdo disfarçado de enfeite.
- Caixa alta + tracking só em **categoria**. Nome de marca vai em caixa própria — e aí o
  dado precisa chegar na caixa certa (`casaDisplay()` no `index.html`: title case **só**
  em quem vem sem informação de caixa; caixa mista é verbatim, senão mutila `BETesporte`,
  `VaideBet`, `KingPanda`).
- Abaixo de 11px: subir um degrau na escada e o peso para 500.

**Não faça**

- `--ink-mute` em texto abaixo de 10px, em qualquer superfície.
- Filho mais legível que o pai (e-mail em `--ink` dentro de grupo em `--ink-mute`).
- Resolver contraste com `#FFFFFF` — **a escala fecha em `--ink`**. "Mudar pra branco" se
  traduz, no sistema, como *subir um degrau na escada*.
- Compensar tom baixo com peso 700 em 9,5px: engorda o borrão, não corrige a leitura.

**`opacity` não é um degrau da escada — é um multiplicador.** Aplicada sobre um tom já
apagado ela derruba o contraste efetivo sem aparecer em nenhum grep de cor: `--ink-mute`
com `opacity:.55` dava ~1,9:1, e `--ink-soft` com `opacity:.7` caía para ~4,4:1, logo
abaixo do mínimo do papel. Se o texto precisa ser mais discreto, **desça um degrau na
escada**, não aplique opacidade.

**Duas exceções, ambas comentadas no CSS para não virarem precedente:**

- **Ícone não é texto.** Caret, seta e o "i" de ajuda (`.operador-caret`, `.casa-arrow`,
  `.sb-op-caret`, `.metric-info`) ficam abaixo do piso, em `--ink-mute`, por desenho.
- **`opacity` como ESTADO é legítima** — `.act-btn.off`, `.update-btn.is-loading`,
  `.host-refresh.is-loading`. Ali ela sinaliza desabilitado/carregando, não hierarquia.

> **A varredura precisa de três critérios, não um.** O grep de `--ink-mute` por px
> literal é cego a tamanho vindo de token (`var(--text-nano)` = 9px), a `opacity` sobre
> tom apagado, e ao papel errado num corpo que passa no piso (label de legenda em 11px
> `--ink-mute` reprova por ser label, não por ser pequeno). Um lint que resolva só o
> primeiro critério dá falso verde.

---

## ⚠️ REGRA DE PROPAGAÇÃO OBRIGATÓRIA

**Toda vez que uma categoria for criada, renomeada ou removida do `MASTER_APOSTAS_2026.md`, os seguintes arquivos DEVEM ser atualizados na mesma sessão, sem exceção:**

| O que atualizar | Onde | O quê |
|---|---|---|
| Tabela de categorias | `MASTER_APOSTAS_2026.md §3` | Adicionar / renomear / remover linha |
| Sinônimos | `MASTER_APOSTAS_2026.md §4` | Adicionar bloco de sinônimos |
| Regras por categoria | `MASTER_APOSTAS_2026.md §5` | Documentar casos especiais |
| Regras por esporte | `MASTER_APOSTAS_2026.md §6` | Atualizar se o esporte for afetado |
| Validação final | `MASTER_APOSTAS_2026.md §9` | Adicionar checagem da nova categoria |
| **Mapa de mercados — só casas afetadas** | `casas/CASA_*.md §9` | **Apenas** as casas cujo §9 já referencia a categoria/rótulo afetado. Buscar com `grep -rl "<categoria>" casas/`. Sob a camada fina, o §9 lista só mercados confirmados — uma categoria nunca vista por uma casa **não** aparece lá e **não** precisa de update. |
| Template de descrição | `MASTER_DESCRICAO_2026.md §12 ou §13` | Adicionar template se o formato for novo |
| Prioridade semântica | `MASTER_APOSTAS_2026.md §7` | Atualizar se houver risco de confusão com Player Props / Outros |

> Os menus de esporte e mercado do editor de tipster **não** entram nesta lista: eles leem
> o MASTER em tempo de execução (`/taxonomia`). Categoria criada aparece lá sozinha.

> **Motivo:** em 13/06/2026 as categorias `Dupla Chance`, `Impedimentos` e `Chutes no Gol` foram criadas no MASTER mas os mapas das casas ficaram desatualizados apontando para `Outros ⚠️`. A **causa raiz** era a duplicação: cada casa reescrevia as 27 categorias. Desde a sessão 49 (camada fina), o §9 lista só o que a casa confirma → a superfície de propagação encolheu para as casas realmente afetadas.

**Checklist rápido ao criar/renomear/remover uma categoria:**

- [ ] `MASTER_APOSTAS §3` (tabela) atualizado
- [ ] `MASTER_APOSTAS §4` (sinônimos) atualizado
- [ ] `MASTER_APOSTAS §9` (validação) atualizado
- [ ] `MASTER_APOSTAS §7` (prioridade semântica) atualizado se houver risco de confusão
- [ ] `MASTER_DESCRICAO §12/§13` atualizado se o formato de descrição for novo
- [ ] `grep -rl "<categoria afetada>" casas/` → atualizar **só** os §9 que aparecerem (renomear/remover); novo nome quase nunca exige update de casa
- [ ] Rodar `/audit-casas` para confirmar que nenhum §9 ficou apontando para categoria inexistente

> Dica: use `/propagar-categoria` para automatizar este checklist.

---

## Convenções de output

> **Fonte canônica:** `global/MASTER_OUTPUT_2026.md` (TAB, 10 colunas, 11ª coluna interna `Código`, decimal vírgula, códigos de resultado). O resumo abaixo é um **espelho operacional** — ao mudar o formato, mude no MASTER primeiro.

- Separador: **TAB real** (U+0009) — nunca espaços, ponto-e-vírgula ou pipe
- **10 colunas para a planilha do usuário**: `Data | Esporte | Tipster | Casa | Parceiro | Aposta | Descrição | Stake | Odd | Resultado`
- **11ª coluna interna** (`Código`): ID/código do bilhete visível no print — nunca vai para a planilha do usuário, só para o banco de dados. A AI sempre retorna essa coluna; se não houver ID visível, a célula fica vazia.
- Decimal: **vírgula** (`2,35`) — nunca ponto
- Resultado: `W · L · V · HW · HL` — ou **vazio** quando a aposta está aberta (não liquidada; ver `MASTER_OUTPUT §13.1` / `MASTER_RESULTADO §1.1`)
- Odd sem limite de casas decimais (planilha usa a precisão completa)

---

## Regras de deduplicação (sistema)

O sistema determina se dois bilhetes são iguais ou diferentes na seguinte ordem de prioridade:

| Situação | Comportamento |
|---|---|
| **ID/código do bilhete disponível e igual** | Mesmo bilhete — UPSERT (atualiza resultado/estado) |
| **ID/código do bilhete disponível e diferente** | Bilhetes distintos — sempre INSERT (mesmo conteúdo idêntico) |
| **Sem ID, conteúdo diferente** (odd, descrição, etc.) | Bilhetes distintos — INSERT |
| **Sem ID, conteúdo idêntico, mesmo lote** | Possível sobreposição de prints — salva **ambas** as linhas (assinaturas distintas via `_counter`: `B`, `B\|2`, …) + aviso amarelo ao usuário; delete se for sobreposição real |
| **Sem ID, conteúdo idêntico, lotes diferentes** | Re-processamento do mesmo bilhete — UPSERT silencioso |

**Limitação:** Para casas onde o ID não é visível no print (ou a AI não consegue lê-lo), dois bilhetes 100% idênticos (mesmos jogos, odds, stake, casa) não têm como ser distinguidos. O sistema salva **ambos** (assinaturas distintas via `_counter`) e avisa. Use o botão de deletar se for sobreposição real.

**Fonte canônica (implementação):** `app/repository.py` — `_assinatura()` e `upsert_bilhetes()`. Esta tabela documenta o comportamento do código; ao mudar a lógica de dedup, **o código é a verdade** (atualize a tabela depois).

### Fonte determinística manda; extração por IA congela.

O UPSERT **congela** `odd`, `data`, `stake`, `esporte`, `aposta` e `descricao` assim que a
aposta resolve. Isso protege a extração por IA: a re-leitura é ruidosa e sobrescrever seria
pior que manter. **Exceção: `origem='sync'`** (fonte determinística — hoje só o
`/polymarket/sync`, que lê a API on-chain). Para ela esses campos são sempre refrescados.

**Por que a exceção existe:** `resultado` nunca foi congelado. Com fonte determinística isso
deixava a linha **meio atualizada** — ao corrigir o cálculo do mercado anulado, o resultado
passou de `L` para `W` e a odd ficou a antiga, dobrada: 28 linhas viraram lucro fantasma
(+R$578 onde o real era −R$11,80). **Blindar metade dos campos é pior que blindar todos ou
nenhum.** O mesmo valia para `esporte`/`aposta`, que só entravam no INSERT e trancaram 40
linhas mal classificadas fora de qualquer correção.

Contrapartida: edição manual de data/stake/odd/esporte/categoria/descrição numa casa
sincronizada **não sobrevive** ao sync. O `tipster` sobrevive.

> **Método:** melhorar o cálculo não basta — confira se ele **chega ao banco**. Depois de
> corrigir qualquer fórmula, diffe `banco × coletor` linha a linha.

**Fonte canônica:** `app/repository.py` — `_ORIGEM_AUTORITATIVA` e o `ON CONFLICT` de
`upsert_bilhetes()`.

### Mexeu em `casa` ou `parceiro` de um bilhete? Recalcule a assinatura.

`casa` e `parceiro` entram no hash de `_assinatura` (com ou sem código de bilhete). Trocar
qualquer um dos dois sem recalcular deixa a linha com o hash antigo: a próxima captura
gera uma assinatura nova, não colide com nada, o UPSERT não dedupa e **o histórico
duplica inteiro**. Vale para renomear conta, unificar casa, mover bilhete e backfill.

Quem já faz certo: `renomear_parceiro()`, `atualizar_bilhete()` (via `_assinatura_pos_edicao`),
`scripts/unificar_casas.py` e `scripts/reparar_orfaos_parceiro.py`. Reuse o laço de
`_counter` deles — duas linhas de conteúdo idêntico precisam escalar, não colidir.

`casa` é **texto** em `bilhetes`, `parceiros`, `casas_meta`, `casa_config`, `correcoes`,
`uso_tokens` e `tipsters.casas`: cada grafia é uma casa **diferente** no sistema. Ao criar
conta, `repository.casa_canonica()` reusa a grafia que já existe; casa nova entra
**verbatim** (nunca title-casear — mutilar nome cria conta paralela).

---

## Excluir dado: mova para tabela isolada, nunca soft-delete

Exclusão destrutiva **move** as linhas para uma tabela que mais nada no sistema lê
(hoje `lixeira_contas`, alimentada pelo botão Excluir do Painel de Contas, retenção
de 7 dias com purga preguiçosa). Nunca marque `excluido = TRUE` na tabela de origem.

**Por quê:** soft-delete em `bilhetes` obrigaria a filtrar em dezenas de queries
espalhadas (dashboard, KPIs, dedup, export, P/L). Um esquecimento vira lucro
fantasma, a mesma família do UPSERT meio-atualizado descrito acima. Tabela separada
tem acoplamento zero por construção.

Duas regras de forma:

- **O snapshot e o DELETE são a MESMA operação** (`DELETE ... RETURNING to_jsonb(b.*)`).
  Ler antes e apagar depois abre janela para gravar uma lixeira que não corresponde
  ao que saiu.
- **Snapshot em JSONB, nunca tabela-espelho.** `bilhetes` ganha coluna via `ALTER TABLE`
  de tempos em tempos, e um espelho pararia de copiar a coluna nova em silêncio.

Restaurar casa o snapshot com as colunas que a tabela tem **hoje** e usa `ON CONFLICT
DO NOTHING`: entre excluir e restaurar o espaço pode ter sido reocupado, e **dado novo
manda**.

**Rota destrutiva reconfere a confirmação no servidor.** A UI trava o botão até o nome
exato ser digitado, mas isso é conveniência, não segurança: um `DELETE` disparado por
engano (histórico do navegador, script, curl) não pode apagar histórico.

**Fonte canônica:** `app/repository.py` (`excluir_parceiro`, `LIXEIRA_DIAS`) e
`scripts/restaurar_conta_lixeira.py`.

---

## API externa por item = latência E falha multiplicadas. Peça a FAIXA.

> **Motivo:** o sync da Polymarket levava mais de 3 minutos e "muitas vezes nem
> funcionava". A Polymarket respondia em 3s. O resto era o **Banco Central**: o câmbio
> era pedido **uma data por vez**, e 76 datas de bilhete viravam **113 chamadas
> sequenciais** (s247).

Duas coisas escalam juntas quando se chama uma API externa em laço, e a segunda é a
que morde:

- **Latência** — 113 × 179ms = 25s com o BCB saudável. Cresce com o histórico, sem teto.
- **Probabilidade de falha** — com o BCB oscilando (medido: 1 falha em 6), 113 chamadas
  são 113 chances de derrubar o sync. Cada falha ainda carrega o backoff do `_get_retry`
  (3 tentativas + 3s), e minutos viram a norma.

**Antes de otimizar o laço, procure o endpoint de faixa.** O BCB entrega 3 anos de PTAX
em **uma** chamada de 1,3s. A pergunta certa quase nunca é "como paralelizo 113
chamadas?", e sim "por que são 113?".

**Dado histórico é imutável — cacheie entre requisições.** Cotação de dia passado nunca
muda: o mapa é de módulo (`polymarket._PTAX_MAPA`) e o 2º sync não gasta rede nenhuma.
Vale para qualquer dado datado e fechado; não vale para saldo, preço ou posição aberta.

**Engolir a exceção transforma falha de rede em dado ausente.** O `_ptax` antigo devolvia
`None` tanto para "não houve boletim nesse dia" quanto para "o BCB caiu" — os dois
indistinguíveis. O laço então tratava o timeout como feriado, recuava 10 dias e só no
fim derrubava o sync inteiro. **Se o chamador precisa distinguir os dois casos, o
`except` não pode achatá-los.**

> **Trocar a fonte de um número exige provar que o número não mudou.** A cotação nova
> foi comparada com a antiga **nas 76 datas, uma a uma**: 0 divergências. Sem isso o
> re-sync mexeria em stake já gravado — `origem='sync'` é `_ORIGEM_AUTORITATIVA` e
> refresca `stake`/`odd`/`data` mesmo em bilhete resolvido. Repare no detalhe que quase
> passou: o BCB republica alguns dias com **dois** boletins, e o endpoint antigo pegava
> o primeiro (`$top=1`) — o mapa mantém a mesma escolha (`setdefault`) de propósito.

---

## Regra de cashout (planilha-compatível)

> **Fonte canônica:** `global/MASTER_RESULTADO_2026.md §5.1.2` (cashout = stake → V) e `§5.6` (cashout ≠ stake → W), com resumo em `MASTER_OUTPUT_2026.md §14`. **Mudou? Mude no MASTER, nunca aqui.**

Resumo: cashout **≠** stake (maior **ou** menor) → **W**, `Odd = Cashout ÷ Stake`. Cashout **=** stake, void ou cancelada → **V**, odd exibida no bilhete.

---

VERSÃO: 2026
ATUALIZADO: 2026-08-05 (sessão 247 — seção "API externa por item")

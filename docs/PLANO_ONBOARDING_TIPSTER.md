# PLANO — Onboarding de tipster em autosserviço

> Pedido do Feca (07/09/2026): *"o ideal é que isso fosse self configurated — que o tipster
> conseguisse fazer tudo sozinho. E que só viesse pronto para a gente aprovar ou tirar as
> dúvidas. Cada novo tipster não pode tomar horas de configuração aqui."*
>
> Vizinhos: [`GUIA_BOT_TIPSTER.md`](GUIA_BOT_TIPSTER.md) (os 8 passos de hoje, e onde eles
> doem), [`PLANO_TIPSTER.md`](PLANO_TIPSTER.md) (o Perfil de Tipster dentro do Sharpen),
> [`PLANO_MULTIUSUARIO_2026.md`](PLANO_MULTIUSUARIO_2026.md) (de onde vem o cadastro).

---

## Parte 1 — em português, sem código

### O que existe hoje

O tipster já faz **duas** coisas sozinho: se cadastra no site e espera aprovação. O resto —
os grupos, os ids, o registro dele no bot, a leitura do formato das mensagens dele e a
importação do histórico — passa inteiro pela nossa mão, e boa parte exige subir código.

### O que passa a existir

Uma página de configuração onde o tipster preenche o que é dele, o sistema **confere
sozinho** o que dá para conferir, e o que sobra chega até nós **já pronto para aprovar**,
não para descobrir.

**O tipster faz sozinho:** cria o grupo de apoio e o canal, adiciona o bot, digita
`/vincular` no apoio (o bot descobre o id sozinho — ninguém digita número), diz como é a
gestão dele (unidade ou %), cola 30 mensagens reais do canal e **confere, uma por uma, se
o sistema entendeu certo**.

**Nós fazemos:** aprovamos a conta, ligamos o bot, aprovamos o formato que ele conferiu, e
aprovamos o lote do histórico antes de ele virar linha no banco.

**A régua da separação:** o que só custa tempo ou dinheiro dele, ele decide; o que **grava
em `bilhetes`** ou **nomeia coisa no sistema**, passa por nós.

| Ele resolve sozinho (com ajuda da IA na tela) | Nós decidimos |
|---|---|
| "o que é stake em unidade / ROI / drawdown / SOA" | **Prefixo do código** (`GV`, `SO`) — colide com código nativo de casa |
| como criar apoio e canal, como dar admin ao bot | **Aprovar a conta** e **ligar o bot** |
| pegar os ids (via `/vincular`) | **Semear o contador** — erro aqui absorve aposta em silêncio |
| conferir o post antes de ir ao ar (modo teste) | **`dono` = username, nunca a marca** |
| ver o que o bot entendeu das mensagens dele | **Aprovar a spec do formato** e o **lote do import** |
| corrigir a leitura apontando o erro | **Casa que não existe no `casas.js`**, slug e marca pública |

---

## Parte 2 — onde as horas vão, medido

Não é impressão: são os artefatos que cada tipster novo produziu.

| Bloco | Artefato | Tamanho | Automatizável |
|---|---|---|---|
| Perfil de leitura | `src/perfis/<x>.js` | 250 a 1.036 linhas (4.806 em 7 perfis) | **parcial** |
| Import do histórico | `scripts/import_*.py` | 15 scripts, 9.659 linhas | **parcial** |
| Registro do tenant | `config.js` + `PERFIS` + 5 env vars + contador | ~40 linhas **+ deploy** | **inteiro** |
| Ids, grupos, permissões | Telegram | — | **inteiro** |

### As três medições que decidem o desenho

**1. Os perfis NÃO compartilham um miolo grande.** Linhas idênticas entre cada par:

```
grego × sohprops ........ 56%   (o grego foi escrito copiando o sohprops, 2 dias depois)
rogerin × sohprops ...... 29%
grego × rogerin ......... 29%
todos os demais pares ... 16% a 35%
```

Logo: **um "motor único parametrizado" que substitua os perfis é fantasia.** O que é comum
é a *interface* (os 7 exportam as mesmas ~12 funções), não a implementação.

**2. O que dá para tirar do código é a parte DECLARATIVA.** No `grego.js` (982 linhas):

| Trecho | Linhas | Natureza |
|---|---|---|
| Cabeçalho documentando o formato medido | 134 | **o levantamento — é isto que custa as horas** |
| Prompt de visão (`SYSTEM`) | 79 | declarativo |
| Template do post (`formatarBilhete`) | 115 | declarativo |
| Regex de stake, emojis de marcação, linhas descartadas | ~100 | declarativo |
| `montarApostas` + `avisosMontagem` | ~234 | **lógica de verdade — continua em código** |

≈ **30% do perfil é declarativo** e cabe numa configuração. O resto segue sendo código —
mas escrito **em cima de um formato já medido e conferido pelo tipster**, que é onde a
ida-e-volta comigo mora hoje.

**3. O import do histórico é o maior item isolado.** O `import_grego_canal_s325.py` (883
linhas) tem **79 prints do canal transcritos à mão dentro do próprio script**. Nenhum
formulário resolve isso; um pipeline resolve.

---

## Parte 3 — as fases

Ordem escolhida por **risco crescente**: a primeira não muda nada do que já está no ar.

### Fase 1 — matar o deploy do tenant

**Problema:** pôr um tipster no ar exige editar `config.js`, editar o registro `PERFIS` do
`index.js`, criar 5 env vars no Railway e fazer deploy. O guard de boot é fail-closed com
`restartPolicyType = ALWAYS`: esquecer uma linha derruba **o bot inteiro** em crash-loop,
não só o tenant novo.

**Solução:** o registro do tenant sai das env vars e vira **tabela no Postgres**, lida pelo
bot no boot e recarregável a quente. Os ids param de ser digitados: `/vincular <código>` no
apoio resolve sozinho — o bot já sabe o próprio `chat.id`, e ele chega **já migrado** (o id
de supergrupo que quebrou a s316 nasce certo).

**Fica de pé, sem exceção:**
- O `SHARPEN_BOT_TOKEN` continua sendo um só, e as três condições de `auth.dono_do_bot`
  (token · dono `ativo` · `bot_habilitado`) continuam valendo.
- Os 7 tenants atuais continuam subindo pelas env vars enquanto a tabela não os tiver —
  migração por tenant, nunca de uma vez.
- O `perfil` continua sendo o nome de um arquivo `.js`. Esta fase **não toca em perfil**.

**Gate:** um tenant novo entra e sai do ar **sem push nenhum**, e derrubar a tabela não
derruba os que já estão no ar.

### Fase 2 — a página de configuração

Tela em `sharpen.bet` que o tipster preenche depois de aprovado. Cada campo com o "por quê"
ao lado e, onde a dúvida é de domínio (unidade, %, ROI, gestão), resposta da IA na própria
tela — sem abrir chamado com a gente.

Coleta: marca pública · admins que postam (vira a coluna `Tipster` por autor) · gestão
(unidade ou % da banca) · apoio e canal (por `/vincular`) · casas que ele usa.

**Confere sozinho, antes de nos mostrar:** o bot está nos dois chats · é admin no canal com
`can_post_messages` **e** `can_edit_messages` · o apoio é grupo e o destino é canal · o
username do cadastro existe e está `ativo` · a marca não colide com slug existente.

Chega para nós como **uma tela de aprovação**, com o que ele preencheu, o que o sistema
conferiu e **só as decisões que são nossas** (prefixo, semente do contador, casa nova).

**Gate:** um tipster que nunca falou com a gente consegue chegar até a fila de aprovação
sem pedir nada por mensagem.

### Fase 3 — o quebra-cabeça do formato

O tipster **cola 30 mensagens reais** do canal (ou sobe o export do Telegram). O sistema lê
e mostra, **lado a lado com a mensagem original, o que entendeu**: quantas apostas, qual a
stake de cada uma, qual a seleção, qual a casa, qual o resultado.

Ele **corrige apontando** — "essa stake é 1,25u, não 12,5", "essa linha não é aposta, é
aviso de bônus", "essas três são simples, não uma múltipla". Cada correção reescreve a
spec. Quando N mensagens seguidas saem certas sem correção, **fecha** e vai para a fila.

O que sai da spec e entra no código sem eu perguntar nada: regex de stake, emojis de
marcação, linhas descartadas, prompt de visão, template do post, prefixo, gestão. O que
continua sendo código escrito por nós: `montarApostas` e `avisosMontagem`.

**Duas armadilhas que a spec tem de cobrir por desenho, porque já custaram bilhete:**
- **A amostra diz o que ele FEZ, não o que ele FAZ.** Casa observada nunca entra no prompt
  como condição — vira `NOMES_CASAS` + `"casa"` no JSON de saída. Senão casa nova é lida
  como print ilegível.
- **`1 print = 1 bilhete` é hipótese, não regra.** N simples num print só viram uma múltipla
  sem erro nenhum. A tela tem de perguntar isso explicitamente.

**Gate:** replay dos perfis atuais contra a spec — o formato de um tipster que já está no ar
tem de ser descrito pela spec nova e produzir o mesmo post, bilhete a bilhete.

### Fase 4 — import do histórico em autosserviço

Upload de CSV/XLSX **ou** do export do Telegram, com mapeamento assistido de colunas,
prévia do que vai entrar e aprovação nossa antes de gravar.

**Bloqueador conhecido:** item **B2** do `BACKLOG.md` — hoje arrastar 3 planilhas processa a
primeira e evapora as outras duas, sem card, alerta ou log (`index.html:5324` manda
`xlsFiles[0]`). Isso é pré-requisito, não detalhe.

**Fica de pé:** a semente do contador continua nossa. Código já usado pela planilha e
reusado pelo bot é absorvido pelo UPSERT — sem erro, sem aviso, sem linha nova.

---

## O que este plano NÃO promete

- **Não elimina a nossa aprovação.** Ela encolhe de horas para minutos, e passa a ser sobre
  decisão, não sobre descoberta.
- **Não elimina o código por tipster.** A fase 3 encolhe o perfil em ~30% e tira de mim o
  levantamento do formato — que é a parte cara. `montarApostas` continua sendo escrita.
- **Não vale para o tipster que ainda não postou nada.** Todo perfil nasce de um export
  medido; sem amostra não há o que inferir.

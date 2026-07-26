# SharpenUp — arquitetura da captura

> **O que é:** referência de como a extensão captura bilhetes e como uma casa se liga ao
> sistema. Documento de **mapa**, não de regra: as regras de domínio vivem nos
> `global/MASTER_*`, as de marca no `pack/CLAUDE.md`, e **o código é a verdade** — ao mudar
> o comportamento, atualize este mapa na mesma sessão.
>
> **Para CRIAR uma casa nova, siga o procedimento:** [`GUIA_CASA_SHARPENUP.md`](GUIA_CASA_SHARPENUP.md).
> **Gate determinístico:** `python tools/audit_sharpenup.py`.
> **Regressão:** `node extensor/harness/run.mjs`.

---

## 1. O caminho de um bilhete

```
   casa (site)
      │  a página baixa o próprio histórico (fetch/XHR)
      ▼
  ┌───────────────┐   window.postMessage        ┌──────────────┐
  │ xx_inject.js  │ ──────────────────────────► │  content.js  │
  │ mundo MAIN    │ ◄────────────────────────── │ mundo isolado│
  │ hook + replay │   {__sharpenupXXReq}        │ robô + texto │
  └───────────────┘                             └──────┬───────┘
                                                       │ chrome.runtime
                                                       ▼
                                              ┌─────────────────┐
                                              │  background.js  │
                                              └────────┬────────┘
                                                       │ POST /captura/enviar (token)
                                                       ▼
                                    ┌──────────────────────────────────┐
                                    │ app/captura.py  (sessão efêmera) │
                                    └────────────────┬─────────────────┘
                                                     │ poll + drenar
                                                     ▼
                                    ┌──────────────────────────────────┐
                                    │ dashboard → /extrair → IA → TSV  │
                                    │ chunking · pré-dedup · cobertura │
                                    └──────────────────────────────────┘
```

**Por que dois mundos:** o `content.js` roda isolado e **não enxerga o `fetch` da página**.
Quem intercepta a resposta da API tem de rodar no mundo `MAIN` — daí o `xx_inject.js`.
Eles só conversam por `postMessage`.

**O que a extensão NÃO faz:** decidir W/L/V, traduzir mercado, calcular P/L. Ela entrega
**texto cru e fiel** (com o marcador `[Código: …]`); quem interpreta é a IA com os
`global/MASTER_*` + `casas/CASA_*.md`. Regra da casa: *cálculo é global, localização é da casa*.

---

## 2. Modos de captura

| Modo | Quando | Custo | Precisão |
|---|---|---|---|
| **API passiva** | a página baixa a lista inteira ao rolar/paginar | baixo | máxima (JSON exato) |
| **API + replay** | a lista pagina, ou tem abas, ou o scroll não dispara | baixo | máxima |
| **Navegação por rota** | o detalhe só existe atrás de um clique e o token rotaciona (bet365) | médio | máxima |
| **Texto (DOM)** | não há API legível, mas o card inteiro está no DOM | baixo | boa |
| **Print (moldura + Snap)** | nada acima serve — é o default de toda casa nova | alto (OCR) | depende do print |

> **Lição da s192 (KTO):** o robô de texto genérico (`roboScroll`) parte o `innerText` por
> **linha em branco**. Se a lista da casa não tiver linha em branco entre bilhetes, os ~140
> cupons viram **um bloco só** com menu e rodapé — a IA lê os primeiros e **perde o resto em
> silêncio**. Antes de escolher "texto", confira essa fronteira. Quase sempre a resposta certa
> é *"vir por trás, pelo F12"*.

---

## 3. Contrato de mensagens (inject ⇄ content)

Toda casa segue o mesmo formato — mudam só as duas letras do prefixo.

**inject → content** (sempre, mesmo com 0 bilhetes — é o heartbeat do autodiagnóstico):

```js
window.postMessage({
  __sharpenupXXData: true,
  hook: true,          // o inject carregou (distingue de "endpoint mudou")
  respostas: 12,       // respostas do endpoint que o hook viu
  <lista>: [...],      // bets / tickets / items / cupons — normalizados
  fim: false,          // fim AUTORITATIVO (a casa disse que acabou), não heurística
}, "*");
```

**content → inject** (o robô pede o acumulado e arranca o replay):

```js
window.postMessage({ __sharpenupXXReq: true, /* dias, limite… */ }, "*");
```

Regras que valem para todos:

1. **Re-enviar sob demanda.** A 1ª página chega no `load`, antes de o content estar
   ouvindo. Sem o `Req`/`enviar()`, ela se perde.
2. **`hook` + `respostas` sempre.** É o que separa "não injetei" de "endpoint mudou" de
   "conta vazia" no autodiagnóstico. Sem isso, falha de captura vira silêncio.
3. **Resolvida vence aberta.** O mesmo bilhete pode voltar nas duas abas; o dado final é
   o liquidado.
4. **`fim` só quando a CASA disse que acabou** (`more:false`, `LastId` ausente,
   `moreAvailable:false`). Teto de tempo é rede de segurança, não critério.
5. **O inject não decide nada.** Ele normaliza campos crus. Status desconhecido sobe cru —
   nunca vira W/L por chute.

---

## 4. Casas de captura hoje

| Casa | Modo | Endpoint | Inject | Chave de dedup | Fim autoritativo | Data que vai pro TSV |
|---|---|---|---|---|---|---|
| **Superbet** | API passiva | `GET /user/<id>/tickets?status=finished\|active` | `sb_inject.js` | `ticketId` | 5 rolagens sem novo | evento mais recente (UTC→SP) |
| **BETesporte** | API passiva | `POST /api/bet/RequestUserTickets` | `be_inject.js` | `id` | 5 s sem novo | `date` (já local) |
| **Betano** | API passiva | `GET /api/ma/bet/bet-history-v3?settled=` | `bn_inject.js` | `BetId` | página sem `LastId` | `PlacedAt` (UTC→SP) |
| **Betfair** | API + replay | `POST /activity/sportsbook` | `bf_inject.js` | `betId` `O/…` | `moreAvailable:false` | `settledDate` (já local) |
| **Pinnacle** | API + replay | `POST /member-service/v2/wager-filter` | `pn_inject.js` | `id` (array posicional!) | replay das 2 abas | data do evento |
| **KTO** | API + replay | `GET /coupon/history.json` (Kambi) | `kto_inject.js` | `couponRef` | `range.more:false` | `placedDate` (UTC→BRT) |
| **Bet365** | rota (`location.hash`) | `/sportshistoryapi/summary` + `/confirmation` | `b3_inject.js` | `BR` (do confirmation) | fim + 0 sem código | kickoff + folga, UK→BR |
| **Tivo** | API + replay (1 chamada) | `POST /api/game/p/messagetosport` (`gethistory`) | `tv_inject.js` | `ID` | `Error:null` + `len == Count` | evento mais recente (UTC→SP) |

Freios no popup: **dias + ID de parada** (Superbet/BETesporte/Betano/KTO/Pinnacle/Tivo) ·
**quantidade + dias + varrer tudo** (Betfair, histórico ilimitado e fora de ordem) ·
**nenhum** (Bet365 — o freio virou o pré-dedup do backend).

---

## 5. Superfície de registro — os 12 pontos

Uma casa nova só funciona ponta a ponta se estiver em **todos** os lugares abaixo. Não há
um registro único: são listas paralelas que precisam concordar. **Rode
`python tools/audit_sharpenup.py` para conferir** — foi construído exatamente para isso.

| # | Onde | O quê | Se faltar |
|---|---|---|---|
| 1 | `casas/CASA_<KEY>.md` | tradução fina (15 seções) | roda em modo cego (funciona, traduz pior) |
| 2 | `app/main.py` `_CASA_DISPLAY` | `"KEY": "Nome Canônico"` | casa não existe para o sistema |
| 3 | `app/main.py` tupla do `_build_chunks` | `"KEY"` | fatia pelo frágil `\n\n` em vez do `[Código:]` |
| 4 | `app/main.py` tupla do pré-dedup | `"KEY"` | paga IA de novo por bilhete já resolvido |
| 5 | `app/repository.py` regex de código | formato do `[Código: …]` | **conferência de cobertura desligada** (perda silenciosa de chunk passa batido) |
| 6 | `app/captura.py` `_MODO_POR_CASA` | `"KEY": "texto"` | a extensão cai em modo print |
| 7 | `app/captura.py` `_HOSTS_POR_CASA` | domínios | backstop casa↔site cego no servidor |
| 8 | `app/static/index.html` `CASAS_CONECTAVEIS` | `'KEY'` | **botão "Conectar" nasce desabilitado — nada roda** (s191) |
| 9 | `app/static/index.html` `NOMES` + `DOMINIOS` | chave e domínio | seletor/favicon quebrados |
| 10 | `app/static/dash/.../data.js` + `inicio.html` | favicon (3 mapas) | ícone quebrado no dashboard/início |
| 11 | `extensor/popup.js` | `CASA_HOSTS` + dispatch do inject | aba já aberta não injeta; sem aviso de aba errada |
| 12 | `extensor/manifest.json` | `content_scripts` + **bump da `version`** | não injeta no load; ninguém vê que há versão nova |

E, dentro do `extensor/content.js`: **ouvinte** da mensagem, **`formatTicketXX`**, **`roboXXPassive`**,
**ramo no `iniciarRobo`** e **entrada no mapa de autodiagnóstico**.

---

## 6. Backend da ponte

- Sessão **em memória** (`app/captura.py`): código `ABCD-EFGH` válido 15 min para conectar,
  sessão viva 6 h, fila de 60 capturas. Restart do Railway derruba as pontes — reconectar.
- `POST /captura/conectar` → `{token, casa, parceiro, modo, dono, versao_atual, desatualizada}`
- `POST /captura/validar` → o popup só diz "conectado" se a sessão existe de fato.
- `POST /captura/enviar` → `token` + `tipo=imagem|texto` + `origem` (host, backstop casa↔site).
- As três são isentas do guarda CSRF (autenticam por código/token).

## 7. Depois da ponte: o que protege o dado

| Guarda | Onde | O que evita |
|---|---|---|
| Pré-dedup por `[Código:]` | `main.py::_dedup_superbet_text` | pagar IA por bilhete já resolvido |
| Chunking por `[Código:]` | `main.py::_build_chunks` | lote grande num request só |
| **Conferência de cobertura** | `repository.py::conferir_cobertura` | **chunk que some sem erro** (s179: 39 de 61 bilhetes) |
| Correção de código | `repository.py::corrigir_codigos_tsv` | ID transposto pela IA virando duplicata |
| UPSERT por código | `repository.py::upsert_bilhetes` | aberta→resolvida atualiza, não duplica |

> A conferência de cobertura só liga se o formato do código for reconhecido (ponto 5). É a
> proteção mais barata do pipeline e a mais fácil de esquecer.

---

## 8. Limites conhecidos (dívida estrutural)

1. **`content.js` roda em TODA página** (`matches: http://*/*`) e já tem 119 KB. Cada casa
   soma ~150 linhas ao mesmo arquivo. Em ~20 casas isso é ~300 KB parseados em todo site que
   o operador abrir. Candidato a `chrome.scripting.registerContentScripts` por host.
2. **7 blocos quase idênticos** (ouvinte + formatador + robô) — ~60 % do arquivo é o mesmo
   laço com nomes trocados. Um `roboPassivoGenerico({chave, mapa, fim, formatar})` colapsaria
   isso e faria casa nova custar ~30 linhas.
3. **Os `*_inject.js` repetem o mesmo esqueleto** (hook de fetch/XHR + `postAll` + `seen`).
   `sb/be/bn_inject` são o mesmo arquivo com 4 diferenças.
4. **Os ouvintes de `message` não checam a origem.** Qualquer página poderia postar
   `__sharpenupXXData` com bilhetes forjados enquanto há pareamento ativo. Conserto barato:
   `if (ev.source !== window && ev.source !== window.top) return;`.
5. **Nenhum teste automatizado da extensão até a s192** — o harness em `extensor/harness/`
   é o começo; hoje cobre só a KTO.

---

VERSÃO: 2026
ATUALIZADO: 2026-07-25 (sessão 194)

# PLANO DE CONSTRUÇÃO — Scanner de Bets (FDC Capital)

## 1. O que o sistema é

Um sistema web que lê bilhetes de apostas (print da casa) e tips (Telegram), extrai para TSV no padrão FDC Capital, organizado por Casa + Parceiro, com sugestão automática de tipster vinda dos grupos do Telegram.

## 2. Princípios que não se quebram

1. O repo é a fonte única de verdade das regras. O app LÊ os MASTERs. Nunca escreve.
2. Nenhuma regra é aprovada sozinha. Git é a porta.
3. O ID do bilhete é a chave de dedup — escopada por (Casa, Parceiro).
4. Arquivar nunca é deletar.
5. O tipster é sugerido, nunca cravado sozinho.
6. Aposta aberta não entra na fila de cópia.
7. Captura é disparada por humano.

## 3. Stack

- Backend: FastAPI (Python)
- Banco: PostgreSQL no Railway
- Frontend: grade editável (padrão exportador Polymarket)
- API de extração: Claude API — Haiku 4.5 padrão, Sonnet 4.6 por escalonamento, Opus só para evolução de regra
- Captura: extensão Octo
- Telegram: TeleFeed (plano pago) + bot oficial

## 4. Estrutura do repo

```
/global/     — MASTER_TSV.md, MASTER_APOSTAS.md, MASTER_ESPORTES.md, MASTER_DESCRICAO.md, MASTER_RESULTADO.md
/casas/      — CASA_MODELO.md, CASA_SUPERBET.md, CASA_BET365.md, CASA_BETANO.md, ...
/golden_set/bilhetes/ — prints + TSV correto fixado
REGRAS_PENDENTES.md
STATUS.md
erros.jsonl
```

## 5. Modelo de dados

- Entidades: Casa, Parceiro, Workspace=(Casa,Parceiro), Tipster, Tip, Bilhete, Correção
- Campos do Bilhete: bilhete_id, assinatura, data, esporte, tipster, aposta, descricao, stake, odd, resultado, extraction_state, copy_state, confianca
- Estados ortogonais: extraction_state (aberta|resolvida) + copy_state (pendente|copiada)
- Dedup: por workspace, chave forte=bilhete_id ou assinatura derivada

## 6. Telegram → tipster

TeleFeed → canal(is) de coleta → bot oficial → webhook /tip-ingest

Granularidade dos canais: por bloco de stake-sinalização.

## 7. Ordem de construção (fases)

- **Fase 0** — Repo + base de conhecimento (semear golden_set)
- **Fase 1** — Núcleo de extração (endpoint /extrair, Haiku cacheado, validar golden set)
- **Fase 2** — Estado e banco (PostgreSQL, workspaces, estados duplos, upsert)
- **Fase 3** — Scanner UI (grade editável, copiar pendentes, arquivar)
- **Fase 4** — Captura (extensão Octo, box ajustável, botão flutuante)
- **Fase 5** — Telegram / tipster (TeleFeed, bot, webhook, matching, arquivamento)
- **Fase 6** — Inspetor + evolução de regra (eval golden set, mineração de erro, loop Claude Code)
- **Fase 7** — Scraper leve (opcional)

## 8. Decisões registradas

- Saída em TSV
- Haiku padrão, Sonnet por escalonamento, Opus só para regras
- Workspace = (Casa, Parceiro)
- Aposta aberta fora da fila
- Tipster carimbado pela origem do canal, confirmado por você
- TeleFeed (não userbot caseiro)
- App lê regras, nunca escreve; git é a porta
- Proteção contra obsolescência: versão travada, golden set como detector de drift, checador de catálogo
- Modelo pinado: `claude-haiku-4-5-20251001` (Haiku 4.5)
- Prompt caching nos 6 masters + arquivo de casa (7 blocos de sistema)
- Chave de API via variável de ambiente `ANTHROPIC_API_KEY` — nunca no código

## 9. Em aberto

- Divisão fina dos MASTERs globais
- Schema exato das tabelas
- Formato do erros.jsonl
- Quais casas entram primeiro além da Superbet
- Fórmula de score do matching tipster

## 10. Fase 1 — detalhamento técnico

### Arquivos planejados para `app/`

```
app/
├── main.py          ← FastAPI + endpoint POST /extrair
├── prompts.py       ← carrega os .md e monta o system prompt
├── config.py        ← MODEL_ID e constantes (sem lógica)
├── requirements.txt ← fastapi, uvicorn[standard], anthropic, python-multipart
└── static/
    └── index.html   ← UI descartável de teste
```

### Montagem do system prompt (7 blocos)

```
Bloco 1  MASTER_PIPELINE_2026.md
Bloco 2  MASTER_ESPORTES_2026.md
Bloco 3  MASTER_APOSTAS_2026.md
Bloco 4  MASTER_DESCRICAO_2026.md
Bloco 5  MASTER_RESULTADO_2026.md
Bloco 6  MASTER_OUTPUT_2026.md
Bloco 7  CASA_<casa>.md  ← cache_control: {"type":"ephemeral"} aqui
```

Mensagem do usuário (sem cache): instrução curta + inputs (imagens base64 + texto livre).

### Modelo pinado

`claude-haiku-4-5-20251001`

---

VERSÃO: 2026
CRIADO: 2026-06-13 (sessão 9)

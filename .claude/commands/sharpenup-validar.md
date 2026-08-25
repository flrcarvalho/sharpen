---
description: Gate antes do commit da extensao - harness, registro das casas, sintaxe, testes e checklist
argument-hint: "[casa]  opcional - default: tudo"
allowed-tools: Bash(node:*), Bash(python:*), Bash(git status:*), Bash(git diff:*), Read, Grep, Glob
---

# Validar a captura: $ARGUMENTS

Gate obrigatorio antes de qualquer commit que toque `extensor/` ou o caminho de captura
no backend. Read-only: **nao corrige nada sem aprovacao**. Rode tudo, depois reporte.

## 1. Gates deterministicos (rode todos, mesmo se um falhar)

```
node extensor/harness/run.mjs $ARGUMENTS
python tools/audit_sharpenup.py
python tools/audit_casas.py
python tools/audit_changelog.py
node --check extensor/content.js
node --check extensor/popup.js
node --check extensor/background.js
node -e "JSON.parse(require('fs').readFileSync('extensor/manifest.json','utf8'));console.log('manifest ok')"
python -m py_compile app/main.py app/captura.py app/repository.py
python -m pytest tests/ -q
```

Rode tambem `node --check` em cada `*_inject.js` tocado. Se a mudanca encostou em UI,
`node scripts/tokens/check-tokens.mjs`.

Mostre a saida integral de cada FAIL. Para cada um, diga **o que corrigir e onde**.

## 2. Checklist de revisao (o que script nenhum pega)

Leia o diff (`git diff`) e confira item a item:

- [ ] **`manifest.json` com `version` bumpada** — sem isso ninguem e avisado da versao nova.
- [ ] **Nota da versao nova no changelog da home** — `python scripts/avisar_testers.py --versao <X.Y.Z> ...`
      publica no grupo E grava em `app/changelog.json` no mesmo ato. O `audit_changelog` acima
      fica vermelho enquanto a versao publicada nao tiver nota.
- [ ] Inject emite `hook:true` + `respostas` **mesmo com 0 bilhetes** (senao falha vira silencio).
- [ ] Inject **re-envia sob demanda** (`__sharpenupXXReq`) — a 1a pagina chega antes do content ouvir.
- [ ] Replay usa o `fetch` **original** guardado, nao o wrapper.
- [ ] Fim da paginacao vem do **sinal da casa**; tempo e so rede de seguranca.
- [ ] `formatTicket*`: `[Codigo:]` na 1a linha · aberta sem resultado · retorno de aberta
      rotulado como **potencial** · status desconhecido "a conferir" · **odd sem truncar**,
      decimal com virgula · W = `retorno / stake`.
- [ ] Janela de dias corta **so resolvidas**; aberta nunca corta.
- [ ] Nenhuma decisao de W/L/V dentro da extensao (o de-para vive na `CASA_*.md`).
- [ ] Casa nova tem entrada em `CODIGO_EXEMPLO` (`tools/audit_sharpenup.py`).
- [ ] Backup feito em `Backups/<nome-descritivo>/`, so dos arquivos editados.
- [ ] Armadilha nova descoberta virou linha no caso do harness (senao ela volta).

## 3. Regressao das casas que ja funcionavam

Se a mudanca tocou `content.js` ou `main.py`, confirme que as outras casas nao regrediram:
o harness cobre as que tem caso; para as demais, cite explicitamente quais **nao** tem
cobertura automatizada e portanto seguem dependendo de teste ao vivo.

## Ao final

Resuma: N gates verdes, N FAIL, N itens do checklist pendentes. Se houver FAIL, **nao
sugira commitar** — proponha a correcao e aguarde. Se tudo verde, diga o que ainda
depende de validacao ao vivo (recarregar extensao + Ctrl+Shift+R na aba da casa).

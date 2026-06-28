# Guia: Cadastrar Nova Casa

> Seguir esta ordem exata. Todas as etapas são obrigatórias.
> Uma mudança por vez — propor, confirmar, executar.

---

## Pré-requisitos

- Nome canônico da casa (ex.: `KingPanda`, `Superbet`)
- Domínio do site (ex.: `kingpanda.bet.br`)
- Pelo menos 3 bilhetes reais: W simples, L simples, Múltipla

---

## Etapa 1 — Backup

Antes de editar qualquer arquivo existente:

```powershell
$dest = "Backups\pre_<nomecasa>_<data>"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item app\main.py "$dest\main.py"
Copy-Item app\static\index.html "$dest\index.html"
```

---

## Etapa 2 — Criar `casas/CASA_<NOME>.md`

Copiar o template `casas/CASA_MODELO.md` e preencher as 15 seções:

| Seção | O que preencher |
|---|---|
| §1 Identidade | Nome canônico · domínio · locale · formato decimal |
| §2 Ingestão | Modo (texto colado / screenshot / export) · anatomia do bilhete · **regra de ordem do output** |
| §3 ID | Visível / ausente / fonte separada · formato · localização |
| §4 Data | Fonte primária (evento) · fallback · desambiguação se houver duas datas |
| §5 Status | Rótulos da casa → `W / L / V / HW / HL` · conferência financeira |
| §6 Boost | Tem ou não · localizador visual |
| §7 Cashout | Tem ou não · localizador |
| §8 Bônus | Tem ou não · política |
| §9 Mapa de mercados | **Só os mercados confirmados** em bilhete real → categoria do `MASTER_APOSTAS_2026 §3`. **Não** listar as 27 categorias nem "aguarda amostra" (ver formato abaixo) |
| §10 Stake | Campo · formato numérico (pt-BR vírgula vs en-US ponto) |
| §11 Odds | Campo principal · regra por resultado (`W / L / V / HW / HL / cashout`) |
| §12 Ruído | Elementos visuais a ignorar |
| §13 Pegadinhas | Erros prováveis específicos desta casa |
| §14 Validações | Checagens específicas (transversais já no template — não remover) |
| §15 Goldens | ≥3 bilhetes reais com TSV esperado; odds cross-checked; em **output order** (último no texto = primeira linha) |

**Nome do arquivo:** `casas/CASA_<NOME_MAIÚSCULO>.md`
Ex.: `CASA_BETANO.md`, `CASA_KINGPANDA.md`, `CASA_NOVAHOUSE.md`

### Formato obrigatório do §9 (camada fina)

```markdown
| <Casa> exibe (rótulo real) | Aposta global |
|---|---|
| `Ambos times marcam` | Ambas Marcam |
| `Vencedor da partida` | ML |
```

- Coluna 1: o **rótulo exato** que a casa exibiu num bilhete real
- Coluna 2: categoria global do `MASTER_APOSTAS_2026 §3` — sempre uma das 27 oficiais
- **Listar APENAS mercados confirmados.** Não cobrir as 27 categorias; não usar linhas `(aguarda amostra)`.
- **Por quê:** as 27 categorias já vivem no `MASTER_APOSTAS_2026 §3`, carregado no prompt em toda extração — repeti-las por casa é duplicação morta que gera drift quando o global muda. A casa só traduz o que ela fala.
- Mercado sem categoria adequada → `Outros` ⚠️ + registrar no §Feedback.

### Regra de ordem do output (§2)

O grid/texto das casas normalmente exibe apostas do mais recente (topo) para o mais antigo (baixo).
O TSV deve sair na ordem **inversa**: último no texto = primeira linha; primeiro no texto = última linha.
Documentar no §2 o padrão específico da casa (grid de colunas, lista vertical, etc.).

---

## Etapa 3 — Registrar em `app/main.py`

Localizar `_CASA_DISPLAY` e adicionar em **ordem alfabética**:

```python
_CASA_DISPLAY: dict[str, str] = {
    "BET365":    "Bet365",
    "BETANO":    "Betano",
    "BETFAIR":   "Betfair",
    "KINGPANDA": "KingPanda",
    "NOVACASA":  "NovaCasa",   # ← adicionar aqui
    "PINNACLE":  "Pinnacle",
    "SUPERBET":  "Superbet",
}
```

- Chave: `NOME_MAIÚSCULO` (como o usuário digita no seletor)
- Valor: nome canônico exato (vai direto na coluna `Casa` do output TSV)

---

## Etapa 4 — Registrar em `app/static/index.html`

Localizar `NOMES` e `DOMINIOS` e adicionar:

```js
const NOMES = {
  ...,
  NOVACASA: 'NovaCasa',          // chave MAIÚSCULA · valor = nome canônico
};
const DOMINIOS = {
  ...,
  NovaCasa: 'novacasa.com.br',   // chave = nome canônico · valor = domínio para favicon
};
```

**Atenção às chaves:**
- `NOMES`: chave `MAIÚSCULA` (igual à chave em `_CASA_DISPLAY`)
- `DOMINIOS`: chave `CamelCase` (igual ao valor canônico — ex.: `KingPanda`, `Bet365`)

---

## Etapa 5 — Commit + push

```powershell
git add casas/CASA_NOVACASA.md app/main.py app/static/index.html
git commit -m "feat(CASA_NOVACASA): adiciona NovaCasa como nova casa" `
           -m "- casas/CASA_NOVACASA.md: 15 secoes, N goldens reais" `
           -m "- app/main.py: NOVACASA adicionado ao _CASA_DISPLAY" `
           -m "- app/static/index.html: NovaCasa adicionado a NOMES e DOMINIOS"
git push
```

Deploy automático via Railway (push em `main`).

---

## Etapa 6 — Atualizar `STATUS.md`

Adicionar entrada na sessão atual com:
- O que foi criado
- IDs dos goldens
- Pendências documentadas (§5 HW/HL, §7 cashout, §8 bônus se não confirmados)
- Hash do commit

---

## Checklist rápido

- [ ] Backup criado em `Backups/pre_<casa>_<data>/`
- [ ] `casas/CASA_<NOME>.md` criado (15 seções preenchidas, goldens verificados)
- [ ] §9 lista só mercados confirmados (sem 27 categorias, sem "aguarda amostra"); categorias ⊆ MASTER_APOSTAS §3
- [ ] `app/main.py` → `_CASA_DISPLAY` atualizado (ordem alfabética)
- [ ] `app/static/index.html` → `NOMES` + `DOMINIOS` atualizados
- [ ] Commit + push realizados
- [ ] `STATUS.md` atualizado

---

## Referência rápida de padrões

| Aspecto | Padrão |
|---|---|
| Nome do arquivo | `casas/CASA_<MAIÚSCULO>.md` |
| Nome canônico | CamelCase exato: `KingPanda`, `Bet365`, `Superbet` |
| Chave `_CASA_DISPLAY` | `"MAIÚSCULO"` |
| Chave `NOMES` (HTML) | `MAIÚSCULO` (sem aspas de objeto JS) |
| Chave `DOMINIOS` (HTML) | `CamelCase` (igual ao nome canônico) |
| §9 colunas | `Casa exibe (rótulo real) \| Aposta global` — só mercados confirmados |
| Goldens: ordem | Último no texto/grid = primeira linha do TSV |
| Goldens: separador | TAB real (U+0009) — nunca espaços |
| Goldens: decimal | Vírgula (`2,76`) — nunca ponto |
| Backup | `Planilhador/Backups/pre_<casa>_<data>/` — nunca em `FDC Capital/Backups/` |
| Push | Sempre imediato após o commit (deploy Railway automático) |

---

VERSÃO: 2026
ATUALIZADO: 2026-06-20

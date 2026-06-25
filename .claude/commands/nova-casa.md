---
description: Cadastro guiado de casa nova (camada fina) - arquivo, registro no app, backup, audit, commit
argument-hint: "<NomeCanonico> <dominio>  (ex.: KTO kto.bet.br)"
allowed-tools: Bash(git:*), Bash(python tools/audit_casas.py:*), Bash(cp:*), Bash(mkdir:*), Read, Write, Edit, Grep, Glob
---

# Cadastrar nova casa: $ARGUMENTS

Siga `GUIA_NOVA_CASA.md`. Uma etapa por vez: propor -> aguardar confirmacao -> executar.
Tudo em pt-BR. Terminal = PowerShell (sem heredoc bash).

**Pre-requisito:** ao menos 3 bilhetes reais ja fornecidos pelo usuario (W simples, L simples, Multipla).
Se nao houver, pare e peca.

## 1. Backup
- Criar `Backups/pre_<casa>_<AAAA-MM-DD>/` e copiar `app/main.py` e `app/static/index.html`.

## 2. casas/CASA_<MAIUSCULO>.md (CAMADA FINA — nao redefinir o global)
- Espelhar a estrutura de `casas/CASA_MODELO.md` (15 secoes).
- **§9:** SO mercados confirmados num bilhete real -> categoria do `MASTER_APOSTAS_2026 §3`.
  NAO listar as 27 categorias. NAO usar linhas `aguarda amostra`. Mercado sem categoria -> `Outras` ⚠️ + §Feedback.
- **§14:** ponteiro `> **Transversais ...**` (MASTER_PIPELINE §8 + MASTER_OUTPUT §17-18) + so validacoes especificas da casa.
- **§5:** traduzir rotulos da casa para W/L/V/HW/HL (nunca copiar sinal visual cru).
- **§15:** goldens reais em output order (ultimo no texto = 1a linha), TAB real entre colunas,
  decimal virgula, odd cross-checked (W: retorno/stake).
- Cada decisao ambigua do dono entra como nota no §13/§Feedback.

## 3. Registro no app
- `app/main.py` `_CASA_DISPLAY`: `"<MAIUSCULO>": "<NomeCanonico>"` em ordem alfabetica.
- `app/static/index.html`: `<MAIUSCULO>` em `NOMES` e `<NomeCanonico>` em `DOMINIOS` (= `<dominio>`).

## 4. Auditoria (gate)
- `python tools/audit_casas.py CASA_<MAIUSCULO>.md` -> tem que sair **sem FAIL**.
- Se falhar, corrigir antes de seguir.

## 5. STATUS + commit + push
- Atualizar `STATUS.md`: o que criou, IDs dos goldens, pendencias (§5 V/HW/HL, §7 cashout, §8 bonus), hash.
- `git add` os arquivos tocados -> `git commit` (Conventional Commits, multiplos -m) -> `git push`.
- Deploy automatico via Railway. Registrar o hash no STATUS.

## Ao final
- Confirmar em 1 linha: casa criada, N goldens, audit OK, commit <hash> enviado.

# RUNBOOK — "Sugerir tipsters" parou de sugerir

> Procedimento. A **regra** vive no [`CLAUDE.md`](../CLAUDE.md) § *"Sugerir tipsters parou?"*:
> o matcher só sugere com folga ≥ 7 e **fica vazio de propósito em empate**, então a
> regressão não gera erro nenhum — ela emudece. Um perfil novo pode matar um perfil antigo
> em silêncio.

O matcher é o `_sugParaBilhete`, inline no `app/static/index.html`.

## Diagnóstico, nesta ordem

**1. Olhe os perfis recentes antes do código.**

```sql
select nome, criado_em from tipsters where dono = '<dono>' order by criado_em desc limit 5
```

Perfil criado ou editado nos últimos dias é o primeiro suspeito. O parser deriva o
**final** de todo valor não-redondo (`49 → 9`, `99 → 9`), então dois perfis podem virar
donos do mesmo final e se anularem.

**2. Prove por remoção, não por dedução.**

Extraia o bloco JS do `index.html`, rode em node contra os perfis e bilhetes **reais** do
banco, e compare o resultado **com e sem** o perfil suspeito. Isola a causa sem editar
nada. Esta é a parte que não se negocia: dedução sobre peso de matcher erra, e a remoção
responde em uma rodada.

**3. Só então mexa no peso — e meça.**

Backtest contra bilhetes já rotulados, antes e depois. Use holdout **temporal**: assinatura
tem ERA, e backtest in-sample pune o acerto de hoje com bilhete velho
(`scripts/backtest_matcher.py`).

## O que não se toca sem medir

Dois cortes da calibragem de stake são load-bearing, e tirar qualquer um **já quebrou o
matcher em produção**:

- **valor redondo** (50/100/250/800) não é digital, é valor comum;
- **`valores.size === 1`** separa "este valor É minha assinatura única" de "é um dos vários
  que aposto".

→ [o caso](CASOS.md#os-dois-cortes-que-já-quebraram-o-matcher-em-produção) ·
[o perfil novo que matou o antigo](CASOS.md#o-perfil-novo-que-matou-o-antigo--multilbb--lbb) ·
[assinatura tem ERA](CASOS.md#assinatura-tem-era)

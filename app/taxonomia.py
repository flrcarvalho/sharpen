"""Taxonomia canônica — esportes e categorias — LIDA dos MASTERs, nunca espelhada.

Fonte de verdade:
  · esportes   → `global/MASTER_ESPORTES_2026.md` §7 (Tabela Oficial de Normalização)
  · categorias → `global/MASTER_APOSTAS_2026.md`  §3 (Tabela Oficial de Categorias)

**Por que ler em vez de copiar:** a alternativa era uma lista embutida no código, que vira
mais uma linha da regra de propagação do CLAUDE.md — e regra escrita sem gate é regra
pulada. Aqui, categoria criada no MASTER aparece no menu sem ninguém lembrar de nada.

O preço é o parse: se o MASTER mudar de forma (renumerar a seção, trocar a tabela por
lista), a extração devolve vazio **em silêncio** — a mesma família de falha que este
módulo existe para consertar. Por isso `tests/test_taxonomia.py` trava âncoras conhecidas
e um piso de tamanho: MASTER reformatado quebra o CI, não o menu do usuário.

Uso: `esportes_canonicos()` / `categorias_canonicas()`. Ambos cacheados (o arquivo só
muda em deploy).
"""

import re
from functools import lru_cache

from config import GLOBAL_DIR

# `## Nome` — só H2 (H3 é subseção: "### Regra Crítica — …", "### Referências auxiliares")
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
# `# 7. Título` — H1 numerado delimita a seção. O `.*$` faz o recorte começar DEPOIS da
# linha inteira do título: sem ele o texto do próprio título entrava na seção.
_H1 = re.compile(r"^#\s+(\d+)\.\s.*$", re.MULTILINE)
# linha de tabela: `| Categoria | Descrição |`
_LINHA_TABELA = re.compile(r"^\|\s*([^|]+?)\s*\|", re.MULTILINE)


def _ler(nome: str) -> str:
    try:
        return (GLOBAL_DIR / nome).read_text(encoding="utf-8")
    except OSError:
        return ""


def _secao(texto: str, numero: str) -> str:
    """Recorta a seção `# <numero>. …` até o próximo H1 numerado (ou o fim)."""
    inicio = None
    for m in _H1.finditer(texto):
        if inicio is None and m.group(1) == numero:
            inicio = m.end()
        elif inicio is not None:
            return texto[inicio:m.start()]
    return texto[inicio:] if inicio is not None else ""


@lru_cache(maxsize=1)
def esportes_canonicos() -> tuple[str, ...]:
    """Valores válidos da coluna `Esporte`, na ordem do MASTER.

    São os H2 da §7 — cada um é o nome canônico exato (`Futebol`, `eSoccer`, `Hóquei`…).
    `Outro` fecha a lista: é válido (§3) mas não tem seção própria na §7.
    """
    nomes = _H2.findall(_secao(_ler("MASTER_ESPORTES_2026.md"), "7"))
    vistos, out = set(), []
    for n in nomes + ["Outro"]:
        if n not in vistos:
            vistos.add(n)
            out.append(n)
    return tuple(out)


@lru_cache(maxsize=1)
def categorias_canonicas() -> tuple[str, ...]:
    """Valores válidos da coluna `Aposta` (mercado), na ordem do MASTER.

    Primeira coluna da tabela da §3, fora o cabeçalho (`Categoria`) e o separador (`---`).
    """
    out, vistos = [], set()
    for c in _LINHA_TABELA.findall(_secao(_ler("MASTER_APOSTAS_2026.md"), "3")):
        c = c.strip()
        if not c or c == "Categoria" or set(c) <= {"-", ":"} or c in vistos:
            continue
        vistos.add(c)
        out.append(c)
    return tuple(out)

#!/usr/bin/env python3
"""Auditoria de consistência casa × global (FDC Capital / Planilhador).

Checa, de forma determinística, a disciplina da "camada fina":
  1. Categorias órfãs   — categoria no §9 de uma casa que NÃO existe no
                          MASTER_APOSTAS_2026 §3 (categoria inventada/renomeada).
  2. Placeholder no §9  — linha "aguarda amostra" dentro do §9 (proibida na
                          camada fina; a lista de categorias vive só no global).
  3. Transversais cruas — bloco "**Transversais (todas as casas):**" com bullets
                          em vez do ponteiro "> **Transversais ...**".
  4. Registro no app    — casa sem entrada em app/main.py (_CASA_DISPLAY) ou em
                          app/static/index.html (NOMES).

Uso:
    python tools/audit_casas.py [CASA_X.md ...]   # default: todas as casas
Saída: relatório legível + exit code 1 se houver qualquer FAIL.
"""
import re
import sys
import pathlib

# Console Windows é cp1252 por padrão — forçar UTF-8 para imprimir →, §, ÷ etc.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASAS_DIR = ROOT / "casas"
MASTER_APOSTAS = ROOT / "global" / "MASTER_APOSTAS_2026.md"
MAIN_PY = ROOT / "app" / "main.py"
INDEX_HTML = ROOT / "app" / "static" / "index.html"

HEADING = re.compile(r"^## \d")


def categorias_oficiais() -> set[str]:
    """Lê a coluna 1 da tabela em MASTER_APOSTAS_2026 §3."""
    txt = MASTER_APOSTAS.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(txt) if l.startswith("# 3."))
    end = next(i for i in range(start + 1, len(txt)) if txt[i].startswith("# "))
    cats = set()
    for l in txt[start:end]:
        if l.lstrip().startswith("|"):
            cells = [c.strip() for c in l.split("|")[1:-1]]
            if len(cells) >= 2 and cells[0] not in ("Categoria", "") and set(cells[0]) != {"-"}:
                cats.add(cells[0])
    return cats


def norm_cat(s: str) -> str:
    """Reduz a célula de categoria ao(s) nome(s) canônico(s): tira ⚠️/markdown
    e qualquer nota entre parênteses (ex.: 'Outros (nicho)' → 'Outros')."""
    s = s.replace("⚠️", "").replace("`", "").replace("*", "")
    s = re.sub(r"\(.*?\)", "", s)  # remove notas entre parênteses
    return s.strip()


def categoria_valida(cell: str, oficiais: set[str]) -> str | None:
    """Retorna a categoria órfã se a célula não casar com o §3, senão None.
    Aceita combinações com '/' (ex.: 'Team Props / Gols')."""
    base = norm_cat(cell)
    if base in ("Aposta global", "") or set(base) <= {"-", ":"}:
        return None
    # delegação explícita ao global (ex.: 'seguir o nome → MASTER_APOSTAS') é válida
    if "MASTER_APOSTAS" in base:
        return None
    tokens = [t.strip() for t in base.split("/") if t.strip()]
    if tokens and all(t in oficiais for t in tokens):
        return None
    return base


def secao(linhas: list[str], num: int) -> tuple[int, int]:
    """Intervalo [ini, fim) da seção '## <num>.'."""
    ini = next((i for i, l in enumerate(linhas) if l.startswith(f"## {num}.")), None)
    if ini is None:
        return (-1, -1)
    fim = next((i for i in range(ini + 1, len(linhas)) if HEADING.match(linhas[i])), len(linhas))
    return (ini, fim)


def auditar_casa(path: pathlib.Path, oficiais: set[str], chaves_main: set[str],
                 chaves_html: set[str]) -> list[tuple[str, str]]:
    """Retorna lista de (severidade, mensagem)."""
    achados = []
    linhas = path.read_text(encoding="utf-8").splitlines()

    # --- §9: categorias órfãs + placeholders ---
    i9, f9 = secao(linhas, 9)
    if i9 == -1:
        achados.append(("FAIL", "§9 (Mapa de mercados) ausente"))
    else:
        for l in linhas[i9:f9]:
            if "aguarda amostra" in l and l.lstrip().startswith("|"):
                achados.append(("FAIL", f"§9 ainda tem placeholder 'aguarda amostra': {l.strip()[:70]}"))
            if l.lstrip().startswith("|"):
                cells = [c.strip() for c in l.split("|")[1:-1]]
                if len(cells) >= 2:
                    orfa = categoria_valida(cells[1], oficiais)
                    if orfa is not None:
                        achados.append(("FAIL", f"§9 categoria órfã '{orfa}' (não existe no MASTER_APOSTAS §3)"))

    # --- §14: transversais cruas ---
    for idx, l in enumerate(linhas):
        if l.strip() == "**Transversais (todas as casas):**":
            achados.append(("WARN", "§14 tem bloco 'Transversais' cru (deveria ser ponteiro '> **Transversais ...**')"))

    # --- estrutura: 15 seções ---
    faltando = [n for n in range(1, 16) if secao(linhas, n)[0] == -1]
    if faltando:
        achados.append(("WARN", f"seções ausentes: {faltando}"))

    # --- registro no app ---
    chave = path.stem.replace("CASA_", "")  # ex.: KTO, BETNACIONAL
    if chave not in chaves_main:
        achados.append(("FAIL", f"'{chave}' ausente em app/main.py (_CASA_DISPLAY)"))
    if chave not in chaves_html:
        achados.append(("FAIL", f"'{chave}' ausente em app/static/index.html (NOMES)"))

    return achados


def main(argv: list[str]) -> int:
    oficiais = categorias_oficiais()
    main_txt = MAIN_PY.read_text(encoding="utf-8")
    html_txt = INDEX_HTML.read_text(encoding="utf-8")
    chaves_main = set(re.findall(r'"([A-Z0-9]+)":\s*"', main_txt))
    chaves_html = set(re.findall(r'\b([A-Z0-9]+):\s*[\'"]', html_txt))

    if argv:
        alvos = [CASAS_DIR / a for a in argv]
    else:
        alvos = sorted(p for p in CASAS_DIR.glob("CASA_*.md") if p.stem != "CASA_MODELO")

    total_fail = 0
    print(f"Categorias oficiais (MASTER_APOSTAS §3): {len(oficiais)}")
    print(f"Casas auditadas: {len(alvos)}\n")
    for path in alvos:
        achados = auditar_casa(path, oficiais, chaves_main, chaves_html)
        fails = [a for a in achados if a[0] == "FAIL"]
        total_fail += len(fails)
        if not achados:
            print(f"  OK   {path.name}")
        else:
            print(f"  {'FAIL' if fails else 'WARN'} {path.name}")
            for sev, msg in achados:
                print(f"         [{sev}] {msg}")
    print()
    if total_fail:
        print(f"RESULTADO: {total_fail} FAIL(s) — corrigir antes de prosseguir.")
        return 1
    print("RESULTADO: sem FAILs. (WARNs são resíduos menores, avaliar manualmente.)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# -*- coding: utf-8 -*-
"""Prova por MUTAÇÃO do gate da procedência do código (s338).

Gate verde não prova nada: quebra-se o código de propósito e confere-se que o teste
FICA VERMELHO. Cada mutação abaixo é um jeito plausível de a cablagem da coluna
`codigo_ocr` estar errada — e todas nascem de um erro que a implementação poderia
cometer sem levantar exceção nenhuma em tempo de escrita.

    python scripts/mutar_codigo_ocr.py

⚠ O que estas mutações NÃO alcançam: o comportamento da Migração B' (adotar, recusar o
ambíguo, não rebaixar quem já foi confirmado) só é exercido com Postgres, em
`tests/test_repository_db.py`. Aqui se prova que a FORMA está cabeada.
"""
import io
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ALVO = RAIZ / "app" / "repository.py"

MUTACOES = [
    ("coluna cabeada só na metade: sai do INSERT e o argumento fica",
     "                         sistema, sistema_linhas, codigo_ocr)",
     "                         sistema, sistema_linhas)"),

    ("argumento Python esquecido (o asyncpg levanta antes de qualquer SQL)",
     "                    row.get(\"sistema\") or None, row.get(\"sistema_linhas\"),\n"
     "                    bool(codigo) and codigo_ocr,\n"
     "                )\n"
     "            except asyncpg.UniqueViolationError:",
     "                    row.get(\"sistema\") or None, row.get(\"sistema_linhas\"),\n"
     "                )\n"
     "            except asyncpg.UniqueViolationError:"),

    ("confiança que nunca é confirmada (COALESCE no lugar do AND)",
     "                        codigo_ocr       = bilhetes.codigo_ocr AND EXCLUDED.codigo_ocr,",
     "                        codigo_ocr       = COALESCE(bilhetes.codigo_ocr, EXCLUDED.codigo_ocr),"),

    ("confiança que SOBE: um print colado depois desconfia do código da API",
     "                        codigo_ocr       = bilhetes.codigo_ocr AND EXCLUDED.codigo_ocr,",
     "                        codigo_ocr       = bilhetes.codigo_ocr OR EXCLUDED.codigo_ocr,"),

    ("o fallback de UniqueViolation esquece a procedência",
     "                        codigo_ocr       = codigo_ocr AND $18,",
     "                        codigo_ocr       = $18,"),

    ("a B' passa a adotar no escuro (cai a trava de candidato único)",
     "                    if cand_ocr and len(cand_ocr) == 1:",
     "                    if cand_ocr:"),

    ("print passa a adotar print (o índice deixa de exigir lote confiável)",
     "        if not codigo_ocr:\n            for casa_k, parc_k in contas_com_cod:",
     "        if True:\n            for casa_k, parc_k in contas_com_cod:"),
]


def pytest_verde() -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_codigo_ocr.py", "-q"],
                       cwd=RAIZ, capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    original = io.open(ALVO, encoding="utf-8").read()
    if not pytest_verde():
        print("O gate já está VERMELHO sem mutação nenhuma — conserte antes de mutar.")
        return 2

    escaparam = []
    try:
        for nome, de, para in MUTACOES:
            if original.count(de) != 1:
                print(f"[ANCORA]  nao encontrada (ou ambigua): {nome}")
                escaparam.append(nome)
                continue
            io.open(ALVO, "w", encoding="utf-8", newline="").write(original.replace(de, para, 1))
            if pytest_verde():
                print(f"[ESCAPOU] {nome}")
                escaparam.append(nome)
            else:
                print(f"[OK]     pego     {nome}")
            io.open(ALVO, "w", encoding="utf-8", newline="").write(original)
    finally:
        io.open(ALVO, "w", encoding="utf-8", newline="").write(original)

    print()
    if escaparam:
        print(f"{len(MUTACOES) - len(escaparam)}/{len(MUTACOES)} pegas. Escaparam: {escaparam}")
        return 1
    print(f"{len(MUTACOES)}/{len(MUTACOES)} mutações detectadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

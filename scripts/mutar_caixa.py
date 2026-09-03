# -*- coding: utf-8 -*-
"""Prova por MUTAÇÃO do gate da Caixa (s314).

Gate verde não prova nada: quebra-se o código de propósito e confere-se que o teste
FICA VERMELHO. Cada mutação abaixo é um jeito plausível de o cálculo estar errado —
e todas foram escritas a partir de um erro real que a implementação poderia cometer.

    python scripts/mutar_caixa.py
"""
import io
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ALVO = RAIZ / "app" / "repository.py"

MUTACOES = [
    ("preso no corte nunca entra na banca",
     '            out["preso_corte"] += stake\n            out["n_preso_corte"] += 1',
     '            out["n_preso_corte"] += 1'),

    ("lançamento anterior ao corte volta a contar",
     '        if corte and (m.get("data") or "") < corte:\n            continue',
     '        if False:\n            continue'),

    ("aposta anterior ao corte volta a contar",
     '        if not no_corte and not (corte and data_iso and data_iso >= corte):\n            continue',
     '        if not no_corte and not data_iso:\n            continue'),

    ("disponível deixa de descontar o que está em aberto",
     '    out["disponivel"] = round(banca - out["aberto"], 2)',
     '    out["disponivel"] = round(banca, 2)'),

    ("a lista de abertas no corte é ignorada",
     '    abertas_corte = {int(i) for i in (ini.get("abertas_corte") or [])}',
     '    abertas_corte = set()'),

    ("divergência recalculada contra a projeção de hoje",
     '    div = None if proj is None else round(float(ult.get("valor") or 0.0) - float(proj), 2)',
     '    div = round(float(ult.get("valor") or 0.0) - out["disponivel"], 2)'),

    ("qualquer lançamento posterior apaga o alerta (sem olhar a data)",
     '              and (m.get("criado_em") or "") > (ult.get("criado_em") or "")]',
     '              ]'),

    ("tolerância afrouxada para 2 centavos",
     "CAIXA_TOL = 0.005",
     "CAIXA_TOL = 0.02"),

    ("saque somado em vez de subtraído",
     '    banca = (out["inicial"] + out["preso_corte"] + out["depositos"]\n'
     '             - out["saques"] + out["ajustes"] + out["pl"])',
     '    banca = (out["inicial"] + out["preso_corte"] + out["depositos"]\n'
     '             + out["saques"] + out["ajustes"] + out["pl"])'),
]


def pytest_verde() -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_caixa.py", "-q"],
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

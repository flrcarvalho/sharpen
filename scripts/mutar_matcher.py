"""Prova por mutação do matcher por evidência (regra "teste verde não é teste que detecta").

Quebra o código de propósito, uma mutação por vez, e exige que o gate correspondente passe a
FALHAR. Mutação que escapa não acusa código ruim — acusa teste que não detecta.

    python scripts/mutar_matcher.py

Dois alvos, porque são dois modos de falha diferentes:

  · `app/matcher.py`  × `tests/test_matcher.py`      — o MODELO decide errado.
  · `app/main.py`     × `tests/test_rota_sugerir.py` — o CONTRATO com a tela quebra. Este é o
    pior: a rota responde 200, e o botão "Sugerir tipsters" só não faz nada (ou volta a errar
    como o matcher antigo) sem erro em lugar nenhum.

Restaura os originais no `finally` (inclusive se o pytest estourar) e confere byte a byte.
Cópias vão para `Backups/_mutacao_matcher/` ANTES de qualquer escrita.

Placar de referência (s289): 15/15 detectadas. A M5 escapou na primeira rodada — o teste não
tinha cenário com tipster sem histórico E treino curto, que é onde a regra morde.
"""
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MODELO = RAIZ / "app" / "matcher.py"
ROTA = RAIZ / "app" / "main.py"
BKP = RAIZ / "Backups" / "_mutacao_matcher"

MUTACOES_MODELO = {
    "M1 confiança ABSOLUTA (MAX_INEDITAS) afrouxada":
        ("MAX_INEDITAS = 0", "MAX_INEDITAS = 9"),
    "M2 confiança RELATIVA (MARGEM) zerada":
        ("MARGEM = 2.5", "MARGEM = 0.0"),
    "M3 parse de stake BR quebrado":
        ('    t = s.replace(".", "").replace(",", ".") if "," in s else s', "    t = s"),
    "M4 pernas deixa de ser contada":
        ('    pernas = d.count(" // ") + 1 if d else 0', "    pernas = 0"),
    "M5 tipster SEM histórico passa a concorrer":
        ("        if not n:\n            continue                      # tipster sem histórico não concorre (nem pode)",
         "        if not n:\n            n = 1"),
    "M6 piso de treino removido":
        ("MIN_TREINO = 200", "MIN_TREINO = 0"),
    "M7 linha sem tipster entra no treino":
        ('        nome = (b.get("tipster") or "").strip()\n        if not nome:\n            continue',
         '        nome = (b.get("tipster") or "").strip()'),
    "M8 cache ignora o TTL":
        ("    if time.monotonic() - ts > TTL_MODELO:", "    if False:"),
    "M9 corte volta a contar casa/valor (novidade vira veto)":
        ('CORTE_IGNORA = ("casa=", "val=")', "CORTE_IGNORA = ()"),
    "M10 corte para de olhar as features estáveis (nada mais veta)":
        ('CORTE_IGNORA = ("casa=", "val=")', 'CORTE_IGNORA = ("casa=", "val=", "esp=", "mkt=", "fim=", "faixa=", "pernas=")'),
}

MUTACOES_ROTA = {
    "R1 a rota mente a fonte (diz 'evidencia' sem treino)":
        ('    fonte = "evidencia" if modelo.treino >= matcher.MIN_TREINO else "declarativo"',
         '    fonte = "evidencia"'),
    "R2 casa dedicada deixa de cravar":
        ("        if len(dono_casa) == 1 and dono_casa[0] in ativos_set:\n"
         "            sugestoes[b.id] = dono_casa[0]\n"
         "            continue",
         "        if False:\n            pass"),
    "R3 casa dedicada crava tipster ARQUIVADO":
        ("        if len(dono_casa) == 1 and dono_casa[0] in ativos_set:",
         "        if len(dono_casa) == 1:"),
    "R4 casa de 2 donos deixa de restringir o pool":
        ("        pool = [n for n in dono_casa if n in ativos_set] if len(dono_casa) == 2 else ativos",
         "        pool = ativos"),
    "R5 o cache do modelo é ignorado (retreina a cada chamada)":
        ("    modelo = matcher.modelo_em_cache(dono)\n    if modelo is None:",
         "    modelo = None\n    if modelo is None:"),
}


def _rodar(alvo, orig, mutacoes, teste, escaparam):
    for nome, (antes, depois) in mutacoes.items():
        if antes not in orig:
            print(f"  ?? PADRÃO NÃO ENCONTRADO: {nome}")
            escaparam.append(nome + " (padrão sumiu — a mutação nem foi aplicada)")
            continue
        alvo.write_text(orig.replace(antes, depois, 1), encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "pytest", teste, "-q"],
                           cwd=str(RAIZ), capture_output=True, text=True)
        linhas = [l for l in r.stdout.strip().splitlines() if l.strip()]
        resumo = linhas[-1] if linhas else "(sem saída)"
        detectada = r.returncode != 0
        print(f"  {'DETECTADA' if detectada else 'ESCAPOU  '}  {nome}  ->  {resumo}")
        if not detectada:
            escaparam.append(nome)
    alvo.write_text(orig, encoding="utf-8")


def main() -> int:
    BKP.mkdir(parents=True, exist_ok=True)
    orig_modelo = MODELO.read_text(encoding="utf-8")
    orig_rota = ROTA.read_text(encoding="utf-8")
    (BKP / "matcher.py.orig").write_text(orig_modelo, encoding="utf-8")
    (BKP / "main.py.orig").write_text(orig_rota, encoding="utf-8")
    escaparam = []
    total = len(MUTACOES_MODELO) + len(MUTACOES_ROTA)
    try:
        print("modelo — app/matcher.py × tests/test_matcher.py")
        _rodar(MODELO, orig_modelo, MUTACOES_MODELO, "tests/test_matcher.py", escaparam)
        print("\ncontrato com a tela — app/main.py × tests/test_rota_sugerir.py")
        _rodar(ROTA, orig_rota, MUTACOES_ROTA, "tests/test_rota_sugerir.py", escaparam)
    finally:
        MODELO.write_text(orig_modelo, encoding="utf-8")
        ROTA.write_text(orig_rota, encoding="utf-8")
        assert MODELO.read_text(encoding="utf-8") == orig_modelo, f"FALHA AO RESTAURAR — veja {BKP}"
        assert ROTA.read_text(encoding="utf-8") == orig_rota, f"FALHA AO RESTAURAR — veja {BKP}"
        print("\noriginais restaurados e conferidos byte a byte.")

    print(f"\n{total - len(escaparam)}/{total} mutações detectadas")
    if escaparam:
        print("ESCAPARAM (o defeito está no TESTE, não no código):")
        for e in escaparam:
            print("  - " + e)
    return 1 if escaparam else 0


if __name__ == "__main__":
    sys.exit(main())

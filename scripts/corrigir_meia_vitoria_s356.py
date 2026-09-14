# -*- coding: utf-8 -*-
"""Devolve o rótulo HW e a odd da casa às meias vitórias gravadas como W (s356).

POR QUE EXISTE
--------------
A extensão rotula meia vitória como `Ganho → W` (o `_resultadoB3` só compara retorno com
stake), a IA obedece o rótulo — que é uma ORDEM, não um recado — e fecha a conta aplicando
a regra de cashout do `MASTER_RESULTADO §5.6`: `odd = retorno ÷ stake`.

O resultado é internamente CONSISTENTE, e é isso que o torna invisível:

    bloco:  stake 99,00 · Odd 2 · Ganho → W (retorno R$ 148,50)
    banco:  stake 99,00 · odd 1,50 · W          ← 99 × 1,50 = 148,50, bate exato
    certo:  stake 99,00 · odd 2,00 · HW         ← (49,50 × 2) + 49,50 = 148,50, também bate

As duas leituras pagam o MESMO dinheiro, então nem a régua do P/L nem o
`_veredito_do_retorno` (que recebia a odd já adulterada) tinham como separá-las. Quem
separa é a PROCEDÊNCIA: `1,50` a IA derivou, `2` a casa imprimiu.

A causa foi corrigida em `repository._veredito_do_retorno`, que agora testa as cinco
fórmulas com a odd do BLOCO antes da odd da linha. Este script trata o que já está gravado.

O QUE MUDA, E O QUE NÃO MUDA
----------------------------
**O P/L não muda** — é o mesmo retorno, e foi por isso que o defeito sobreviveu tanto tempo.
O que volta é o RÓTULO (`W` → `HW`) e a ODD (a derivada → a da casa). Com eles voltam o win
rate, o ROI por faixa de odd e a assinatura de stake/odd que o matcher de tipster lê.

SEGURANÇA
---------
· Só toca linha cujo bloco cru está guardado em `sombra_rotulos` e cujo retorno bate com a
  fórmula de HW **pela odd do bloco**, com a mesma tolerância do gate.
· **Pula bilhete com correção humana** em `resultado` ou `odd`: decisão do dono manda sobre
  captura, certa ou errada (regra do `CLAUDE.md`).
· Grava por `atualizar_bilhete`, então a trilha fica em `correcoes` e a assinatura é
  reavaliada — `resultado` e `odd` não entram no hash, mas reusar o caminho oficial evita
  que a próxima coluna que entrar no hash nos pegue de surpresa.
· Ensaio é o padrão.

USO:
    python scripts/corrigir_meia_vitoria_s356.py
    python scripts/corrigir_meia_vitoria_s356.py --dono Feca
    python scripts/corrigir_meia_vitoria_s356.py --dono Feca --aplicar
"""
import argparse
import asyncio
import os
import sys
from collections import Counter
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import repository as R  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip()
    print("DATABASE_URL ausente (nem no ambiente nem no .env).", file=sys.stderr)
    raise SystemExit(2)


def _bate(a: float, b: float) -> bool:
    """A mesma tolerância do gate: R$ 0,10 ou 0,5%, o que for maior."""
    return abs(a - b) <= max(0.10, abs(b) * 0.005)


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dono", default=None, help="restringe a um dono (ex.: Feca)")
    ap.add_argument("--casa", default=None, help="restringe a uma casa (ex.: Bet365)")
    ap.add_argument("--aplicar", action="store_true",
                    help="executa; sem isto é ENSAIO e nada no banco muda")
    args = ap.parse_args()

    url = _database_url()
    # `atualizar_bilhete` grava pelo pool do `database`, que lê a env var. Sem isto o
    # ensaio funciona (conexão própria) e o --aplicar morre na primeira escrita.
    os.environ.setdefault("DATABASE_URL", url)
    conn = await asyncpg.connect(url)
    try:
        # O bloco cru mais RECENTE de cada (dono, casa, código).
        blocos: dict[tuple, str] = {}
        for r in await conn.fetch(
                "SELECT dono, casa, codigo, bruto FROM sombra_rotulos ORDER BY criado_em"):
            blocos[(r["dono"], r["casa"], r["codigo"])] = r["bruto"]
        print(f"blocos crus guardados na sombra: {len(blocos)}")

        filtros = ["codigo_bilhete IS NOT NULL", "extraction_state = 'resolvida'"]
        params = []
        if args.dono:
            params.append(args.dono)
            filtros.append(f"dono = ${len(params)}")
        if args.casa:
            params.append(args.casa)
            filtros.append(f"casa = ${len(params)}")
        linhas = await conn.fetch(
            f"""SELECT id, dono, casa, parceiro, data, descricao, stake, odd, resultado,
                       codigo_bilhete, sistema
                  FROM bilhetes WHERE {' AND '.join(filtros)}""", *params)

        # Correção humana manda: bilhete com registro em `correcoes` para estes campos sai.
        travados = set()
        for r in await conn.fetch(
                "SELECT DISTINCT bilhete_id FROM correcoes WHERE campo IN ('resultado','odd')"):
            travados.add(r["bilhete_id"])

        alvos, pulados_humanos = [], 0
        for l in linhas:
            if l["sistema"]:
                continue                      # odd de sistema é a MÉDIA, não a do cupom
            bruto = blocos.get((l["dono"], l["casa"], l["codigo_bilhete"]))
            if not bruto:
                continue
            info = R._financeiro_do_texto(
                "[Código: %s]\n%s" % (l["codigo_bilhete"], bruto)).get(l["codigo_bilhete"])
            if not info or info.get("sistema"):
                continue
            stake = R._num_or_none(l["stake"])
            odd_bloco = R._num_bloco(info.get("odd_total")) if info.get("odd_total") else None
            if not stake or stake <= 0 or not odd_bloco or odd_bloco <= 0:
                continue
            retorno = R._retorno_do_bloco(info, stake)
            if retorno is None:
                continue
            # é meia vitória pela odd da CASA, e a linha diz outra coisa?
            if not _bate(retorno, (stake / 2) * odd_bloco + stake / 2):
                continue
            if l["resultado"] == "HW" and _bate(R._num_or_none(l["odd"]) or 0, odd_bloco):
                continue                      # já está certo
            if l["id"] in travados:
                pulados_humanos += 1
                continue
            alvos.append((l, info.get("odd_total"), odd_bloco, retorno))

        print(f"linhas conferidas: {len(linhas)} · a corrigir: {len(alvos)}"
              + (f" · puladas por correção humana: {pulados_humanos}" if pulados_humanos else ""))
        if not alvos:
            print("Nada a fazer.")
            return 0

        print("\n" + "=" * 96)
        delta_pl = 0.0
        for l, odd_txt, odd_bloco, retorno in alvos:
            pl_a = R.calcular_pl(l["stake"], l["odd"], l["resultado"]) or 0.0
            pl_n = R.calcular_pl(l["stake"], odd_txt, "HW") or 0.0
            delta_pl += pl_n - pl_a
            print(f"#{l['id']:<7} {l['casa']:8} {l['parceiro'][:24]:24} {l['data']} "
                  f"stake={l['stake']:>9}  {l['resultado']} @ {str(l['odd'])[:12]:<12} "
                  f"→  HW @ {odd_txt:<6}  (retorno {retorno:,.2f} · P/L {pl_a:,.2f}→{pl_n:,.2f})")
            print(f"          {(l['descricao'] or '')[:88]}")
        print("=" * 96)
        print(f"{len(alvos)} linha(s) · delta de P/L: R$ {delta_pl:+,.2f} "
              "(perto de zero por desenho — o que volta é o rótulo e a odd)")
        print("por conta:", Counter(l["parceiro"] for l, _, _, _ in alvos).most_common(8))

        if not args.aplicar:
            print("\nENSAIO — nada foi alterado. Rode de novo com --aplicar.")
            return 0

        n = 0
        for l, odd_txt, _ob, _r in alvos:
            await R.atualizar_bilhete(l["id"], {"resultado": "HW", "odd": odd_txt}, l["dono"])
            n += 1
        print(f"\n{n} linha(s) corrigida(s), com a trilha gravada em `correcoes`.")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

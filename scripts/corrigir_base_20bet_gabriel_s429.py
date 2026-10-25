"""Refaz a base 20bet do Gabriel pelo cru da API (sessão 429, 25/10/2026).

O que aconteceu: o Gabriel capturou a 20bet três vezes pela extensão, excluindo tudo entre uma
e outra porque "cada vez dá um resultado", e por fim subiu PRINTS da lista do Betting history.
A lista só mostra o resumo (ID, odd, stake, status), sem as pernas, e a IA gravou
`Mercado Especial - REVISAR` nas 65 apostas. O P/L variava por causa de uma aposta só: a
`68703441` (W com perna devolvida, a casa pagou 127,8 sobre 30) ia ao banco ora com a odd cheia
do card (7,29), ora com retorno ÷ stake (4,26). A Ficha recusava e a IA decidia.

A fonte é o cru que a extensão guardou (`captura_crua`, 3 por aposta, idênticos entre as
capturas), montado pela MESMA Ficha da rota (`ficha.montar_ficha`, `ficha.derivar`), com o
adaptador corrigido na s429:

  • ODD e RESULTADO: sempre da Ficha (`ficha.derivar`). Ficha recusada = a aposta NÃO é tocada.
  • DESCRIÇÃO: a do dicionário da Ficha (`virada.descricao`) quando ele cobre; senão, a que a IA
    já tinha escrito LENDO AS PERNAS nas capturas pela extensão do mesmo dia (`sombra_tsv` e
    `correcoes`). Uma leitura da IA só serve se passa nas três réguas contra a Ficha: uma
    perna por ` // `, os dois times de TODA perna no texto, e `checar_fidelidade` (todo nome e
    decimal existe no bilhete). Entre as que passam, a do estilo do padrão (sem o rótulo
    `Mercado:` na frente, período traduzido). Nenhuma passa = a aposta NÃO é tocada.
  • ESPORTE e CATEGORIA: do dicionário quando ele traduz e está no Master; senão o da leitura
    escolhida da IA, se está no Master; senão a régua do `MASTER_ESPORTES §2` (3+ jogos
    diferentes = `Múltiplos`).

Stake, data, código, conta e tipster ficam: a stake em R$ é a conversão do `/salvar` (moeda da
conta, cotação do dia). A assinatura não muda (o código entra nela, a descrição não). Cada
campo que muda vira uma linha em `correcoes` (origem `script_s429`).

    python scripts/corrigir_base_20bet_gabriel_s429.py            # ensaio (não escreve)
    python scripts/corrigir_base_20bet_gabriel_s429.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import descricao_check  # noqa: E402
import dicionario  # noqa: E402
import ficha  # noqa: E402
import virada  # noqa: E402
from database import get_pool  # noqa: E402
from limpar_cru_filtro import _carregar_env  # noqa: E402

DONO, CASA, CASA_KEY = "Gabriel", "20bet", "20BET"
DESDE = datetime(2026, 10, 25, 19, 30, tzinfo=timezone.utc)       # a 1ª captura do dia: 19:36
CAMPOS = ("esporte", "aposta", "descricao", "odd", "resultado")
DESTINO = ROOT / "Backups" / "s429_20bet_ganha_devolvida" / "base_gabriel_antes.json"
_INGLES = re.compile(r"\b(1st|2nd|3rd|4th|quarto - |parte - )", re.I)


def _fold(s) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def _bloco(f: dict) -> str:
    """O bilhete em texto, para o `checar_fidelidade`: o que a casa mandou, perna a perna."""
    campos = ("evento", "mandante", "visitante", "liga_casa", "mercado_casa", "selecao_casa",
              "linha", "odd")
    return "\n".join(" | ".join(str(p.get(k) or "") for k in campos) for p in f["pernas"])


def _fiel(desc: str, f: dict) -> bool:
    if not desc or "REVISAR" in desc:
        return False
    if len(desc.split(" // ")) != len(f["pernas"]):
        return False
    if not all(_fold(p.get("mandante")) in _fold(desc) and _fold(p.get("visitante")) in _fold(desc)
               for p in f["pernas"]):
        return False
    return not descricao_check.checar_fidelidade(desc, _bloco(f))


def _estilo(desc: str) -> int:
    """Menor = mais perto do padrão: sem `Rótulo:` antes da seleção, período em português."""
    return desc.count(":") + len(_INGLES.findall(desc))


def _mesmo_valor(a, b) -> bool:
    try:
        return Decimal(str(a).replace(",", ".")) == Decimal(str(b).replace(",", "."))
    except InvalidOperation:
        return False


def _esporte_pela_regra(f: dict) -> str | None:
    jogos = {_fold(p.get("evento")) for p in f["pernas"]} - {""}
    return "Múltiplos" if len(jogos) >= 3 else None


async def _leituras_da_ia(conn) -> tuple[dict, list[str]]:
    """({código: [(esporte, categoria, descrição)]} das linhas TSV da IA, [descrições soltas]
    do `correcoes`, sem código: só valem se casarem com UMA aposta pelas réguas)."""
    por_codigo: dict[str, list] = {}
    for r in await conn.fetch(
            "SELECT titular_final, candidato_final FROM sombra_tsv WHERE dono = $1 AND casa = $2 "
            "AND criado_em >= $3 ORDER BY criado_em", DONO, CASA, DESDE):
        for texto in (r["titular_final"], r["candidato_final"]):
            for ln in (texto or "").splitlines():
                col = ln.split("\t")
                if len(col) >= 11 and col[10].strip():
                    por_codigo.setdefault(col[10].strip(), []).append(
                        (col[1].strip(), col[5].strip(), col[6].strip()))
    soltas = set()
    for r in await conn.fetch(
            "SELECT valor_anterior, valor_novo FROM correcoes WHERE dono = $1 AND casa = $2 "
            "AND campo = 'descricao' AND criado_em >= $3", DONO, CASA, DESDE):
        soltas |= {r["valor_anterior"], r["valor_novo"]}
    return por_codigo, sorted(s for s in soltas if s)


def _novo(cru: dict, termos: dict, da_ia: list, soltas: list) -> tuple[dict | None, str]:
    f, motivos = ficha.montar_ficha("vv", cru, CASA_KEY)
    if f is None or motivos:
        return None, f"Ficha recusou: {motivos}"
    d = ficha.derivar(f)
    esporte, categoria, faltam = dicionario.traduzir(f, termos)
    if faltam or not virada.no_master(esporte, categoria):
        esporte = categoria = None
    desc, fonte = virada.descricao(f, termos), "dicionário"
    leitura = None
    if not desc:
        boas = [(e, c, t) for e, c, t in da_ia if _fiel(t, f)]
        boas += [("", "", t) for t in soltas if _fiel(t, f)]
        if not boas:
            return None, "nenhuma descrição fiel (dicionário nem IA)"
        leitura = min(boas, key=lambda x: (_estilo(x[2]), x[0] == ""))
        desc, fonte = leitura[2], "IA, lendo as pernas"
    if esporte is None and leitura and virada.no_master(leitura[0], leitura[1]):
        esporte, categoria = leitura[0], leitura[1]
    if esporte is None:
        esporte = _esporte_pela_regra(f)
        categoria = "Múltipla" if len(f["pernas"]) > 1 else None
    if not virada.no_master(esporte, categoria):
        return None, f"esporte/categoria fora do Master: {esporte!r} / {categoria!r}"
    return {"esporte": esporte, "aposta": categoria, "descricao": desc,
            "odd": d["odd"] or "", "resultado": d["resultado"] or None, "_fonte": fonte}, ""


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch(
            "SELECT id, codigo_bilhete, esporte, aposta, descricao, odd, resultado, stake, "
            "extraction_state FROM bilhetes WHERE dono = $1 AND casa = $2 ORDER BY codigo_bilhete",
            DONO, CASA)
        crus = {r["codigo"]: json.loads(r["cru"]) for r in await conn.fetch(
            "SELECT DISTINCT ON (codigo) codigo, cru::text AS cru FROM captura_crua "
            "WHERE dono = $1 AND casa = $2 ORDER BY codigo, id DESC", DONO, CASA_KEY)}
        termos = await dicionario.carregar(conn, CASA_KEY)
        por_codigo, soltas = await _leituras_da_ia(conn)

        mudancas, falhas, fontes = [], [], {}
        for b in linhas:
            cod = b["codigo_bilhete"]
            if cod not in crus:
                falhas.append((cod, "sem cru"))
                continue
            novo, motivo = _novo(crus[cod], termos, por_codigo.get(cod, []), soltas)
            if novo is None:
                falhas.append((cod, motivo))
                continue
            fontes[novo["_fonte"]] = fontes.get(novo["_fonte"], 0) + 1
            if _mesmo_valor(b["odd"], novo["odd"]):
                novo["odd"] = b["odd"]          # `9,80` × `9,8`: forma, não dinheiro; não reescreve
            difs ={c: (b[c], novo[c]) for c in CAMPOS if (b[c] or None) != (novo[c] or None)}
            if difs:
                mudancas.append((b, novo, difs))

        print(f"{len(linhas)} apostas · {len(mudancas)} a corrigir · {len(falhas)} não tocadas · "
              f"descrição: {fontes}")
        for cod, motivo in falhas:
            print(f"  NÃO TOCA {cod}: {motivo}")
        for b, novo, difs in mudancas:
            print(f"  {b['codigo_bilhete']} ({novo['_fonte']}):")
            for c, (antes, depois) in difs.items():
                print(f"      {c}: {antes!r} → {depois!r}")

        if not aplicar:
            print("\nensaio: nada escrito. Rode com --aplicar.")
            return
        if not mudancas:
            print("nada a fazer.")
            return
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(json.dumps(
            {"gravado_em": datetime.now(timezone.utc).isoformat(),
             "linhas": [dict(b) for b in linhas]},
            ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nsnapshot ANTES: {DESTINO}")
        async with conn.transaction():
            for b, novo, difs in mudancas:
                await conn.execute(
                    "UPDATE bilhetes SET esporte = $2, aposta = $3, descricao = $4, odd = $5, "
                    "resultado = $6, atualizado_em = NOW() WHERE id = $1",
                    b["id"], novo["esporte"], novo["aposta"], novo["descricao"], novo["odd"],
                    novo["resultado"])
                for c, (antes, depois) in difs.items():
                    await conn.execute(
                        "INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, "
                        "valor_novo, descricao, origem) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                        b["id"], DONO, CASA, c, antes, depois, novo["descricao"], "script_s429")
        print(f"gravado: {len(mudancas)} apostas.")


if __name__ == "__main__":
    asyncio.run(main())

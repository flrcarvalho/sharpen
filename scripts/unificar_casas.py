"""Unifica casas que existem no banco em mais de uma grafia.

Cada base importada trouxe a sua grafia ("PixBet" no Feca, "Pixbet" no Jonathan), e o
sistema trata `casa` como TEXTO: cada variante virou uma casa diferente — contas, KPIs,
filtros e favicon separados. Este script funde as variantes nas grafias que o Feca escolheu
(sessão 199).

**A assinatura é recalculada**, não opcional: `casa` entra no hash de `_assinatura` (com ou
sem código de bilhete). Trocar a casa sem recalcular deixaria o hash velho, a próxima
captura não deduparia e o histórico duplicaria — mesma armadilha do rename de conta (s198).

Onde o nome da casa mora (levantado no `information_schema`, não chutado):
`bilhetes`, `parceiros`, `casas_meta`, `casa_config`, `correcoes`, `uso_tokens` e
`tipsters.casas` (lista em TEXTO, separada por vírgula).

Uso:
    python scripts/unificar_casas.py              → relatório (não escreve nada)
    python scripts/unificar_casas.py --aplicar    → aplica tudo numa transação

Idempotente: aplicado, o relatório volta zerado.
"""
import asyncio
import csv
import os
import sys
from datetime import datetime, timezone

import asyncpg
from dotenv import load_dotenv

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_RAIZ, ".env"))
sys.path.insert(0, os.path.join(_RAIZ, "app"))

from repository import _assinatura  # noqa: E402

# Grafia VELHA → grafia que fica. Escolhidas pelo Feca, uma a uma (sessão 199).
# `Betboo` × `Betboom` NÃO entram: são casas diferentes (betboo.com × betboom.bet.br).
MAPA = {
    "BetBra":        "Betbra",
    # s284 — a seta INVERTEU. A s199 elegeu "Faz1Bet", mas dois imports posteriores
    # (LavaPessoal s222, arrudex s277) trouxeram "Faz1bet" e viraram a maioria: 107
    # bilhetes contra 26. Na hora de registrar a casa no `_CASA_DISPLAY` (captura pelo
    # SharpenUp), foi preciso escolher UMA — o round-trip do `/salvar` passa a impor a
    # grafia registrada, e a outra vira conta de grade vazia (o bug da s249).
    # Escolhida "Faz1bet" por três critérios independentes: a MARCA escreve minúsculo
    # (`faz1bet` no HTML de faz1.bet.br, 7 ocorrências, nenhuma com B maiúsculo), é a
    # maioria dos bilhetes, e mover 26 linhas de Lava/Feca/Jonathan toca menos base de
    # terceiro do que mover as 107 de arrudex/LavaPessoal.
    "Faz1Bet":       "Faz1bet",
    # Resíduo pré-s204 vivo só em `correcoes` (1 linha). Entra junto para a grafia
    # não sobreviver em nenhuma das 7 tabelas.
    "Faz1be":        "Faz1bet",
    # s289 — mesma situação da Faz1bet acima, e pela mesma razão: a SportingBet entrou no
    # `_CASA_DISPLAY` ao ganhar captura pelo SharpenUp, e a partir daí o round-trip do
    # `/salvar` impõe UMA grafia. A base decidiu, não a marca: `SportingBet` tem 119
    # bilhetes / 5 contas / 4 donos (Feca, Tonelada, Jonathan, LavaPessoal) contra 4
    # bilhetes / 1 conta de `Sportingbet` (Diogo). Sem esta linha, os 4 bilhetes do Diogo
    # continuariam gravados numa casa que a conta dele não enxerga — grade vazia, sem erro
    # nenhum, exatamente o bug da s249.
    "Sportingbet":   "SportingBet",
    "Matchbook":     "MatchBook",
    "Multibet":      "MultiBet",
    "Pixbet":        "PixBet",
    "Esportiva Bet": "Esportiva",     # difere no sufixo, não na caixa
    "7k Bet":        "7K",            # idem
    "Fullbet":       "Fulltbet",      # mesma casa (fulltbet.bet.br), confirmado pelo Feca
    # s249: as 2 contas nasceram à mão como "JonBet" ANTES de a casa entrar no
    # `_CASA_DISPLAY` (s248). Enquanto a chave não existia no mapa, o round-trip
    # `_casa_display(_display_to_key("JonBet"))` caía no ramo verbatim e devolvia a
    # grafia intacta; com a chave, ele passou a devolver "Jonbet" e o /salvar gravou
    # os bilhetes numa casa que conta nenhuma enxerga (a grade filtra `casa = $1`
    # EXATO). A marca escreve "Jonbet" — conferido em jonbet.bet.br.
    # Aqui `bilhetes` tem ZERO linha na grafia velha (as 13 já estão em "Jonbet"),
    # então esta entrada não move bilhete nem recalcula assinatura: corrige só a
    # conta e as tabelas de metadado que ficaram do lado errado.
    "JonBet":        "Jonbet",
    # s270: a casa REBATIZOU — "Rei do Pitaco" virou "Pitaco" (`pitaco.bet.br`), e o Feca
    # decidiu que Pitaco é o nome padrão. Não é diferença de caixa nem de sufixo: são nomes
    # distintos, como `Esportiva Bet` → `Esportiva` acima. Move bilhete de TRÊS donos (Feca,
    # Diogo e LavaPessoal), e por isso **recalcula assinatura** — sem isso a próxima captura
    # não deduparia e o histórico duplicaria inteiro.
    #
    # Migração parcial seria PIOR que nenhuma: o registro da casa deixa de ter a chave
    # `REIDOPITACO` na mesma sessão, então quem ficasse na grafia velha perderia o botão
    # "Conectar" e cairia em modo print, em silêncio.
    "Rei do Pitaco": "Pitaco",
}

# Contas de typo que ficaram vazias. Só some se tiver ZERO bilhete (conferido em tempo de execução).
CONTAS_VAZIAS = [("Jonathan", "Faz1be", "Pessoal")]

# (tabela, coluna) onde o nome da casa é o valor inteiro da célula.
TABELAS_SIMPLES = [
    ("parceiros", "casa"), ("casas_meta", "casa"), ("casa_config", "casa"),
    ("correcoes", "casa"), ("uso_tokens", "casa"),
]
# Tabelas cuja unicidade inclui a casa → uma fusão pode colidir e o UPDATE explodiria.
UNICIDADE = {"parceiros": ("dono", "casa", "nome"), "casas_meta": ("dono", "casa"),
             "casa_config": ("dono", "casa")}

_BACKUP_DIR = os.path.join(_RAIZ, "Backups", "s199-unificar-casas")


async def relatorio(conn) -> int:
    total = 0
    print("== BILHETES por variante ==")
    for de, para in MAPA.items():
        rows = await conn.fetch(
            "SELECT dono, COUNT(*) n FROM bilhetes WHERE casa = $1 GROUP BY 1 ORDER BY 2 DESC", de)
        for r in rows:
            print(f"  {de:<15} -> {para:<12} | {r['dono']:<9} | {r['n']:>4} bilhete(s)")
            total += r["n"]
    print(f"  total de bilhetes a mover: {total}")

    print("\n== OUTRAS TABELAS ==")
    for tab, col in TABELAS_SIMPLES:
        n = await conn.fetchval(
            f"SELECT COUNT(*) FROM {tab} WHERE {col} = ANY($1::text[])", list(MAPA))
        if n:
            print(f"  {tab:<12}: {n} linha(s)")
    n_tip = 0
    for r in await conn.fetch("SELECT id, casas FROM tipsters WHERE casas IS NOT NULL AND casas <> ''"):
        if any(i.strip() in MAPA for i in r["casas"].split(",")):
            n_tip += 1
    if n_tip:
        print(f"  {'tipsters':<12}: {n_tip} linha(s) (lista `casas` em texto)")

    print("\n== COLISÕES (têm de ser ZERO antes de aplicar) ==")
    col = await colisoes(conn)
    for c in col:
        print("  " + c)
    if not col:
        print("  nenhuma")
    return len(col)


async def colisoes(conn) -> list[str]:
    """Toda unicidade que a fusão violaria. Aborta o script se houver alguma."""
    achados = []
    for de, para in MAPA.items():
        for tab, cols in UNICIDADE.items():
            outras = [c for c in cols if c != "casa"]
            sel = ", ".join(outras)
            cond = " AND ".join(f"o.{c} = v.{c}" for c in outras)
            n = await conn.fetchval(
                f"""SELECT COUNT(*) FROM {tab} v
                     WHERE v.casa = $1
                       AND EXISTS (SELECT 1 FROM {tab} o WHERE o.casa = $2 AND {cond})""",
                de, para)
            if n:
                achados.append(f"{tab}: {n} linha(s) de '{de}' já existem em '{para}' ({sel})")
        n = await conn.fetchval(
            """SELECT COUNT(*) FROM bilhetes b
                WHERE b.casa = $1
                  AND EXISTS (SELECT 1 FROM bilhetes o
                               WHERE o.dono = b.dono AND o.casa = $2
                                 AND o.parceiro = b.parceiro AND o.assinatura = b.assinatura)""",
            de, para)
        if n:
            achados.append(f"bilhetes: {n} linha(s) de '{de}' colidem por assinatura em '{para}'")
    return achados


async def _backup(conn) -> str:
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    alvo = os.path.join(_BACKUP_DIR, f"{carimbo}-bilhetes.csv")
    rows = await conn.fetch(
        """SELECT id, dono, casa, parceiro, assinatura, codigo_bilhete, data, aposta, stake, odd
             FROM bilhetes WHERE casa = ANY($1::text[]) ORDER BY id""", list(MAPA))
    with open(alvo, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "dono", "casa", "parceiro", "assinatura", "codigo_bilhete",
                    "data", "aposta", "stake", "odd"])
        for r in rows:
            w.writerow([r[c] for c in ("id", "dono", "casa", "parceiro", "assinatura",
                                       "codigo_bilhete", "data", "aposta", "stake", "odd")])
    return alvo


async def aplicar(conn) -> None:
    bkp = await _backup(conn)
    print(f"backup: {bkp}\n")

    async with conn.transaction():
        for de, para in MAPA.items():
            # Bilhetes: lê ANTES (o recálculo precisa do conteúdo do hash), troca a casa,
            # depois recalcula — a checagem de colisão da assinatura tem de enxergar as
            # irmãs já na casa nova.
            antes = await conn.fetch(
                """SELECT id, dono, casa, parceiro, data, aposta, descricao, stake, odd,
                          codigo_bilhete, assinatura
                     FROM bilhetes WHERE casa = $1 ORDER BY id""", de)
            if antes:
                await conn.execute("UPDATE bilhetes SET casa = $1 WHERE casa = $2", para, de)
            recalc = 0
            for b in antes:
                final = {
                    "casa": para, "parceiro": b["parceiro"], "data": b["data"] or "",
                    "aposta": b["aposta"] or "", "descricao": b["descricao"] or "",
                    "stake": b["stake"] or "", "odd": b["odd"] or "",
                    "codigo_bilhete": b["codigo_bilhete"] or "",
                }
                tem_codigo = bool(final["codigo_bilhete"].strip())
                nova = None
                for cnt in range(1, 51):
                    sig = _assinatura(final, _counter=cnt)
                    livre = await conn.fetchval(
                        """SELECT NOT EXISTS (
                               SELECT 1 FROM bilhetes
                                WHERE dono = $1 AND casa = $2 AND parceiro = $3
                                  AND assinatura = $4 AND id <> $5)""",
                        b["dono"], para, b["parceiro"], sig, b["id"])
                    if livre:
                        nova = sig
                        break
                    if tem_codigo:
                        break
                if nova and nova != b["assinatura"]:
                    await conn.execute(
                        "UPDATE bilhetes SET assinatura = $1, atualizado_em = NOW() WHERE id = $2",
                        nova, b["id"])
                    recalc += 1
                elif not nova:
                    raise RuntimeError(
                        f"assinatura de {b['id']} colide em '{para}' — abortado, nada foi gravado")

            outras = 0
            for tab, cnome in TABELAS_SIMPLES:
                res = await conn.execute(
                    f"UPDATE {tab} SET {cnome} = $1 WHERE {cnome} = $2", para, de)
                outras += int(res.split()[-1])

            # `tipsters.casas` é uma LISTA em texto ("Bet365, Esportiva Bet, Betano"):
            # troca o item exato, nunca por substring (senão "Esportiva" casaria dentro de
            # "Esportiva Bet" e sobraria "Esportiva Bet" pela metade).
            tips = 0
            for r in await conn.fetch(
                    "SELECT id, casas FROM tipsters WHERE casas IS NOT NULL AND casas <> ''"):
                itens = [i.strip() for i in r["casas"].split(",")]
                if de not in itens:
                    continue
                novos, vistos = [], set()
                for i in itens:
                    n = para if i == de else i
                    if n and n not in vistos:      # a fusão pode duplicar item na lista
                        vistos.add(n)
                        novos.append(n)
                await conn.execute("UPDATE tipsters SET casas = $1 WHERE id = $2",
                                   ", ".join(novos), r["id"])
                tips += 1

            if antes or outras or tips:
                print(f"  {de:<15} -> {para:<12} | {len(antes):>4} bilhete(s) "
                      f"({recalc} assinatura(s)) · {outras} outra(s) linha(s) · {tips} tipster(s)")

        # Contas de typo que ficaram vazias
        for dono, casa, nome in CONTAS_VAZIAS:
            n = await conn.fetchval(
                "SELECT COUNT(*) FROM bilhetes WHERE dono=$1 AND casa=$2 AND parceiro=$3",
                dono, casa, nome)
            if n:
                print(f"  conta {casa}/{nome} ({dono}) NÃO apagada: tem {n} bilhete(s)")
                continue
            res = await conn.execute(
                "DELETE FROM parceiros WHERE dono=$1 AND casa=$2 AND nome=$3", dono, casa, nome)
            print(f"  conta vazia {casa}/{nome} ({dono}): {res}")


async def main() -> None:
    global MAPA, CONTAS_VAZIAS
    aplicar_flag = "--aplicar" in sys.argv

    # `--somente <grafia>`: aplica UMA entrada do MAPA em vez do mapa inteiro.
    # Existe porque o mapa é cumulativo e uma base importada DEPOIS de uma unificação
    # ressuscita a grafia velha (s249: os 42 `Faz1bet` do LavaPessoal reapareceram na
    # s222, muito depois da s199). Sem o filtro, corrigir uma casa arrastaria a base de
    # outro dono na mesma transação — e recalcularia assinatura lá. O relatório segue
    # mostrando o mapa TODO quando o filtro não é usado, para o resíduo não sumir de vista.
    if "--somente" in sys.argv:
        alvo = sys.argv[sys.argv.index("--somente") + 1]
        if alvo not in MAPA:
            print(f"ABORTADO: '{alvo}' não está no MAPA. Grafias: {', '.join(MAPA)}")
            return
        MAPA = {alvo: MAPA[alvo]}
        CONTAS_VAZIAS = []      # limpeza de typo da s199, não pertence a um recorte
        print(f"[--somente] recorte ativo: {alvo!r} -> {MAPA[alvo]!r}\n")

    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        n_col = await relatorio(conn)
        if not aplicar_flag:
            print("\n(relatório apenas — rode com --aplicar para gravar)")
            return
        if n_col:
            print("\nABORTADO: resolva as colisões acima antes de aplicar.")
            return
        print("\n== APLICANDO ==")
        await aplicar(conn)
        print("\n== RELATÓRIO PÓS-UNIFICAÇÃO ==")
        await relatorio(conn)
    finally:
        await conn.close()


asyncio.run(main())

"""Corrige RESULTADO e ODD conferindo o banco contra o BLOCO CRU (sessão 321).

NASCEU DE: o caixa da conta `denisesampa01` não bateu. A causa era uma linha só —
`Under 4.0 Gols [Loiske v TP-T]`, stake 99,00, gravada com **odd 195,53**. O bloco do
robô diz `Status: Ganho → W (retorno R$ 195,53)` e imprime `Odd: 1,975` logo abaixo: a IA
copiou o RETORNO para a coluna Odd. P/L de +R$ 19.258,47 onde o real era +R$ 96,53.

O MECANISMO QUE FALTAVA (a raiz, corrigida à parte em `repository.corrigir_stake_tsv`):
desde a s311 a stake é determinística — vem do `Stake:` do bloco, sem IA no caminho. A
odd só era recalculada como EFEITO COLATERAL disso (`_odd_da_stake`, chamado dentro do
`if` que só roda quando a stake diverge). Stake certa + odd errada passava reto. E o
`resultado` nunca teve conferência nenhuma.

O QUE ESTE SCRIPT USA: `sombra_rotulos` guarda o bloco cru de cada extração desde 26/08.
Casando bloco × banco por (dono, código), o RETORNO do bloco decide o resultado e a odd
sem nenhuma heurística — as mesmas cinco fórmulas do `calcular_pl`, ao contrário:

    retorno == 0                        → L
    retorno == stake                    → V
    retorno == stake × odd              → W
    retorno == (stake/2) × odd + stake/2 → HW
    retorno == stake/2                  → HL   (só com linha asiática partida na descrição)
    nenhuma delas                       → cashout: W, odd = retorno ÷ stake (MASTER §5.6)

TRÊS ARMADILHAS MEDIDAS, todas load-bearing (tirar qualquer uma produz estrago):

  1. O TEXTO DO STATUS NÃO SERVE DE FONTE. `_resultadoB3` (`extensor/content.js`) escreve
     `Ganho → W` para QUALQUER retorno > stake — meia vitória inclusive. Confiar no rótulo
     textual "corrigiria" 14 bilhetes HW que estão certos. Só a aritmética do retorno vale.
  2. A BETFAIR EMITE O RETORNO EM FORMATO INGLÊS (`Retorno 1,642.38`) enquanto stake e odd
     saem em BR (`300,00` / `5,4746`). Um parser BR lê 1,64 e "corrige" a odd de 5,4746
     para 0,0054 — cinco linhas certas destruídas. `_num` decide pelo ÚLTIMO separador.
  3. EDIÇÃO HUMANA MANDA. Nos bilhetes 211706/211711/211747 (Betano, dono Lava) alguém
     editou o resultado à mão em 30/08 22:17, invertendo o que a captura dizia (`W→L` e
     `L→W` no mesmo minuto, cruzados). Certo ou errado, isso é decisão do dono da conta:
     bilhete com correção humana em `resultado` ou `odd` é PULADO e sai no relatório.

E O QUE ELE NÃO FAZ: só mexe onde o DINHEIRO muda (|Δ P/L| ≥ R$ 0,01). Onde o retorno é
exatamente stake/2 o rótulo lê como HL ou como cashout de metade — ambíguo — mas o P/L é
idêntico nos dois; trocar ali seria ruído por ruído, a mesma razão pela qual o UPSERT
congela a extração por IA.

COBERTURA: a sombra começa em 26/08/2026. Nada antes disso é conferível por aqui. Casa
cujo bloco não imprime retorno realizado (BETesporte só tem `Retorno potencial:`) fica de
fora por construção — fail-closed: sem prova, não se corrige nada.

Uso:
    python scripts/corrigir_resultado_odd_s321.py             # ensaio (não escreve)
    python scripts/corrigir_resultado_odd_s321.py --aplicar
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete, calcular_pl  # noqa: E402

DESTINO = ROOT / "Backups" / "s321-odd-resultado-contra-bloco" / "bilhetes_antes.json"

# Piso de escrita, em reais de P/L. Não é conservadorismo: abaixo dele a "correção" TROCA
# a odd limpa da casa por um número derivado de arredondamento. Medido no ensaio: com piso
# de R$ 0,01 entram 26 linhas de Δ = R$ 0,01 do tipo `odd 1,925 → 1,925087108` — o bloco
# imprime `Odd: 1,925` e o retorno vem arredondado ao centavo, então o quociente
# retorno÷stake carrega o resto da divisão. A odd exibida é a verdadeira ali; reescrevê-la
# é ruído com cara de precisão, a mesma razão pela qual o UPSERT congela extração por IA.
PISO = 1.00

# `Stake:` e `Status:` no início da linha — o mesmo formato que todos os formatadores do
# `content.js` emitem. O valor não é ancorado no fim: a Betano imprime
# `Odd total: 2,596 (= Retorno ÷ Stake)` e a Superbet põe sufixo no Status.
_RE_STAKE = re.compile(r"^Stake:\s*(?:R\$\s*)?([\d][\d.,]*)", re.M)
_RE_STATUS = re.compile(r"^Status:\s*(.+)$", re.M)
# Retorno REALIZADO. O lookbehind mantém `Retorno potencial:` (BETesporte, e toda aposta
# em aberto) fora daqui de propósito: potencial não é retorno, e tratá-lo como tal
# liquidaria aposta viva pelo valor que ela PODERIA pagar.
_RE_RETORNO = re.compile(r"(?<!potencial )\bretornos?\b[: ]*(?:R\$\s*)?([\d][\d.,]*)", re.I)
# Linha asiática PARTIDA (`3.0,3.5` · `2,5/3,0` · `4.0-4.5`) ou quarter (`+0.25`). É o
# único lugar onde meia vitória/derrota existe — ver a Escada do MASTER_RESULTADO §7.
_RE_PARTIDA = re.compile(r"\d+[.,]\d+\s*[,/\-]\s*[-+]?\d+[.,]\d+|[-+]?\d+[.,](?:25|75)\b")
# A odd que a casa IMPRIME. `Odd total:` nas casas que dão a odd combinada, `Odd:` nas de
# seleção única. Não ancorada no fim: a Betano escreve `Odd total: 2,596 (= Retorno ÷ Stake)`.
_RE_ODD_BLOCO = re.compile(r"^Odd(?: total)?:\s*([\d][\d.,]*)", re.M)

# Tolerância: R$ 0,10 ou 0,5% do valor, o que for maior. Absoluta sozinha reprova odd de
# muitas casas decimais (a exibida vem arredondada e o retorno, não); relativa sozinha é
# frouxa demais em valor baixo.
def _bate(a: float, b: float) -> bool:
    return abs(a - b) <= max(0.10, abs(b) * 0.005)


def _num(s) -> float | None:
    """Número em BR (`1.642,38`) ou EN (`1,642.38`). O ÚLTIMO separador é o decimal.

    A Betfair mistura os dois no MESMO bloco (stake e odd em BR, retorno em EN), então
    escolher o formato por casa não resolveria — a decisão tem de ser por token.

    UM separador só é SEMPRE decimal, mesmo com 3 dígitos depois. A regra "3 dígitos =
    milhar", que serve para dinheiro, destrói ODD: `1,775` vira 1775 e o bilhete passa a
    valer mil vezes mais. Não há ambiguidade a perder — todo valor monetário nos blocos sai
    do `_brl`, que sempre imprime 2 casas, então milhar nunca aparece sozinho (`1.642` sem
    decimal não existe; `1.642,38` tem os dois separadores e é resolvido pela regra acima).
    """
    if s is None:
        return None
    # `.rstrip(".")` pelo mesmo motivo do `_num_or_none`: a IA às vezes trunca a odd com
    # reticências (`1,45070184...`) e o banco guarda assim. Sem isto o último separador
    # vira o ponto das reticências, o float estoura e a linha é PULADA EM SILÊNCIO — foi o
    # que deixou o #213733 de fora da primeira aplicação.
    s = str(s).strip().rstrip(".")
    if not s:
        return None
    i_ponto, i_virg = s.rfind("."), s.rfind(",")
    if i_ponto >= 0 and i_virg >= 0:
        dec, mil = (".", ",") if i_ponto > i_virg else (",", ".")
    elif i_virg >= 0:
        dec, mil = ",", "."
    elif i_ponto >= 0:
        dec, mil = ".", ","
    else:
        try:
            return float(s)
        except ValueError:
            return None
    try:
        return float(s.replace(mil, "").replace(dec, "."))
    except ValueError:
        return None


def retorno_do_bloco(status: str, stake: float) -> float | None:
    """Retorno realizado que o bloco declara. None = o bloco não prova nada → não mexe."""
    s = status.lower()
    if "em aberto" in s:
        return None
    achado = _RE_RETORNO.search(status)
    if achado:
        return _num(achado.group(1))
    # Sem valor explícito, só os dois extremos são deriváveis do rótulo sem ambiguidade.
    if "perdido" in s or "perdeu" in s or "lost" in s:
        return 0.0
    if "devolvid" in s or "void" in s or "anulad" in s:
        return stake
    return None


def veredito(stake: float, odd: float, retorno: float, descricao: str, odd_bloco: str | None):
    """(resultado, odd nova ou None) que o retorno determina. Ordem importa.

    W antes de HW: quando as duas fórmulas batem (odd 1,00) o bilhete é W. HL por último e
    só com linha partida — sem ela, retorno = stake/2 é cashout de metade, não meia derrota.
    """
    if retorno == 0:
        return "L", None
    if _bate(retorno, stake):
        return "V", None
    if _bate(retorno, stake * odd):
        return "W", None
    if _bate(retorno, (stake / 2) * odd + stake / 2):
        return "HW", None
    if _bate(retorno, stake / 2) and _RE_PARTIDA.search(descricao or ""):
        return "HL", None
    # Cashout / odd que a IA errou: a odd é o que o dinheiro provou (`MASTER_RESULTADO
    # §5.6` e `MASTER_RESULTADO §7.1`: em W, odd = Retorno ÷ Stake), não a exibida.
    calculada = retorno / stake
    # Mesma preferência do `repository._odd_da_stake`: quando o bloco IMPRIME a odd e ela
    # bate com a conta, vale o texto do bloco — preserva a precisão original da casa
    # (`MASTER_OUTPUT`: odd sem limite de casas decimais) em vez de gravar uma dízima
    # nascida do retorno arredondado ao centavo. No `#243096` isso é `1,975`, não
    # `1,9750505051`. Quando a odd impressa NÃO bate (cashout), o quociente manda.
    if odd_bloco is not None:
        n = _num(odd_bloco)
        if n is not None and abs(n - calculada) <= 0.005:
            return "W", odd_bloco
    return "W", f"{calculada:.10f}".rstrip("0").rstrip(".").replace(".", ",")


async def main() -> None:
    aplicar = "--aplicar" in sys.argv
    corte = datetime.now(timezone.utc)          # correções DEPOIS daqui são deste script
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch("""
            SELECT DISTINCT ON (s.dono, s.codigo)
                   s.dono, s.codigo, s.casa, s.bruto,
                   b.id, b.odd, b.resultado, b.stake, b.descricao, b.parceiro,
                   b.extraction_state, b.archived
              FROM sombra_rotulos s
              JOIN bilhetes b ON b.dono = s.dono AND b.codigo_bilhete = s.codigo
             WHERE s.codigo <> '' AND b.resultado IN ('W', 'L', 'V', 'HW', 'HL')
             ORDER BY s.dono, s.codigo, s.criado_em DESC
        """)
        # Campos que um humano já corrigiu à mão. Vale por (bilhete, campo): quem editou o
        # tipster não blindou o resultado.
        travados = set()
        for r in await conn.fetch(
                "SELECT bilhete_id, campo FROM correcoes "
                "WHERE campo IN ('resultado', 'odd') AND criado_em < $1", corte):
            travados.add((r["bilhete_id"], r["campo"]))

    conferidos = corrigir = 0
    pulados_humano, snapshot = [], []
    for r in linhas:
        m_status, m_stake = _RE_STATUS.search(r["bruto"]), _RE_STAKE.search(r["bruto"])
        if not m_status or not m_stake:
            continue
        stake, odd = _num(m_stake.group(1)), _num(r["odd"])
        if stake is None or odd is None or stake <= 0:
            continue
        retorno = retorno_do_bloco(m_status.group(1), stake)
        if retorno is None:
            continue
        conferidos += 1

        m_odd = _RE_ODD_BLOCO.search(r["bruto"])
        res_novo, odd_nova = veredito(stake, odd, retorno, r["descricao"],
                                      m_odd.group(1) if m_odd else None)
        pl_antes = calcular_pl(r["stake"], r["odd"], r["resultado"])
        pl_novo = calcular_pl(r["stake"], odd_nova or r["odd"], res_novo)
        if pl_antes is None or pl_novo is None:
            continue
        if abs(pl_novo - pl_antes) < PISO:
            continue                            # ver PISO: abaixo dele, corrigir é piorar

        campos = {}
        if res_novo != r["resultado"]:
            campos["resultado"] = res_novo
        if odd_nova:
            campos["odd"] = odd_nova
        bloqueados = [c for c in campos if (r["id"], c) in travados]
        if bloqueados:
            pulados_humano.append((r, res_novo, odd_nova, pl_antes, pl_novo, bloqueados))
            continue

        corrigir += 1
        snapshot.append({
            "id": r["id"], "dono": r["dono"], "casa": r["casa"], "parceiro": r["parceiro"],
            "codigo": r["codigo"], "descricao": r["descricao"], "stake": r["stake"],
            "odd_antes": r["odd"], "odd_depois": odd_nova or r["odd"],
            "resultado_antes": r["resultado"], "resultado_depois": res_novo,
            "retorno_bloco": round(retorno, 2),
            "pl_antes": pl_antes, "pl_depois": pl_novo, "delta": round(pl_novo - pl_antes, 2),
        })
        print(f'{r["id"]:>7} {r["casa"]:<9} {r["dono"]:<9} {r["parceiro"][:24]:<24} '
              f'{r["resultado"]}→{res_novo:<3} stake={r["stake"]:>9} retorno={retorno:>9.2f} '
              f'P/L {pl_antes:>11,.2f} → {pl_novo:>11,.2f}  Δ {pl_novo - pl_antes:>10,.2f}')
        print(f'        odd {r["odd"]} → {odd_nova or r["odd"]}   {(r["descricao"] or "")[:86]}')
        if aplicar:
            ok = await atualizar_bilhete(r["id"], campos, r["dono"])
            if not ok:
                print(f'        ⚠ UPDATE não aplicou no bilhete {r["id"]}')

    delta = sum(s["delta"] for s in snapshot)
    print("\n" + "=" * 96)
    print(f"conferidos contra o bloco: {conferidos} · a corrigir: {corrigir} · "
          f"Δ P/L total: R$ {delta:,.2f}")
    por_dono = {}
    for s in snapshot:
        por_dono[s["dono"]] = round(por_dono.get(s["dono"], 0) + s["delta"], 2)
    print("Δ por dono:", por_dono)

    if pulados_humano:
        print(f"\nPULADOS — resultado/odd editados à mão (decisão do dono): {len(pulados_humano)}")
        for r, rn, on, pa, pn, campos in pulados_humano:
            print(f'  {r["id"]:>7} {r["casa"]:<9} {r["dono"]:<9} banco={r["resultado"]} · '
                  f'bloco diz {rn} · P/L {pa:,.2f} → {pn:,.2f} · travado em {campos}')
            print(f'          {(r["descricao"] or "")[:88]}')

    if aplicar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        # APENSA, nunca sobrescreve: o script é feito para rodar de novo (a cada rodada só
        # sobra o que ainda diverge), e uma segunda passada com 1 linha apagaria o registro
        # das 32 da primeira. O snapshot é o único lugar onde o ANTES existe.
        anterior = []
        if DESTINO.exists():
            try:
                anterior = json.loads(DESTINO.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                print("⚠ snapshot anterior ilegível — o novo NÃO será gravado por cima")
                anterior = None
        if anterior is not None:
            DESTINO.write_text(json.dumps(anterior + snapshot, ensure_ascii=False, indent=1),
                               encoding="utf-8")
            print(f"\n✔ aplicado. Snapshot do ANTES ({len(anterior) + len(snapshot)} linhas "
                  f"acumuladas) em {DESTINO}")
    else:
        print("\nENSAIO — nada foi escrito. Rode com --aplicar para gravar.")


asyncio.run(main())

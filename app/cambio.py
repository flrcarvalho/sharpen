"""Câmbio das contas que apostam em outra moeda (s390).

A moeda é da CONTA (`parceiros.moeda`), nunca da casa nem do que a API manda: a Bet Panda
devolve `currency: "$"` e pede `currency=USD` na URL com a carteira em Tether. A API não
distingue USD de USDT, o cadastro distingue.

Só a STAKE converte. A odd não tem moeda, e o P/L é derivado de stake × odd na leitura
(`calcular_pl`), então converter a stake leva o P/L junto, sem um segundo caminho.

Uma fonte por moeda, cada uma com a régua dela:

- **USD** → PTAX/BCB, o MESMO mapa e a MESMA escolha de data do Polymarket
  (`polymarket._cotacao_para`). Duas réguas de dólar no sistema dariam dois números para
  a mesma aposta.
- **USDT** → USDT/BRL da Binance, candle diário, preço de **ABERTURA**. A abertura do dia
  D é fixa desde 00:00 UTC de D; o fechamento só existe no fim do dia. Com o fechamento,
  a aposta de hoje gravaria uma stake que muda a cada reenvio, e o UPSERT CONGELA a stake
  quando a aposta liquida: o número final dependeria da hora da liquidação.
- **EUR, AUD** (s392) → PTAX/BCB pelo endpoint genérico `CotacaoMoedaPeriodo`, só o
  boletim de **Fechamento** e o mesmo recuo de 10 dias do dólar: é a mesma régua do USD,
  aplicada a outra moeda. O endpoint devolve 5 boletins por dia (abertura, três
  intermediários, fechamento); pegar o primeiro do dia seria a abertura, outra régua.
- **ARS** (s392) → não existe no PTAX (medido em 03/10/2026: o BCB publica AUD, CAD, CHF,
  DKK, EUR, GBP, JPY, NOK, SEK e USD). Sai do cruzamento de dois candles da Binance, os
  dois na ABERTURA pelo mesmo motivo do USDT: `USDT/BRL ÷ USDT/ARS`. É o dólar cripto da
  Argentina, perto do paralelo e longe do oficial (decisão da s392, com aval do Feca). O
  par USDT/ARS começa em 28/04/2023; antes disso não há cotação e a linha é recusada.

Sem cotação a linha NÃO grava (vira rejeitada no `/salvar`). Gravar USDT como se fosse
R$ é o erro caro; recusar é recuperável, basta reenviar.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx

import polymarket as _poly

# A moeda nativa do sistema. Conta sem moeda cadastrada é BRL, e aí nada converte.
BRL = "BRL"
# Moedas que a conta pode escolher. A ordem é a do seletor.
MOEDAS = ("BRL", "USD", "USDT", "EUR", "AUD", "ARS")
# As que saem do PTAX genérico (`CotacaoMoedaPeriodo`). O USD fica FORA de propósito: ele
# usa o mapa do Polymarket, e duas réguas de dólar dariam dois números para a mesma aposta.
_PTAX_MOEDAS = ("EUR", "AUD")
_BCB_MOEDA_PERIODO = (_poly._BCB_ODATA + "CotacaoMoedaPeriodo(moeda=@moeda,"
                      "dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)")

# Binance: o espelho público de dados de mercado primeiro (é só leitura de candle e não
# passa pelo bloqueio geográfico da api.binance.com), a API principal como reserva.
# Medido em 03/10/2026: os dois devolvem o mesmo candle, byte a byte.
_BINANCE_HOSTS = ("https://data-api.binance.vision", "https://api.binance.com")
_BINANCE_KLINES = "/api/v3/klines"
_BINANCE_LIMITE = 1000          # teto de candles por chamada da API

# Mapa de MÓDULO, igual ao `_PTAX_MAPA`: o candle de um dia passado nunca muda, e a
# abertura do dia corrente também não. ISO 'YYYY-MM-DD' (dia UTC do candle) → abertura.
_USDT_MAPA: dict[str, float] = {}
# O mesmo, para o par USDT/ARS (s392): pesos argentinos por 1 USDT, na abertura do dia.
_USDTARS_MAPA: dict[str, float] = {}
# PTAX genérico (s392), por moeda: ISO → cotacaoVenda do boletim de Fechamento. E a faixa
# já carregada de cada uma, (de, até), para o 2º lote não ir à rede.
_PTAX_MOEDA_MAPA: dict[str, dict[str, float]] = {}
_PTAX_MOEDA_FAIXA: dict[str, tuple[str, str]] = {}
# PTAX "de hoje" da última carga: o fallback do Polymarket para aposta dos últimos 7 dias.
_HOJE_USD: dict[str, float | None] = {"v": None}


def _iso_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def _ms_utc(iso: str) -> int:
    d = datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1000)


async def _klines(client: httpx.AsyncClient, inicio_ms: int, simbolo: str = "USDTBRL") -> list:
    """Uma página de candles diários a partir de `inicio_ms`, tentando os hosts em ordem.
    Levanta quando os dois falham: falha de rede NÃO pode virar "não há cotação"."""
    params = {"symbol": simbolo, "interval": "1d", "startTime": inicio_ms,
              "limit": _BINANCE_LIMITE}
    ultimo: Exception | None = None
    for host in _BINANCE_HOSTS:
        try:
            r = await _poly._get_retry(client, host + _BINANCE_KLINES, params)
            dados = r.json()
            if isinstance(dados, list):
                return dados
            ultimo = RuntimeError(f"resposta inesperada da Binance ({host})")
        except Exception as exc:   # noqa: BLE001 — tenta o próximo host
            ultimo = exc
    raise ultimo or RuntimeError("Binance indisponível")


async def _carregar_par(client: httpx.AsyncClient, de_iso: str, simbolo: str,
                       mapa: dict[str, float]) -> None:
    """Carrega no `mapa` os candles do par de `de_iso` até hoje, paginando de 1000 em 1000.
    Uma chamada cobre ~2 anos e 9 meses; o histórico inteiro sai em uma ou duas."""
    inicio = _ms_utc(de_iso)
    while True:
        pagina = await _klines(client, inicio, simbolo)
        for k in pagina:
            # [abertura_ms, open, high, low, close, ...]
            mapa.setdefault(_iso_utc(int(k[0])), float(k[1]))
        if len(pagina) < _BINANCE_LIMITE:
            return
        inicio = int(pagina[-1][0]) + 1


async def _carregar_usdt(client: httpx.AsyncClient, de_iso: str) -> None:
    await _carregar_par(client, de_iso, "USDTBRL", _USDT_MAPA)


async def _carregar_ptax_moeda(client: httpx.AsyncClient, moeda: str, de_iso: str) -> None:
    """Garante no `_PTAX_MOEDA_MAPA[moeda]` a faixa `[de_iso − 10 dias .. hoje]`, em UMA
    chamada. Mesma janela do `_garantir_cobertura` do dólar; levanta se o BCB não responde.

    O filtro de boletim é feito AQUI, não no `$filter` da API: o OData do BCB recusa o
    `tipoBoletim eq 'Fechamento'` conforme a codificação do espaço na URL (medido em
    03/10/2026, `+` dá 400), e um 400 aqui viraria "câmbio indisponível" para sempre."""
    hoje = _poly._hoje_iso()
    de = _poly._iso_mais(de_iso, -_poly._RECUO_MAX_DIAS)
    faixa = _PTAX_MOEDA_FAIXA.get(moeda)
    if faixa and de >= faixa[0] and hoje <= faixa[1]:
        return
    if faixa:
        de = min(de, faixa[0])
    params = {
        "@moeda": f"'{moeda}'",
        "@dataInicial": f"'{_poly._mdy(de)}'",
        "@dataFinalCotacao": f"'{_poly._mdy(hoje)}'",
        # Sem `$select`: o BCB passou a devolver 403 a ele (s404, ver `_carregar_periodo`).
        "$format": "json",
    }
    r = await _poly._get_retry(client, _BCB_MOEDA_PERIODO, params)
    mapa = _PTAX_MOEDA_MAPA.setdefault(moeda, {})
    for item in r.json().get("value", []):
        if item.get("tipoBoletim") != "Fechamento":
            continue
        iso = str(item.get("dataHoraCotacao") or "")[:10]
        cot = item.get("cotacaoVenda")
        if len(iso) == 10 and cot:
            mapa.setdefault(iso, float(cot))   # 1º do dia, como o `$top=1` do dólar
    _PTAX_MOEDA_FAIXA[moeda] = (de, hoje)


def _ptax_moeda_ate(moeda: str, iso: str) -> float | None:
    """Último Fechamento publicado ATÉ `iso`, recuando no máximo 10 dias: a mesma escolha
    do `_cotacao_do_mapa` do dólar (fim de semana, feriado, e hoje antes das 13h)."""
    mapa = _PTAX_MOEDA_MAPA.get(moeda) or {}
    for back in range(0, _poly._RECUO_MAX_DIAS):
        val = mapa.get(_poly._iso_mais(iso, -back))
        if val:
            return val
    return None


async def carregar(moeda: str, isos: list[str]) -> None:
    """Garante no mapa da moeda a cotação de todas as datas pedidas, em chamada de FAIXA.
    Levanta `CambioIndisponivel` se a fonte não responde."""
    datas = sorted(i for i in isos if i)
    if not datas or moeda == BRL:
        return
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if moeda == "USD":
                # O `_garantir_cobertura` do Polymarket já pede a faixa [data − 10 .. hoje].
                await _poly._garantir_cobertura(client, datas[0])
                # A "cotação de hoje" é o fallback das apostas dos últimos 7 dias.
                _HOJE_USD["v"] = await _poly._ptax_hoje(client)
            elif moeda == "USDT":
                faltando = [i for i in datas if i not in _USDT_MAPA]
                if faltando:
                    await _carregar_usdt(client, faltando[0])
            elif moeda == "ARS":
                # Os DOIS pares, cada um com o que lhe falta: o cruzamento só existe no dia
                # em que os dois candles existem.
                falta_brl = [i for i in datas if i not in _USDT_MAPA]
                if falta_brl:
                    await _carregar_usdt(client, falta_brl[0])
                falta_ars = [i for i in datas if i not in _USDTARS_MAPA]
                if falta_ars:
                    await _carregar_par(client, falta_ars[0], "USDTARS", _USDTARS_MAPA)
            elif moeda in _PTAX_MOEDAS:
                await _carregar_ptax_moeda(client, moeda, datas[0])
        except _poly.CambioIndisponivel:
            raise
        except Exception as exc:
            raise _poly.CambioIndisponivel(
                f"Câmbio {moeda}→BRL indisponível agora. Tente de novo em alguns minutos."
            ) from exc


def cotacao(moeda: str, iso: str) -> float | None:
    """Cotação moeda→BRL do dia `iso`, já carregada por `carregar`. None = não há.
    Nunca vai à rede: quem chama carrega a faixa antes, uma vez por lote."""
    if moeda == BRL:
        return 1.0
    if not iso:
        return None
    if moeda == "USD":
        val = _poly._cotacao_do_mapa(iso)
        if val:
            return val
        # Mesma regra do Polymarket: só aposta recente cai na cotação de hoje.
        idade = (datetime.now(_poly.BRT).date()
                 - datetime.strptime(iso, "%Y-%m-%d").date()).days
        return _HOJE_USD["v"] if idade <= _poly._COTACAO_FALLBACK_DIAS else None
    if moeda == "USDT":
        return _USDT_MAPA.get(iso)
    if moeda == "ARS":
        # R$ por USDT ÷ pesos por USDT = R$ por peso. Os dois do MESMO dia, sem recuo:
        # a Binance tem candle todo dia, e faltar um deles é dado ausente, não feriado.
        brl, ars = _USDT_MAPA.get(iso), _USDTARS_MAPA.get(iso)
        return brl / ars if brl and ars else None
    if moeda in _PTAX_MOEDAS:
        return _ptax_moeda_ate(moeda, iso)
    return None


# ── Conversão das linhas do /salvar ──────────────────────────────────────────

def _iso_da_linha(row: dict, carimbo: str | None) -> str:
    """A data em que o DINHEIRO SAIU: o carimbo de colocação quando o robô manda
    (`AAAAMMDDhhmmss`), senão a data do bilhete (`DD/MM/AAAA` ou ISO). É a data da
    aposta, a mesma escolha do Polymarket (data da compra). Sem nenhuma das duas, ''.

    ⚠️ **A data do bilhete é a do EVENTO, e o evento pode ser amanhã** (s391): aposta
    ABERTA em jogo futuro pedia a cotação de um dia que ainda não existe, e a linha era
    RECUSADA — na 1ª captura da DEX Sport, 10 das 12 abertas sumiram assim. O dinheiro
    saiu no máximo HOJE, então data posterior a hoje vira hoje: a cotação mais próxima
    que existe (no USDT, a abertura do dia, fixa desde 00:00 UTC). Com o carimbo de
    colocação a data é exata; isto é o piso para quem não manda carimbo."""
    if carimbo and len(carimbo) >= 8 and carimbo[:8].isdigit():
        iso = f"{carimbo[:4]}-{carimbo[4:6]}-{carimbo[6:8]}"
    else:
        d = (row.get("data") or "").strip()
        if len(d) == 10 and d[2] == "/" and d[5] == "/":
            iso = f"{d[6:10]}-{d[3:5]}-{d[0:2]}"
        elif len(d) >= 10 and d[4] == "-" and d[7] == "-":
            iso = d[:10]
        else:
            return ""
    hoje = datetime.now(_poly.BRT).date().isoformat()
    return hoje if iso > hoje else iso


def datas_do_lote(rows: list[dict], carimbos: dict | None) -> list[str]:
    """As datas de cotação que o lote vai precisar, para `carregar` pedir a faixa."""
    carimbos = carimbos or {}
    return [_iso_da_linha(r, carimbos.get((r.get("codigo_bilhete") or "").strip()))
            for r in rows]


def _fmt_money(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def converter_linhas(rows: list[dict], moeda: str, carimbos: dict | None,
                     num) -> tuple[list[dict], list[dict]]:
    """Converte a stake de cada linha da moeda da conta para BRL.

    Devolve (linhas_ok, rejeitadas) no formato do `validar_linhas`, para o `/salvar`
    tratar as duas recusas pelo mesmo caminho. `num` é o parser de número do sistema
    (`repository._num_or_none`), passado de fora para não haver uma segunda régua.

    - Conta em BRL: no-op, nada muda e nenhuma coluna nova é preenchida.
    - Stake vazia (aposta aberta lida pela metade): passa sem conversão e sem moeda —
      ausência viaja como ausência, e o `validar_linhas` já a trata como aviso.
    - Sem cotação para a data: a linha é RECUSADA. Nunca grava a moeda como se fosse R$.
    """
    if moeda == BRL:
        return rows, []
    carimbos = carimbos or {}
    ok: list[dict] = []
    rejeitadas: list[dict] = []
    for i, row in enumerate(rows):
        bruto = (row.get("stake") or "").strip()
        valor = num(bruto) if bruto else None
        if valor is None:
            ok.append(row)
            continue
        iso = _iso_da_linha(row, carimbos.get((row.get("codigo_bilhete") or "").strip()))
        taxa = cotacao(moeda, iso)
        if not taxa:
            # `linha` é a posição 1-based no TSV PARSEADO (a mesma do `validar_linhas`),
            # que o `/salvar` marca em `_linha` antes de validar: o front remonta o mapa
            # código→id pelas linhas aceitas, e uma posição errada tiraria o id da boa.
            rejeitadas.append({
                "linha": row.get("_linha", i + 1),
                "campo": "stake",
                "valor": bruto,
                "erro": f"sem cotação {moeda}→BRL para {iso or 'data ausente'}",
                "resumo": " · ".join(x for x in [row.get("data"), row.get("aposta"),
                                                 row.get("descricao")] if x)[:80],
            })
            continue
        row["moeda"] = moeda
        row["stake_orig"] = round(valor, 2)
        row["cotacao"] = taxa
        row["stake"] = _fmt_money(valor * taxa)
        ok.append(row)
    return ok, rejeitadas


# ── A moeda que a CASA disse × a moeda da CONTA (s391, passo 2b) ──────────────
#
# O `content.js` escreve `Moeda: X` no bloco só quando X não é real (`_linhaMoeda`). Lido
# do TEXTO CRU, como o carimbo: é dado da casa, não da IA. A moeda da conta continua
# mandando na conversão; isto só AVISA quando as duas discordam, sem bloquear a gravação.
_MOEDA_RE = re.compile(r"^Moeda:\s*(\S[^\r\n]*?)\s*$", re.MULTILINE)

# O que a casa pode dizer sem contradizer cada moeda de conta. **USD e USDT cabem um no
# outro** (decisão do Feca, 04/10/2026: "usdt e usd não devem causar problemas"): a casa
# não distingue as duas — a Bet Panda manda `$` com carteira em Tether, a SapphireBet manda
# `USD` com a conta do Feca em USDT —, então o cadastro decide e o aviso viraria ruído a
# cada captura. O aviso continua para o que muda a ordem de grandeza: dólar numa conta em
# real, real numa conta em dólar, moeda fora da tabela.
_COMPATIVEIS = {
    "BRL": {"BRL", "R$"},
    "USD": {"USD", "US$", "$", "USDT"},
    "USDT": {"USDT", "$", "USD", "US$"},
    # s392. O `$` solto NÃO cabe no peso argentino: é a grafia das casas cripto em dólar, e
    # aceitá-lo calaria justamente o caso caro (dólar gravado como peso, ~1.600× menor).
    "EUR": {"EUR", "€"},
    "AUD": {"AUD", "A$", "AU$"},
    "ARS": {"ARS", "AR$"},
}


def moedas_do_texto(texto: str | None) -> list[str]:
    """As moedas distintas que a casa informou no lote, na ordem em que aparecem.
    Lote sem linha `Moeda:` (casa em real, print, extensão antiga) devolve `[]`."""
    if not texto:
        return []
    vistas: list[str] = []
    for m in _MOEDA_RE.finditer(texto):
        v = m.group(1).strip()
        if v and v not in vistas:
            vistas.append(v)
    return vistas


def moedas_contraditorias(moeda_conta: str, vistas: list[str] | None) -> list[str]:
    """As moedas que a casa informou e que NÃO cabem na moeda cadastrada da conta.
    Comparação sem caixa: a Dex Sport manda `usdt`."""
    ok = _COMPATIVEIS.get(moeda_conta, {moeda_conta})
    return [v for v in (vistas or []) if str(v).strip().upper() not in ok]

"""A chave da casa (`SPORTSBETIO`) a partir de qualquer grafia (`Sportsbet.io`), em Python e em SQL.

s438 (D39, consultoria 022): a virada guardava a chave sem espaço (`ficha_virada.casa`,
`captura_crua.casa`, `virada_log.casa`), mas reconstruía a chave de `bilhetes.casa` tirando SÓ o
espaço. `Sportsbet.io` virava `SPORTSBET.IO`, `Stake.com` virava `STAKE.COM`, `Betão` virava
`BETÃO`, e nenhum deles batia com a chave do registro (`main._CASA_DISPLAY`: `SPORTSBETIO`,
`STAKECOM`, `BETAO`). Sem erro nenhum, a Ficha deixava de ver a linha que já existia: "liquidada no
banco", "cru igual já gravado", "tem linha" e o aviso de não lidas falhavam em silêncio nessas
casas (6 apostas da Stake.com do Feca davam "sem linha" estando no banco), e a semente gravava
chaves paralelas no dicionário (`SPORTSBET.IO`, `STAKE.COM`, `BETÃO`).

A regra: tira espaço, PONTO e acento, e põe em maiúsculas. Medido contra as 62 casas do
`_CASA_DISPLAY` em 01/11/2026: todas dão exatamente a chave, sem colisão
(`tests/test_virada.py::test_chave_da_casa_bate_com_o_registro_inteiro`). A mesma regra existe em
SQL (`sql`), e as duas têm de dar o mesmo resultado (gate no harness de banco).

Não serve para decidir a GRAFIA de uma casa nova (`main.casa_oficial`, que mantém o ponto de
propósito: `Locas.bet` × `Locasbet` foi decisão do Feca). Aqui é só a comparação com a chave.
"""
from __future__ import annotations

import re

# Os acentos que aparecem em nome de casa (português). O Postgres de produção não tem a extensão
# `unaccent`, e `translate` com a MESMA tabela nos dois lados garante o mesmo resultado.
ACENTOS_DE = "áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"
ACENTOS_PARA = "aaaaaeeeeiiiiooooouuuucnAAAAAEEEEIIIIOOOOOUUUUCN"
_TABELA = str.maketrans(ACENTOS_DE, ACENTOS_PARA)
_FORA = re.compile(r"[\s.]+")


def chave(casa: str | None) -> str:
    """`Sportsbet.io` → `SPORTSBETIO`; `Vitória Bet` → `VITORIABET`; `DEX Sport` → `DEXSPORT`."""
    return _FORA.sub("", str(casa or "").translate(_TABELA)).upper()


def sql(coluna: str) -> str:
    """A mesma regra como expressão SQL sobre `coluna` (ex.: `sql("b.casa")`)."""
    return (f"upper(regexp_replace(translate({coluna}, '{ACENTOS_DE}', '{ACENTOS_PARA}'), "
            f"'[[:space:].]+', '', 'g'))")

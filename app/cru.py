"""O JSON CRU da casa, como a extensão o manda à `/captura/ficha` (Projeto Ficha Sharpen, s409).

Decisão do Feca (11/10): a extensão manda o objeto de cada bilhete exatamente como a casa
devolveu, e quem monta a Ficha é o servidor, com um adaptador por família
(`app/adaptadores/`). Assim casa nova migra sem atualizar o SharpenUp.

O FILTRO é o que impede dado de pessoa ou de sessão de ser guardado. Regra do Feca:
**nome EXATO, numa lista FECHADA.** Nunca por pedaço do nome (apagaria `CurrentBetBalance`,
que é o retorno; `betSlipNumber`, que é o código; `total_multiplier`, o ComboBOOST) e nunca
por formato do valor (apagaria o código UUID da DEX e o nanoid da Shuffle). A única exceção é
o e-mail, reconhecido pelo VALOR.

A comparação de nome é igualdade sem caixa (`Email` = `email`), nunca "contém".

Gate obrigatório (`tests/test_cru.py`): em toda fixture com adaptador, a Ficha montada do cru
FILTRADO é idêntica à do cru sem filtro.
"""
from __future__ import annotations

import hashlib
import json
import re

# Ponto de partida tirado das fixtures da bancada (consultoria, 11/10), mais os óbvios. Os
# quatro do fim (s409) identificam o CLIENTE na casa, e nenhum inject nem formatador os usa:
# `CurrentBalanceDetails` (Bolsa de Aposta), `CustomerId` (7Games/Betão/R7), `CustomerCode`
# (Betbra/Bolsa) e `playerId` (Novibet, número real de cliente).
NOMES_FILTRADOS = frozenset(n.casefold() for n in (
    "client_ip", "ip_address", "user", "username", "login-id", "loginDomainId",
    "BonusUserId", "CurrentBalance",
    "email", "password", "cpf", "phone", "cookie", "authorization", "access_token",
    "refresh_token",
    "CurrentBalanceDetails", "CustomerId", "CustomerCode", "playerId",
))
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
MAX_BYTES = 64 * 1024


def filtrar(obj, _caminho: str = "") -> tuple[object, list[str]]:
    """(cópia sem os campos da lista, caminhos removidos). Nunca muda o original."""
    removidos: list[str] = []

    def _f(o, cam):
        if isinstance(o, dict):
            novo = {}
            for k, v in o.items():
                c = f"{cam}.{k}" if cam else str(k)
                if str(k).casefold() in NOMES_FILTRADOS:
                    removidos.append(c)
                    continue
                if isinstance(v, str) and _EMAIL.match(v.strip()):
                    removidos.append(c + " (e-mail pelo valor)")
                    continue
                novo[k] = _f(v, c)
            return novo
        if isinstance(o, list):
            return [_f(x, f"{cam}[]") for x in o]
        return o

    return _f(obj, _caminho), removidos


def canonico(obj) -> str:
    """Texto estável do objeto: a mesma aposta dá sempre o mesmo hash."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def impressao(obj) -> str:
    return hashlib.sha256(canonico(obj).encode("utf-8")).hexdigest()

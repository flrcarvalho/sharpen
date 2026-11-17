"""Teto GLOBAL de chamadas simultâneas à IA (s459, auditoria ESCALA A4).

O semáforo de 8 era criado por requisição: 4 usuários extraindo ao mesmo tempo = 32 chamadas
simultâneas (medido pelo auditor com um stub). Aqui várias "extrações" disputam o semáforo
global real e o pico não passa do teto.

O que NÃO está coberto: a cota por dono (um usuário ainda pode ocupar o teto inteiro).
"""
import asyncio

import main


def test_pico_de_chamadas_respeita_o_teto_global():
    ativos = {"n": 0, "pico": 0}

    async def chamada():
        async with main._ia_global():
            ativos["n"] += 1
            ativos["pico"] = max(ativos["pico"], ativos["n"])
            await asyncio.sleep(0.01)
            ativos["n"] -= 1

    async def extracao():
        sem = asyncio.Semaphore(main._MAX_CONCURRENT)

        async def uma():
            async with sem:
                await chamada()
        await asyncio.gather(*(uma() for _ in range(main._MAX_CONCURRENT * 2)))

    async def quatro_usuarios():
        await asyncio.gather(*(extracao() for _ in range(4)))

    asyncio.run(quatro_usuarios())
    assert ativos["pico"] <= main._MAX_IA_GLOBAL
    assert main._MAX_IA_GLOBAL < 4 * main._MAX_CONCURRENT


def test_os_dois_caminhos_de_chamada_passam_pelo_teto():
    """Guarda estática (o comportamento acima não prova que as rotas o usam): os dois laços
    que chamam a IA (`_call_chunk_inner` e a repescagem `_uma`) entram pelo teto global."""
    from pathlib import Path
    src = Path(main.__file__).read_text(encoding="utf-8")
    assert src.count("async with sem, _ia_global():") == 2

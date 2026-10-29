"""Gate da contagem da barra de progresso do Processar (s433, entrega 1.2).

A tela mostra "N de M apostas prontas". O M e o N saem do pré-dedup do `/extrair`
(`_dedup_superbet_text`, preenchendo `info["total"]` e `info["para_ia"]`) e viajam no
1º evento do fluxo (`_com_triagem`). Os testes rodam o `_dedup_superbet_text` real, com as
duas idas ao banco dubladas, como em `test_barreira_recaptura.py`.

O QUE ESTES TESTES **NÃO** COBREM:

  • **A casa virada.** O ramo da Ficha (`virada.resolver_no_extrair`) toca o banco e não é
    exercido aqui; a contagem vem do MESMO `mantidos` depois dele, então a conta não muda,
    mas o código que tira o bilhete da IA por esse caminho fica de fora.
  • **A decisão de NÃO mandar a contagem** (lote com imagem ou planilha) mora no `extrair`,
    que precisa do app inteiro. Só a forma do fluxo é testada.
  • **A tela.** A barra foi medida no Chrome headless (STATUS da s433), não aqui.
"""
import asyncio
import json
import sys

sys.path.insert(0, "app")

import main  # noqa: E402

DOIS = """[Código: A1]
Stake: 10,00
Status: Ganhou → W

[Código: B2]
Stake: 20,00
Status: Em aberto (aguardando resultado — NÃO liquidar; sem resultado)
"""

# O scroll da casa repete o bilhete: o mesmo código duas vezes é UMA aposta.
REPETIDO = DOIS + """
[Código: A1]
Stake: 10,00
Status: Ganhou → W
"""

UM = """[Código: Z9]
Stake: 5,00
Status: Perdeu → L
"""


def _rodar(texto, resolvidos=()):
    orig_res, orig_con = main.get_codigos_resolvidos, main.blocos_conhecidos

    async def _fake_resolvidos(codigos, dono, casa=None, parceiro=None):
        return {c for c in codigos if c in set(resolvidos)}

    async def _fake_conhecidos(dono, casa, codigos, parceiro=None, gravados=False):
        return {}

    main.get_codigos_resolvidos, main.blocos_conhecidos = _fake_resolvidos, _fake_conhecidos
    info = {}
    try:
        asyncio.run(main._dedup_superbet_text(texto, "Feca", "Novibet", "conta1", info=info))
    finally:
        main.get_codigos_resolvidos, main.blocos_conhecidos = orig_res, orig_con
    return info


def _conta(info):
    return {"total": info["total"], "para_ia": info["para_ia"]}


def test_o_que_ja_esta_salvo_conta_como_pronto():
    info = _rodar(DOIS, resolvidos=("A1",))
    assert _conta(info) == {"total": 2, "para_ia": 1}


def test_codigo_repetido_pelo_scroll_conta_uma_vez():
    info = _rodar(REPETIDO)
    assert info["total"] == 2
    assert info["para_ia"] == 2


def test_tudo_salvo_da_zero_para_a_ia():
    info = _rodar(DOIS, resolvidos=("A1", "B2"))
    assert _conta(info) == {"total": 2, "para_ia": 0}
    assert info["lendo"] == []


def test_bilhete_unico_tambem_e_contado():
    """Um bloco só sai pelo atalho do começo da função, antes de qualquer consulta."""
    info = _rodar(UM)
    assert _conta(info) == {"total": 1, "para_ia": 1}
    assert info["lendo"] == [{"codigo": "Z9", "data": "", "stake": "5,00"}]


# ── A linha "processando" (entrega 1.3): só o que segue à IA, copiado do bloco ──

COM_DATA = """[Código: C3]
Data: 28/10/2026
Stake: 30,00
Status: Perdeu → L

[Código: D4]
Data: 29/10/2026
Stake: 12,50
Stake: 15,00
Status: Em aberto (aguardando resultado — NÃO liquidar; sem resultado)
"""


def test_lendo_traz_so_o_que_vai_para_a_ia():
    info = _rodar(DOIS, resolvidos=("A1",))
    assert [r["codigo"] for r in info["lendo"]] == ["B2"]
    assert info["lendo"][0]["stake"] == "20,00"


def test_lendo_copia_data_e_stake_do_bloco():
    info = _rodar(COM_DATA)
    assert info["lendo"][0] == {"codigo": "C3", "data": "28/10/2026", "stake": "30,00"}


def test_stake_ambigua_vai_vazia():
    """Dois valores de Stake no mesmo bloco: a régua do `corrigir_stake_tsv` não escreve."""
    info = _rodar(COM_DATA)
    assert info["lendo"][1] == {"codigo": "D4", "data": "29/10/2026", "stake": ""}


def test_a_contagem_e_o_primeiro_evento_do_fluxo():
    async def corpo():
        yield 'data: {"chunk_progress": 1, "of": 2}\n\n'
        yield 'data: {"done": true}\n\n'

    async def coletar():
        return [ev async for ev in main._com_triagem(corpo(), {"total": 9, "prontas": 7})]

    eventos = asyncio.run(coletar())
    assert len(eventos) == 3
    assert json.loads(eventos[0][6:]) == {"triagem": {"total": 9, "prontas": 7}}
    assert eventos[1:] == ['data: {"chunk_progress": 1, "of": 2}\n\n', 'data: {"done": true}\n\n']

"""Gate da barreira de recaptura (`docs/PLANO_BARREIRA_RECAPTURA.md`, Fase 1).

Os blocos abaixo são **capturas reais** da `sombra_rotulos` de produção, inclusive o
par antes/depois de uma liquidação da Novibet — que é o caso que a barreira EXISTE
para deixar passar.

**Estes testes exercitam `_dedup_superbet_text`, que é o código que roda**, não um
helper paralelo. A primeira versão testava uma função `triar_blocos` que reimplementava
a decisão, e ela foi removida por isso: teste que reimplementa o código sob teste é
falso verde nº 1 do `CLAUDE.md`. As duas dependências de banco são substituídas por
funções de mentira; o resto é o caminho real.

O QUE ESTES TESTES **NÃO** COBREM, e é bom saber antes de confiar no verde:

  • **Não tocam o banco.** O `JOIN` de `blocos_conhecidos` com `bilhetes` (a costura 3:
    hash gravado não é bilhete salvo) é SQL e não é exercido aqui. Ele tem de ser
    conferido contra o Postgres real antes de a barreira valer em produção.
  • **Não cobrem casa sem marcador de código.** Print e texto colado não entram no
    `_dedup_superbet_text` (a lista `_CASAS_MARCADOR_CODIGO` decide antes).
  • **Não medem economia.** Isso é simulação e medição em produção, não teste.
"""
import asyncio
import sys

sys.path.insert(0, "app")

import main  # noqa: E402
import repository  # noqa: E402

# ── Blocos reais (sombra de produção) ─────────────────────────────────────────

# O MESMO bilhete da Novibet, antes e depois de liquidar. Repare que não muda só o
# Status: a odd vai de potencial para `Retorno ÷ Stake`. É por isso que a chave é o
# bloco inteiro, e não o par (código, resultado).
NOVIBET_ABERTA = """[Código: 475962111]
Data: 27/08/2026
Stake: 162,50
Status: Em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd: 4,59666667
Retorno potencial: R$ 746,91 (POTENCIAL — a aposta não liquidou)

[Código: 475962999]
Data: 27/08/2026
Stake: 50,00
Status: Em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd: 2,10
"""

NOVIBET_UMA_LIQUIDOU = """[Código: 475962111]
Data: 27/08/2026
Stake: 162,50
Status: Ganhou → W
Odd: 2,89666667 (= Retorno ÷ Stake)
Retorno: R$ 746,91
Liquidado em: 27/08/2026 10:10:57

[Código: 475962999]
Data: 27/08/2026
Stake: 50,00
Status: Em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd: 2,10
"""

SEM_CODIGO = """Stake: 100,00
Status: Ganho → W (retorno R$ 180,00)
"""


def _hashes(texto):
    """A memória que a barreira teria depois de ler `texto`. Usa o MESMO recorte do
    gravador (`blocos_por_codigo`), que é o ponto do mecanismo.

    Código na caixa em que veio, como o `registrar_blocos_vistos` grava. Até a s407
    este helper fazia `.upper()`, a mesma premissa do código sob teste, e com códigos
    só numéricos ninguém via a diferença: o verde escondia a barreira morta da DEX Sport
    e da Shuffle."""
    return {c: repository.hash_bloco(b)
            for c, b in repository.blocos_por_codigo(texto).items()}


_ULTIMA_CHAMADA: dict = {}   # o que o pré-dedup mandou ao banco na última `_rodar` (s448)


def _rodar(texto, *, resolvidos=(), memoria=None, nao_salvos=(), apagados=(), casa="Novibet"):
    """Roda o `_dedup_superbet_text` real com as duas idas ao banco dubladas.

    `nao_salvos`: códigos cujo hash está na memória mas cuja leitura NÃO chegou ao banco
    (o bilhete é mais velho que o hash). O dublê imita o SQL de `blocos_conhecidos`: com
    `gravados=True` eles somem do retorno; sem, aparecem (s424).

    `apagados`: o hash está no `bloco_visto`, mas a linha saiu de `bilhetes` (o usuário
    apagou). Somem com o JOIN e aparecem com `exigir_linha=False` (s447)."""
    memoria = memoria or {}
    vistos = _ULTIMA_CHAMADA
    vistos.clear()
    orig_res = main.get_codigos_resolvidos
    orig_con = main.blocos_conhecidos

    async def _fake_resolvidos(codigos, dono, casa=None, parceiro=None, vereditos=None):
        # `resolvidos` pode ser {código: resultado gravado} (s448): o dublê só imita o SQL
        # (o que está liquidado nesta conta) e usa o `reliquidou` REAL para o resto.
        gravado = resolvidos if isinstance(resolvidos, dict) else {c: "" for c in resolvidos}
        vistos["vereditos"] = dict(vereditos or {})
        return {c for c in codigos if c in gravado
                and not repository.reliquidou(gravado[c], (vereditos or {}).get(c))}

    async def _fake_conhecidos(dono, casa, codigos, parceiro=None, gravados=False,
                               exigir_linha=True):
        return {c: memoria[c] for c in codigos
                if c in memoria and not (gravados and c in set(nao_salvos))
                and not (exigir_linha and c in set(apagados))}

    main.get_codigos_resolvidos = _fake_resolvidos
    main.blocos_conhecidos = _fake_conhecidos
    try:
        return asyncio.run(
            main._dedup_superbet_text(texto, "Feca", casa, "conta1"))
    finally:
        main.get_codigos_resolvidos = orig_res
        main.blocos_conhecidos = orig_con


def _codigos(texto):
    return set(repository.blocos_por_codigo(texto))


# ── Recorte dos blocos (camada pura, usada pelos dois lados) ─────────────────


def test_texto_sem_codigo_nao_produz_bloco():
    """Print e casa sem marcador não têm chave. A barreira não os alcança, e é
    melhor devolver vazio do que inventar uma chave."""
    assert repository.blocos_por_codigo(SEM_CODIGO) == {}
    assert repository.blocos_por_codigo(None) == {}


def test_teto_corta_o_bloco_mas_a_barreira_nao_usa_teto():
    """A sombra corta em 4000 para não guardar bilhete-monstro. A barreira NÃO corta:
    um byte diferente depois do teto é uma mudança que ela precisa enxergar."""
    longo = "[Código: X1]\n" + ("a" * 5000) + "FIM\n"
    assert len(repository.blocos_por_codigo(longo, teto=100)["X1"]) == 100
    assert repository.blocos_por_codigo(longo)["X1"].endswith("FIM\n")


def test_hash_ignora_a_borda_porque_os_dois_recortes_diferem():
    """O mesmo bilhete passa por dois recortes e um re-join. Só o miolo é estável.
    Sem esta normalização a barreira não pularia NADA, em silêncio."""
    assert repository.hash_bloco("  miolo  ") == repository.hash_bloco("miolo")
    assert repository.hash_bloco("miolo\n\n") == repository.hash_bloco("\nmiolo")
    assert repository.hash_bloco("miolo a") != repository.hash_bloco("miolo b")


def test_hash_nao_levanta_em_bloco_estranho():
    """A barreira roda no caminho da extração: bloco com byte solto tem de gerar UM
    hash estável, nunca uma exceção."""
    assert repository.hash_bloco(None) == repository.hash_bloco("")
    assert len(repository.hash_bloco("\udcff bloco torto")) == 40


# ── A decisão, no código que roda ────────────────────────────────────────────


def test_sem_memoria_nada_e_pulado():
    saida, skipped = _rodar(NOVIBET_ABERTA)
    assert skipped == 0
    assert _codigos(saida) == {"475962111", "475962999"}


def test_bloco_identico_e_pulado():
    """O caso do Feca: extraí as últimas 48h, extraio de novo 2h depois e nada
    mudou. Nada pode custar."""
    saida, skipped = _rodar(NOVIBET_ABERTA, memoria=_hashes(NOVIBET_ABERTA))
    assert skipped == 2
    assert saida == "", "lote inteiro conhecido tem de sair vazio, não meio vazio"


def test_bilhete_que_liquidou_volta_para_a_ia_e_o_vizinho_nao():
    """A metade que importa: um liquidou e o outro não. Só o que mudou pode custar."""
    saida, skipped = _rodar(NOVIBET_UMA_LIQUIDOU, memoria=_hashes(NOVIBET_ABERTA))
    assert skipped == 1
    assert _codigos(saida) == {"475962111"}, "o que liquidou tem de ser reprocessado"


def test_resolvido_no_banco_continua_saindo_como_antes():
    """A barreira NOVA não pode desligar a que já existia: bilhete já resolvido no
    banco continua sendo descartado, com ou sem memória de hash."""
    saida, skipped = _rodar(NOVIBET_ABERTA, resolvidos=["475962999"])
    assert skipped == 1
    assert _codigos(saida) == {"475962111"}


def test_memoria_de_bilhete_que_nao_esta_no_banco_nao_pula():
    """Costura 3, no nível da unidade: `blocos_conhecidos` só devolve código que tem
    linha em `bilhetes`. Devolvendo vazio (bilhete não salvo), nada é pulado."""
    saida, skipped = _rodar(NOVIBET_ABERTA, memoria={})
    assert skipped == 0
    assert _codigos(saida) == {"475962111", "475962999"}


def test_leitura_que_nao_foi_salva_nao_pula_a_aposta_que_liquidou():
    """O caso da MyStake 308613169 (s424, 20/10/2026). A aposta estava aberta no banco
    desde a 1ª captura. Ela liquidou, a IA leu o bloco novo (o hash dele foi gravado no
    fim da extração), e o `/salvar` dessa leitura nunca aconteceu. Na captura seguinte o
    bloco é byte a byte o lido, e a barreira o pulava como "sem mudança": a aposta ganha
    ficava aberta para sempre, com R$ 912,38 fora da Caixa.

    O hash existe, mas a leitura não chegou ao banco: tem de voltar para a IA. E o
    vizinho, cuja leitura foi salva, continua pulando (a economia da barreira fica)."""
    saida, skipped = _rodar(NOVIBET_UMA_LIQUIDOU, memoria=_hashes(NOVIBET_UMA_LIQUIDOU),
                            nao_salvos=["475962111"])
    assert _codigos(saida) == {"475962111"}, "a liquidação não salva tem de ser relida"
    assert skipped == 1, "o vizinho salvo e igual continua pulando"


def test_um_byte_diferente_ja_reprocessa():
    """Na dúvida, processa. O modo de falha aceitável é 'custou dinheiro'; o
    inaceitável é 'deixou de gravar mudança'."""
    mudado = NOVIBET_ABERTA.replace("Stake: 162,50", "Stake: 162,51")
    saida, _ = _rodar(mudado, memoria=_hashes(NOVIBET_ABERTA))
    assert "475962111" in _codigos(saida)


# ── Prova por mutação ────────────────────────────────────────────────────────


def test_mutacao_hash_do_recorte_errado_nao_pula_nada():
    """**A mutação mais importante desta suíte.** O `_dedup_superbet_text` tem DOIS
    recortes à mão: o `block` do `_split_superbet_bilhetes` (com o marcador) e o de
    `blocos_por_codigo` (sem). O gravador usa o segundo. Hashear o primeiro faz a
    barreira **nunca disparar, sem erro nenhum** — e ninguém reclama de economia que
    não aconteceu.

    Aqui a memória é montada pelo recorte ERRADO e o resultado tem de ser zero salto."""
    memoria_errada = {}
    for b in main._split_superbet_bilhetes(NOVIBET_ABERTA):
        m = main._SUPERBET_ID_RE.search(b)
        if m:
            memoria_errada[m.group(1).strip()] = repository.hash_bloco(b)
    saida, skipped = _rodar(NOVIBET_ABERTA, memoria=memoria_errada)
    assert skipped == 0, "hash do recorte errado não pode pular nada"
    assert _codigos(saida) == {"475962111", "475962999"}
    # e o recorte CERTO continua pulando — a outra metade da prova
    assert _rodar(NOVIBET_ABERTA, memoria=_hashes(NOVIBET_ABERTA))[1] == 2


def test_mutacao_hash_sem_strip_deixaria_de_pular():
    """Se `hash_bloco` parasse de normalizar a borda, o hash gravado (recorte do
    gravador) deixaria de bater com o conferido (texto re-emendado). Verde aqui com o
    `strip()` removido significaria que a normalização é redundante."""
    original = repository.hash_bloco
    try:
        import hashlib
        repository.hash_bloco = lambda b: hashlib.sha1(
            (b or "").encode("utf-8", "replace")).hexdigest()
        main.hash_bloco = repository.hash_bloco
        memoria = {c: repository.hash_bloco(b + "\n")   # borda diferente
                   for c, b in repository.blocos_por_codigo(NOVIBET_ABERTA).items()}
        assert _rodar(NOVIBET_ABERTA, memoria=memoria)[1] == 0
    finally:
        repository.hash_bloco = original
        main.hash_bloco = original
    # restaurado: a mesma borda diferente volta a bater
    memoria = {c: repository.hash_bloco(b + "\n")
               for c, b in repository.blocos_por_codigo(NOVIBET_ABERTA).items()}
    assert _rodar(NOVIBET_ABERTA, memoria=memoria)[1] == 2


# ── Código com minúscula: DEX Sport (UUID) e Shuffle (nanoid), s407 ──────────
#
# O banco compara código por IGUALDADE EXATA (`codigo_bilhete = ANY($1)` e o JOIN com
# `bloco_visto`), e os dublês de `_rodar` fazem o mesmo (`c in set(...)`). Por isso
# estes casos pegam a barreira que passa o código para maiúsculas: o código gravado
# (minúsculo) nunca casa, e nada é pulado. Foi o que aconteceu em produção até a s407:
# Feca × Shuffle mandou 60 bilhetes já liquidados de 63 à IA, e na DEX Sport cada
# bilhete era pago 6,44 vezes em média.
#
# Blocos no formato do `formatTicketDX` e do `formatTicketSHF` (`extensor/content.js`),
# com códigos na forma real das duas casas.

DEX_LOTE = """[Código: 4b836669-0c1e-4f2a-9d3b-7a51e2c08f14]
Data (evento mais recente): 09/10/2026 15:00
Stake: 25,00
Status: Perdeu → L
Status (API): result 2 · status 3 · settlementStatus 2
Odd: 1,85
Tipo: Simples
Seleções:
- Total: Under 1.5 [perna perdida]

[Código: e91f03a2-55d7-4c8b-b0a6-1f2d3c4b5a69]
Data (evento mais recente): 12/10/2026 21:00
Stake: 10,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Status (API): result 0 · status 2 · settlementStatus 0
Odd: 2,40
Tipo: Simples
Seleções:
- 1x2: Zamalek [perna não decidida]
"""

SHF_LOTE = """[Código: V1StGXR8_Z5jdHi6B-myT]
Data (evento mais recente): 10/10/2026 16:00
Stake: 35,00
Status: Ganhou → W (retorno 64,75 USDT)
Odd: 1,85 (= Retorno ÷ Stake)
Tipo: Simples
Seleções:
- Resultado: Flamengo [perna ganha]

[Código: aB3xQ9kLm2Pz7Rt0Yw4Ue]
Data (evento mais recente): 12/10/2026 20:00
Stake: 20,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd: 3,10
Tipo: Simples
Seleções:
- Resultado: Empate [perna em aberto]
"""


def test_dex_resolvido_com_minuscula_sai_pelo_estado():
    """O caso da DEX Sport: bilhete liquidado no banco, código UUID minúsculo. Tem de
    sair antes da IA; com `.upper()` na barreira ele voltava a cada captura."""
    resolvido = "4b836669-0c1e-4f2a-9d3b-7a51e2c08f14"
    saida, skipped = _rodar(DEX_LOTE, resolvidos=[resolvido])
    assert skipped == 1
    assert _codigos(saida) == {"e91f03a2-55d7-4c8b-b0a6-1f2d3c4b5a69"}


def test_shuffle_aberta_identica_sai_pelo_hash():
    """O caso da Shuffle: aposta aberta relida sem mudar nada. O hash gravado tem a
    chave com caixa mista do nanoid, e tem de casar."""
    saida, skipped = _rodar(SHF_LOTE, resolvidos=["V1StGXR8_Z5jdHi6B-myT"],
                            memoria=_hashes(SHF_LOTE))
    assert skipped == 2
    assert saida == ""


def test_shuffle_nanoid_e_sensivel_a_caixa():
    """A outra metade: no nanoid `aB3…` e `Ab3…` são bilhetes DIFERENTES. Bilhete
    resolvido com outra caixa não pode pular o do lote; pular o errado some com
    aposta. A barreira compara como o banco compara, por igualdade exata.

    Limite: este caso NÃO detecta a volta do `.upper()` (os dois anteriores detectam,
    medido por mutação na s407). Ele trava a outra correção errada possível, comparar
    sem caixa, só no lado Python; uma comparação sem caixa feita no SQL passaria aqui,
    porque o dublê do banco não roda SQL."""
    outra_caixa = "Ab3xQ9kLm2Pz7Rt0Yw4Ue"
    saida, skipped = _rodar(SHF_LOTE, resolvidos=[outra_caixa])
    assert skipped == 0
    assert "aB3xQ9kLm2Pz7Rt0Yw4Ue" in _codigos(saida)


# ── s447: apagou e recapturou numa casa virada ───────────────────────────────


def test_aposta_apagada_e_recapturada_conta_como_texto_igual_para_a_ficha(monkeypatch):
    """O caso da Cloudbet do Feca (11/11/2026): 32 apostas abertas gravadas pela Ficha,
    apagadas pelo usuário e recapturadas 25 s depois com o texto igual. A extensão não
    reenvia cru igual, então o cru guardado é velho; e o `iguais` exigia a linha no banco,
    que tinha sido apagada. Resultado: "texto mudou sem cru novo", 32 seguradas, 0 gravadas.

    O `iguais` tem de olhar só o hash. E a BARREIRA continua exigindo a linha: a apagada
    não pode ser pulada como "sem mudança" (ela tem de voltar à Ficha ou à IA)."""
    import virada
    recebidos = {}

    async def _resolver(dono, casa_key, casa, parceiro, codigos, iguais, **kw):
        recebidos["iguais"] = set(iguais)
        recebidos["codigos"] = set(codigos)
        return set(), 0.0, {}, set()

    async def _nada(*a, **k):
        return None

    monkeypatch.setattr(virada, "virada", lambda k: True)
    monkeypatch.setattr(virada, "resolver_no_extrair", _resolver)
    monkeypatch.setattr(virada, "registrar", _nada)
    monkeypatch.setattr(virada, "vigia_por_dia", lambda: 0)
    apagados = ["475962111", "475962999"]
    saida, skipped = _rodar(NOVIBET_ABERTA, memoria=_hashes(NOVIBET_ABERTA),
                            apagados=apagados)
    assert recebidos["iguais"] == set(apagados), "a apagada com texto igual é texto igual"
    assert recebidos["codigos"] == set(apagados)
    assert skipped == 0 and _codigos(saida) == set(apagados), \
        "a barreira não pode pular a apagada: sem a linha, ela tem de ser relida"


# ── s448: a CASA reliquidou uma aposta já liquidada ──────────────────────────
# Blocos REAIS da captura da 1win do Feca (Ellen [Eu], 11/11/2026), recortados nas linhas que
# a decisão usa. A 381894004 foi paga como ganha a 2,84 (perna do Kristiansund anulada) e a
# casa a refez como PERDIDA em 09/11 16:55; o banco ficou com W porque o pré-dedup a pulava.

UMWIN_RELIQUIDADA = """[Código: 381894004]
Data (evento mais recente): 07/11/2026 12:00:00
Stake: 40,00
Moeda: USDT
Status: Perdeu → L
Status (API): status=1 · betType=express
Tipo: Múltipla (2 seleções)
Odd: 8,52 (a da casa, cortada em 2 casas — é a que paga)
Liquidado em: 09/11/2026 16:55:41

[Código: 390629480]
Data (evento mais recente): 11/11/2026 13:30:00
Stake: 50,00
Moeda: USDT
Status: Perdeu → L
Status (API): status=1 · betType=express
Tipo: Múltipla (2 seleções)
Odd: 5,01 (a da casa, cortada em 2 casas — é a que paga)
Liquidado em: 11/11/2026 13:48:40
"""

UMWIN_A_CONFERIR = UMWIN_RELIQUIDADA.replace(
    "Status: Perdeu → L\nStatus (API): status=1 · betType=express\nTipo: Múltipla (2 seleções)\n"
    "Odd: 8,52", "Status: status 9 — a conferir\nStatus (API): status=9 · betType=express\n"
    "Tipo: Múltipla (2 seleções)\nOdd: 8,52", 1)


def test_vereditos_do_texto_le_o_status_de_cada_bloco():
    v = repository.vereditos_do_texto(repository.blocos_por_codigo(UMWIN_RELIQUIDADA))
    assert v == {"381894004": "L", "390629480": "L"}
    sem = repository.vereditos_do_texto(repository.blocos_por_codigo(UMWIN_A_CONFERIR))
    assert sem == {"390629480": "L"}, "sem `→ X` não há veredito: nada se reabre sem prova"


def test_reliquidou_compara_so_a_classe():
    r = repository.reliquidou
    assert r("W", "L") and r("L", "W") and r("V", "L") and r("HL", "W") and r("W", "V")
    assert not r("W", "W") and not r("HW", "W") and not r("HL", "L"), \
        "mesma classe não é reliquidação: o texto escreve W também para meia vitória"
    assert not r("", "L") and not r("W", "") and not r("W", None) and not r("X", "L")


def test_reliquidada_pela_casa_volta_a_leitura():
    """O caso: banco W, casa L. O bilhete deixa de ser "já resolvido" e segue para a leitura."""
    saida, skipped = _rodar(UMWIN_RELIQUIDADA,
                            resolvidos={"381894004": "W", "390629480": "L"}, casa="1win")
    assert _codigos(saida) == {"381894004"}, "a reliquidada vai, a que bate segue pulada"
    assert skipped == 1
    assert _ULTIMA_CHAMADA["vereditos"] == {"381894004": "L", "390629480": "L"}, \
        "o pré-dedup tem de mandar o veredito de cada bloco ao banco"


def test_liquidada_que_bate_continua_pulada():
    saida, skipped = _rodar(UMWIN_RELIQUIDADA,
                            resolvidos={"381894004": "L", "390629480": "L"}, casa="1win")
    assert saida == "" and skipped == 2, "sem contradição o pré-dedup economiza como sempre"


def test_mesma_classe_nao_reabre():
    """Banco HL, texto L: meia derrota e derrota são a mesma classe. Reabrir aqui faria a IA
    reler toda meia a cada captura, e o rótulo do texto nem decide a meia."""
    saida, skipped = _rodar(UMWIN_RELIQUIDADA,
                            resolvidos={"381894004": "HL", "390629480": "L"}, casa="1win")
    assert saida == "" and skipped == 2


def test_bloco_sem_veredito_nao_reabre():
    saida, skipped = _rodar(UMWIN_A_CONFERIR,
                            resolvidos={"381894004": "W", "390629480": "L"}, casa="1win")
    assert saida == "" and skipped == 2, "'a conferir' não prova reliquidação nenhuma"


# ── RC44: a rota do cru grava durante a espera do `/extrair` ─────────────────


def test_rc44_liquidada_pela_rota_do_cru_durante_a_espera_nao_vai_a_ia(monkeypatch):
    """A corrida da 20BET do Gabriel (06/11/2026, parecer 023 §2.3): o "já no banco" do
    pré-dedup deu vazio, a rota do cru gravou as apostas liquidadas enquanto o `/extrair`
    esperava o cru, e a `aplicar` as pulou (`_liquidados`) sem motivo. 129 foram à IA à toa.

    O dublê da Ficha grava no "banco" (o dict do dublê de `get_codigos_resolvidos`) no meio
    da chamada e não resolve nem dá motivo, como a `aplicar` faz com o liquidado. Depois da
    espera o `/extrair` tem de perguntar de novo. Mutação: sem a segunda conferência, as
    duas vão à IA (detectada)."""
    import virada
    banco: dict = {}
    registro = {}

    async def _resolver(dono, casa_key, casa, parceiro, codigos, iguais, **kw):
        banco.update({"475962111": "W", "475962999": "L"})   # a rota do cru gravou agora
        return set(), 0.0, {}, set()

    async def _registrar(dono, casa_key, capturadas, ja_no_banco, pela_ficha, inalterados,
                         para_ia, espera=0.0, motivos=None, segurados=0):
        registro.update(ja_no_banco=ja_no_banco, para_ia=para_ia, motivos=motivos)

    monkeypatch.setattr(virada, "virada", lambda k: True)
    monkeypatch.setattr(virada, "resolver_no_extrair", _resolver)
    monkeypatch.setattr(virada, "registrar", _registrar)
    monkeypatch.setattr(virada, "vigia_por_dia", lambda: 0)
    saida, skipped = _rodar(NOVIBET_UMA_LIQUIDOU, resolvidos=banco)
    assert saida == "" and skipped == 2, "liquidada durante a espera não vai à IA"
    assert registro == {"ja_no_banco": 2, "para_ia": 0, "motivos": {}}

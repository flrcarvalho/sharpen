"""Contrato de texto de 4 campos — Bet365 (s386, `app/contrato_texto.py`).

Dados: `golden_set/contrato_bet365.json` — blocos REAIS da Bet365 e as respostas de IA
JÁ SALVAS (a decisão que a produção gravou para aquele bloco, e os 12 lotes de 4 campos
que o protótipo devolveu). Nenhuma chamada ao modelo: o cliente da API é trocado por um
falso que devolve essas respostas.

O ESPERADO dos números NÃO sai do leitor (senão o teste reimplementaria o código): vem
do banco, onde não há correção registrada, do DINHEIRO do texto (retorno − stake) para o
P/L, e de conta feita à mão onde o banco está errado (as duas múltiplas marcadas).

O QUE ESTE ARQUIVO NÃO COBRE, e é bom saber antes de confiar no verde:
  • a resposta de um modelo de verdade ao prompt enxuto (só respostas salvas);
  • a tela: o `done` é conferido como dado, ninguém renderiza a grade;
  • o banco: a preservação das correções pelo mesmo /salvar está em
    `test_contrato_texto_db.py`, que só roda com `TEST_DATABASE_URL`;
  • outras casas (o módulo só suporta a Bet365, e isso É testado).
"""
import asyncio
import json
import pathlib
import re
import types
from decimal import Decimal

import pytest

import contrato_texto as ct
import main
import repository as repo

_G = json.loads((pathlib.Path(__file__).resolve().parents[1] / "golden_set"
                 / "contrato_bet365.json").read_text(encoding="utf-8"))
ITENS = _G["itens"]
LOTES4 = _G["lotes4"]
CASA, PARCEIRO = "Bet365", "Conta Teste"
_COD = re.compile(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]")


def _texto(itens):
    return "\n\n".join(f"[Código: {i['codigo']}]\n{i['bruto']}" for i in itens)


def _resp(itens, pular=()):
    """A resposta de 4 campos a partir da decisão JÁ GRAVADA pela IA de produção."""
    ls = [f"{i['codigo']}\t{i['ia']['esporte']}\t{i['ia']['aposta']}\t{i['ia']['descricao']}"
          for i in itens if i["codigo"] not in pular]
    return "```tsv\n" + "\n".join(ls) + "\n```"


def _tipo(prefixo):
    return [i for i in ITENS if i["tipo"].startswith(prefixo)]


def _recusados_depois():
    """Os `depois:` que CONTINUAM recusados. Desde a s386 o portão normaliza a forma que o
    MASTER já decide (` @ `→` v `, Mais/Menos de→Over/Under): esses dois golden passaram a
    ser aceitos, com a descrição normalizada (ver `test_forma_normalizada_vira_linha`)."""
    return [i for i in _tipo("depois:") if ct.normalizar_forma(i["ia"]["descricao"]) == i["ia"]["descricao"]]


def _cobertos():
    return [i for i in ITENS if not i["tipo"].startswith(("antes:", "depois:"))]


def _num(s):
    return repo._num_or_none(s)


# ── 1. Desligado por padrão ────────────────────────────────────────────────────

def test_desligado_por_padrao_e_so_a_bet365(monkeypatch):
    monkeypatch.delenv("CONTRATO_TEXTO_CASAS", raising=False)
    assert ct.ligado("BET365") is False
    monkeypatch.setenv("CONTRATO_TEXTO_CASAS", "betano, BET365")
    assert ct.ligado("BET365") is True
    assert ct.ligado("BETANO") is False, "casa fora de CASAS_SUPORTADAS não liga"
    monkeypatch.setenv("CONTRATO_TEXTO_CASAS", "")
    assert ct.ligado("BET365") is False


# ── 2. Números pelo código, contra fonte independente ──────────────────────────

@pytest.mark.parametrize("it", _cobertos(), ids=lambda i: f"{i['tipo']}:{i['codigo']}")
def test_numeros_do_codigo_batem_com_o_banco_e_com_o_dinheiro(it):
    lt = ct.ler_numeros(it["codigo"], it["bruto"])
    assert lt.rota == "coberto", lt.motivos
    c = lt.campos
    b = it["banco"]
    assert b, "o golden só traz item coberto com esperado do banco"
    assert c["data"]["valor"] == b["data"]
    assert abs(c["stake"]["valor"] - _num(b["stake"])) < 0.005
    assert c["resultado"]["valor"] == b["resultado"]
    res = b["resultado"]
    if res in ("W",) and lt.retorno is not None:
        # §5.2.1: em W com retorno, a odd é Retorno ÷ Stake; a prova é o dinheiro.
        assert abs(c["stake"]["valor"] * c["odd"]["valor"] - lt.retorno) <= 0.006
    else:
        # L, V, HW, HL, aberta: a odd é a da casa (ou o produto das pernas), e o banco
        # (ou a conta à mão, onde ele está errado) é a referência.
        assert abs(Decimal(repr(c["odd"]["valor"])) - Decimal(repr(_num(b["odd"])))) < Decimal("1e-9")
    if res and lt.retorno is not None:
        assert abs(c["pl"]["valor"] - (lt.retorno - c["stake"]["valor"])) <= 0.01


def test_multipla_em_que_o_banco_esta_errado_sai_com_o_produto_das_pernas():
    errados = [i for i in ITENS if i.get("banco_odd_errada")]
    assert errados, "o golden tem de carregar os casos de conta errada no banco"
    for it in errados:
        lt = ct.ler_numeros(it["codigo"], it["bruto"])
        assert lt.campos["odd"]["texto"] == it["banco"]["odd"]
        assert lt.campos["odd"]["texto"] != it["banco_odd_errada"]


# ── 3. Encaminhamento, com o motivo NOMEADO ────────────────────────────────────

def test_extensao_antiga_vai_ao_caminho_atual_e_diz_por_que():
    itens = _tipo("antes: Data (encerramento)")
    assert itens
    p = ct.particionar(_texto(itens))
    assert not p.cobertos
    for _c, bloco, motivos in p.atual:
        assert "Data (encerramento)" in motivos[0] and "anterior à s339" in motivos[0]
        assert bloco.startswith("[Código: ")


def test_bloco_sem_data_vai_ao_caminho_atual():
    itens = _tipo("antes: sem data")
    assert itens
    p = ct.particionar(_texto(itens))
    assert [m[0] for _c, _b, m in p.atual] == ["data ausente (nenhuma linha de data)"] * len(itens)


def test_codigo_repetido_ou_vazio_no_texto_nao_entra_no_contrato():
    um = _cobertos()[0]
    dup = ct.particionar(_texto([um, _cobertos()[1], um]))
    assert um["codigo"] not in dup.cobertos
    assert [m[0] for c, _b, m in dup.atual if c == um["codigo"]] == ["código repetido no mesmo texto"] * 2
    vazio = ct.particionar("[Código: ]\n" + um["bruto"] + "\n\n" + _texto([_cobertos()[1]]))
    assert [m[0] for _c, _b, m in vazio.atual] == ["bloco com [Código] vazio"]
    assert list(vazio.cobertos) == [_cobertos()[1]["codigo"]]


def test_prompt_enxuto_e_o_recorte_verbatim_dos_tres_masters_e_do_mapa_da_casa():
    blocos = ct.build_system_enxuto("BET365")
    textos = [b["text"] for b in blocos]
    tudo = "\n".join(textos)
    assert len(blocos) == 4
    assert textos[0].startswith("# MASTER_ESPORTES_2026")
    assert textos[1].startswith("# MASTER_APOSTAS_2026")
    assert textos[2].startswith("# MASTER_DESCRICAO_2026")
    assert "Mapa de mercados" in textos[3] and "Ruído a ignorar" not in textos[3]
    for fora in ("MASTER_PIPELINE_2026\n## Pipeline", "# MASTER_RESULTADO_2026",
                 "# MASTER_OUTPUT_2026", "Validação Final", "Referências auxiliares"):
        assert fora not in tudo, fora
    assert "cache_control" in blocos[2] and "cache_control" in blocos[3]
    assert "cache_control" not in blocos[0]
    # verbatim: um trecho do MASTER sai igual, byte a byte
    principio = "**Princípio fundamental:** a categoria registra o **objeto** da aposta"
    assert principio in textos[1]


def test_rejeitado_depois_da_ia_vai_ao_caminho_atual_e_diz_por_que():
    itens = _recusados_depois()
    assert itens
    p = ct.particionar(_texto(itens))
    assert len(p.cobertos) == len(itens), "estes os NÚMEROS cobrem; quem reprova é a descrição"
    mt = ct.montar(p, _resp(itens), CASA, PARCEIRO)
    assert not mt.linhas
    assert len(mt.rejeitados) == len(itens)
    assert all(m[0].startswith("descrição reprovada") for _c, _b, m in mt.rejeitados)


def test_falso_alarme_do_avaliador_fica_identificado_no_encaminhamento():
    """`-1.0,-1.5` → `-1.25` é o que o MASTER §10.1.1 manda, e o gate de fidelidade o
    reprova. O contrato não resolve isso: encaminha, e o motivo diz qual foi o gate."""
    lote = next(l for l in LOTES4 if any(b["codigo"] == "PR5301560641I" for b in l["blocos"]))
    p = ct.particionar(_texto(lote["blocos"]))
    mt = ct.montar(p, lote["resposta"], CASA, PARCEIRO)
    fora = {c: m for c, _b, m in mt.rejeitados}
    assert "PR5301560641I" in fora
    assert "linha da aposta não existe no bilhete: '1.25'" in fora["PR5301560641I"][0]


# ── 4. Lote misto: sem perda, sem duplicação, sem troca de campos ──────────────

def _lote_misto():
    return ITENS  # todos os tipos juntos, na ordem do golden


def test_lote_misto_cada_bilhete_sai_uma_vez_e_com_os_proprios_numeros():
    texto = _texto(_lote_misto())
    p = ct.particionar(texto)
    mt = ct.montar(p, _resp(_lote_misto()), CASA, PARCEIRO)
    saida = list(mt.linhas) + [c for c, _b, _m in mt.atual]
    assert sorted(saida) == sorted(_COD.findall(texto)), "perda ou duplicação"
    por_cod = {i["codigo"]: i for i in ITENS}
    for cod, linha in mt.linhas.items():
        col = linha.split("\t")
        lt = p.cobertos[cod]
        assert col[10] == cod
        # números: os do PRÓPRIO bloco
        assert (col[0], col[7], col[8], col[9]) == (
            lt.campos["data"]["valor"], lt.campos["stake"]["texto"],
            lt.campos["odd"]["texto"], lt.campos["resultado"]["valor"])
        # rótulos: os da resposta do PRÓPRIO código (salvo o ajuste estrutural nomeado)
        ia = por_cod[cod]["ia"]
        ajustados = {a[1] for a in mt.ajustes if a[0] == cod}
        if "esporte" not in ajustados:
            assert col[1] == ia["esporte"]
        if "aposta" not in ajustados:
            assert col[5] == ia["aposta"]
        assert col[6] == ct.normalizar_forma(ia["descricao"])
        assert (col[2], col[3], col[4]) == ("", CASA, PARCEIRO)


@pytest.mark.parametrize("caso", ["ausente", "duplicada", "inventada", "3 campos",
                                  "categoria", "esporte", "outro jogo"])
def test_defeito_na_resposta_manda_so_aquele_bilhete_ao_caminho_atual(caso):
    alvo = next(i for i in _cobertos() if i["tipo"].startswith("simples"))
    outros = [i for i in _cobertos() if i is not alvo][:5]
    itens = [alvo] + outros
    p = ct.particionar(_texto(itens))
    ls = _resp(itens).split("\n")[1:-1]
    cols = ls[0].split("\t")
    if caso == "ausente":
        ls = ls[1:]
    elif caso == "duplicada":
        ls = ls + [ls[0]]
    elif caso == "inventada":
        ls[0] = "\t".join([cols[0][:-3] + "XYZ"] + cols[1:])
    elif caso == "3 campos":
        ls[0] = "\t".join(cols[:3])
    elif caso == "categoria":
        ls[0] = "\t".join(cols[:2] + ["Qualquer Coisa", cols[3]])
    elif caso == "esporte":
        ls[0] = "\t".join([cols[0], "Bocha Aquatica"] + cols[2:])
    elif caso == "outro jogo":
        ls[0] = "\t".join(cols[:3] + ["Over 2.5 Gols [Time Inventado v Outro Time]"])
    mt = ct.montar(p, "```tsv\n" + "\n".join(ls) + "\n```", CASA, PARCEIRO)
    fora = {c for c, _b, _m in mt.rejeitados}
    assert alvo["codigo"] in fora and alvo["codigo"] not in mt.linhas
    assert set(mt.linhas) == {o["codigo"] for o in outros}, "o resto do lote não pode ir junto"


def test_sistema_leva_a_12a_coluna():
    sis = _tipo("sistema")
    assert sis
    p = ct.particionar(_texto(sis))
    mt = ct.montar(p, _resp(sis), CASA, PARCEIRO)
    assert mt.linhas
    for linha in mt.linhas.values():
        col = linha.split("\t")
        assert len(col) == 12 and re.match(r"^\d+x ", col[11]), linha


def test_multipla_com_categoria_errada_e_ajustada_pelo_codigo_e_nomeada():
    mult = next(i for i in _cobertos() if i["tipo"].startswith("multipla"))
    p = ct.particionar(_texto([mult]))
    ia = dict(mult["ia"], aposta="Gols")
    mt = ct.montar(p, _resp([dict(mult, ia=ia)]), CASA, PARCEIRO)
    assert mt.linhas[mult["codigo"]].split("\t")[5] == "Múltipla"
    assert (mult["codigo"], "aposta", "Gols", "Múltipla") in mt.ajustes


def test_as_respostas_reais_do_prototipo_associam_sem_perda():
    for lote in LOTES4:
        texto = _texto(lote["blocos"])
        p = ct.particionar(texto)
        mt = ct.montar(p, lote["resposta"], CASA, PARCEIRO)
        saida = list(mt.linhas) + [c for c, _b, _m in mt.atual]
        assert sorted(saida) == sorted(_COD.findall(texto))
        assert not mt.descartadas


# ── 5. Ordem final e junção das duas metades ──────────────────────────────────

def test_ordem_final_e_a_do_texto_invertida_com_as_duas_metades_intercaladas():
    texto = _texto(ITENS)
    cods = _COD.findall(texto)
    contrato = [f"d\te\t\tc\tp\ta\tdesc\t1,00\t2\tW\t{c}" for c in cods[0::2]]
    # o caminho de hoje entrega JÁ invertido (é o `_combine_parallel_results`)
    antigas = [f"d\te\t\tc\tp\ta\tdesc\t1,00\t2\tL\t{c}" for c in reversed(cods[1::2])]
    final = ct.ordenar_final(texto, antigas, contrato)
    assert [l.split("\t")[10] for l in final] == list(reversed(cods))


def test_linha_antiga_sem_codigo_nao_some_nem_pula_de_lugar():
    texto = _texto(ITENS[:4])
    cods = _COD.findall(texto)
    antigas = [f"x\t\t\t\t\t\t\t\t\t\t{cods[3]}", "orfa\t\t\t\t\t\t\t\t\t\t",
               f"x\t\t\t\t\t\t\t\t\t\t{cods[1]}"]
    contrato = [f"x\t\t\t\t\t\t\t\t\t\t{c}" for c in (cods[0], cods[2])]
    final = ct.ordenar_final(texto, antigas, contrato)
    assert len(final) == 5
    assert final[1].startswith("orfa"), "fica logo depois da linha que a precedia"


def test_juntar_resultado_preserva_as_notas_do_caminho_antigo():
    antigo = "```tsv\nCAB\nL1\n```\n\n## Notas Críticas\nnota do antigo"
    novo = ct.juntar_resultado(antigo, ["A", "B"], "CAB")
    assert novo.startswith("```tsv\nCAB\nA\nB\n```") and "nota do antigo" in novo
    assert ct.juntar_resultado("", ["A"], "CAB").endswith("## Notas Críticas\nNenhuma")


# ── 6. As correções de hoje, rodadas por cima da linha final ──────────────────

def test_corrigir_stake_tsv_de_producao_nao_muda_nada_na_linha_do_contrato():
    p = ct.particionar(_texto(_cobertos()))
    mt = ct.montar(p, _resp(_cobertos()), CASA, PARCEIRO)
    assert mt.tsv
    tsv2, info = repo.corrigir_stake_tsv(mt.tsv, p.texto_ia)
    assert tsv2 == mt.tsv and info["stakes"] == 0 and info["financeiro"] == 0


def test_linha_final_passa_na_validacao_do_salvar_e_cai_na_mesma_assinatura():
    """O /salvar faz `parse_tsv` → `validar_linhas` → `upsert_bilhetes`. A assinatura de
    bilhete com código é `ID|casa|parceiro|codigo`: a linha do contrato bate na MESMA
    linha do banco que a linha de hoje bateria — e o UPSERT (congelamento, correções) é o
    mesmo SQL para as duas."""
    p = ct.particionar(_texto(_cobertos()))
    mt = ct.montar(p, _resp(_cobertos()), CASA, PARCEIRO)
    rows = repo.parse_tsv(mt.tsv)
    boas, rejeitadas = repo.validar_linhas(rows)
    assert not rejeitadas and len(boas) == len(mt.linhas)
    for r in boas:
        hoje = dict(r, aposta="Outra Coisa", descricao="outra", odd="9,99", stake="1,00")
        assert repo._assinatura(r) == repo._assinatura(hoje)


# ── 7. Juiz da sombra de 4 campos ──────────────────────────────────────────────

def test_juiz_da_sombra_de_4_campos_tem_as_chaves_do_juiz_de_hoje():
    p = ct.particionar(_texto(_cobertos()[:6]))
    chaves_hoje = set(repo.pontuar_saida("", None))
    pl = ct.pontuar_4campos(_resp(_cobertos()[:6]), p)
    assert set(pl) == chaves_hoje
    assert pl["blocos"] == 6 and pl["sem_codigo"] == 0 and pl["cod_inventado"] == 0
    ruim = _resp(_cobertos()[:6], pular={_cobertos()[0]["codigo"]}) + "\nXYZ\ta\tb\n"
    pl2 = ct.pontuar_4campos(ruim, p)
    assert pl2["sem_codigo"] == 1


# ── 8. O fluxo real: /extrair ligado e desligado, sem rede ─────────────────────

class _Transitorio(Exception):
    pass


class _Fin:
    def __init__(self, texto, stop="end_turn"):
        self.stop_reason = stop
        self.usage = types.SimpleNamespace(input_tokens=100, output_tokens=50,
                                           cache_read_input_tokens=1000,
                                           cache_creation_input_tokens=10)
        self.content = [types.SimpleNamespace(type="text", text=texto)]


class _Stream:
    def __init__(self, texto, erro=None):
        self._t, self._e = texto, erro

    async def __aenter__(self):
        if self._e:
            raise self._e
        return self

    async def __aexit__(self, *a):
        return False

    @property
    async def text_stream(self):
        yield self._t

    async def get_final_message(self):
        return _Fin(self._t)


class _ClienteFalso:
    """Devolve, para cada chamada, a resposta SALVA dos códigos que ela recebeu."""

    def __init__(self, respostas, erros=None):
        self.respostas, self.erros = respostas, list(erros or [])
        self.chamadas = []
        self.messages = self

    def stream(self, model, max_tokens, system, messages, **kw):
        txt = messages[0]["content"][0]["text"]
        cods = _COD.findall(txt)
        self.chamadas.append({"system": system, "cods": cods})
        if self.erros:
            e = self.erros.pop(0)
            if e is not None:
                return _Stream("", e)
        corpo = "\n".join(self.respostas[c] for c in cods if c in self.respostas)
        return _Stream("```tsv\n" + corpo + "\n```")


def _linha_hoje(cod):
    """O que o caminho de hoje (falso) devolve para um código: marcada, para a junção
    poder ser conferida sem ambiguidade."""
    return f"01/01/2026\tHOJE\t\t{CASA}\t{PARCEIRO}\tML\tlinha de hoje {cod}\t1,00\t2\tL\t{cod}"


@pytest.fixture
def fluxo(monkeypatch):
    """Liga o /extrair sem rede: IA falsa, caminho de hoje falso, registros capturados."""
    from fastapi.testclient import TestClient
    reg = {"uso": [], "hoje": [], "sombra": [], "sombra_rot": [], "barreira": []}

    async def _hoje(*a, **k):
        texto_x = a[5] if len(a) > 5 else a[4]
        reg["hoje"].append({"texto": texto_x, "caminho": k.get("caminho")})
        cods = _COD.findall(texto_x or "")
        linhas = [_linha_hoje(c) for c in reversed(cods)]
        yield f"data: {json.dumps({'keepalive': True})}\n\n"
        yield "data: " + json.dumps({
            "done": True, "stop_reason": "end_turn", "modelo": "m",
            "resultado": "```tsv\n" + main._TSV_HEADER + "\n" + "\n".join(linhas)
                         + "\n```\n\n## Notas Críticas\nNenhuma",
            "tokens": {"input": 7, "output": 7, "cache_read": 7, "cache_write": 7},
            "cobertura": {"marca": "do caminho de hoje"}}) + "\n\n"

    async def _uso(*a, **k):
        reg["uso"].append({"args": a, "caminho": k.get("caminho")})

    async def _sombra(*a, **k):
        reg["sombra"].append({"args": a, **k})

    async def _rot(*a, **k):
        reg["sombra_rot"].append(a)

    async def _barr(*a, **k):
        reg["barreira"].append(a)

    async def _dedup(texto, *a, **k):
        return texto, 0

    monkeypatch.setattr(main, "_stream_parallel", _hoje)
    monkeypatch.setattr(main, "_stream_sequential", _hoje)
    monkeypatch.setattr(main, "registrar_uso", _uso)
    monkeypatch.setattr(main, "_sombra_modelo", _sombra)
    monkeypatch.setattr(main, "registrar_sombra", _rot)
    monkeypatch.setattr(main, "_barreira_lembrar", _barr)
    monkeypatch.setattr(main, "_dedup_superbet_text", _dedup)
    monkeypatch.setattr(main, "_sombra_vale_agora", lambda: True)
    monkeypatch.setattr(main, "_is_retryable", lambda e: isinstance(e, _Transitorio))
    monkeypatch.setattr(main, "_RETRY_BASE", 0.0)
    main.app.dependency_overrides[main.usuario_atual] = lambda: "TDono"
    cli = TestClient(main.app)

    def extrair(texto, cliente_ia):
        monkeypatch.setattr(main, "_client", cliente_ia)
        r = cli.post("/extrair", data={"casa": CASA, "parceiro": PARCEIRO, "texto": texto})
        assert r.status_code == 200, r.text
        evs = [json.loads(l[6:]) for l in r.text.split("\n") if l.startswith("data: ")]
        return evs

    yield extrair, reg
    main.app.dependency_overrides.pop(main.usuario_atual, None)


def _respostas_salvas(itens):
    return {i["codigo"]: f"{i['codigo']}\t{i['ia']['esporte']}\t{i['ia']['aposta']}\t"
                         f"{i['ia']['descricao']}" for i in itens}


def test_extrair_desligado_e_o_caminho_de_hoje_inteiro(fluxo, monkeypatch):
    extrair, reg = fluxo
    monkeypatch.delenv("CONTRATO_TEXTO_CASAS", raising=False)
    ia = _ClienteFalso(_respostas_salvas(ITENS))
    texto = _texto(ITENS)
    evs = extrair(texto, ia)
    assert ia.chamadas == [], "desligado não chama o contrato"
    assert len(reg["hoje"]) == 1 and reg["hoje"][0]["caminho"] is None
    assert reg["hoje"][0]["texto"] == texto
    done = evs[-1]
    assert done["done"] and "contrato" not in done


def test_extrair_ligado_lote_misto_ponta_a_ponta(fluxo, monkeypatch):
    extrair, reg = fluxo
    monkeypatch.setenv("CONTRATO_TEXTO_CASAS", "BET365")
    # 1ª chamada falha ANTES do 1º token (transitória) e é repetida: conta como tentativa.
    ia = _ClienteFalso(_respostas_salvas(ITENS), erros=[_Transitorio("503")])
    texto = _texto(ITENS)
    evs = extrair(texto, ia)
    done = evs[-1]
    assert done["done"], evs[-3:]

    p = ct.particionar(texto)
    finais = main._extract_tsv_rows(done["resultado"])
    cods_final = [l.split("\t")[10] for l in finais]
    # sem perda, sem duplicação, na ordem de hoje (texto invertido)
    assert cods_final == list(reversed(_COD.findall(texto)))
    # o caminho de hoje recebeu SÓ os encaminhados (antes + depois), marcado
    assert len(reg["hoje"]) == 1 and reg["hoje"][0]["caminho"] == "atual_pos_contrato"
    hoje = set(_COD.findall(reg["hoje"][0]["texto"]))
    info = done["contrato"]
    assert len(hoje) == info["encaminhados_antes"] + info["rejeitados_depois"]
    assert info["encaminhados_antes"] == len(p.atual)
    # EXATO: só os que a própria resposta salva reprova. Um a mais é bilhete bom que
    # voltou a pagar o caminho caro (ex.: ler só a resposta do 1º lote) — sem erro nenhum.
    assert info["rejeitados_depois"] == len(_recusados_depois())
    assert len(ct.lotes_ia(p, main._BILHETES_POR_CHUNK)) > 1, "o lote tem de exercitar várias chamadas"
    # cada linha veio do lado certo, sem troca de campos
    for linha in finais:
        cod = linha.split("\t")[10]
        if cod in hoje:
            assert linha == _linha_hoje(cod)
        else:
            lt = p.cobertos[cod]
            col = linha.split("\t")
            assert (col[0], col[7], col[8], col[9]) == (
                lt.campos["data"]["valor"], lt.campos["stake"]["texto"],
                lt.campos["odd"]["texto"], lt.campos["resultado"]["valor"])
    # sistema com a 12ª coluna, também no fluxo
    for it in _tipo("sistema"):
        if it["codigo"] not in hoje:
            linha = next(l for l in finais if l.split("\t")[10] == it["codigo"])
            assert len(linha.split("\t")) == 12
    # custo completo: contrato registrado à parte, com tentativas contadas
    contrato4 = [u for u in reg["uso"] if u["caminho"] == "contrato4"]
    assert len(contrato4) == 1
    n_lotes = len(ct.lotes_ia(p, main._BILHETES_POR_CHUNK))
    assert info["chamadas"] == n_lotes and info["tentativas"] == 1
    assert len(ia.chamadas) == n_lotes + 1
    tk = contrato4[0]["args"][5]
    assert tk == {"input": 100 * n_lotes, "output": 50 * n_lotes,
                  "cache_read": 1000 * n_lotes, "cache_write": 10 * n_lotes}
    assert done["tokens"]["input"] == 100 * n_lotes + 7, "tokens do done = as duas metades"
    # o prompt que a IA recebeu é o ENXUTO
    assert ia.chamadas[-1]["system"] == ct.build_system_enxuto("BET365")
    # sombra do Haiku: mesmo system, mesmos lotes, juiz de 4 campos, marcada
    s4 = [s for s in reg["sombra"] if s.get("contrato") == "contrato4"]
    assert len(s4) == 1 and s4[0]["args"][2] == ct.build_system_enxuto("BET365")
    assert len(s4[0]["args"][3]) == n_lotes
    # o resto do `done` do caminho de hoje chega intacto
    assert done["cobertura"] == {"marca": "do caminho de hoje"}
    assert done["scroll_overlap_indices"] == []
    # barreira de recaptura e sombra do tradutor lembram SÓ os aceitos (os rejeitados, o
    # caminho de hoje lembra — e aqui ele é falso, então não lembra nada)
    aceitos = set(cods_final) - hoje
    assert len(reg["barreira"]) == 1 and set(_COD.findall(reg["barreira"][0][2])) == aceitos
    assert len(reg["sombra_rot"]) == 1 and set(_COD.findall(reg["sombra_rot"][0][2])) == aceitos


def test_os_dois_geradores_de_hoje_repassam_o_caminho_ao_registro_de_uso():
    import inspect
    for f in (main._stream_parallel, main._stream_sequential):
        src = inspect.getsource(f)
        assert "caminho: str | None = None" in src
        assert "total_tokens, caminho=caminho))" in src, f.__name__


def test_sombra_de_modelo_no_contrato_julga_pelos_4_campos(monkeypatch):
    itens = _cobertos()[:6]
    p = ct.particionar(_texto(itens))
    gravado = {}

    async def _grava(*a, **k):
        gravado["args"], gravado["kw"] = a, k

    monkeypatch.setattr(main, "_client", _ClienteFalso(_respostas_salvas(itens)))
    monkeypatch.setattr(main, "registrar_sombra_modelo", _grava)
    lotes = [[{"type": "text", "text": t}, {"type": "text", "text": "instr"}]
             for t in ct.lotes_ia(p, 6)]
    asyncio.run(main._sombra_modelo("TDono", CASA, [], lotes, p.texto_ia, "claude-sonnet-5",
                                    contrato="contrato4", particao=p))
    placar = gravado["args"][7]
    assert gravado["kw"] == {"contrato": "contrato4"}
    assert placar["blocos"] == 6 and placar["linhas"] == 6
    assert placar["coluna_comida"] == 0, "o juiz de 11 colunas marcaria as 6"


def test_extrair_ligado_lote_do_contrato_que_falha_vai_inteiro_ao_caminho_de_hoje(fluxo, monkeypatch):
    extrair, reg = fluxo
    monkeypatch.setenv("CONTRATO_TEXTO_CASAS", "BET365")
    cob = _cobertos()[:4]
    ia = _ClienteFalso(_respostas_salvas(cob), erros=[RuntimeError("fatal")])
    evs = extrair(_texto(cob), ia)
    done = evs[-1]
    assert done["done"]
    assert done["contrato"]["motivos_depois"] == {"chamada do contrato falhou": len(cob)}
    assert sorted(_COD.findall(reg["hoje"][0]["texto"])) == sorted(i["codigo"] for i in cob)
    assert len(main._extract_tsv_rows(done["resultado"])) == len(cob)


def test_extrair_ligado_sem_nada_coberto_nao_chama_o_contrato(fluxo, monkeypatch):
    extrair, reg = fluxo
    monkeypatch.setenv("CONTRATO_TEXTO_CASAS", "BET365")
    antes = _tipo("antes:")
    ia = _ClienteFalso({})
    done = extrair(_texto(antes), ia)[-1]
    assert ia.chamadas == [] and not [u for u in reg["uso"] if u["caminho"] == "contrato4"]
    assert done["contrato"]["encaminhados_antes"] == len(antes)
    assert len(main._extract_tsv_rows(done["resultado"])) == len(antes)


def test_extrair_ligado_falha_do_caminho_de_hoje_derruba_o_lote(fluxo, monkeypatch):
    extrair, reg = fluxo
    monkeypatch.setenv("CONTRATO_TEXTO_CASAS", "BET365")

    async def _quebra(*a, **k):
        yield "data: " + json.dumps({"error": "falhou"}) + "\n\n"

    monkeypatch.setattr(main, "_stream_parallel", _quebra)
    monkeypatch.setattr(main, "_stream_sequential", _quebra)
    evs = extrair(_texto(ITENS), _ClienteFalso(_respostas_salvas(ITENS)))
    assert evs[-1] == {"error": "falhou"}
    assert not any(e.get("done") for e in evs), "entregar só a metade esconderia a perda"


def test_extrair_ligado_imagem_segue_o_caminho_de_hoje():
    """Lote com imagem, PDF, CSV ou XLS nunca entra no contrato (é o `so_texto`)."""
    import inspect
    src = inspect.getsource(main.extrair)
    assert "so_texto and _contrato.ligado(casa_key)" in src
    assert 'base_content[0].get("type") == "text"' in src and "not betfair_dates" in src


def test_descricao_truncada_nao_passa_no_portao():
    """s386: com a saída cortada no meio (`[Independi`), a linha passava nos gates de forma
    e era gravada. Todo confronto aberto tem de fechar, e a descrição termina nele."""
    import taxonomia
    it = next(i for i in ITENS if i.get("ia", {}).get("descricao", "").endswith("]"))
    lt = ct.ler_numeros(it["codigo"], it["bruto"])
    esp, cat = set(taxonomia.esportes_canonicos()), set(taxonomia.categorias_canonicas())
    e, a, d = it["ia"]["esporte"], it["ia"]["aposta"], it["ia"]["descricao"]
    assert ct.aceitar_4campos(lt, e, a, d, esp, cat)[3] is None
    cortada = d[:d.rindex("[") + 4]
    motivo = ct.aceitar_4campos(lt, e, a, cortada, esp, cat)[3]
    assert motivo and "truncada" in motivo


def test_forma_da_casa_e_normalizada_sem_mudar_o_sentido():
    """s386: sem pensamento, o Sonnet copiava `A @ B` e `Mais de` da casa; o portão recusava
    (§5, §11) e o bloco pagava o caminho atual. Separador e Over/Under o código decide."""
    d = "Aaron Judge - Mais de 1.5 Bases [NY Yankees @ BOS Red Sox] // Menos de 8.5 Corridas [A @ B]"
    assert ct.normalizar_forma(d) == ("Aaron Judge - Over 1.5 Bases [NY Yankees v BOS Red Sox]"
                                      " // Under 8.5 Corridas [A v B]")
    # o que está DENTRO do confronto (nomes) nunca é tocado, só o separador
    assert ct.normalizar_forma("Over 2.5 Gols [Mais de Mil FC v B]") == "Over 2.5 Gols [Mais de Mil FC v B]"
    # idempotente e neutro no que já está na forma
    ok = "Over 2.5 Gols [A v B]"
    assert ct.normalizar_forma(ok) == ok


def test_forma_normalizada_vira_linha_e_o_ajuste_fica_nomeado():
    normalizaveis = [i for i in _tipo("depois:") if i not in _recusados_depois()]
    assert len(normalizaveis) == 2
    p = ct.particionar(_texto(normalizaveis))
    mt = ct.montar(p, _resp(normalizaveis), CASA, PARCEIRO)
    for i in normalizaveis:
        linha = mt.linhas[i["codigo"]].split("	")
        assert linha[6] == ct.normalizar_forma(i["ia"]["descricao"])
        assert "Mais de" not in linha[6] and "Menos de" not in linha[6]
        assert any(a[0] == i["codigo"] and a[1] == "descricao" for a in mt.ajustes)

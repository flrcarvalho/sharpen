# -*- coding: utf-8 -*-
"""Gate da sessão efêmera do /realtrial (Fatia 3).

O QUE ESTE ARQUIVO **NÃO** COBRE:
  · não toca o banco — `criar_sessao_trial` e `_purgar_trials` não são
    exercitadas. A purga por idade e o `starts_with` só têm prova de leitura.
  · não prova o caminho HTTP de ponta a ponta (a rota é exercitada por
    `escopo_de_leitura` e pelos gates de token, não por um cliente real).
  · não prova que o SharpenUp captura para a base do trial — isso é o
    navegador do visitante contra produção.

O que ele cobre é a regra que não pode falhar: **um visitante nunca vê o que
outro capturou**, e o trial não escreve na base de demonstração.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "app"))

import auth  # noqa: E402


def _cache(**usuarios):
    """Troca o cache de identidade por um controlado (e devolve o anterior)."""
    antes = auth._usuarios_cache
    auth._usuarios_cache = {
        u: {"senha_hash": None, "status": "ativo", "role": "user",
            "parent_owner": p, "planilha_url": None}
        for u, p in usuarios.items()
    }
    return antes


# ── escopo de leitura ────────────────────────────────────────────────────────
def test_trial_le_a_propria_base_e_a_da_demonstracao():
    antes = _cache(trial_abc123=None, realtrial=None)
    try:
        assert auth.escopo_de_leitura("trial_abc123") == ["trial_abc123", "realtrial"]
    finally:
        auth._usuarios_cache = antes


def test_UM_TRIAL_NUNCA_VE_O_OUTRO():
    """A regra que nao pode falhar. O visitante usa o SharpenUp na casa DELE,
    com apostas reais dele; se o escopo de um trial alcancasse outro, a
    carteira real de uma pessoa apareceria para a proxima que abrisse o link."""
    antes = _cache(trial_aaa=None, trial_bbb=None, realtrial=None)
    try:
        escopo = auth.escopo_de_leitura("trial_aaa")
        assert "trial_bbb" not in escopo
        assert escopo == ["trial_aaa", "realtrial"]
    finally:
        auth._usuarios_cache = antes


def test_conta_normal_nao_ganha_a_base_de_demonstracao():
    """A uniao do trial nao pode vazar para quem tem conta de verdade: o
    supervisor veria 48 mil bilhetes ficticios misturados no P/L dele."""
    antes = _cache(Feca=None, Lava="Feca", realtrial=None)
    try:
        escopo = auth.escopo_de_leitura("Feca")
        assert "realtrial" not in escopo
        assert escopo == ["Feca", "Lava"]     # dono + operador, como sempre foi
    finally:
        auth._usuarios_cache = antes


def test_operador_comum_continua_vendo_so_a_propria_base():
    antes = _cache(Feca=None, Lava="Feca", realtrial=None)
    try:
        assert auth.escopo_de_leitura("Lava") == ["Lava"]
    finally:
        auth._usuarios_cache = antes


def test_o_proprio_dono_da_demonstracao_nao_se_duplica():
    antes = _cache(realtrial=None)
    try:
        assert auth.escopo_de_leitura("realtrial") == ["realtrial"]
    finally:
        auth._usuarios_cache = antes


def test_eh_trial_so_pelo_prefixo():
    assert auth.eh_trial("trial_abc")
    assert not auth.eh_trial("Feca")
    assert not auth.eh_trial("")
    assert not auth.eh_trial(None)


# ── o trial NAO escreve na base de demonstracao ──────────────────────────────
def test_trial_nao_pode_ver_como_a_demonstracao():
    """`pode_ver_como` e' o unico portao que troca o dono EFETIVO (o que as
    rotas de escrita usam). Se um trial pudesse assumir `realtrial`, ele
    editaria e apagaria a base compartilhada."""
    antes = _cache(trial_aaa=None, realtrial=None)
    try:
        assert not auth.pode_ver_como("trial_aaa", "realtrial")
        assert not auth.pode_ver_como("trial_aaa", "Feca")
        assert auth.pode_ver_como("trial_aaa", "trial_aaa")
    finally:
        auth._usuarios_cache = antes


def test_demonstracao_nao_vira_supervisora_dos_trials():
    """Se os trials fossem pendurados em `realtrial` por `parent_owner`, o dono
    da demonstracao passaria a enxergar a carteira REAL de todo visitante."""
    antes = _cache(trial_aaa="realtrial", realtrial=None)
    try:
        # Mesmo com o parent_owner apontando para la (configuracao errada), o
        # escopo do trial continua sendo ele + a demo, e nunca outro trial.
        assert auth.escopo_de_leitura("trial_aaa") == ["trial_aaa", "realtrial"]
    finally:
        auth._usuarios_cache = antes


# ── cache de identidade ──────────────────────────────────────────────────────
def test_registrar_no_cache_vale_na_hora():
    """Sem isto a sessao nasce morta: `ler_token` exige usuario ATIVO no cache
    e o refresher so passa a cada 60 s."""
    antes = _cache(Feca=None)
    try:
        assert not auth._usuario_ativo("trial_novo")
        auth.registrar_usuario_no_cache("trial_novo", {
            "senha_hash": None, "status": "ativo", "role": "user",
            "parent_owner": None, "planilha_url": None})
        assert auth._usuario_ativo("trial_novo")
    finally:
        auth._usuarios_cache = antes


def test_registrar_no_cache_troca_o_dict_inteiro():
    """A invariante do modulo e' leitura sem lock: o cache e' SUBSTITUIDO, nunca
    mutado item a item."""
    antes = _cache(Feca=None)
    try:
        ref = auth._usuarios_cache
        auth.registrar_usuario_no_cache("trial_x", {"status": "ativo"})
        assert auth._usuarios_cache is not ref, "mutou o dict em vez de trocar"
        assert "Feca" in auth._usuarios_cache, "perdeu quem ja estava no cache"
    finally:
        auth._usuarios_cache = antes


def test_token_de_trial_sobrevive_aos_gates_de_ler_token():
    """Conta sem senha: `impressao_senha` devolve a constante de 'sem hash', e
    o gate de senha do `ler_token` compara igual contra igual. Se isso mudasse,
    todo cookie de trial morreria na primeira request."""
    antes = _cache(trial_zzz=None)
    try:
        token = auth.criar_token("trial_zzz")
        assert auth.ler_token(token) == "trial_zzz"
    finally:
        auth._usuarios_cache = antes


def test_trial_suspenso_perde_a_sessao_na_hora():
    """Mesmo gate de status de qualquer conta: e' o que faz a purga expulsar
    quem ja esta com o cookie na mao."""
    antes = _cache(trial_zzz=None)
    try:
        token = auth.criar_token("trial_zzz")
        auth.registrar_usuario_no_cache("trial_zzz", {
            "senha_hash": None, "status": "suspenso", "role": "user",
            "parent_owner": None, "planilha_url": None})
        assert auth.ler_token(token) is None
    finally:
        auth._usuarios_cache = antes


def test_trial_nao_loga_pela_tela_de_login():
    """A conta nasce sem hash, e `verificar_credenciais` e' fail-closed. A
    unica porta do trial e' o cookie que a rota entrega."""
    antes = _cache(trial_zzz=None)
    try:
        assert not auth.verificar_credenciais("trial_zzz", "")
        assert not auth.verificar_credenciais("trial_zzz", "qualquer")
    finally:
        auth._usuarios_cache = antes


# ── tetos de uso (Fatia 4) ───────────────────────────────────────────────────
# NAO COBERTO aqui: o caminho HTTP do 429 (exige cliente e banco). O que se
# prova e' a REGRA e a ordem em que ela e aplicada no arquivo.
def test_tetos_existem_e_sao_finitos():
    """Teto ausente ou infinito transforma a rota publica num endpoint de IA
    gratuito -- cada extracao custa dinheiro de verdade."""
    assert isinstance(auth.TRIAL_MAX_EXTRACOES, int)
    assert 0 < auth.TRIAL_MAX_EXTRACOES <= 50
    assert isinstance(auth.TRIAL_SESSOES_POR_IP, int)
    assert 0 < auth.TRIAL_SESSOES_POR_IP <= 10


def test_o_teto_e_conferido_ANTES_de_ler_o_upload():
    """A chamada a IA e' o que custa, mas processar o upload gasta banda e
    memoria. Recusar depois de ler os arquivos e' pagar por quem foi barrado.

    Le o arquivo REAL (recorte), nunca uma copia do trecho."""
    fonte = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    # Ancorar num laco especifico (`for img in imagens:`) nao serve: uma leitura
    # com OUTRO nome de variavel passaria na frente do teto sem quebrar o teste
    # -- medido, foi a unica mutacao que escapou na 1a rodada. A ancora certa e'
    # a PRIMEIRA mencao ao upload dentro do CORPO da rota, seja qual for a forma.
    corpo = fonte[fonte.index("async def extrair("):]
    corpo = corpo[corpo.index("):") + 2:]          # pula a assinatura
    i_teto = corpo.index("TRIAL_MAX_EXTRACOES")
    i_upload = min(corpo.index("imagens"), corpo.index("pdfs"))
    assert i_teto < i_upload, "o teto do trial ficou DEPOIS da leitura do upload"


def test_o_teto_de_extracao_vive_no_BANCO_nao_em_memoria():
    """Contador em memoria zera no deploy, e o Railway faz deploy o tempo todo:
    bastaria esperar um restart para ganhar creditos novos. O de IP pode ser em
    memoria porque ele nao guarda dinheiro, so atrito."""
    fonte = (RAIZ / "app" / "repository.py").read_text(encoding="utf-8")
    assert "async def extracoes_do_trial" in fonte
    assert "FROM uso_tokens WHERE dono" in fonte


def test_so_o_trial_e_limitado():
    """Conta de verdade nao pode tomar 429 por causa deste teto."""
    fonte = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    i = fonte.index("TRIAL_MAX_EXTRACOES")
    trecho = fonte[max(0, i - 600):i]
    assert "eh_trial(dono)" in trecho, "o teto nao esta atras do gate de trial"


# ── dono_leitura: so LEITURA, nunca escrita ──────────────────────────────────
def _rotas_do_main():
    """Recorta do main.py REAL cada (metodo, rota, assinatura). Nunca uma copia
    do trecho: copiar o codigo para o teste e' o 1o modo de falso verde."""
    import re
    fonte = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    pad = re.compile(
        r'@app\.(get|post|patch|delete|put)\("([^"]+)"[^)]*\)\s*\n'
        r'(?:async )?def [a-zA-Z_0-9]+\((.*?)\)\s*:', re.S)
    return [(m.group(1), m.group(2), m.group(3)) for m in pad.finditer(fonte)]


def test_NENHUMA_rota_de_escrita_usa_dono_leitura():
    """`dono_leitura` faz o visitante ler a base de demonstracao. Numa rota de
    ESCRITA isso o faria EDITAR e APAGAR a base que todo mundo ve -- de uma
    tacada, e sem erro nenhum. E' o gate mais importante deste arquivo."""
    ruins = [(m, r) for m, r, a in _rotas_do_main()
             if m != "get" and "dono_leitura" in a]
    assert not ruins, f"rota de escrita lendo a base compartilhada: {ruins}"


def test_o_feed_e_os_eventos_NAO_usam_dono_leitura():
    """Os dois montam a uniao por `escopo_de_leitura`. Com `dono_leitura` o
    escopo viraria ['realtrial'] e o visitante perderia de vista o que ele
    mesmo capturou -- justamente o que a demonstracao existe para provar."""
    for metodo, rota, args in _rotas_do_main():
        if rota in ("/dashboard/data", "/eventos"):
            assert "dono_leitura" not in args, f"{rota} nao pode usar dono_leitura"
            assert "dono_efetivo" in args, f"{rota} perdeu o dono_efetivo"


def test_as_telas_de_gestao_leem_a_base_de_demonstracao():
    """MEDIDO antes do conserto: 270 contas e 110 tipsters existiam e as telas
    mostravam ZERO, porque filtravam pelo dono efemero do visitante."""
    por_rota = {r: a for m, r, a in _rotas_do_main() if m == "get"}
    for rota in ("/parceiros", "/tipsters/cadastro", "/caixa/visao",
                 "/custos/store", "/custos/conta", "/casas/config"):
        assert rota in por_rota, f"{rota} sumiu do main.py"
        assert "dono_leitura" in por_rota[rota], f"{rota} voltou a nascer vazia"


def test_dono_leitura_so_desvia_para_o_trial():
    """Conta de verdade nao pode passar a ler a base de demonstracao: o
    supervisor veria 48 mil bilhetes ficticios na propria tela."""
    fonte = (RAIZ / "app" / "auth.py").read_text(encoding="utf-8")
    corpo = fonte[fonte.index("def dono_leitura("):]
    corpo = corpo[:corpo.index("def registrar_usuario_no_cache")]
    assert "eh_trial(real)" in corpo, "o desvio nao esta atras do gate de trial"
    assert "return dono_efetivo(request)" in corpo, "conta normal perdeu o caminho normal"

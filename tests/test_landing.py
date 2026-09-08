"""Landing de venda — hoje em PRÉVIA (s294), não publicada.

A página chegou a servir a rota `/` por uns 20 minutos e foi retirada no mesmo dia,
a pedido do Feca: *"para uma primeira versão tá bom, mas não quero ela online"*. Ela
vive em `/landing`, que exige sessão.

O que estes testes travam, e por que cada um existe:

  1. NINGUÉM DE FORA ALCANÇA. Anônimo em `/` e em `/landing` vai para o login. Este
     é o teste que impede a página de voltar ao ar por acidente — um refactor
     distraído no `root()` republicaria uma peça de marketing inacabada, e nada
     no app quebraria para avisar.
  2. O FECA CONSEGUE REVISAR. Com sessão, `/landing` serve a página. Sem isso a
     prévia não serve para nada e alguém a devolveria para `/` só para poder vê-la.
  3. IMAGEM REFERENCIADA EXISTE NO DISCO. `<img>` quebrado não derruba página
     nenhuma: ela só fica com um buraco, e quem descobre é o visitante. Como as
     imagens nascem de um pipeline manual (`scripts/demo/capturar.mjs` →
     `otimizar.py`), esquecer de regerar é o erro provável.
  4. DARK ONLY. A regra de marca (docs/marketing/README.md) já foi quebrada uma
     vez: um bloco de tema claro fez o documento sair BRANCO para quem tinha o
     SO em tema claro. Aqui o gate é o mesmo, na página que o público vê.
  5. O CTA CHEGA NO CADASTRO. Este é o acoplamento silencioso: a landing aponta
     para `/login#cadastro` e quem trata esse hash é o `login.html`. Some o
     handler lá e o botão continua funcionando — só que entrega o formulário
     ERRADO, sem erro nenhum, para todo visitante que decidiu criar conta.

NÃO cobre: aparência. Nada aqui mede contraste, espaçamento ou se o print está
legível — isso é olho humano e `node scripts/tokens/check-tokens.mjs`.
"""
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

cliente = TestClient(main.app)

ESTATICO = Path(main.__file__).parent / "static"
LANDING = ESTATICO / "landing.html"


def _landing_txt() -> str:
    return LANDING.read_text(encoding="utf-8")


# Frase do <h1>. Na s331 o topo passou a prometer PRATICIDADE, que é o que o
# apostador quer saber: um robô que planilha por ele. As versões anteriores
# prometiam uma subtração ("você lucra menos do que pensa") e depois controle.
TITULO = "30 minutos por semana"


# ── 1. ninguém de fora alcança ───────────────────────────────────────────────
def test_anonimo_nao_ve_a_landing_em_lugar_nenhum():
    for rota in ("/", "/landing"):
        r = cliente.get(rota, follow_redirects=False)
        assert r.status_code == 303, f"{rota}: esperado redirect, veio {r.status_code}"
        assert r.headers["location"] == "/login", f"{rota} -> {r.headers.get('location')}"


def test_a_pagina_se_declara_nao_indexavel_enquanto_for_previa():
    """`noindex` e a rota andam JUNTOS: publicar é mexer nos dois.

    Sozinho, cada um falha em silêncio — página pública com `noindex` não aparece
    no Google (o motivo de existir), e página em prévia com `index` seria indexada
    no dia em que a rota voltasse. Este teste amarra os dois estados.
    """
    html = _landing_txt()
    publica = "/landing" not in Path(main.__file__).read_text(encoding="utf-8")
    if publica:
        assert 'content="index, follow"' in html, "a landing está pública e mandou o Google ignorá-la"
    else:
        assert 'content="noindex, nofollow"' in html, (
            "a landing está em PRÉVIA (rota /landing existe) mas se declara indexável"
        )


# ── 2. o Feca consegue revisar ───────────────────────────────────────────────
def test_com_sessao_a_previa_abre():
    r = cliente.get("/landing", cookies={auth.COOKIE_NAME: auth.criar_token("Feca")},
                    follow_redirects=False)
    assert r.status_code == 200
    assert TITULO in r.text


def test_logado_continua_caindo_no_planilhador():
    r = cliente.get("/", cookies={auth.COOKIE_NAME: auth.criar_token("Feca")},
                    follow_redirects=False)
    assert r.status_code == 200
    # O Planilhador não tem o título da landing; a landing não tem a grade.
    assert TITULO not in r.text


# ── 3. imagens ───────────────────────────────────────────────────────────────
def test_toda_imagem_referenciada_existe_no_disco():
    refs = set(re.findall(r'(?:src|content)="(/static/[^"]+\.(?:webp|svg|png|jpg))"',
                          _landing_txt()))
    assert refs, "nenhuma imagem encontrada — o recorte do regex quebrou?"
    faltando = [u for u in refs if not (ESTATICO / u.removeprefix("/static/")).exists()]
    assert not faltando, (
        f"{len(faltando)} imagem(ns) referenciada(s) e ausente(s): {faltando}. "
        "Regere com scripts/demo/capturar.mjs + scripts/demo/otimizar.py."
    )


def test_imagem_de_print_declara_dimensao():
    """Sem width/height a página pula quando cada print carrega (layout shift)."""
    for tag in re.findall(r"<img\b[^>]*>", _landing_txt()):
        if "/static/landing/img/" not in tag:
            continue
        assert "width=" in tag and "height=" in tag, f"<img> sem dimensão: {tag[:110]}"


# ── 4. dark only ─────────────────────────────────────────────────────────────
def test_sem_tema_claro():
    css = re.sub(r"/\*.*?\*/", "", _landing_txt(), flags=re.S)   # ignora comentário
    assert "prefers-color-scheme" not in css
    assert '[data-theme="light"]' not in css
    assert 'data-theme="dark"' in _landing_txt()


# ── 5. o CTA chega onde promete ──────────────────────────────────────────────
def test_cta_de_cadastro_tem_quem_o_atenda_no_login():
    assert '/login#cadastro' in _landing_txt(), "a landing perdeu o CTA de cadastro"
    login = (ESTATICO / "login.html").read_text(encoding="utf-8")
    assert "#cadastro" in login, (
        "login.html não trata o hash #cadastro: o CTA da landing continua "
        "clicável e entrega o formulário de LOGIN a quem quis criar conta."
    )
    assert re.search(r"location\.hash\s*===\s*'#cadastro'", login), (
        "o handler do #cadastro sumiu ou mudou de forma no login.html"
    )

# ── 6. sem travessão: a voz não pode soar de robô ────────────────────────────
def test_nenhum_travessao_no_texto():
    """Regra de marca do Feca (s331): *"não utilizamos traço largo em frases.

    Não temos linguagem artificial de ChatGPT."* O travessão virou assinatura de
    texto gerado por IA, e uma peça de venda que o leitor identifica como escrita
    por robô perde a confiança antes do argumento.

    O gate existe porque regra sem gate não se cumpre neste repo: a página tinha
    **69** travessões quando a regra foi dita.

    Três caracteres parecidos convivem no arquivo e só UM é proibido. Os outros
    dois são load-bearing e o teste prova que continuam lá:
      U+2014 EM DASH      —   proibido
      U+2212 MINUS SIGN   −   o menos do dinheiro (UI_REFERENCE §5.1)
      U+2500 BOX DRAWING  ─   as réguas dos comentários de CSS
    """
    txt = _landing_txt()
    assert "\u2014" not in txt, (
        "travessão (U+2014) voltou à landing: use ponto, vírgula ou parênteses. "
        "Se a frase só funciona com travessão, ela está comprida demais."
    )
    assert "\u2212" in txt, "o menos do dinheiro (U+2212) sumiu junto: era para ficar"


# ── 7. vídeo referenciado existe no disco ────────────────────────────────────
def test_todo_video_referenciado_existe():
    """Irmão do teste 3, para a mídia que entrou na s331.

    O teste 3 cobre `<img>`. Os clipes entraram como `<video>` com dois `<source>`
    e um `poster`, e nada disso passa por lá. `<video>` quebrado é PIOR que `<img>`
    quebrado: não deixa buraco na página, simplesmente não toca, e o visitante não
    tem como saber que devia haver movimento ali.

    NÃO cobre: se o clipe mostra o que a legenda promete. Isso é olho humano.
    """
    txt = _landing_txt()
    refs = re.findall(r'(?:src|poster)="(/static/landing/video/[^"]+)"', txt)
    assert refs, "a landing não referencia vídeo nenhum: o teste virou no-op"
    for ref in refs:
        caminho = ESTATICO / ref.removeprefix("/static/")
        assert caminho.exists(), f"vídeo referenciado e ausente no disco: {ref}"
        assert caminho.stat().st_size > 1024, f"vídeo vazio ou truncado: {ref}"

    # Todo <video> precisa dos DOIS formatos: webm não toca em Safari antigo e o
    # visitante ficaria com o poster parado, sem erro nenhum.
    assert txt.count("<video") == txt.count('type="video/webm"'), \
        "algum <video> ficou sem source webm"
    assert txt.count("<video") == txt.count('type="video/mp4"'), \
        "algum <video> ficou sem source mp4 (Safari não toca só webm)"

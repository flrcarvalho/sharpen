"""Landing pública em `/` (s294) — a única porta de entrada de quem ainda não é cliente.

O que estes testes travam, e por que cada um existe:

  1. VISITANTE VÊ A LANDING. Até a s294 `/` mandava todo mundo para `/login`, que
     é a tela de quem JÁ tem conta. Se um refactor restaurar o redirect, a
     sharpen.bet volta a não ter o que mostrar — e nada no app quebraria para
     avisar.
  2. SESSÃO CONTINUA MANDANDO. Quem está logado tem de cair no Planilhador ao
     digitar o domínio, como sempre foi. É a metade da mudança que não pode
     regredir junto.
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


# ── 1. visitante ─────────────────────────────────────────────────────────────
def test_visitante_recebe_a_landing_e_nao_o_login():
    r = cliente.get("/", follow_redirects=False)
    assert r.status_code == 200, f"esperado 200, veio {r.status_code} (redirect de volta?)"
    corpo = r.text
    # Âncoras de conteúdo, não de markup: o teste não pode passar só porque
    # alguma página respondeu 200.
    assert "landing" in corpo or "Criar conta" in corpo
    assert "O seu resultado" in corpo


# ── 2. sessão ────────────────────────────────────────────────────────────────
def test_logado_continua_caindo_no_planilhador():
    r = cliente.get("/", cookies={auth.COOKIE_NAME: auth.criar_token("Feca")},
                    follow_redirects=False)
    assert r.status_code == 200
    # O Planilhador não tem o título da landing; a landing não tem a grade.
    assert "O seu resultado, depois dos custos" not in r.text


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

"""Identidade do bloco de tipster da sidebar: nome, plano e a ponte dono → vitrine (s362).

O bloco separa IDENTIDADE (o nome, em sans) de DIREITO DE ACESSO (o plano, selo âmbar),
e só consegue dar tipografia diferente a cada um porque eles são campos diferentes no
registro. Enquanto o plano vivia colado no nome (`Soh Props - Vip`), a tela não tinha
como separá-los, e o nome inteiro lia como rótulo.

O que este arquivo NÃO cobre: `resumo_perfil` e as rotas `/conta/*` (precisam do
Postgres, que só existe no CI) e a aparência do bloco (isso se mede renderizando).
"""
import pathlib
import re
import sys

import pytest

sys.path.insert(0, "app")
import main  # noqa: E402


REGISTRO = main.TIPSTERS_PUBLICOS


def test_todo_tipster_publico_declara_plano_mesmo_que_vazio():
    """`None` é uma declaração ("sem assinatura"); chave ausente é esquecimento, e o
    front leria `undefined` como se fosse um plano."""
    for slug, cfg in REGISTRO.items():
        assert "plano" in cfg, f"{slug} não declara `plano`"


def test_o_plano_nao_pode_estar_escondido_dentro_do_nome():
    """Este é o gate de verdade: `nome` é só a marca. Um `- VIP` que volte para dentro
    dele desfaz a separação em silêncio — a tela continua funcionando, e o selo âmbar
    simplesmente some junto com a hierarquia que ele existia para criar."""
    for slug, cfg in REGISTRO.items():
        nome = cfg["nome"].casefold()
        assert not nome.endswith("vip"), f"{slug}: o plano voltou para dentro do nome"
        assert " - " not in cfg["nome"], f"{slug}: sufixo de plano no nome ({cfg['nome']})"


def test_quem_tem_plano_tem_plano_em_caixa_alta_e_curto():
    """O selo é mono caixa-alta com tracking. Plano longo não cabe na sidebar de 264px
    e seria truncado com reticências no lugar da palavra que importa."""
    for slug, cfg in REGISTRO.items():
        plano = cfg["plano"]
        if plano is None:
            continue
        assert plano == plano.upper(), f"{slug}: plano fora de caixa alta"
        assert len(plano) <= 12, f"{slug}: plano longo demais para o selo"


def test_perfil_publico_do_dono_acha_pelo_username_do_cadastro():
    """A ponte marca ↔ username. Ela existe porque os dois divergem de propósito em 5
    dos 8 tipsters (a marca é `Soh Props`, o username do cadastro é `sohprops`)."""
    p = main.perfil_publico_do_dono("sohprops")
    assert p == {"slug": "sohpropsvips", "nome": "Soh Props", "plano": "VIP"}


def test_perfil_publico_do_dono_ignora_caixa():
    """`Flurray` no registro, `flurray` vindo da sessão: casar por string crua deixaria
    o tipster com o próprio nome trocado pelo username na sidebar dele."""
    assert main.perfil_publico_do_dono("FLURRAY")["nome"] == "Fleury"
    assert main.perfil_publico_do_dono("flurray")["slug"] == "fleury"


def test_dono_sem_vitrine_nao_inventa_perfil():
    """Quem não tem página pública cai no nome de usuário e em "Sem plano" — nunca num
    plano herdado de outra conta."""
    assert main.perfil_publico_do_dono("Feca") is None
    assert main.perfil_publico_do_dono("") is None


def test_a_logo_publica_e_registrada_antes_do_slug_dinamico():
    """O Starlette casa rotas na ORDEM DE REGISTRO. Se `/tipsters/{slug}` viesse antes,
    ele engoliria `/tipsters/<slug>/logo` e a vitrine nunca acharia a imagem — sem erro
    nenhum, só o monograma para sempre."""
    caminhos = [r.path for r in main.app.routes if getattr(r, "path", "").startswith("/tipsters/{slug}")]
    assert caminhos.index("/tipsters/{slug}/logo") < caminhos.index("/tipsters/{slug}")
    assert caminhos.index("/tipsters/{slug}/data") < caminhos.index("/tipsters/{slug}")

# ── O bloco em si, rodado de verdade ─────────────────────────────────────────

def test_bloco_da_sidebar_em_node():
    """`tests/js/sb_tipster.mjs` carrega o /static/sb-tipster.js REAL num DOM dublado.
    Provado por mutação: 10/10 detectadas (ver o cabeçalho do .mjs).

    O que ele NÃO cobre está escrito lá: CSS, upload de verdade e arrastar-e-soltar.
    """
    import shutil
    import subprocess
    if shutil.which("node") is None:
        pytest.skip("node ausente")
    raiz = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run(["node", str(raiz / "tests" / "js" / "sb_tipster.mjs")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

# ── O badge do plano: tinta ESCURA sobre acento ──────────────────────────────

def test_o_selo_do_plano_usa_tinta_escura_sobre_o_acento():
    """A Escada de Tinta inverte quando o fundo vira o próprio acento: medido,
    `#FFFFFF` sobre `--accent` dá 3,36:1 e reprova, enquanto `var(--bg)` dá 5,8:1
    (e 8,7:1 sobre `--warn`). É a regra que a sidebar já quebrou uma vez — os
    `.pend-badge`/`.open-badge` usam `#fff` literal e são desvio conhecido.

    ⚠️ Este gate lê a DECLARAÇÃO no CSS, não o pixel. Contraste de verdade se mede
    renderizando (foi assim que os 5,79:1 e 8,67:1 desta fatia foram conferidos);
    o que ele impede é alguém copiar o `#fff` do desvio vizinho para cá.
    """
    css = (pathlib.Path(__file__).resolve().parent.parent
           / "app" / "static" / "shell.css").read_text(encoding="utf-8")
    ini = css.index(".sb-tipster__plan {")
    regra = css[ini:css.index("}", ini)]
    # Só as declarações de `color`, e não a regra inteira: o primeiro rascunho procurava
    # a palavra "white" no bloco e reprovava no `white-space: nowrap`. Substring de CSS
    # não é leitura de CSS.
    tintas = [v.strip() for v in re.findall(r"(?<![-\w])color:\s*([^;]+)", regra)]
    assert tintas == ["var(--bg)"], f"a tinta do selo devia ser var(--bg), e é {tintas}"
    # E o fundo tem de ser sólido de token: badge sem fundo volta a ser rótulo, e foi
    # justamente o rótulo que o Feca trocou por badge.
    assert "background: var(--warn)" in regra

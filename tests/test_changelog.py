"""Changelog da home: a nota da versão publicada é obrigatória.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
A caixa "SharpenUp — versão a versão" do `/inicio` ficou 8 versões atrás duas vezes
(s254 e s292). Bumpar o `manifest.json` é obrigatório para a extensão funcionar;
escrever a nota não era obrigatório para nada. Este gate dá consequência ao segundo:
versão publicada sem nota fica VERMELHA no CI.

O QUE ESTE ARQUIVO **NÃO** COBRE (não confunda verde com garantia)
------------------------------------------------------------------
* Não sabe se a nota é boa, se descreve a mudança certa, nem se o texto respeita a
  regra de conteúdo do Feca ("só informamos, sem detalhes"). Isso é revisão humana.
* Não prova que a mensagem chegou ao grupo — nenhum teste toca a rede, e `getUpdates`
  é proibido no projeto. O que amarra os dois é o `scripts/avisar_testers.py`, que
  publica e grava na mesma operação; aqui se testa só a metade que grava.
* Não renderiza a home: que `renderNovidades` monte a caixa a partir do JSON é
  exercido por `tests/js/`, não aqui.

As mutações abaixo foram TODAS conferidas quebrando o dado de propósito — cada uma
falha vermelha sem a asserção correspondente.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import audit_changelog as audit  # noqa: E402  (o gate REAL, não uma cópia dele)


def _carregar_script():
    """Importa scripts/avisar_testers.py pelo caminho (não é pacote)."""
    spec = importlib.util.spec_from_file_location(
        "avisar_testers", RAIZ / "scripts" / "avisar_testers.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def repo_falso(tmp_path, monkeypatch):
    """Cópia dos 3 arquivos que o gate lê, com os caminhos do módulo redirecionados.

    Assim a MUTAÇÃO roda contra o código de produção do audit — o teste não
    reimplementa nenhuma regra dele (a armadilha da s286)."""
    (tmp_path / "app" / "static").mkdir(parents=True)
    (tmp_path / "extensor").mkdir()
    shutil.copy(audit.CHANGELOG, tmp_path / "app" / "changelog.json")
    shutil.copy(audit.MANIFEST, tmp_path / "extensor" / "manifest.json")
    shutil.copy(audit.INICIO, tmp_path / "app" / "static" / "inicio.html")
    monkeypatch.setattr(audit, "RAIZ", tmp_path)
    monkeypatch.setattr(audit, "CHANGELOG", tmp_path / "app" / "changelog.json")
    monkeypatch.setattr(audit, "MANIFEST", tmp_path / "extensor" / "manifest.json")
    monkeypatch.setattr(audit, "INICIO", tmp_path / "app" / "static" / "inicio.html")
    return tmp_path


def _muda_changelog(raiz, fn):
    p = raiz / "app" / "changelog.json"
    dados = json.loads(p.read_text(encoding="utf-8"))
    fn(dados)
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def _muda_manifest(raiz, versao):
    p = raiz / "extensor" / "manifest.json"
    dados = json.loads(p.read_text(encoding="utf-8"))
    dados["version"] = versao
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


# ── o gate, contra o repo de verdade ─────────────────────────────────────────
def test_repo_esta_verde():
    assert audit.auditar() == [], "changelog fora de dia — rode python tools/audit_changelog.py"


def test_a_copia_intocada_tambem_esta_verde(repo_falso):
    # Sem isto, uma mutação poderia "detectar" um defeito que a própria cópia criou.
    assert audit.auditar() == []


# ── mutações: cada uma é um jeito real de a home divergir ────────────────────
def test_versao_publicada_sem_nota_falha(repo_falso):
    """O caso das s254/s292: alguém bumpa o manifest e não escreve a nota."""
    _muda_manifest(repo_falso, "0.9.99")
    falhas = audit.auditar()
    assert any("NÃO existe nota" in f for f in falhas), falhas


def test_versao_dispensada_explicitamente_passa(repo_falso):
    """A saída de emergência existe, mas é declarada — não é silêncio."""
    _muda_manifest(repo_falso, "0.9.99")
    _muda_changelog(repo_falso, lambda d: d.setdefault("sharpenup_sem_nota", {}).update(
        {"0.9.99": "build interno, nunca distribuído"}))
    assert audit.auditar() == []


def test_nota_adiantada_falha(repo_falso):
    """Nota de versão que ninguém pode baixar manda o tester atrás de um .zip que não existe."""
    _muda_changelog(repo_falso, lambda d: d["sharpenup"].insert(
        0, {"id": "su-9999", "v": "v9.9.9", "data": "2026-08-24", "texto": "Nova casa: **X**."}))
    assert any("adiantada" in f or "ninguém pode baixar" in f for f in audit.auditar())


def test_fora_de_ordem_falha(repo_falso):
    """A home corta as N primeiras: fora de ordem, a versão nova some da caixa."""
    _muda_changelog(repo_falso, lambda d: d["sharpenup"].append(d["sharpenup"].pop(0)))
    assert any("ordem decrescente" in f for f in audit.auditar())


def test_id_duplicado_falha(repo_falso):
    """id é a identidade: duplicado, o localStorage de 'já vi' mata a entrada nova."""
    _muda_changelog(repo_falso, lambda d: d["sharpenup"].insert(1, dict(d["sharpenup"][0])))
    assert any("id duplicado" in f for f in audit.auditar())


def test_asterisco_solto_falha(repo_falso):
    """`*assim*` sai literal na tela — o render só faz **negrito** (aconteceu na 0.6.41)."""
    def mut(d):
        d["sharpenup"][0]["texto"] = "Nova casa: *Lottu*."
    _muda_changelog(repo_falso, mut)
    assert any("asterisco solto" in f for f in audit.auditar())


def test_data_invalida_falha(repo_falso):
    def mut(d):
        d["novidades"][0]["data"] = "24/08/2026"
    _muda_changelog(repo_falso, mut)
    assert any("AAAA-MM-DD" in f for f in audit.auditar())


def test_array_de_volta_no_html_falha(repo_falso):
    """Se alguém reintroduzir o array no inicio.html, a fonte única acabou — e o gate
    pararia de significar qualquer coisa, porque a home não leria mais o JSON."""
    p = repo_falso / "app" / "static" / "inicio.html"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "const NOV_DIAS=45;", "const NOVIDADES=[];\nconst NOV_DIAS=45;"), encoding="utf-8")
    assert any("array de changelog embutido" in f for f in audit.auditar())


def test_home_sem_fetch_falha(repo_falso):
    """Sem a busca, as duas caixas somem da home sem erro nenhum."""
    p = repo_falso / "app" / "static" / "inicio.html"
    p.write_text(p.read_text(encoding="utf-8").replace("/changelog", "/nada"), encoding="utf-8")
    assert any("não busca /changelog" in f for f in audit.auditar())


# ── a rota que a home consome ────────────────────────────────────────────────
def test_rota_exige_sessao():
    from fastapi.testclient import TestClient
    sys.path.insert(0, str(RAIZ / "app"))
    import main

    cliente = TestClient(main.app)
    assert cliente.get("/changelog").status_code == 401


def test_rota_devolve_as_duas_listas(monkeypatch):
    from fastapi.testclient import TestClient
    sys.path.insert(0, str(RAIZ / "app"))
    import main

    monkeypatch.setattr(main, "usuario_do_request", lambda req: "Feca")
    r = TestClient(main.app).get("/changelog")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["sharpenup"] and corpo["novidades"], "listas vazias na home"
    # Sem no-store, o navegador serviria changelog velho e o bump de deploy não apareceria.
    assert "no-store" in r.headers.get("cache-control", "")


def test_json_ilegivel_vira_lista_vazia(tmp_path, monkeypatch):
    """JSON quebrado tem de derrubar as CAIXAS, nunca a home inteira."""
    sys.path.insert(0, str(RAIZ / "app"))
    import main

    ruim = tmp_path / "changelog.json"
    ruim.write_text("{ isto não é json", encoding="utf-8")
    monkeypatch.setattr(main, "_CHANGELOG_PATH", ruim)
    monkeypatch.setattr(main, "_changelog_cache", None)
    assert main._ler_changelog() == {"novidades": [], "sharpenup": []}


# ── o script que publica ─────────────────────────────────────────────────────
def test_mensagem_ao_grupo_leva_a_mesma_nota_da_home():
    mod = _carregar_script()
    entrada = {"id": "su-0653", "v": "v0.6.53", "data": "2026-08-25",
               "texto": "Nova casa: **Betsson**.", "itens": ["Abra **Minhas Apostas**."]}
    msg = mod.montar_mensagem(entrada, "0.6.53")
    assert "<b>SharpenUp 0.6.53</b>" in msg
    assert "Nova casa: <b>Betsson</b>." in msg          # o mesmo negrito que a home mostra
    assert "• Abra <b>Minhas Apostas</b>." in msg
    assert "sharpen.bet/extensao" in msg                 # a ação do tester, sempre
    assert "**" not in msg                               # asterisco cru nunca vai ao grupo


def test_envio_falho_nao_grava_no_changelog(tmp_path, monkeypatch, capsys):
    """A garantia central: home e grupo contam a MESMA história. Se o envio falhou,
    a home não pode anunciar uma versão que o tester nunca foi avisado de baixar."""
    mod = _carregar_script()
    copia = tmp_path / "changelog.json"
    shutil.copy(audit.CHANGELOG, copia)
    antes = copia.read_text(encoding="utf-8")
    monkeypatch.setattr(mod, "CHANGELOG", copia)
    monkeypatch.setattr(mod, "ler_token", lambda: "token-falso")
    monkeypatch.setattr(mod, "conferir_destino", lambda token: None)
    monkeypatch.setattr(mod, "chamar", lambda *a, **k: {"ok": False, "description": "chat not found"})
    versao = json.loads(audit.MANIFEST.read_text(encoding="utf-8"))["version"]
    monkeypatch.setattr(sys, "argv", ["avisar_testers.py", "--versao", versao,
                                      "--texto", "x", "--enviar"])
    with pytest.raises(SystemExit):
        mod.main()
    assert copia.read_text(encoding="utf-8") == antes, "gravou mesmo com o envio falhando"
    assert "chat not found" in capsys.readouterr().err   # o description, que é o diagnóstico


def test_ensaio_nao_envia_nem_grava(tmp_path, monkeypatch):
    """Padrão do script: sem --enviar, ninguém toca no grupo nem no arquivo."""
    mod = _carregar_script()
    copia = tmp_path / "changelog.json"
    shutil.copy(audit.CHANGELOG, copia)
    antes = copia.read_text(encoding="utf-8")
    monkeypatch.setattr(mod, "CHANGELOG", copia)

    def explode(*a, **k):
        raise AssertionError("o ensaio chamou a API do Telegram")

    monkeypatch.setattr(mod, "chamar", explode)
    monkeypatch.setattr(mod, "ler_token", explode)
    versao = json.loads(audit.MANIFEST.read_text(encoding="utf-8"))["version"]
    monkeypatch.setattr(sys, "argv", ["avisar_testers.py", "--versao", versao, "--texto", "x"])
    mod.main()
    assert copia.read_text(encoding="utf-8") == antes


def test_nota_de_versao_diferente_do_manifest_aborta(monkeypatch):
    """Nota escrita antes do bump: o tester baixaria uma versão sem a mudança."""
    mod = _carregar_script()
    monkeypatch.setattr(sys, "argv", ["avisar_testers.py", "--versao", "9.9.9",
                                      "--texto", "x", "--enviar"])
    with pytest.raises(SystemExit):
        mod.main()


def test_gravar_poe_no_topo_e_nao_duplica(tmp_path, monkeypatch):
    mod = _carregar_script()
    copia = tmp_path / "changelog.json"
    shutil.copy(audit.CHANGELOG, copia)
    monkeypatch.setattr(mod, "CHANGELOG", copia)
    entrada = {"id": "su-0653", "v": "v0.6.53", "data": "2026-08-25", "texto": "Nova casa: **X**."}
    mod.gravar(entrada, "0.6.53")
    mod.gravar({**entrada, "texto": "Nova casa: **X** (corrigido)."}, "0.6.53")
    lista = json.loads(copia.read_text(encoding="utf-8"))["sharpenup"]
    assert lista[0]["id"] == "su-0653" and "corrigido" in lista[0]["texto"]
    assert sum(1 for e in lista if e["id"] == "su-0653") == 1


# ── o render da home, executado de verdade ───────────────────────────────────
@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_render_da_home_em_node():
    """`tests/js/novidades_render.mjs` recorta o renderNovidades REAL do inicio.html e o
    roda contra o changelog REAL, com DOM dublado. Provado por mutação: 6/6 detectadas
    (ver o cabeçalho do .mjs)."""
    r = subprocess.run(["node", str(RAIZ / "tests" / "js" / "novidades_render.mjs")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

#!/usr/bin/env python3
"""Auditoria da SUPERFÍCIE DE REGISTRO do SharpenUp (FDC Capital / Planilhador).

Uma casa nova só funciona ponta a ponta se ela estiver registrada em ~12 lugares
espalhados por 4 camadas (backend, front do dashboard, extensão, documentação).
Nada, hoje, garante que as listas concordem entre si — e é exatamente aí que as
sessões se perdem:

  • s191 — KTO estava em `_MODO_POR_CASA` (backend dizia "texto") mas fora de
    `CASAS_CONECTAVEIS` (front) → o botão "Conectar" nascia morto e NADA da
    sessão anterior chegava a rodar.
  • s189 — bet365 fora do `_build_chunks`/pré-dedup → lote inteiro num request só.
  • s192 — bet365 emite `[Código: BR…]`, mas nenhuma regex de `repository.py`
    reconhece o formato → a conferência de cobertura (o guarda contra perda
    silenciosa de chunk, s179) fica DESLIGADA justo na casa de maior volume.

Este script lê as listas reais e cruza. Determinístico, read-only, sem rede.

Uso:
    python tools/audit_sharpenup.py            # todas as casas
    python tools/audit_sharpenup.py KTO BET365 # só as citadas
Saída: relatório legível + exit code 1 se houver qualquer FAIL.
"""
import json
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"
EXT = ROOT / "extensor"

MAIN_PY = APP / "main.py"
CAPTURA_PY = APP / "captura.py"
INDEX_HTML = APP / "static" / "index.html"
INICIO_HTML = APP / "static" / "inicio.html"
DATA_JS = APP / "static" / "dash" / "assets" / "js" / "data.js"
POPUP_JS = EXT / "popup.js"
CONTENT_JS = EXT / "content.js"
MANIFEST = EXT / "manifest.json"

# ── Exemplo REAL do código de bilhete que cada casa de captura emite no marcador
# `[Código: …]`. Serve para provar que `repository.py::codigos_do_texto` reconhece o
# formato — é esse gabarito que liga a conferência de cobertura (perda silenciosa de
# chunk, s179). CASA NOVA DE CAPTURA ENTRA AQUI, com um código real do bilhete.
CODIGO_EXEMPLO: dict[str, str] = {
    "SUPERBET":   "891L-YJ3VAH",
    "BETANO":     "20675937607",
    "BETESPORTE": "190989817",
    "BETFAIR":    "O/25146258/0001775",
    "PINNACLE":   "3089350167",
    "KTO":        "12939510404",
    "TIVO":       "298710215",
    # Betfast é espelho da Tivo e compartilha o espaço de IDs do motor BetConstruct — este é
    # um bilhete real da conta (o W de 22/07, retorno R$ 1.604,28).
    "BETFAST":    "298388575",
    "VAIDEBET":   "5234878919",
    # id real da conta (o W de 09/08 na Bahia × Vasco, stake 124 → retorno 198,40). A
    # Esportiva é espelho da VaideBet e compartilha o espaço de IDs do motor Altenar:
    # mesmo formato numérico de 10 dígitos.
    "ESPORTIVA":  "5277832732",
    # id real da conta (o W de 08/08 no Boca × Vélez, stake 30 → retorno 99,00). 3ª casa do
    # motor Altenar: mesmo espaço de IDs, numérico de 10 dígitos.
    "JOGODEOURO": "5273475058",
    # id real da conta (a múltipla W de 02/08 com "Ganhos extra" de R$ 0,15). 4ª casa do
    # motor Altenar: mesmo espaço de IDs, numérico de 10 dígitos.
    "BETPIX365":  "5255274526",
    "BET365":     "JR8714690761I",
    # ticket_id real da conta (a Super Odds aberta de 01/08) — formato NXBNAC + 24 dígitos.
    "BETNACIONAL": "NXBNAC000142211281785609607878",
    # id real do BetBy (a ganha de 04/08, R$ 623,01) — numérico de 19 dígitos. ⚠ Os ids da
    # Jonbet são QUASE IDÊNTICOS entre si (…475463 × …475401 diferem em 3 chars): ela fica
    # FORA do snap por edit-distance de `corrigir_codigos_tsv` de propósito — nenhuma das três
    # regexes de lá casa 19 dígitos. A cobertura funciona pelo marcador genérico.
    "JONBET":     "2696533322854707365",
    # id real do BetBy (a ganha de 05/08, R$ 906,00 — `sum` 300 × `total_k` 3,02). Betboom é
    # espelho da Jonbet e compartilha o espaço de IDs do motor: mesmo formato numérico de 19
    # dígitos e, pelo mesmo motivo da Jonbet, FORA do snap por edit-distance.
    "BETBOOM":    "2696881722674520125",
    # `internal_bet_id` real da conta (a perdida de 07/08, stake R$18,88 @3,95) — numérico de
    # 7 dígitos. ⚠ É o ID que o CARD estampa; o `ticket_id` (11 dígitos) NÃO vai para o
    # marcador, senão print e captura gerariam códigos diferentes para o mesmo bilhete.
    "STAKE":      "8342050",
}

# Casas de captura cuja ingestão é condicional no backend (o texto pode vir do
# fluxo legado, sem marcador) — não exigimos presença literal nas tuplas do main.py.
CONDICIONAIS_NO_BACKEND = {"BETFAIR"}


# ── leitura das listas reais ──────────────────────────────────────────────────

def _txt(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def casas_display() -> dict[str, str]:
    """`_CASA_DISPLAY` do main.py: CHAVE_MAIUSCULA -> Nome Canônico."""
    src = _txt(MAIN_PY)
    m = re.search(r"_CASA_DISPLAY[^=]*=\s*\{(.*?)\n\}", src, re.DOTALL)
    if not m:
        raise SystemExit("FATAL: não achei _CASA_DISPLAY em app/main.py")
    return dict(re.findall(r'"([A-Z0-9]+)":\s*"([^"]+)"', m.group(1)))


def modo_por_casa() -> dict[str, str]:
    src = _txt(CAPTURA_PY)
    m = re.search(r"_MODO_POR_CASA\s*=\s*\{(.*?)\}", src, re.DOTALL)
    return dict(re.findall(r'"([A-Z0-9]+)":\s*"(\w+)"', m.group(1))) if m else {}


def hosts_backend() -> dict[str, set[str]]:
    src = _txt(CAPTURA_PY)
    m = re.search(r"_HOSTS_POR_CASA\s*=\s*\{(.*?)\n\}", src, re.DOTALL)
    out: dict[str, set[str]] = {}
    if m:
        for chave, corpo in re.findall(r'"([A-Z0-9]+)":\s*\(([^)]*)\)', m.group(1)):
            out[chave] = set(re.findall(r'"([^"]+)"', corpo))
    return out


def hosts_popup() -> dict[str, set[str]]:
    src = _txt(POPUP_JS)
    m = re.search(r"const CASA_HOSTS\s*=\s*\{(.*?)\n\}", src, re.DOTALL)
    out: dict[str, set[str]] = {}
    if m:
        for nome, corpo in re.findall(r'"([^"]+)":\s*\[([^\]]*)\]', m.group(1)):
            out[nome] = set(re.findall(r'"([^"]+)"', corpo))
    return out


def conectaveis() -> set[str]:
    m = re.search(r"const CASAS_CONECTAVEIS\s*=\s*new Set\(\[(.*?)\]\)", _txt(INDEX_HTML), re.DOTALL)
    return set(re.findall(r"'([A-Z0-9]+)'", m.group(1))) if m else set()


def normaliza_conectavel() -> str:
    """A normalização que `_casaConectavel` aplica ANTES de consultar o Set.

    Existe porque estar na lista NÃO basta: o front consulta com a casa **como está no
    banco** (o display, `Jogo de Ouro`), enquanto as chaves do Set são as do
    `_CASA_DISPLAY`, sem espaço. Até a s256 toda casa de captura tinha nome de uma palavra
    e `.toUpperCase()` bastava; a Jogo de Ouro foi a primeira composta e o botão "Conectar"
    nasceu desabilitado **com a casa devidamente registrada** — o audit passava verde
    porque conferia a lista, não o runtime. Devolve "" se a função sumiu/mudou de forma.
    """
    m = re.search(r"function _casaConectavel\(casa\)\s*\{\s*return CASAS_CONECTAVEIS\.has\((.*?)\);", _txt(INDEX_HTML))
    return m.group(1) if m else ""


def display_casa_conectavel(display: str) -> bool:
    """Simula `_casaConectavel(display)` do front — o teste que faltava."""
    expr = normaliza_conectavel()
    chave = display.upper()
    if "replace" in expr:                      # tira espaços, como o front faz hoje
        chave = re.sub(r"\s+", "", chave)
    return chave in conectaveis()


def bloco(src: str, nome: str, abre: str = "{", fecha: str = "}") -> str:
    """Corpo textual do literal `nome = { … }` (primeiro fechamento em coluna 0/1)."""
    m = re.search(re.escape(nome) + r"\s*=\s*" + re.escape(abre) + r"(.*?)\n\s*" + re.escape(fecha),
                  src, re.DOTALL)
    return m.group(1) if m else ""


_CHAVE_JS = re.compile(r"""(?:[{,]|^)\s*(?:'([^']+)'|"([^"]+)"|([A-Za-z_$][\w$]*))\s*:""", re.M)


def chaves_js(corpo: str) -> set[str]:
    """Chaves de um objeto JS (aspas simples/duplas ou identificador nu).

    Vários mapas do projeto põem MAIS DE UMA chave por linha (`SUPERBET: 'Superbet',
    BET365: 'Bet365',`) — por isso a âncora é `{`/`,`/início de linha, não só o início.
    Comentários saem antes: uma linha `// … no dashboard):` casaria como chave.
    """
    limpo = re.sub(r"//[^\n]*", "", corpo)
    return {a or b or c for a, b, c in _CHAVE_JS.findall(limpo)}


def tuplas_backend_com(chave: str) -> tuple[bool, bool]:
    """(está no chunker, está no pré-dedup) do main.py.

    Desde a s194 as duas decisões saem da MESMA lista nomeada `_CASAS_MARCADOR_CODIGO` — antes
    eram duas tuplas literais repetidas a ~1100 linhas de distância, e foi assim que a Pinnacle
    ficou fora das duas. Aqui conferimos as três coisas: a casa está na lista, e cada um dos
    dois pontos de uso realmente CONSULTA a lista (ninguém re-inlinou um literal).
    """
    src = _txt(MAIN_PY)
    m = re.search(r"_CASAS_MARCADOR_CODIGO\s*=\s*frozenset\(\{(.*?)\}\)", src, re.DOTALL)
    if not m:                                    # lista sumiu → não dá para afirmar nada
        return False, False
    na_lista = f'"{chave}"' in m.group(1)
    usa_chunker = bool(re.search(r"casa_key\.upper\(\) in _CASAS_MARCADOR_CODIGO:", src))
    usa_predup = bool(re.search(r"if casa_key\.upper\(\) in _CASAS_MARCADOR_CODIGO or", src))
    return (na_lista and usa_chunker), (na_lista and usa_predup)


def injects_popup() -> dict[str, str]:
    """Dispatch do popup: Nome Canônico -> arquivo de inject."""
    src = _txt(POPUP_JS)
    trecho = src[src.find("const inj ="):src.find("const inj =") + 900]
    return dict(re.findall(r'casa === "([^"]+)"\s*\?\s*"([\w.]+)"', trecho))


def manifest_injects() -> dict[str, list[str]]:
    """arquivo de inject -> lista de matches declarados no manifest."""
    man = json.loads(_txt(MANIFEST))
    out: dict[str, list[str]] = {}
    for cs in man.get("content_scripts", []):
        for js in cs.get("js", []):
            out.setdefault(js, []).extend(cs.get("matches", []))
    return out


def content_dispatch() -> set[str]:
    """Casas com ramo próprio em `iniciarRobo` (senão caem no roboScroll genérico)."""
    src = _txt(CONTENT_JS)
    ini = src.find("async function iniciarRobo()")
    fim = src.find("async function roboScroll(", ini)
    return set(re.findall(r'casa === "(\w+)"', src[ini:fim]))


def chave_runtime_content(display: str) -> str:
    """O valor que a variável `casa` do `iniciarRobo` REALMENTE assume para este display.

    O `content.js` recebe do pareamento o NOME DE EXIBIÇÃO (`Jogo de Ouro`), não a chave
    (`JOGODEOURO`), e normaliza antes de comparar. Reproduzimos a normalização real lendo a
    linha do código — se ela mudar, o audit acompanha em vez de mentir.

    Sem isto o audit era um espelho: comparava o literal `casa === "jogodeouro"` com a chave
    `JOGODEOURO.lower()` — a mesma string, dos dois lados, e nunca o valor de runtime. Foi
    assim que a Jogo de Ouro passou verde enquanto raspava o rodapé do site (s256).
    """
    m = re.search(r'const casa = \(cfg\.casa \|\| ""\)\.toLowerCase\(\)(.*?);', _txt(CONTENT_JS))
    expr = m.group(1) if m else ""
    v = display.lower()
    if "replace" in expr:                      # tira espaços, como o content.js faz hoje
        v = re.sub(r"\s+", "", v)
    return v


def content_diag() -> set[str]:
    """Casas com entrada no mapa de autodiagnóstico (0 bilhetes → causa provável)."""
    src = _txt(CONTENT_JS)
    m = re.search(r"const diag = \{(.*?)\}\[casa\]", src, re.DOTALL)
    return set(re.findall(r"(?m)^\s*(\w+):\s*\{", m.group(1))) if m else set()


def codigo_reconhecido(exemplo: str) -> bool:
    """`repository.py::codigos_do_texto` enxerga esse formato de código?"""
    sys.path.insert(0, str(APP))
    try:
        from repository import codigos_do_texto  # noqa: PLC0415
    except Exception as e:                                    # pragma: no cover
        print(f"  (aviso: não consegui importar repository.py: {e})")
        return True                                           # não acusa falso positivo
    return bool(codigos_do_texto(f"[Código: {exemplo}]"))


# ── auditoria por casa ────────────────────────────────────────────────────────

def auditar(chave: str, display: str, ctx: dict) -> list[tuple[str, str]]:
    a: list[tuple[str, str]] = []
    modo = ctx["modos"].get(chave, "print")

    # ── camada IA / dashboard (vale para TODA casa) ──
    if not (ROOT / "casas" / f"CASA_{chave}.md").exists():
        a.append(("WARN", f"sem casas/CASA_{chave}.md (roda em modo cego — ok, mas sem tradução fina)"))
    if chave not in ctx["nomes_html"]:
        a.append(("FAIL", "ausente em index.html NOMES"))
    for rotulo, chaves in (("index.html DOMINIOS", ctx["dominios_html"]),
                           ("dash/data.js CASA_ICONS", ctx["icons_js"]),
                           ("dash/data.js HOUSE_DOMAIN", ctx["house_js"]),
                           ("inicio.html CASA_DOMAIN", ctx["dominio_inicio"])):
        if display not in chaves:
            a.append(("WARN", f"'{display}' ausente em {rotulo} (favicon quebrado nessa tela)"))

    if modo != "texto":
        return a   # casa de print: acaba aqui (não usa robô nem inject)

    # ── camada de captura (só casas de robô) ──
    hb = ctx["hosts_back"].get(chave)
    if not hb:
        a.append(("FAIL", "modo 'texto' sem entrada em captura.py _HOSTS_POR_CASA "
                          "(o backstop casa↔site do servidor fica cego)"))
    if chave not in ctx["conectaveis"]:
        a.append(("FAIL", "ausente em index.html CASAS_CONECTAVEIS → o botão 'Conectar' "
                          "nasce DESABILITADO e nada da captura roda (bug da s191)"))
    # Estar na lista NÃO basta: o front consulta com o DISPLAY vindo do banco
    # (`parceiroSelecionado.casa`), não com a chave. Casa de nome composto quebrava aqui
    # com tudo "registrado" — foi o botão morto da Jogo de Ouro na s256.
    elif not display_casa_conectavel(display):
        a.append(("FAIL", f"'{display}' não passa por `_casaConectavel()` em runtime "
                          f"(o front consulta com o nome do banco, não com a chave '{chave}') → "
                          "botão 'Conectar' DESABILITADO mesmo com a casa registrada"))
    hp = ctx["hosts_popup"].get(display)
    if hp is None:
        a.append(("WARN", f"'{display}' ausente em popup.js CASA_HOSTS "
                          "(sem a mensagem amigável de 'aba errada'; não bloqueia)"))
    elif hb and hp != hb:
        a.append(("FAIL", f"popup.js CASA_HOSTS {sorted(hp)} ≠ captura.py _HOSTS_POR_CASA {sorted(hb)}"))

    # ⚠ O que importa é o valor de RUNTIME, não a chave: o content.js recebe o display do
    # pareamento. Casa de nome composto cai no roboScroll genérico — e o robô genérico não
    # falha, ele RASPA A PÁGINA (na s256 a Jogo de Ouro mandou o rodapé do site para a IA).
    runtime = chave_runtime_content(display)
    if runtime not in ctx["dispatch"]:
        a.append(("FAIL", f'content.js iniciarRobo() sem ramo para `casa === "{runtime}"` '
                          f'(o valor real que "{display}" assume em runtime) → cai no '
                          "roboScroll genérico e RASPA A PÁGINA em vez de falhar"))
    if runtime not in ctx["diag"]:
        a.append(("WARN", "sem entrada no mapa de autodiagnóstico do content.js "
                          "(0 bilhetes vira aviso genérico, sem causa provável)"))

    inj = ctx["inj_popup"].get(display)
    if inj:
        if not (EXT / inj).exists():
            a.append(("FAIL", f"popup.js aponta para {inj}, que não existe em extensor/"))
        matches = ctx["inj_manifest"].get(inj)
        if not matches:
            a.append(("FAIL", f"{inj} não está declarado no manifest.json content_scripts → "
                              "só injeta via popup (aba já aberta antes falha em silêncio)"))
        elif hb:
            faltando = [h for h in hb if not any(h in m for m in matches)]
            if faltando:
                a.append(("WARN", f"manifest.json não cobre {faltando} para {inj}"))

    chunker, predup = ctx["tuplas"](chave)
    if chave not in CONDICIONAIS_NO_BACKEND:
        if not chunker:
            # Sem a tupla o texto ainda fatia pelo fallback `\n\n` (os robôs juntam os
            # blocos com linha em branco), então HOJE costuma funcionar. É WARN e não
            # FAIL por isso — mas é frágil: um bloco que contenha linha em branco vira
            # dois bilhetes. O marcador `[Código:]` é a fronteira certa (bug da s189).
            a.append(("WARN", "ausente na tupla do chunker (main.py _build_chunks) → fatia "
                              "pelo fallback frágil `\\n\\n` em vez do marcador [Código:]"))
        if not predup:
            a.append(("FAIL", "ausente na tupla do pré-dedup (main.py) → paga IA de novo "
                              "por TODO bilhete já resolvido no banco a cada recaptura"))

    ex = CODIGO_EXEMPLO.get(chave)
    if not ex:
        a.append(("WARN", "sem exemplo de código em tools/audit_sharpenup.py CODIGO_EXEMPLO "
                          "(não dá para provar que a conferência de cobertura funciona)"))
    elif not codigo_reconhecido(ex):
        a.append(("FAIL", f"repository.py não reconhece o código '{ex}' → conferência de "
                          "cobertura DESLIGADA nesta casa (perda silenciosa de chunk passa batido)"))
    return a


def main(argv: list[str]) -> int:
    display = casas_display()
    ctx = {
        "modos": modo_por_casa(),
        "hosts_back": hosts_backend(),
        "hosts_popup": hosts_popup(),
        "conectaveis": conectaveis(),
        "nomes_html": chaves_js(bloco(_txt(INDEX_HTML), "const NOMES")),
        "dominios_html": chaves_js(bloco(_txt(INDEX_HTML), "const DOMINIOS")),
        "icons_js": chaves_js(bloco(_txt(DATA_JS), "CASA_ICONS")),
        "house_js": chaves_js(bloco(_txt(DATA_JS), "HOUSE_DOMAIN")),
        "dominio_inicio": chaves_js(bloco(_txt(INICIO_HTML), "const CASA_DOMAIN")),
        "dispatch": content_dispatch(),
        "diag": content_diag(),
        "inj_popup": injects_popup(),
        "inj_manifest": manifest_injects(),
        "tuplas": tuplas_backend_com,
    }

    alvos = [c.upper() for c in argv] if argv else sorted(display)
    desconhecidas = [c for c in alvos if c not in display]
    for c in desconhecidas:
        print(f"  ?    {c}: não existe em _CASA_DISPLAY (app/main.py)")
    alvos = [c for c in alvos if c in display]

    modo = ctx["modos"]
    captura = [c for c in alvos if modo.get(c) == "texto"]
    print(f"Casas registradas: {len(display)}  ·  auditadas: {len(alvos)}  "
          f"·  de captura (robô): {len(captura)}\n")

    total_fail = 0
    for chave in alvos:
        achados = auditar(chave, display[chave], ctx)
        fails = [x for x in achados if x[0] == "FAIL"]
        total_fail += len(fails)
        rotulo = "robô" if modo.get(chave) == "texto" else "print"
        if not achados:
            print(f"  OK   {chave} ({rotulo})")
        else:
            print(f"  {'FAIL' if fails else 'WARN'} {chave} ({rotulo})")
            for sev, msg in achados:
                print(f"         [{sev}] {msg}")
    print()
    if total_fail:
        print(f"RESULTADO: {total_fail} FAIL(s) — a casa NÃO está registrada por inteiro.")
        return 1
    print("RESULTADO: sem FAILs. (WARNs são cosméticos/diagnóstico — avaliar caso a caso.)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

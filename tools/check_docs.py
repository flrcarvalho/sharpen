#!/usr/bin/env python3
"""Gate de documentacao — falha quando o repo volta a inchar.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O invariante #4 do CLAUDE.md ("podar snapshots... nunca copiar o HISTORICO")
estava escrito, era claro, e foi ignorado ate `Backups/` chegar a 551 pastas e
128 MB, com 165 copias de STATUS.md/HISTORICO.md dentro. O ritual /encerrar
mandava manter 3 sessoes no STATUS.md; o arquivo chegou a 187 KB.

Regra sem gate nao e cumprida neste repo — isso esta medido, nao suposto.
Este script e o gate.

O QUE ELE CHECA
---------------
  0. CLAUDE.md nao passa de CLAUDE_MAX_KB e docs/CASOS.md nao passa de CASOS_MAX_KB.
  1. STATUS.md nao passa de STATUS_MAX_KB.
  2. STATUS.md nao tem mais de MAX_BLOCOS_SESSAO blocos "## Sessao".
  3. STATUS.md nao tem mais de MAX_ANTERIOR paragrafos "_Anterior:".
  4. Backups/ nao guarda arquivo que comece com STATUS ou HISTORICO.
  5. Nenhum link markdown relativo aponta para arquivo inexistente.
  6. Toda ANCORA (`arquivo.md#secao`) resolve contra um titulo real do alvo.

Por que (2) e (3) existem, se ja ha (1): **byte sozinho e gate fraco.** Um
STATUS de 49 KB so de historia passa no teto e ja perdeu o proposito. As duas
checagens estruturais medem a FORMA que o /encerrar manda (estado atual + no
maximo 3 sessoes), e um STATUS que volte a crescer estoura elas antes do byte.

Por que (4) e por PREFIXO e nao por nome exato: uma copia renomeada
(`STATUS.md-antes-do-corte`) e a mesma copia. Backup deliberado de cirurgia
tambem reprova, e isso e o comportamento certo — o invariante #4 manda nunca
copiar estes dois para `Backups/`, e o git guarda o estado anterior.

O QUE ELE **NAO** CHECA (limite declarado, para o verde nao virar promessa falsa)
--------------------------------------------------------------------------------
  * Nao le CONTEUDO: 3 blocos de sessao gigantes dentro do teto passam.
  * A checagem de ancora cobre so os .md vivos; ancora para fora do repo nao e vista.
  * Nao olha o BACKLOG.md: nada aqui percebe pendencia que sumiu dele.
  * A checagem (4) e VAZIA no CI: `Backups/` e gitignored, entao a pasta nem
    existe no checkout. Ela so tem efeito rodando local. Quando a pasta falta,
    o script DIZ que nao exerceu a checagem, em vez de contar como verde.

USO
---
    python tools/check_docs.py            # 0 = ok, 1 = FAIL
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _kb(caminho: str) -> float:
    """Tamanho em KB contando a quebra de linha SEMPRE como 1 byte (LF).

    ⚠️ **O mesmo arquivo dava dois tamanhos, e o gate dava dois vereditos.** Medido na
    s385 com o `CLAUDE.md`: **64,03 KB no disco do Feca** (LF) e **65,04 KB no checkout
    do CI** (CRLF, porque o git converte na saida no Windows e o runner recebe o que o
    repo guarda). A diferenca eram **1.035 bytes, exatamente um por linha** — e o teto e'
    65 KB, entao o mesmo arquivo passava aqui e reprovava la.

    O efeito pratico e' o pior possivel para um teto: quem edita local le "sobra 1 KB" e
    **nao sobra**. O CI reprova depois, longe de quem escreveu, e a leitura natural e'
    "o gate esta maluco".

    Medimos o conteudo CANONICO, que e' o que o git guarda (LF). Assim o numero e' o
    mesmo em qualquer maquina e o teto quer dizer uma coisa so.
    """
    with open(caminho, "rb") as fh:
        bruto = fh.read()
    return len(bruto.replace(b"\r\n", b"\n")) / 1024

STATUS_MAX_KB = 50
CLAUDE_MAX_KB = 65
CASOS_MAX_KB = 60
MAX_BLOCOS_SESSAO = 3
MAX_ANTERIOR = 2
PREFIXOS_PROIBIDOS_EM_BACKUPS = ("STATUS", "HISTORICO")
IGNORAR = {"node_modules", "Backups", ".git", ".pytest_cache", "_backups", "__pycache__", "venv", ".venv"}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BLOCO_SESSAO_RE = re.compile(r"(?m)^## Sess[aã]o\b")
ANTERIOR_RE = re.compile(r"(?m)^_Anterior:")

falhas: list[str] = []
avisos: list[str] = []


def _status() -> str | None:
    caminho = os.path.join(RAIZ, "STATUS.md")
    if not os.path.exists(caminho):
        falhas.append("STATUS.md nao existe na raiz.")
        return None
    return open(caminho, encoding="utf-8", errors="replace").read()


def checar_tamanho_claude() -> None:
    """CLAUDE.md — o arquivo de regras, auto-carregado em toda sessao.

    ⚠️ O TETO TRAVA CRESCIMENTO; ELE NAO MANDA CORTAR. Ao encostar nele, mova o CASO
    para o docs/CASOS.md. NUNCA corte os blocos "sintoma para reconhecer isto noutro
    campo": sao eles que fazem uma sessao nova reconhecer a FAMILIA de um defeito antes
    de repeti-la. E nunca suba o teto para nao cortar — foi assim que o STATUS.md
    chegou a 187 KB.
    """
    caminho = os.path.join(RAIZ, "CLAUDE.md")
    if not os.path.exists(caminho):
        falhas.append("CLAUDE.md nao existe na raiz.")
        return
    kb = _kb(caminho)
    if kb > CLAUDE_MAX_KB:
        falhas.append(
            f"CLAUDE.md tem {kb:.1f} KB — o teto e {CLAUDE_MAX_KB} KB.\n"
            f"       Mova CASO para docs/CASOS.md (bilhete, casa, valor em R$, numero da\n"
            f"       sessao). NAO corte regra, NAO corte bloco de sintoma, NAO suba o teto."
        )
    else:
        print(f"  OK   CLAUDE.md: {kb:.1f} KB (teto {CLAUDE_MAX_KB} KB)")


def checar_tamanho_casos() -> None:
    """docs/CASOS.md — o deposito de casos que o CLAUDE.md deixou de carregar.

    Ele nasceu com ~26 KB no Lote E da faxina. O teto existe para avisar quando ele
    virar o proximo HISTORICO e precisar de particao — nao para impedir que cresca.
    Ele NAO e auto-carregado em sessao nenhuma; ler e ato deliberado.
    """
    caminho = os.path.join(RAIZ, "docs", "CASOS.md")
    if not os.path.exists(caminho):
        avisos.append("docs/CASOS.md ainda nao existe — checagem de tamanho NAO exercida.")
        return
    kb = _kb(caminho)
    if kb > CASOS_MAX_KB:
        falhas.append(
            f"docs/CASOS.md tem {kb:.1f} KB — o teto e {CASOS_MAX_KB} KB.\n"
            f"       Hora de partir por assunto, como o docs/historico/ ja foi partido.\n"
            f"       O teto e sinal de particao, nao de excesso: caso nao se apaga."
        )
    else:
        print(f"  OK   docs/CASOS.md: {kb:.1f} KB (teto {CASOS_MAX_KB} KB)")


def checar_tamanho_status(txt: str) -> None:
    kb = len(txt.encode("utf-8")) / 1024
    if kb > STATUS_MAX_KB:
        falhas.append(
            f"STATUS.md tem {kb:.1f} KB — o teto e {STATUS_MAX_KB} KB.\n"
            f"       O changelog do topo guarda no maximo as 3 ultimas sessoes;\n"
            f"       o resto vai para docs/historico/ (ver /encerrar e CLAUDE.md #10)."
        )
    else:
        print(f"  OK   STATUS.md: {kb:.1f} KB (teto {STATUS_MAX_KB} KB)")


def checar_forma_status(txt: str) -> None:
    """As duas checagens ESTRUTURAIS. Byte sozinho e gate fraco."""
    blocos = len(BLOCO_SESSAO_RE.findall(txt))
    if blocos > MAX_BLOCOS_SESSAO:
        falhas.append(
            f"STATUS.md tem {blocos} blocos '## Sessao' — o maximo e {MAX_BLOCOS_SESSAO}.\n"
            f"       Mova o mais antigo para docs/historico/, preservando o texto integral."
        )
    else:
        print(f"  OK   STATUS.md: {blocos} bloco(s) '## Sessao' (maximo {MAX_BLOCOS_SESSAO})")

    anteriores = len(ANTERIOR_RE.findall(txt))
    if anteriores > MAX_ANTERIOR:
        falhas.append(
            f"STATUS.md tem {anteriores} paragrafos '_Anterior:' — o maximo e {MAX_ANTERIOR}.\n"
            f"       A cadeia '_Anterior:' cobre a sessao que NAO tem mais bloco proprio;\n"
            f"       o excedente vai para a cadeia do docs/historico/."
        )
    else:
        print(f"  OK   STATUS.md: {anteriores} paragrafo(s) '_Anterior:' (maximo {MAX_ANTERIOR})")


def checar_backups() -> None:
    pasta = os.path.join(RAIZ, "Backups")
    if not os.path.isdir(pasta):
        # Nao e verde: e checagem nao exercida. Dizer isso e o ponto.
        avisos.append(
            "Backups/ nao existe neste checkout (a pasta e gitignored, entao no CI "
            "ela nunca esta la). A checagem de copias NAO foi exercida aqui."
        )
        return
    achados: list[str] = []
    for dp, dns, fns in os.walk(pasta):
        for fn in fns:
            if fn.startswith(PREFIXOS_PROIBIDOS_EM_BACKUPS):
                achados.append(os.path.relpath(os.path.join(dp, fn), RAIZ).replace(os.sep, "/"))
    if achados:
        total = sum(os.path.getsize(os.path.join(RAIZ, a)) for a in achados) / 1024 / 1024
        amostra = "\n".join(f"         {a}" for a in achados[:5])
        falhas.append(
            f"Backups/ guarda {len(achados)} arquivo(s) comecando por "
            f"{' / '.join(PREFIXOS_PROIBIDOS_EM_BACKUPS)} ({total:.1f} MB).\n"
            f"       O git ja versiona os dois — copiar de novo e peso puro "
            f"(invariante #4).\n{amostra}"
            + (f"\n         ... e mais {len(achados) - 5}" if len(achados) > 5 else "")
        )
    else:
        print(f"  OK   Backups/: nada comecando por {' / '.join(PREFIXOS_PROIBIDOS_EM_BACKUPS)}")


def _slug(titulo: str) -> str:
    """Ancora no estilo GitHub: minusculas, remove o que nao e letra/digito/espaco/hifen,
    e troca CADA espaco por UM hifen.

    ⚠️ Nao colapse espacos. O caractere removido que estava ENTRE dois espacos deixa os
    dois para tras, e eles viram `--`:

        "5. Superficie de registro — os 12 pontos"  ->  5-superficie-de-registro--os-12-pontos
        "3. Contrato de mensagens (inject ⇄ content)" -> 3-contrato-de-mensagens-inject--content

    Colapsar com `\\s+` gera `-` onde o GitHub gera `--`, e o gate passa a REPROVAR ancora
    correta e APROVAR ancora quebrada. Foi o que aconteceu no bloco 1 do Lote E: eu
    "consertei" 5 ancoras que estavam certas.
    """
    s = re.sub(r"[`*_]", "", titulo.strip().lower())
    s = "".join(c for c in s if unicodedata.category(c)[0] in "LNZ" or c in "- ")
    return s.strip().replace(" ", "-")


_TITULO_RE = re.compile(r"(?m)^#{1,6}\s+(.*?)\s*$")


def checar_ancoras(mds: list[str]) -> None:
    """Link `alvo.md#ancora` tem de casar um titulo real do alvo.

    Sem isto, renomear um titulo do CASOS.md quebra a navegacao do CLAUDE.md sem
    ninguem perceber — o mesmo defeito (#24 da auditoria de 19/07) que esta faxina
    fechou no HISTORICO.
    """
    cache: dict[str, set[str]] = {}

    def ancoras_de(caminho: str) -> set[str]:
        if caminho not in cache:
            try:
                txt = open(caminho, encoding="utf-8", errors="replace").read()
            except OSError:
                cache[caminho] = set()
            else:
                cache[caminho] = {_slug(t) for t in _TITULO_RE.findall(txt)}
        return cache[caminho]

    quebradas: list[str] = []
    total = 0
    for caminho in mds:
        try:
            txt = open(caminho, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for _rotulo, alvo in LINK_RE.findall(txt):
            if "#" not in alvo:
                continue
            destino, _, ancora = alvo.partition("#")
            destino, ancora = destino.strip(), ancora.strip()
            if not destino or not ancora:
                continue
            if destino.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            absoluto = os.path.normpath(os.path.join(os.path.dirname(caminho), destino))
            if not absoluto.endswith(".md") or not os.path.exists(absoluto):
                continue          # arquivo inexistente ja e pego por checar_links
            total += 1
            if ancora not in ancoras_de(absoluto):
                origem = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                quebradas.append(f"{origem} -> {alvo}")

    if quebradas:
        lista = "\n".join(f"         {q}" for q in quebradas)
        falhas.append(
            f"{len(quebradas)} de {total} ancora(s) nao resolvem contra um titulo do alvo:\n"
            f"{lista}"
        )
    else:
        print(f"  OK   ancoras: {total} conferidas contra os titulos do alvo")


def _todos_md() -> list[str]:
    mds: list[str] = []
    for dp, dns, fns in os.walk(RAIZ):
        dns[:] = [d for d in dns if d not in IGNORAR]
        mds.extend(os.path.join(dp, fn) for fn in fns if fn.endswith(".md"))
    return mds


def _dentro_da_raiz(absoluto: str) -> bool:
    """O caminho resolvido ainda esta dentro do repositorio?

    `os.path.commonpath` em vez de `startswith`: uma pasta irma chamada
    `Planilhador_backup` comeca com a string do RAIZ e NAO esta dentro dele.
    """
    try:
        return os.path.commonpath([os.path.abspath(absoluto), RAIZ]) == RAIZ
    except ValueError:      # drives diferentes no Windows
        return False


def checar_links(mds: list[str]) -> None:
    """Confere os links markdown, separando QUEBRADO de FORA DE ESCOPO.

    ⚠️ Este gate deixou o CI VERMELHO por sessoes a fio, e o estrago nao foi cosmetico.
    Os `../pack/CLAUDE.md` e `../pack/tokens/tokens.css` apontam para a pasta IRMA, que
    existe na maquina do Feca e **nunca** existe no checkout: o repo publicado e' so o
    `Planilhador/`. Cinco links legitimos reprovavam toda execucao.

    **CI cronicamente vermelho nao e' gate.** Ninguem distingue a falha nova da de
    sempre, e uma quebra REAL (um kwarg colidindo num teste) ja passou despercebida ate
    alguem abrir o log a mao. Era o item 1.7 do BACKLOG.

    **A regra: link que sai da raiz do repo NUNCA reprova, e sempre e' RELATADO.** Se ele
    resolve nesta maquina, sai como conferido; se nao resolve, sai NOMEADO na lista de
    "nao conferiveis daqui". Quem le a saida ve exatamente quais links a maquina dele nao
    pode julgar, e o gate nao depende de onde roda.

    ⚠️ **Duas tentativas mais espertas falharam antes desta, e o registro delas e' o que
    impede a terceira.**

      1. Olhar so o ARQUIVO: ausente virava "fora de escopo" sempre, e um
         `../pack/CLAUDEE.md` escrito errado passava em silencio em toda maquina. Trocar
         um alarme que toca sempre por um alarme mudo nao e' conserto.
      2. Olhar a PASTA do alvo ("se a pasta existe, da' para julgar"): parece certo e
         quebra no caso mais simples. `CLAUDE.md -> ../CLAUDE.md` tem como pasta o
         DIRETORIO ACIMA DO REPO, que existe em toda maquina, inclusive no runner do CI
         (`/home/runner/work/sharpen/`). O gate julgou, nao achou o arquivo, e reprovou —
         exatamente o falso vermelho que ele existe para acabar. Pego pelo proprio teste
         novo, no CI, antes de virar problema de alguem.

    Detectar erro de digitacao FORA do repo exige saber que aquela pasta irma deveria
    estar ali, e isso o repo nao sabe de dentro. Fica relatado, nao adivinhado.
    """
    quebrados: list[str] = []
    fora_ausentes: list[str] = []
    fora_conferidos = 0
    for caminho in mds:
        try:
            txt = open(caminho, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for _rotulo, alvo in LINK_RE.findall(txt):
            destino = alvo.split("#")[0].strip()
            if not destino or destino.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            absoluto = os.path.normpath(os.path.join(os.path.dirname(caminho), destino))
            existe = os.path.exists(absoluto)
            if _dentro_da_raiz(absoluto):
                if not existe:
                    origem = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                    quebrados.append(f"{origem} -> {alvo}")
            elif existe:
                fora_conferidos += 1
            else:
                origem = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                fora_ausentes.append(f"{origem} -> {alvo}")

    if quebrados:
        lista = "\n".join(f"         {q}" for q in quebrados)
        falhas.append(f"{len(quebrados)} link(s) markdown quebrado(s):\n{lista}")
    else:
        print(f"  OK   links markdown: {len(mds)} arquivos varridos, nenhum quebrado")
    if fora_conferidos or fora_ausentes:
        print(f"  OK   fora da raiz do repo: {fora_conferidos} conferido(s) nesta maquina, "
              f"{len(fora_ausentes)} nao conferivel(is) daqui")
        # NOMEADOS, e nao so contados: e' a unica pista que alguem tem de um link de fora
        # escrito errado. Contagem sozinha vira "ignorado em silencio".
        for q in fora_ausentes:
            print(f"         {q}")


def main() -> int:
    print("check_docs — gate de documentacao\n")
    checar_tamanho_claude()
    checar_tamanho_casos()
    txt = _status()
    if txt is not None:
        checar_tamanho_status(txt)
        checar_forma_status(txt)
    checar_backups()
    mds = _todos_md()
    checar_links(mds)
    checar_ancoras(mds)

    for a in avisos:
        print(f"\n  AVISO  {a}")

    if falhas:
        print()
        for f in falhas:
            print(f"  FAIL  {f}")
        print(f"\nRESULTADO: {len(falhas)} FAIL.")
        return 1

    print("\nRESULTADO: sem FAILs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

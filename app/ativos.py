"""Versão de asset pelo CONTEÚDO, calculada pelo servidor (s459, auditoria de 17/11).

O problema (NAVEGADOR C2/M1/M4, SERVIDOR P8): JS e CSS saíam sem `Cache-Control`, e a única
forma de o navegador buscar o arquivo novo era alguém trocar o `?v=N` à mão no HTML. Medido no
git: 96 de 470 commits que mudaram um asset não trocaram o `?v=` (20 %). O `data.js` ficou em
`?v=32` por 5 mudanças seguidas. Para quem estava com a versão velha em cache, F5 não resolvia:
o navegador nem pedia o arquivo (cache heurístico), e o defeito "voltava" para uns e não para
outros. O ETag do StaticFiles vem de `mtime`+tamanho, não do conteúdo, o que piorava.

A regra agora mora num lugar só:
  · todo HTML que o app serve tem as referências `.js`/`.css` LOCAIS reescritas para
    `?v=<hash do conteúdo>` (o `?v=` escrito à mão é ignorado e substituído);
  · o asset pedido com o hash CERTO vai `immutable` por um ano (a URL muda quando o conteúdo
    muda); qualquer outro pedido (sem `v`, ou com `v` velho/manual) vai `no-cache`, que obriga
    o navegador a revalidar (custa um 304);
  · o ETag do HTML é o hash do HTML JÁ REESCRITO: asset novo muda o ETag da página mesmo que
    o arquivo HTML em si não tenha mudado;
  · `BUILD_ID` é o hash do conjunto de assets, e a casca recarrega quando ele muda (3.1).

O que fica fora: URL montada dentro do JS (`new Worker('…?v=1')`, `importScripts`). Ela não é
reescrita, mas cai no `no-cache`, então nunca fica velha — só não ganha o `immutable`.
"""
from __future__ import annotations

import hashlib
import os
import posixpath
import re
import threading
from pathlib import Path

STATIC = Path(__file__).parent / "static"
# Prefixo de URL → pasta. Ordem importa: o mais específico primeiro.
MONTAGENS: tuple[tuple[str, Path], ...] = (
    ("/dashboard/", STATIC / "dash"),
    ("/static/", STATIC),
)
EXTENSOES = (".js", ".css")
IMUTAVEL = "public, max-age=31536000, immutable"
REVALIDA = "no-cache"

_lock = threading.Lock()
_hashes: dict[str, tuple[int, int, str | None]] = {}   # url → (mtime_ns, tamanho, hash)
# (rota, hash do original) → (reescrito, etag, ((url, hash usado), …))
_html: dict[tuple[str, str], tuple[str, str, tuple]] = {}
_build: str | None = None

_REF = re.compile(
    r"""(\b(?:src|href)\s*=\s*)(["'])([^"'#?\s]+?\.(?:js|css))(?:\?[^"'#]*)?(["'])""",
    re.IGNORECASE,
)


def arquivo_da_url(url: str) -> Path | None:
    """O arquivo em disco que a URL serve, ou None. Nunca sai da pasta montada."""
    for prefixo, raiz in MONTAGENS:
        if url.startswith(prefixo):
            rel = url[len(prefixo):]
            alvo = (raiz / rel).resolve()
            try:
                alvo.relative_to(raiz.resolve())
            except ValueError:
                return None
            return alvo if alvo.is_file() else None
    return None


def hash_da_url(url: str) -> str | None:
    """Hash curto do conteúdo do asset que a URL serve (None se não existe)."""
    arq = arquivo_da_url(url)
    if arq is None:
        return None
    try:
        st = arq.stat()
    except OSError:
        return None
    with _lock:
        hit = _hashes.get(url)
        if hit and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
            return hit[2]
    try:
        h = hashlib.sha256(arq.read_bytes()).hexdigest()[:12]
    except OSError:
        return None
    with _lock:
        _hashes[url] = (st.st_mtime_ns, st.st_size, h)
    return h


def _base(rota: str) -> str:
    return rota if rota.endswith("/") else rota.rsplit("/", 1)[0] + "/"


def reescrever(html: str, rota: str, usados: list | None = None) -> str:
    """Troca cada referência `.js`/`.css` local por `?v=<hash>`. Externa fica como está.
    `usados` (opcional) recebe os pares (url, hash) aplicados."""
    base = _base(rota or "/")

    def troca(m: re.Match) -> str:
        ref = m.group(3)
        if m.group(2) != m.group(4) or re.match(r"^(?:[a-z]+:|//)", ref, re.I):
            return m.group(0)
        url = ref if ref.startswith("/") else posixpath.normpath(base + ref)
        h = hash_da_url(url)
        if not h:
            return m.group(0)
        if usados is not None:
            usados.append((url, h))
        return f"{m.group(1)}{m.group(2)}{ref}?v={h}{m.group(4)}"

    return _REF.sub(troca, html)


def html_versionado(corpo: bytes, rota: str) -> tuple[bytes, str]:
    """(HTML reescrito, ETag do conteúdo reescrito). Guardado por rota + hash do original, e
    reaproveitado só enquanto cada asset referenciado continua com o hash que foi usado."""
    chave = (rota, hashlib.sha256(corpo).hexdigest())
    with _lock:
        hit = _html.get(chave)
    if hit and all(hash_da_url(u) == h for u, h in hit[2]):
        return hit[0].encode("utf-8"), hit[1]
    usados: list = []
    # O carimbo da identidade do código vai junto (a casca compara com `/versao`, 3.1).
    texto = reescrever(corpo.decode("utf-8"), rota, usados).replace("__SHARPEN_BUILD__", build_id())
    etag = '"' + hashlib.sha256(texto.encode("utf-8")).hexdigest()[:20] + '"'
    with _lock:
        if len(_html) > 200:
            _html.clear()
        _html[chave] = (texto, etag, tuple(usados))
    return texto.encode("utf-8"), etag


def cache_control_do_asset(url: str, v: str | None) -> str:
    """`immutable` só quando o `?v=` pedido é o hash do conteúdo de agora."""
    if v and v == hash_da_url(url):
        return IMUTAVEL
    return REVALIDA


def e_asset(url: str) -> bool:
    return url.lower().endswith(EXTENSOES) and any(url.startswith(p) for p, _ in MONTAGENS)


def build_id() -> str:
    """Hash do conjunto de JS/CSS/HTML servidos. Muda quando QUALQUER arquivo de tela muda, e só
    nesse caso (deploy só de servidor não pede recarga a ninguém)."""
    global _build
    if _build:
        return _build
    h = hashlib.sha256()
    for raiz, _dirs, arqs in sorted(os.walk(STATIC)):
        for nome in sorted(arqs):
            if nome.lower().endswith((".js", ".css", ".html")):
                p = Path(raiz) / nome
                h.update(str(p.relative_to(STATIC)).replace("\\", "/").encode())
                try:
                    h.update(p.read_bytes())
                except OSError:
                    pass
    _build = h.hexdigest()[:12]
    return _build

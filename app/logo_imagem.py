"""Normalização e saneamento da logo da conta (avatar do bloco de tipster, s362).

PURO: sem banco, sem FastAPI, sem I/O de disco — bytes entram, bytes saem. É o que
permite ao gate (`tests/test_logo_imagem.py`) exercer as regras de verdade em vez de
subir um servidor.

Duas famílias de entrada, dois destinos:

  · RASTER (png/jpg/webp) → sempre sai **PNG 256×256 RGBA**, a arte centrada por
    `contain` sobre fundo TRANSPARENTE. `contain` e não `cover` porque logo de
    tipster é quase sempre horizontal, e `cover` cortaria o nome da marca fora.
  · SVG → continua SVG, saneado.

⚠️ **O tipo vem dos BYTES, nunca do que o cliente declarou.** O `content_type` do
multipart e a extensão do arquivo são dado do remetente, e viram o `Content-Type` da
resposta quando a logo é servida de volta: confiar neles é deixar quem envia escolher
como o navegador interpreta o conteúdo. `farejar()` lê a assinatura do arquivo.

Sobre o SVG: ele é servido dentro de `<img src=…>`, contexto em que nenhum navegador
atual executa script. O saneamento aqui é a segunda camada (a terceira é o
`Content-Security-Policy` + `X-Content-Type-Options: nosniff` da rota), para o caso de
alguém um dia abrir a URL direto na barra de endereços — aí o SVG vira documento e o
script rodaria na origem do app.
"""

from __future__ import annotations

import io
import re

LIMITE_BYTES = 2 * 1024 * 1024          # 2 MB — o que o SPEC §4 fixou
LADO = 256                              # o quadrado normalizado
FORMATOS = ("png", "jpg", "webp", "svg")  # o que a tela oferece, em PT-BR no aviso

# Teto de pixels contra "bomba de descompressão" (arquivo de 50 KB que vira 40.000 ×
# 40.000 na memória). O Pillow tem um limite próprio; cravamos o nosso para não
# depender da versão instalada.
MAX_PIXELS = 40_000_000


class LogoInvalida(ValueError):
    """Arquivo recusado. A mensagem é PT-BR e vai direto para o usuário."""


def farejar(dados: bytes) -> str | None:
    """Tipo real do arquivo pela assinatura: 'png' | 'jpeg' | 'webp' | 'svg' | None."""
    if dados[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if dados[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "webp"
    # SVG é texto: aceita BOM, XML prolog, comentário e DOCTYPE antes do <svg.
    cabeca = dados[:1024].lstrip(b"\xef\xbb\xbf \t\r\n")
    if cabeca[:1] == b"<" and b"<svg" in dados[:4096].lower():
        return "svg"
    return None


# ── SVG: o que sai fora ──────────────────────────────────────────────────────
# Cada padrão existe por um vetor concreto, e o comentário diz qual — senão a
# próxima sessão "limpa" a lista achando que é paranoia.
_SVG_FORA = (
    # Script inline e o <foreignObject>, que reintroduz HTML (e <script>) dentro do SVG.
    re.compile(r"<\s*(script|foreignObject|iframe|embed|object)\b.*?<\s*/\s*\1\s*>",
               re.I | re.S),
    # A mesma família em forma auto-fechada (<script/>), que o par acima não pega.
    re.compile(r"<\s*(script|foreignObject|iframe|embed|object)\b[^>]*/\s*>", re.I),
    # DOCTYPE/ENTITY: a porta do XXE (entidade externa lendo arquivo do servidor).
    re.compile(r"<!DOCTYPE.*?>", re.I | re.S),
    re.compile(r"<!ENTITY.*?>", re.I | re.S),
)
# Handler de evento em qualquer elemento (onload, onclick, onmouseover, …).
_SVG_ON = re.compile(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
# href/xlink:href que não seja âncora interna nem data:image — mata javascript: e o
# <use href="http://…"> que puxa conteúdo de fora em tempo de render.
_SVG_HREF = re.compile(
    r"\s(?:xlink:)?href\s*=\s*(\"(?!#|data:image/)[^\"]*\"|'(?!#|data:image/)[^']*')",
    re.I,
)


def sanear_svg(texto: str) -> str:
    """Devolve o SVG sem script, sem handler de evento e sem referência externa."""
    for padrao in _SVG_FORA:
        texto = padrao.sub("", texto)
    texto = _SVG_ON.sub("", texto)
    texto = _SVG_HREF.sub("", texto)
    return texto


def _normalizar_raster(dados: bytes) -> bytes:
    """Raster → PNG 256×256 RGBA, `contain` centrado sobre fundo transparente."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover — só num ambiente sem a dependência
        raise LogoInvalida(
            "Servidor sem suporte a imagem: envie a logo em SVG ou avise o suporte."
        )

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        im = Image.open(io.BytesIO(dados))
        im.load()                      # força a decodificação aqui, com o try em volta
    except Exception:
        raise LogoInvalida("Não consegui ler esta imagem. Ela pode estar corrompida.")

    # RGBA sempre: o fundo do quadrado é transparente, e converter depois de colar
    # achataria a transparência da própria arte contra preto.
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    # `thumbnail` só REDUZ. Logo menor que 256 fica no tamanho original, centrada —
    # ampliar borraria a arte para ganhar pixel que não existe no arquivo.
    im.thumbnail((LADO, LADO), Image.LANCZOS)
    quadro = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    quadro.paste(im, ((LADO - im.width) // 2, (LADO - im.height) // 2))
    saida = io.BytesIO()
    quadro.save(saida, "PNG", optimize=True)
    return saida.getvalue()


def normalizar(dados: bytes) -> tuple[str, bytes]:
    """Valida e normaliza a logo enviada. Devolve `(mime, bytes)` prontos para gravar.

    Levanta `LogoInvalida` com mensagem PT-BR em tudo que não passa: vazio, acima de
    2 MB, formato fora da lista, arquivo ilegível.
    """
    if not dados:
        raise LogoInvalida("Arquivo vazio.")
    if len(dados) > LIMITE_BYTES:
        raise LogoInvalida(
            f"Arquivo acima do limite de {LIMITE_BYTES // (1024 * 1024)} MB."
        )
    tipo = farejar(dados)
    if tipo is None:
        raise LogoInvalida("Formato não aceito. Envie PNG, JPG, WEBP ou SVG.")
    if tipo == "svg":
        try:
            texto = dados.decode("utf-8")
        except UnicodeDecodeError:
            raise LogoInvalida("SVG precisa estar em UTF-8.")
        limpo = sanear_svg(texto)
        if "<svg" not in limpo.lower():
            raise LogoInvalida("Este SVG não tem desenho nenhum depois da limpeza.")
        return "image/svg+xml", limpo.encode("utf-8")
    return "image/png", _normalizar_raster(dados)

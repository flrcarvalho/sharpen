# -*- coding: utf-8 -*-
"""Injeta as fontes da marca (Manrope + JetBrains Mono, subset latin) como
data URI no lugar do marcador <!--FONTS-->.

A CSP do Artifact bloqueia host externo, entao webfont por URL cairia em
fallback silencioso. O subset `latin` (U+0000-00FF) ja cobre todo o pt-BR
(acentos vivem no Latin-1 Supplement); o `latin-ext` fica de fora de proposito
para nao dobrar o peso do arquivo.
"""
import base64
import pathlib
import sys

FONTS_DIR = pathlib.Path(
    r"C:\Users\Fernando\Downloads\FDC Capital\Planilhador\app\static\fonts"
)

FACES = [
    ("Manrope", "manrope-latin.woff2"),
    ("JetBrains Mono", "jetbrainsmono-latin.woff2"),
]


def css_fontes() -> str:
    partes = []
    for familia, arquivo in FACES:
        dados = (FONTS_DIR / arquivo).read_bytes()
        b64 = base64.b64encode(dados).decode("ascii")
        partes.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:400 800;"
            "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (familia, b64)
        )
    return "\n".join(partes)


def main(origem: str, destino: str) -> None:
    src = pathlib.Path(origem).read_text(encoding="utf-8")
    if "<!--FONTS-->" not in src:
        raise SystemExit("marcador <!--FONTS--> nao encontrado em %s" % origem)
    out = src.replace("<!--FONTS-->", css_fontes())
    pathlib.Path(destino).write_text(out, encoding="utf-8")
    kb = len(out.encode("utf-8")) / 1024
    print("ok: %s -> %s (%.0f KB)" % (origem, destino, kb))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

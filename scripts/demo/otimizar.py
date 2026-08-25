# -*- coding: utf-8 -*-
"""Converte as capturas PNG em WebP para a landing.

    python scripts/demo/otimizar.py <pasta-das-capturas>

Por que existe: `capturar.mjs` grava PNG a 2x (deviceScaleFactor 2) porque e' o
formato sem perda em que o print nasce -- 14 telas + 7 recortes dao ~10 MB. Uma
pagina de vendas com 10 MB de imagem morre no 4G do celular, que e' de onde vem
a maior parte de quem clica num link.

O destino e' `app/static/landing/img/`, servido pelo mount `/static`.

Duas larguras, porque os dois usos sao diferentes:
  - TELA (`NN-nome`): a pagina inteira, usada em tamanho grande. 1400 px.
  - RECORTE (`rN-nome`): um card so, usado como destaque. 1200 px ja passa do
    tamanho que a landing reserva, entao sobra nitidez em tela retina.

Nao recortamos nada aqui: o enquadramento e' decidido no `capturar.mjs`, por
SELETOR. Cortar por pixel neste passo quebraria em silencio quando a tela mudar.
"""
import pathlib
import sys

from PIL import Image

LARGURA_TELA = 1400
LARGURA_RECORTE = 1200
QUALIDADE = 80

RAIZ = pathlib.Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "app" / "static" / "landing" / "img"


def converter(origem: pathlib.Path):
    DESTINO.mkdir(parents=True, exist_ok=True)
    pngs = sorted(origem.glob("*.png"))
    if not pngs:
        sys.exit(f"nenhum PNG em {origem} — rode o capturar.mjs antes.")

    total_antes = total_depois = 0
    for png in pngs:
        alvo_largura = LARGURA_RECORTE if png.stem.startswith("r") else LARGURA_TELA
        with Image.open(png) as im:
            im = im.convert("RGB")
            if im.width > alvo_largura:
                altura = round(im.height * alvo_largura / im.width)
                im = im.resize((alvo_largura, altura), Image.LANCZOS)
            saida = DESTINO / f"{png.stem}.webp"
            im.save(saida, "WEBP", quality=QUALIDADE, method=6)

        antes, depois = png.stat().st_size, saida.stat().st_size
        total_antes += antes
        total_depois += depois
        print(f"  {png.stem:24} {antes // 1024:5} KB -> {depois // 1024:4} KB"
              f"  ({im.width}x{im.height})")

    print(f"\n{len(pngs)} imagens · {total_antes // 1024} KB -> {total_depois // 1024} KB"
          f" ({100 - round(100 * total_depois / total_antes)}% menor)")
    print(f"em {DESTINO}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    converter(pathlib.Path(sys.argv[1]))

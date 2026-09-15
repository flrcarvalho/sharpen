"""Gates da logo da conta (avatar do bloco de tipster na sidebar, s362).

Cobre `app/logo_imagem.py` (puro: bytes entram, bytes saem) e o registro de tipsters
públicos, que é de onde saem nome e plano do bloco.

O que este arquivo NÃO cobre, para o verde não virar promessa falsa:
  · as rotas (`/conta/logo`, `/tipsters/<slug>/logo`) e a gravação em `conta_logo` —
    precisam do Postgres, que só existe no CI (ver `tests/conftest.py`);
  · o CSS e o JS do bloco — medir tela é o `scripts/demo/servidor_demo.py` em headless,
    não pytest;
  · se o navegador de fato bloqueia script num SVG servido — o saneamento aqui é uma
    das três camadas (as outras são o `<img>` e o CSP da rota).

Todas as asserções abaixo foram provadas por MUTAÇÃO: quebrando a regra no código, o
teste correspondente falha. As mutações que NÃO foram detectadas estão anotadas.
"""
import io
import sys

import pytest

import logo_imagem


# ── Assinatura do arquivo (o tipo vem dos bytes, não do que o cliente declarou) ──

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)
JPEG_CABECA = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP_CABECA = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 64
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'


def test_farejar_le_a_assinatura_e_nao_a_extensao():
    assert logo_imagem.farejar(PNG_1PX) == "png"
    assert logo_imagem.farejar(JPEG_CABECA) == "jpeg"
    assert logo_imagem.farejar(WEBP_CABECA) == "webp"
    assert logo_imagem.farejar(SVG) == "svg"


def test_farejar_recusa_o_que_nao_e_imagem():
    # Um executável renomeado para .png continua sendo um executável.
    assert logo_imagem.farejar(b"MZ\x90\x00" + b"\x00" * 64) is None
    assert logo_imagem.farejar(b"") is None


def test_svg_com_prolog_xml_e_bom_ainda_e_svg():
    # Exportador de vetor costuma escrever as duas coisas antes do <svg.
    com_prolog = b'\xef\xbb\xbf<?xml version="1.0"?>\n<!-- logo -->\n' + SVG
    assert logo_imagem.farejar(com_prolog) == "svg"


# ── Limites e recusas ────────────────────────────────────────────────────────

def test_arquivo_vazio_e_recusado():
    with pytest.raises(logo_imagem.LogoInvalida):
        logo_imagem.normalizar(b"")


def test_acima_de_2mb_e_recusado_antes_de_decodificar():
    gordo = PNG_1PX + b"\x00" * logo_imagem.LIMITE_BYTES
    with pytest.raises(logo_imagem.LogoInvalida) as e:
        logo_imagem.normalizar(gordo)
    assert "MB" in str(e.value)


def test_formato_fora_da_lista_e_recusado():
    with pytest.raises(logo_imagem.LogoInvalida) as e:
        logo_imagem.normalizar(b"GIF89a" + b"\x00" * 32)
    assert "PNG" in str(e.value)


# ── Saneamento do SVG ────────────────────────────────────────────────────────
# Cada caso é um vetor concreto. Sem eles, "limpar a lista de regex" vira refactor
# inocente na próxima sessão.

@pytest.mark.parametrize("veneno", [
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><rect/></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><script src="x.js"/><rect/></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><rect onload="alert(1)"/></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg" onmouseover="alert(1)"><rect/></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><script>x</script></foreignObject><rect/></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"><rect/></a></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><use xlink:href="http://fora/x.svg"/><rect/></svg>',
    b'<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>',
])
def test_svg_perigoso_sai_saneado_e_nao_recusado(veneno):
    """O arquivo continua servindo: recusar o SVG inteiro por um atributo faria o
    tipster achar que a logo dele "não funciona". O que sai é o veneno."""
    mime, limpo = logo_imagem.normalizar(veneno)
    texto = limpo.decode("utf-8").lower()
    assert mime == "image/svg+xml"
    assert "<script" not in texto
    assert "foreignobject" not in texto
    assert "javascript:" not in texto
    assert "<!entity" not in texto
    assert "<!doctype" not in texto
    assert "onload=" not in texto and "onmouseover=" not in texto
    assert "http://fora" not in texto
    assert "<rect" in texto          # o desenho legítimo sobrevive


def test_svg_ancora_interna_sobrevive():
    """`href="#grad"` é como um gradiente é referenciado dentro do próprio arquivo.
    Cortá-lo junto com o externo apagaria a cor de metade das logos."""
    dentro = b'<svg xmlns="http://www.w3.org/2000/svg"><use href="#grad"/><rect fill="url(#grad)"/></svg>'
    _, limpo = logo_imagem.normalizar(dentro)
    assert b'href="#grad"' in limpo


def test_arquivo_que_so_parecia_svg_por_causa_do_script_e_recusado():
    """HTML renomeado para .svg: o `<svg` que o fareja viu estava DENTRO do script.
    Tirado o script, não sobrou desenho nenhum — e o que sobrou não vai para o banco."""
    html = b'<html><body><script>var s = "<svg/>";</script></body></html>'
    assert logo_imagem.farejar(html) == "svg"      # o fareja se deixa enganar aqui
    with pytest.raises(logo_imagem.LogoInvalida):  # e a checagem pós-limpeza pega
        logo_imagem.normalizar(html)


# ── Normalização do raster ───────────────────────────────────────────────────

pillow = pytest.importorskip("PIL.Image", reason="Pillow ausente no ambiente local")


def _png(largura, altura, cor=(255, 0, 0, 255)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGBA", (largura, altura), cor).save(buf, "PNG")
    return buf.getvalue()


def test_raster_sai_sempre_no_quadrado_de_256():
    from PIL import Image
    mime, dados = logo_imagem.normalizar(_png(900, 300))
    assert mime == "image/png"
    im = Image.open(io.BytesIO(dados))
    assert im.size == (logo_imagem.LADO, logo_imagem.LADO)


def test_logo_horizontal_nao_e_cortada_e_o_resto_fica_transparente():
    """`contain`, não `cover`. Logo de tipster é quase sempre horizontal: com `cover`
    o nome da marca sairia do quadro, e ninguém repara até ver a própria logo torta."""
    from PIL import Image
    _, dados = logo_imagem.normalizar(_png(800, 200))
    im = Image.open(io.BytesIO(dados)).convert("RGBA")
    # A arte ocupa a largura inteira e uma faixa central de 64px (800x200 → 256x64).
    assert im.getpixel((128, 128))[3] == 255        # centro: arte
    assert im.getpixel((128, 4))[3] == 0            # topo: transparente, não preto
    assert im.getpixel((128, 251))[3] == 0          # base: idem
    assert im.getpixel((0, 128))[3] == 255          # borda lateral: arte chegou até a ponta


def test_imagem_menor_que_256_nao_e_ampliada():
    """Ampliar borra a arte para ganhar pixel que não existe no arquivo."""
    from PIL import Image
    _, dados = logo_imagem.normalizar(_png(64, 64))
    im = Image.open(io.BytesIO(dados)).convert("RGBA")
    assert im.size == (256, 256)
    assert im.getpixel((128, 128))[3] == 255        # a arte está no centro
    assert im.getpixel((4, 4))[3] == 0              # e a moldura continua vazia


def test_png_com_transparencia_nao_e_achatado_contra_preto():
    from PIL import Image
    _, dados = logo_imagem.normalizar(_png(256, 256, (0, 200, 0, 128)))
    im = Image.open(io.BytesIO(dados)).convert("RGBA")
    assert im.getpixel((128, 128))[3] == 128


def test_arquivo_corrompido_com_assinatura_boa_e_recusado_sem_estourar():
    truncado = PNG_1PX[:20] + b"\x00" * 40
    with pytest.raises(logo_imagem.LogoInvalida):
        logo_imagem.normalizar(truncado)

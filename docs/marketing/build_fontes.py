# -*- coding: utf-8 -*-
"""Gera as duas formas publicaveis de um documento HTML da marca.

A FONTE (versionada) e' um documento completo: <!DOCTYPE html> +
<html data-theme="dark"> + <head> + <body>, com o marcador <!--FONTS--> no
lugar das @font-face. Dela saem duas saidas:

  1. .build.html     -- documento completo, com Manrope + JetBrains Mono
                        embutidas em base64. Abre offline, com duplo-clique,
                        fora do projeto. E' o entregavel para humanos.

  2. .fragment.html  -- <title> + <style> + conteudo do <body>, SEM o envelope
                        de documento. E' o que o Artifact aceita: ele embrulha
                        o arquivo no proprio esqueleto, e uma segunda <html>
                        dentro geraria markup invalido.

O subset `latin` (U+0000-00FF) ja cobre todo o pt-BR -- os acentos vivem no
Latin-1 Supplement. O `latin-ext` fica de fora de proposito: dobraria o peso
sem cobrir nada que estas paginas usem.

GATE DE TEMA: o script recusa gerar se a fonte tiver `prefers-color-scheme` ou
`data-theme="light"`. Foi exatamente esse bloco que fez as duas primeiras
versoes abrirem BRANCAS em maquina com tema claro. Os documentos da marca sao
dark only, e o gate existe para a regra nao depender de eu lembrar dela.

Uso:
    python build_fontes.py <fonte>.html            # gera as duas saidas
    python build_fontes.py <fonte>.html <saida>    # so o documento, no caminho dado
"""
import base64
import pathlib
import re
import sys

FONTS_DIR = pathlib.Path(
    r"C:\Users\Fernando\Downloads\FDC Capital\Planilhador\app\static\fonts"
)

FACES = [
    ("Manrope", "manrope-latin.woff2"),
    ("JetBrains Mono", "jetbrainsmono-latin.woff2"),
]

MARCADOR = "<!--FONTS-->"


def css_fontes() -> str:
    """@font-face com a fonte inteira em data URI."""
    partes = []
    for familia, arquivo in FACES:
        caminho = FONTS_DIR / arquivo
        if not caminho.exists():
            raise SystemExit("fonte nao encontrada: %s" % caminho)
        b64 = base64.b64encode(caminho.read_bytes()).decode("ascii")
        partes.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:400 800;"
            "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (familia, b64)
        )
    return "\n".join(partes)


def fragmento(doc: str) -> str:
    """Extrai title + style + interior do body.

    Falha se algum pedaco faltar: melhor quebrar aqui do que publicar um
    fragmento mudo (sem estilo) e so descobrir olhando a pagina no ar.
    """
    titulo = re.search(r"<title>.*?</title>", doc, re.S)
    estilo = re.search(r"<style>.*?</style>", doc, re.S)
    corpo = re.search(r"<body[^>]*>(.*)</body>", doc, re.S)
    faltando = [nome for nome, achado in
                (("<title>", titulo), ("<style>", estilo), ("<body>", corpo))
                if not achado]
    if faltando:
        raise SystemExit("fragmento impossivel, faltou: %s" % ", ".join(faltando))
    return "%s\n%s\n%s" % (titulo.group(0), estilo.group(0), corpo.group(1).strip())


def sem_comentarios(doc: str) -> str:
    """Remove comentarios CSS e HTML antes de auditar o tema.

    Sem isso o gate acusa a propria nota de rodape do arquivo ("Sem
    prefers-color-scheme, sem data-theme=light") e recusa um documento
    correto -- o gate tem de ler o CSS, nao a prosa sobre o CSS.
    """
    doc = re.sub(r"/\*.*?\*/", "", doc, flags=re.S)
    doc = re.sub(r"<!--(?!FONTS-->).*?-->", "", doc, flags=re.S)
    return doc


def kb(texto: str) -> float:
    return len(texto.encode("utf-8")) / 1024


def main(argv) -> None:
    origem = pathlib.Path(argv[1])
    src = origem.read_text(encoding="utf-8")

    if MARCADOR not in src:
        raise SystemExit("marcador %s nao encontrado em %s" % (MARCADOR, origem))
    if not src.lstrip().startswith("<!DOCTYPE html>"):
        raise SystemExit("%s nao e' documento completo: falta o <!DOCTYPE html>" % origem)
    if 'data-theme="dark"' not in src:
        raise SystemExit('%s nao tem data-theme="dark" no <html>' % origem)
    codigo = sem_comentarios(src)
    if "prefers-color-scheme" in codigo or 'data-theme="light"' in codigo:
        raise SystemExit(
            "%s tem tema claro (prefers-color-scheme / data-theme=\"light\").\n"
            "Documento da marca e' DARK ONLY -- foi isso que fez a pagina abrir\n"
            "branca em maquina com tema claro. Remova o bloco antes de gerar." % origem
        )

    doc = src.replace(MARCADOR, css_fontes())

    if len(argv) > 2:                       # saida unica, caminho explicito
        saidas = [(pathlib.Path(argv[2]), doc)]
    else:
        base = origem.with_suffix("")
        saidas = [
            (base.with_name(base.name + ".build.html"), doc),
            (base.with_name(base.name + ".fragment.html"), fragmento(doc)),
        ]

    for destino, conteudo in saidas:
        destino.write_text(conteudo, encoding="utf-8")
        print("ok: %s (%.0f KB)" % (destino.name, kb(conteudo)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv)

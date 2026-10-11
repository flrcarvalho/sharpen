"""Sombra de NÚMEROS (s407): o candidato gravaria a MESMA stake, odd e resultado?

A pergunta é do Feca, com o critério dele: *"A única coisa que não pode errar é número.
A odd tem que ser 100% igual, a stake tem que ser 100% igual, o resultado tem que ser
100% igual. Se ele entregar uma palavra diferente na descrição, não importa."*

O placar antigo da sombra (`repository.pontuar_saida`) confere código, colunas e
descrição, e nunca comparou número. Este módulo compara, aposta a aposta, QUATRO
versões de cada campo:

    titular bruto    o Sonnet antes de qualquer fiscal
    titular final    o que voltou para a tela (o que o usuário salva)
    candidato bruto  o Haiku como veio
    candidato final  o Haiku depois dos MESMOS fiscais determinísticos

A métrica principal é `candidato final == titular final`: se trocar, o que iria para o
banco seria igual? As outras três dizem quem errou e quem salvou.

Função PURA, sem I/O e sem IA. A régua de número é a do `/salvar`: `parse_tsv` lê as
colunas e `_num_or_none` (a mesma do `valor_monetario_valido`) lê o número. Igualdade
por `Decimal`, SEM tolerância: `1,85` = `1.85` e `8,9688` = `8,96880`, mas `1,85` ≠ `1,86`.

O QUE ESTA COMPARAÇÃO NÃO COBRE:
  • Linha sem código. Sem chave não há com quem parear, e parear por posição seria
    chute. Ela é CONTADA (`sem_chave_*`), nunca comparada.
  • Descrição, esporte e categoria. Por decisão do Feca, não decidem nada aqui.
"""
from decimal import Decimal

from repository import _RESULTADOS_VALIDOS, _num_or_none, codigos_do_texto, parse_tsv

CAMPOS = ("stake", "odd", "res")


def norm_numero(v) -> str | None:
    """Número na régua do `/salvar`, como texto canônico. `None` = vazio.

    Ilegível vira `!<cru>`: o `/salvar` recusaria a linha, e dois lixos iguais ainda
    contam como iguais, porque gravariam a mesma recusa.
    """
    s = (str(v).strip() if v is not None else "")
    if not s:
        return None
    n = _num_or_none(s)
    if n is None:
        return "!" + s
    # `repr` do float é o menor texto que volta ao MESMO float: `8,9688` e `8,96880`
    # caem no mesmo valor, e `.normalize()` tira o zero à direita que sobrar.
    d = Decimal(repr(n)).normalize()
    return format(d, "f")


def norm_resultado(v) -> str | None:
    """Código de resultado. `None` = aposta aberta; fora do conjunto vira `!<cru>`."""
    s = (str(v).strip().upper() if v is not None else "")
    if not s:
        return None
    return s if s in _RESULTADOS_VALIDOS else "!" + s


def _indexar(tsv: str | None) -> tuple[dict, int]:
    """{(código, ocorrência): {stake, odd, res}} e quantas linhas ficaram sem código.

    O mesmo código duas vezes no lote pareia pela ORDEM de aparição: é o que o banco
    faria com duas linhas de mesmo código (a segunda escala, não some).
    """
    idx: dict = {}
    vistos: dict = {}
    sem_chave = 0
    for row in parse_tsv(tsv or ""):
        cod = (row.get("codigo_bilhete") or "").strip()
        if not cod:
            sem_chave += 1
            continue
        vistos[cod] = vistos.get(cod, 0) + 1
        idx[(cod, vistos[cod])] = {
            "stake": norm_numero(row.get("stake")),
            "odd": norm_numero(row.get("odd")),
            "res": norm_resultado(row.get("resultado")),
        }
    return idx, sem_chave


def comparar(titular_bruto: str | None, titular_final: str | None,
             candidato_bruto: str | None, candidato_final: str | None,
             texto: str | None, codigo_ocr: bool = False) -> dict:
    """Compara as quatro versões aposta a aposta. Devolve {"linhas": [...], "resumo": {...}}.

    Cada linha: codigo, ocorrencia, `<campo>_tb/_tf/_cb/_cf`, faltou, sobrou,
    inventado e `igual_<campo>` (None quando um dos lados finais não tem a aposta).

    `inventado` é julgado no candidato BRUTO contra o gabarito de códigos do texto
    (`codigos_do_texto`, o mesmo da cobertura). Sem gabarito (casa sem marcador) não há
    como julgar, e nada é marcado. Com `codigo_ocr` (lote com IMAGEM) também não: ali o
    código vem do card, legitimamente fora do texto, e o `_corrigir_codigos_fantasma`
    é no-op pelo mesmo motivo.
    """
    tb, _ = _indexar(titular_bruto)
    tf, sem_tf = _indexar(titular_final)
    cb, _ = _indexar(candidato_bruto)
    cf, sem_cf = _indexar(candidato_final)

    linhas = []
    for chave in list(tf) + [k for k in cf if k not in tf]:
        a, b = tf.get(chave), cf.get(chave)
        linha = {"codigo": chave[0], "ocorrencia": chave[1],
                 "faltou": b is None, "sobrou": a is None, "inventado": False}
        for c in CAMPOS:
            linha[f"{c}_tb"] = (tb.get(chave) or {}).get(c)
            linha[f"{c}_tf"] = (a or {}).get(c)
            linha[f"{c}_cb"] = (cb.get(chave) or {}).get(c)
            linha[f"{c}_cf"] = (b or {}).get(c)
            linha[f"igual_{c}"] = (a[c] == b[c]) if (a is not None and b is not None) else None
        linhas.append(linha)

    gabarito = set() if codigo_ocr else set(codigos_do_texto(texto))
    inventados = 0
    if gabarito:
        for (cod, oc), v in cb.items():
            if cod in gabarito:
                continue
            inventados += 1
            linha = {"codigo": cod, "ocorrencia": oc, "faltou": False, "sobrou": False,
                     "inventado": True}
            for c in CAMPOS:
                linha.update({f"{c}_tb": None, f"{c}_tf": None, f"{c}_cb": v[c],
                              f"{c}_cf": None, f"igual_{c}": None})
            linhas.append(linha)

    pares = [l for l in linhas if not (l["faltou"] or l["sobrou"] or l["inventado"])]
    resumo = {
        "comparadas": len(pares),
        "iguais_stake": sum(1 for l in pares if l["igual_stake"]),
        "iguais_odd": sum(1 for l in pares if l["igual_odd"]),
        "iguais_res": sum(1 for l in pares if l["igual_res"]),
        "iguais_tres": sum(1 for l in pares if all(l[f"igual_{c}"] for c in CAMPOS)),
        "faltou": sum(1 for l in linhas if l["faltou"]),
        "sobrou": sum(1 for l in linhas if l["sobrou"]),
        "inventado": inventados,
        "sem_chave_titular": sem_tf,
        "sem_chave_candidato": sem_cf,
    }
    return {"linhas": linhas, "resumo": resumo}

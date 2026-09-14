# -*- coding: utf-8 -*-
"""Canonização de NOME DE TIPSTER — fonte única para o import e para o rename.

O problema (s355, base do Diogo): o mesmo tipster aparece em várias grafias que
diferem só por **caixa** (`peixe` / `Peixe`) ou por **acento** (`araujo` /
`Araújo`). Como `tipster` é TEXTO em `bilhetes`, em `tipsters.nome` e nas CHAVES
de `custo_store.custo_tipster`, cada grafia é um tipster diferente no sistema —
o dashboard mostra dois cards, o custo lançado numa grafia não aparece na outra.

**Por que um módulo e não uma função em cada script:** o import (que escreve as
linhas novas) e o rename (que arruma as que já estão no banco) precisam chegar
ao MESMO nome. Dois normalizadores independentes concordam hoje e divergem no
primeiro acento — `Araújo` isolado viraria `Araujo` num lado e `Araújo` no
outro, e o tipster nasceria partido de novo. É a mesma razão de o `parseNum` do
dashboard ser um só (CLAUDE.md, item 6 da regra de UI).

Regra de decisão, determinística e provada pelo dado (nunca por palpite):

1. **Grupo** = grafias que coincidem depois de `casefold` + remoção de acento +
   colapso de espaço. `araujo`, `ARAUJO` e `Araújo` caem no mesmo grupo.
2. **Vencedora do grupo**: se alguma variante tem acento, vence a **acentuada
   mais frequente** — o acento é informação que a digitação sem acento perdeu, e
   o contrário nunca é verdade. Sem nenhuma acentuada, vence a mais frequente.
   Empate desempata pela ordem alfabética (estável, para o mapa não mudar de uma
   rodada para outra).
3. A vencedora sai em **Title Case** (decisão do Feca, s355), aplicado só na
   primeira letra de cada palavra — o resto do token é preservado, senão `CP4`
   viraria `Cp4`… mas `cp4` (que é como está na base) continua `Cp4`. Caixa
   interna só se preserva quando a origem já a tinha.

O mapa fica num JSON versionado ao lado (`tipsters_diogo_map.json`): ele é o
de-para auditável, e é onde entra qualquer **merge semântico** que o Feca pedir
depois (`pei` → `Peixe`), sem tocar em código.

⚠️ O merge por caixa/acento é automático. Merge de APELIDO (`pei` × `peixe`)
NUNCA é inferido aqui — dois apelidos parecidos podem ser duas pessoas.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter

MAPA_PATH = os.path.join(os.path.dirname(__file__), 'tipsters_diogo_map.json')

_ESPACO = re.compile(r'\s+')


def limpar(nome) -> str:
    """Trim + colapso de espaço. Não muda caixa nem acento."""
    if nome is None:
        return ''
    return _ESPACO.sub(' ', str(nome)).strip()


def chave(nome) -> str:
    """Chave de agrupamento: sem caixa, sem acento, sem espaço duplo."""
    base = limpar(nome).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', base)
                   if unicodedata.category(c) != 'Mn')


def _tem_acento(nome: str) -> bool:
    return any(unicodedata.category(c) == 'Mn'
               for c in unicodedata.normalize('NFD', nome))


def title_case(nome: str) -> str:
    """Primeira letra de cada palavra em caixa alta; o resto verbatim."""
    return ' '.join(p[:1].upper() + p[1:] for p in limpar(nome).split(' ') if p)


def construir_mapa(contagem: Counter) -> dict[str, str]:
    """`{grafia bruta: nome canônico}` a partir da contagem de TODAS as grafias.

    A contagem tem de vir do universo INTEIRO (export + banco) — decidir o
    vencedor olhando só uma das fontes faz as duas chegarem a nomes diferentes.
    """
    grupos: dict[str, Counter] = {}
    for bruto, n in contagem.items():
        nome = limpar(bruto)
        if not nome:
            continue
        grupos.setdefault(chave(nome), Counter())[nome] += n

    mapa: dict[str, str] = {}
    for variantes in grupos.values():
        acentuadas = {k: v for k, v in variantes.items() if _tem_acento(k)}
        pool = acentuadas or dict(variantes)
        vencedora = sorted(pool.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        canon = title_case(vencedora)
        for grafia in variantes:
            mapa[grafia] = canon
    return mapa


def salvar_mapa(mapa: dict[str, str], caminho: str = MAPA_PATH) -> None:
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(mapa, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def carregar_mapa(caminho: str = MAPA_PATH) -> dict[str, str]:
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)


def canonico(nome, mapa: dict[str, str] | None = None) -> str:
    """Nome canônico de uma grafia.

    Consulta o mapa pela grafia exata e, se não achar, pela chave sem
    caixa/acento — assim uma grafia nova que só difere por caixa de uma já
    mapeada não escapa. Sem mapa nenhum, cai no Title Case.
    """
    nome = limpar(nome)
    if not nome:
        return ''
    mapa = carregar_mapa() if mapa is None else mapa
    if nome in mapa:
        return mapa[nome]
    k = chave(nome)
    for grafia, canon in mapa.items():
        if chave(grafia) == k:
            return canon
    return title_case(nome)

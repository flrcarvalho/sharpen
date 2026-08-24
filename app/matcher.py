"""Atribuição de tipster por EVIDÊNCIA — aprende do que o dono já rotulou à mão.

Por que existe (s289)
---------------------
O matcher anterior (`_sugParaBilhete`, inline no `app/static/index.html`) pontuava o que o
dono DECLARA no perfil de Tipster / Método: casas, esportes, mercados e uma "dica de stake".
Medido na base real, ele fazia 47 % de cobertura com **75 % de precisão** na carteira do Feca,
e 212 dos 287 erros iam para um único tipster — o Arrudex. Três causas, todas do desenho:

1. **Amplitude de declaração virava pontos.** O Arrudex declara 3 esportes, 10 mercados e 8
   casas; o SóChutes declara 1 esporte. Quem declara mais aparece em mais bilhetes.
2. **O filtro duro de esporte decapitava o dono certo.** 955 dos 2.424 bilhetes de 30 dias têm
   esporte "Múltiplos"; o SóChutes, que só declara "Futebol", era eliminado em todos eles.
3. **Sobrar por eliminação virava certeza.** Com os concorrentes vetados, o atalho
   `ranked.length === 1` cravava o último de pé com score 3 — sem folga nenhuma.

E a declaração nem sempre é verdadeira: a observação do Arrudex diz "sempre com final redondo
(0)" e 98 bilhetes reais dele, na mesma janela, não são redondos. **Perfil é o que o dono
acha; a base é o que ele faz.** Aqui a base manda.

Medido com holdout TEMPORAL (treina no passado, testa nos últimos 30 dias), por dono
(cobertura / precisão):

    dono       matcher declarativo     este módulo
    Feca         47 % / 74 %           55 % / 90 %
    Gabriel      12 % / 99 %           26 % / 97 %
    Jonathan     10 % / 41 %           12 % / 94 %

Na carteira do Feca isso é 295 erros virando 134, com MAIS bilhetes sugeridos (1.156 → 1.344);
os erros que caíam no Arrudex passam de 155 para 6, e os 165 bilhetes do SóChutes na janela
saem de 0 acertos para 82.

Um limite que nenhum ajuste tira: tipster NOVO não tem histórico, então não concorre, e o
bilhete dele ou fica vazio ou vai para o vizinho mais parecido. Foi o caso do Fatuch — 132
bilhetes na janela, ZERO no treino (10 % dos bilhetes do Feca estão nessa situação). O modelo
sai disso sozinho: ele é retreinado a cada 5 min e o rótulo humano o invalida na hora, então
as primeiras correções do dono já entram no lote seguinte.

O modelo
--------
Naive-Bayes multinomial sobre features categóricas do bilhete (casa · esporte · mercado ·
final/valor/faixa da stake · nº de pernas), treinado só nos rótulos de procedência **humana**
— `origem_tipster = 'sugerido'` fica de fora, senão o sistema aprende do próprio chute.

Dois cortes são load-bearing; tirar qualquer um já quebrou o matcher na medição:

* **MARGEM** — só sugere com folga em log-odds sobre o 2º colocado. É a confiança RELATIVA,
  herdada da folga-7 do matcher antigo: empate fica vazio, não chuta.
* **MAX_INEDITAS** — e a confiança ABSOLUTA, que faltava. Naive-Bayes escolhe o melhor entre
  os CONHECIDOS: um tipster novo, ainda sem histórico, não concorre, e todo bilhete dele vira
  erro com margem alta. Foi o caso do `Fatuchex` na base do Gabriel — 138 erros num só nome.
  Se alguma feature do bilhete nunca apareceu para o vencedor, ele não é o dono: ninguém
  conhecido é. Ligar este corte levou o Gabriel de 74 % para 94 % de precisão.

Fonte da medição: `scripts/backtest_matcher.py` (roda contra o Postgres, read-only).
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict
from typing import Any, Iterable, Optional

# Folga mínima em log-odds sobre o 2º colocado. 2,5 é o ponto de operação medido: ~90 % ou mais
# de precisão nos três donos com histórico, com cobertura igual ou maior que a do declarativo.
# Curva medida (cobertura/precisão, Feca · Gabriel · Jonathan): 2,0 → 58/89 · 31/94 · 14/89;
# 2,5 → 55/90 · 26/97 · 12/94; 4,0 → 38/95 · 15/99 · 9/99. Apertar mais compra precisão parando
# de sugerir — o que não serve para nada.
MARGEM = 2.5
# Features do bilhete que o vencedor pode nunca ter feito. 0 = nenhuma (ver docstring).
MAX_INEDITAS = 0
# Abaixo disto o modelo não se sustenta e a rota devolve o dono ao matcher declarativo.
MIN_TREINO = 200
# Suavização de Laplace. Baixa de propósito: features raras precisam pesar.
ALFA = 0.35
# Vida do modelo em memória. O treino é barato (~26 mil linhas em menos de 1s) e o dono rotula
# à mão o tempo todo — 5 min mantém a sugestão acompanhando o que ele acabou de corrigir.
TTL_MODELO = 300.0

_CACHE: dict[str, tuple[float, "Modelo"]] = {}


def _norm(s: Any) -> str:
    return "" if s is None else str(s).strip().lower()


def _num(v: Any) -> float:
    """Stake em número. Vem como Decimal do Postgres e como STRING BR ('250,00', '1.234,50')
    do front — `float('250,00')` estoura, então a vírgula decimal é tratada à mão."""
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.,-]", "", "" if v is None else str(v))
    if not s:
        return 0.0
    t = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return float(t)
    except ValueError:
        return 0.0


def features(casa: Any, esporte: Any, aposta: Any, stake: Any, descricao: Any) -> list[str]:
    """As features categóricas de um bilhete. Mesmo espaço de sinais do matcher declarativo
    (casa, esporte, mercado, stake) mais o nº de pernas — que separa a múltipla de 3 pernas do
    SóChutes da dupla do Arrudex, coisa que nenhum perfil declara."""
    f = ["casa=" + _norm(casa), "esp=" + _norm(esporte), "mkt=" + _norm(aposta)]
    n = _num(stake)
    if n:
        cent = round(n * 100) % 100
        inteiro = round(n)
        # Final da stake é a assinatura clássica (o "final 7" do Fatuch, o final 6 do Peixe).
        # Stake quebrada guarda os CENTAVOS: eles são o código de identidade em algumas
        # carteiras (o "(21)" do Arrudex na base do Jonathan).
        f.append("fim=" + ("q%02d" % cent if cent else str(inteiro % 10)))
        f.append("val=" + str(inteiro))
        f.append("faixa=" + str(int(math.log10(max(n, 1.0)) * 2)))
    d = descricao or ""
    # ` // ` é o único separador de seleção (MASTER_DESCRICAO §19), inclusive em mesmo-jogo.
    pernas = d.count(" // ") + 1 if d else 0
    f.append("pernas=" + (str(pernas) if pernas <= 4 else "5+"))
    return f


class Modelo:
    """Contagens por tipster × feature. Só leitura depois de treinado."""

    __slots__ = ("cls", "cnt", "tot", "vocab", "total")

    def __init__(self) -> None:
        self.cls: Counter = Counter()                       # tipster -> nº de bilhetes
        self.cnt: dict[str, Counter] = defaultdict(Counter)  # tipster -> feature -> nº
        self.tot: Counter = Counter()                       # tipster -> nº de features
        self.vocab: int = 1
        self.total: int = 0

    @property
    def treino(self) -> int:
        return self.total


def treinar(linhas: Iterable[dict]) -> Modelo:
    """Treina no histórico rotulado. `linhas` = dicts com casa/esporte/aposta/stake/descricao/
    tipster — já filtrados por dono e por procedência humana pelo chamador."""
    m = Modelo()
    vocab: set[str] = set()
    for b in linhas:
        nome = (b.get("tipster") or "").strip()
        if not nome:
            continue
        m.cls[nome] += 1
        for f in features(b.get("casa"), b.get("esporte"), b.get("aposta"), b.get("stake"), b.get("descricao")):
            m.cnt[nome][f] += 1
            m.tot[nome] += 1
            vocab.add(f)
    m.vocab = max(len(vocab), 1)
    m.total = sum(m.cls.values())
    return m


def sugerir(m: Modelo, ativos: Iterable[str], casa: Any, esporte: Any, aposta: Any,
            stake: Any, descricao: Any) -> Optional[str]:
    """O tipster mais provável, ou None quando o modelo não tem convicção.

    None não é falha — é a resposta certa para bilhete ambíguo. A coluna fica vazia e o dono
    decide, que é melhor do que um chute que ele vai ter de caçar depois."""
    if not m.total:
        return None
    feats = features(casa, esporte, aposta, stake, descricao)
    ranked: list[tuple[float, str]] = []
    for nome in ativos:
        n = m.cls.get(nome, 0)
        if not n:
            continue                      # tipster sem histórico não concorre (nem pode)
        # PRIOR UNIFORME de propósito — sem o `log(n / m.total)` do Naive-Bayes de manual.
        # A pergunta aqui não é "qual tipster é mais provável em geral", é "de quem é ESTE
        # bilhete", e o prior por volume dá vantagem estrutural ao maior da carteira: ele
        # trocava o vício de "o Arrudex leva tudo" por "o Peixe leva tudo" (108 erros num nome
        # só na base do Feca). Medido, tirar o prior levou o Gabriel de 93,8 % para 98,5 % de
        # precisão e o Jonathan de 91,8 % para 95,3 %, ao custo de ~5 pontos de cobertura.
        lp = 0.0
        cnt = m.cnt[nome]
        den = m.tot[nome] + ALFA * m.vocab
        for f in feats:
            lp += math.log((cnt[f] + ALFA) / den)
        ranked.append((lp, nome))
    if not ranked:
        return None
    ranked.sort(reverse=True)
    topo = ranked[0][1]
    # Confiança ABSOLUTA: o bilhete precisa se parecer com o que o vencedor já fez.
    if sum(1 for f in feats if m.cnt[topo][f] == 0) > MAX_INEDITAS:
        return None
    if len(ranked) == 1:
        return topo
    # Confiança RELATIVA: sem folga sobre o 2º, fica vazio.
    return topo if (ranked[0][0] - ranked[1][0]) >= MARGEM else None


def modelo_em_cache(dono: str) -> Optional[Modelo]:
    v = _CACHE.get(dono)
    if not v:
        return None
    ts, m = v
    if time.monotonic() - ts > TTL_MODELO:
        _CACHE.pop(dono, None)
        return None
    return m


def guardar_modelo(dono: str, m: Modelo) -> None:
    _CACHE[dono] = (time.monotonic(), m)


def invalidar(dono: str) -> None:
    """Chamado quando o dono rotula à mão: o próximo lote já treina com a correção dele."""
    _CACHE.pop(dono, None)

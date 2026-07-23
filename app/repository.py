import hashlib
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone

import asyncpg

from database import get_pool
from descricao_check import resumo_lote

logger = logging.getLogger("scanner")

# Colunas do TSV (índices 0–9)
_COLS = ["data", "esporte", "tipster", "casa", "parceiro",
         "aposta", "descricao", "stake", "odd", "resultado"]

_RESULTADOS_VALIDOS = {"W", "L", "V", "HW", "HL"}


def _norm_odd(v: str) -> str:
    """Normaliza odd para 2 casas decimais antes de gerar a assinatura.

    Absorve variações de precisão entre chunks paralelos: o AI pode ler
    a odd exibida no cabeçalho ("1,83") ou calcular RO/stake ("1,8331168...").
    Ambas representam a mesma aposta; sem normalização viriam assinaturas
    diferentes e o UPSERT falharia, inserindo duplicatas silenciosas.
    """
    try:
        return f"{round(float(v.replace(',', '.')), 2):.2f}"
    except (ValueError, AttributeError):
        return v


def _num_or_none(v) -> float | None:
    """Converte número ("1.234,50" / "1,81" / "75.2606") para float; None se ilegível.

    Duas convenções coexistem no histórico:
      - BR com vírgula decimal: "1.234,50" → ponto é milhar, vírgula é decimal.
      - Odd calculada com ponto decimal: "75.26066..." (múltiplas Betano, s50),
        sem vírgula nenhuma → o ponto JÁ é o separador decimal.

    Regra: se há vírgula, ela manda (ponto = milhar). Sem vírgula, o ponto é
    decimal e deve ser preservado — removê-lo transformava "75.26" em 7526...,
    estourando o P/L derivado. Confirmado no banco: 5 odds nesse formato, 0 stakes.

    Devolve None (não 0.0) quando ausente/ilegível — para os pontos onde um valor
    inválido NÃO pode virar zero em silêncio: o guard de odd em `calcular_pl` (uma
    vitória com odd ilegível não pode virar −stake) e a validação de entrada da API.
    """
    if v is None:
        return None
    s = str(v).strip().rstrip(".")  # remove reticências/ponto solto ao final
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")  # padrão BR: ponto = milhar
    # sem vírgula: o ponto (se houver) já é decimal — não mexe
    try:
        return float(s)
    except ValueError:
        return None


def _num(v) -> float:
    """`_num_or_none` com 0.0 no lugar de None — compat com os filtros `> 0` a jusante."""
    n = _num_or_none(v)
    return n if n is not None else 0.0


def calcular_pl(stake, odd, resultado) -> float | None:
    """P/L líquido da aposta (= coluna L da planilha de origem).

    Campo DERIVADO — calculado sob demanda na leitura, nunca persistido. Assim
    edições de stake/odd/resultado refletem na hora e o app continua só lendo
    o banco. Espelha o SWITCH da planilha:

        Valor (retorno bruto)        P/L = Valor − stake
        W  → stake × odd
        L  → 0
        V  → stake                   (void/cashout=stake → P/L = 0)
        HW → (stake/2) × odd + stake/2
        HL → stake/2

    A odd já vem normalizada pelas regras de extração (W: RO÷stake com boost;
    cashout≠stake: cashout÷stake), então `stake × odd` reproduz o retorno real
    sem tratamento extra. Retorna None enquanto a aposta está aberta (sem
    resultado), equivalente ao "-" da planilha.
    """
    res = (resultado or "").strip().upper()
    if res not in _RESULTADOS_VALIDOS:
        return None
    s = _num(stake)
    # A odd só entra em W e HW. Nesses, uma odd ilegível/≤0 NÃO pode virar 0.0 em
    # silêncio (transformaria uma vitória em −stake no P/L da grade e no agregado).
    # Devolve None = "não calculável" → a linha é tratada como aberta: fica fora do
    # feed e dos KPIs, e a Análise IA já sinaliza "sem odd" para o operador corrigir.
    # Para L/V/HL a odd é irrelevante ao P/L, então não bloqueia.
    o = 0.0
    if res in ("W", "HW"):
        o = _num_or_none(odd)
        if o is None or o <= 0:
            return None
    valor = {
        "W":  s * o,
        "L":  0.0,
        "V":  s,
        "HW": (s / 2) * o + (s / 2),
        "HL": s / 2,
    }[res]
    return round(valor - s, 2)


def unidade_vigente(escada, data_iso: str | None) -> float | None:
    """Valor da unidade (R$) vigente numa data, dada a ESCADA de um tipster.

    `escada` = lista de segmentos {vigente_desde: 'YYYY-MM-DD', valor: float}, cada um
    dizendo "a partir de vigente_desde, 1u vale `valor` reais" (função-degrau no tempo).
    Retorna o valor do degrau ativo em `data_iso`. Datas ANTES do primeiro degrau usam
    o primeiro valor (a 1ª stake vale da primeira aposta pra trás também — sem buraco de
    "sem stake", regra do Feca). Escada vazia ou data ilegível → None.

    NUNCA reprocessa o passado com a unidade nova: é o degrau que preserva o resultado
    real em u (o exemplo dos 135u do PLANO_TIPSTER). Mesma filosofia derivada de
    `calcular_pl` — nada em "u" é persistido; guarda-se só a escada.
    """
    if not escada or not data_iso:
        return None
    segs = sorted(escada, key=lambda s: s["vigente_desde"])
    aplicavel = segs[0]["valor"]  # clamp à esquerda: antes do 1º degrau vale o 1º valor
    for s in segs:
        if s["vigente_desde"] <= data_iso:
            aplicavel = s["valor"]
        else:
            break
    return aplicavel


def pl_em_unidades(linhas, escada, unidade_fallback: float | None = None) -> dict:
    """Resultado em UNIDADES de um conjunto de apostas de UM tipster.

    `linhas` = lista de {pl: float, data: 'YYYY-MM-DD'} já com o P/L em R$ derivado
    (calcular_pl) e a data resolvida. Para cada aposta divide o P/L pela unidade
    VIGENTE NA DATA dela (degrau) e soma:  P/L em u = Σ (pl_R$ ÷ unidade_da_data).

    Sem escada: cai no `unidade_fallback` (a stake média do cliente) e marca
    usou_fallback. Sem escada E sem fallback: a aposta entra em sem_unidade e fica de
    fora da soma. O número em u só é "de carteira honesto" quando sem_unidade == 0
    (senão a soma é parcial → a UI avisa).
    """
    total = 0.0
    usou_fallback = False
    sem_unidade = 0
    n = 0
    for ln in linhas:
        pl = ln.get("pl")
        if pl is None:
            continue
        u = unidade_vigente(escada, ln.get("data"))
        if u is None and unidade_fallback is not None:
            u, usou_fallback = unidade_fallback, True
        if u is None or u <= 0:
            sem_unidade += 1
            continue
        total += pl / u
        n += 1
    return {"u": round(total, 2), "usou_fallback": usou_fallback,
            "sem_unidade": sem_unidade, "n": n}


def sugerir_tipster(bilhete: dict, tipsters: list, *, limite: int = 3) -> list[dict]:
    """ESQUELETO da auto-atribuição (Perfil de Tipster, Fase B) — função PURA.

    Dado um `bilhete` ({casa, stake, texto}) e a lista de tipsters CADASTRADOS (cada um
    com nome, casas, stake_min, stake_max, apelidos), pontua e ranqueia os candidatos.
    NÃO está plugada na extração — é de gaveta: quando a extração passar a devolver o
    texto de marca d'água do print (`texto`), esta função vira a sugestão do tipster.

    Sinais (pesos):
      - apelido / marca d'água presente no texto → +100 (forte e específico)
      - casa do bilhete entre as casas do tipster → +10
      - stake dentro da faixa [stake_min, stake_max] → +5
    Só devolve candidatos com score > 0, do maior pro menor. O sort é estável → empate
    preserva a ordem de entrada. Comparações são case-insensitive e ignoram espaços.
    """
    def _norm(s):
        return s.strip().lower() if isinstance(s, str) else ""

    def _slug(s):
        return re.sub(r"\s+", "", _norm(s))

    casa = _slug(bilhete.get("casa"))
    texto = _norm(bilhete.get("texto"))
    stake = _num_or_none(bilhete.get("stake"))

    ranked = []
    for t in tipsters:
        score, motivos = 0, []
        apelidos = [a for a in (_norm(x) for x in (t.get("apelidos") or "").split(",")) if a]
        if texto and any(a in texto for a in apelidos):
            score += 100
            motivos.append("apelido")
        casas = {c for c in (_slug(x) for x in (t.get("casas") or "").split(",")) if c}
        if casa and casa in casas:
            score += 10
            motivos.append("casa")
        smin, smax = t.get("stake_min"), t.get("stake_max")
        if stake is not None and (smin is not None or smax is not None):
            if (smin is None or stake >= smin) and (smax is None or stake <= smax):
                score += 5
                motivos.append("stake")
        if score > 0:
            ranked.append({"nome": t.get("nome"), "score": score, "motivos": motivos})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:limite] if limite else ranked


# Parceiro no formato "Conta [Fornecedor]" → separa conta e fornecedor.
# Mesmo regex do Code.gs (getData) para o dashboard bater com a planilha.
_PARCEIRO_RE = re.compile(r"^(.+?)\s*\[(.+?)\]$")


def _data_iso(v) -> str | None:
    """Data do banco (DD/MM/YYYY) → ISO (YYYY-MM-DD), formato que o dashboard espera.

    Passa direto se já estiver em ISO. Devolve None se ilegível (a linha é então
    descartada do feed, espelhando o filtro de data do Code.gs).
    """
    s = (v or "").strip() if isinstance(v, str) else (str(v).strip() if v else "")
    if not s:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{int(mth):02d}-{int(d):02d}"
    return None


# ── Validação de entrada (fronteira da API) ───────────────────────────────────
# Um valor financeiro inválido nunca deve entrar no banco e contaminar o P/L
# derivado (odd×stake). Estas checagens são a barreira usada pelos validators
# Pydantic das rotas de escrita (PATCH/manual). Vazio = permitido (campo opcional
# ou "limpar"); quando preenchido, tem de ser válido.

def resultado_valido(v) -> bool:
    """True se `v` é vazio (aposta aberta) ou um código de resultado conhecido."""
    s = (str(v).strip().upper() if v is not None else "")
    return s == "" or s in _RESULTADOS_VALIDOS


def estado_extracao(resultado, odd) -> str:
    """Deriva `extraction_state` de (resultado, odd). 'resolvida' EXIGE resultado
    canônico E odd utilizável (> 0). Sem odd (linha colapsada / ilegível) → 'aberta'
    (aguardando informação): a aposta não polui o feed nem duplica em silêncio até o
    operador completar a odd. Decisão do Feca (sessão 133): resultado sem odd não é
    'resolvida limpa'. Casa com o guard de odd de `calcular_pl` (vitória sem odd = P/L
    não-calculável), evitando linha 'resolvida' que some do feed."""
    res = (resultado or "").strip().upper()
    if res not in _RESULTADOS_VALIDOS:
        return "aberta"
    if (_num_or_none(odd) or 0) <= 0:
        return "aberta"
    return "resolvida"


def valor_monetario_valido(v) -> bool:
    """True se `v` é vazio ou um número > 0 (stake/odd). Rejeita lixo e ≤ 0."""
    s = (str(v).strip() if v is not None else "")
    if not s:
        return True
    n = _num_or_none(s)
    return n is not None and n > 0


def data_valida(v) -> bool:
    """True se `v` é vazio ou uma data reconhecível (DD/MM/YYYY ou ISO)."""
    s = (str(v).strip() if v is not None else "")
    return not s or _data_iso(s) is not None


def parse_tsv(tsv: str) -> list[dict]:
    """Converte bloco TSV em lista de dicts. Ignora linhas vazias e cabeçalho."""
    rows = []
    for line in tsv.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 10:
            continue
        row = dict(zip(_COLS, parts[:10]))
        # Ignora linha de cabeçalho se presente
        if row["data"].lower() in ("data", "date", "código"):
            continue
        # 11ª coluna: código do bilhete (opcional)
        codigo = parts[10].strip() if len(parts) > 10 else ""
        if codigo:
            row["codigo_bilhete"] = codigo
        rows.append(row)
    return rows


# ── Correção determinística do ID contra o texto-fonte ────────────────────────
# O ID do bilhete é a IDENTIDADE (dedup por ID; regra do CLAUDE.md). Porém a IA
# NÃO reproduz um número de 18–19 dígitos com fidelidade: transpõe/inventa dígitos
# ao escrever a resposta, DIFERENTE a cada extração — mesmo lendo do texto colado.
# Resultado: o mesmo bilhete re-extraído recebe IDs diferentes → a dedup por ID acha
# que é novo → duplicata (ver STATUS sessão 100, conta KingPanda·Ellen 178→83).
#
# Fix (respeita "o ID é rei"): quando há TEXTO colado, os IDs verdadeiros estão nele
# literalmente. Esta função NÃO deduplica por conteúdo — só garante que o ID gravado
# é um ID que EXISTE no texto-fonte. Nunca inventa: se não dá para recuperar com
# segurança, deixa o ID como veio e conta como "incerto".
_ID_TEXTO_RE = re.compile(r"ID:\s*(\d{12,25})")
# Superbet: o código vem exato do DOM no marcador [Código: XXXX-XXXXXX] (alfanumérico,
# ~11 chars). Só entra no conjunto de IDs reais para VALIDAR (claim exato); o gate
# _ID_MINLEN=16 abaixo bloqueia naturalmente o snap por edit-distance nesses códigos
# curtos — logo, código Superbet errado vira "incerto", nunca é corrompido por snap.
_ID_SUPERBET_RE = re.compile(r"\[Código:\s*([0-9A-Za-z]{3,6}-[0-9A-Za-z]{4,8})\]")
# BETesporte: mesmo marcador [Código: ...], mas o id vem da API como número puro
# (ex.: 189070937). Também só valida por claim exato (o gate _ID_MINLEN=16 barra o snap
# por edit-distance nesses ~9 dígitos → código errado vira "incerto", nunca é corrompido).
_ID_BETESPORTE_RE = re.compile(r"\[Código:\s*(\d{6,12})\]")
_ID_MINLEN = 16    # ID muito curto = a IA truncou demais → irrecuperável, não arrisca
_ID_MARGIN = 3     # o ID real mais próximo tem de ganhar do 2º por ≥3 (senão ambíguo)
_ID_MAXDIST = 8    # acima disso a leitura destruiu o número → não confia no snap
# Gates calibrados nas 108 cópias garbled reais da conta KingPanda·Ellen:
# corrigem 81, ZERO corrupção, 27 ficam "incerto" (IDs truncados p/ 12–15 dígitos).


def _edit_distance(a: str, b: str) -> int:
    """Distância de Levenshtein (sem libs). Números curtos → barato."""
    if a == b:
        return 0
    n = len(b)
    dp = list(range(n + 1))
    for i, ca in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, cb in enumerate(b, 1):
            prev, dp[j] = dp[j], min(dp[j] + 1, dp[j - 1] + 1, prev + (ca != cb))
    return dp[n]


def codigos_do_texto(texto: str | None) -> list[str]:
    """Códigos de bilhete presentes no texto-fonte, na ORDEM em que aparecem, sem repetir.

    É a lista determinística do que a extração TEM de devolver: cada `[Código: …]` /
    `ID: …` é uma fronteira de bilhete injetada pelo robô a partir do DOM/API — não é
    leitura de IA. Serve de gabarito para `conferir_cobertura`.

    Casas sem esse marcador (Bet365, prints) devolvem lista vazia → quem chama trata
    como "não dá para conferir" e segue o comportamento antigo.
    """
    if not texto:
        return []
    achados: list[tuple[int, str]] = []
    for rx in (_ID_TEXTO_RE, _ID_SUPERBET_RE, _ID_BETESPORTE_RE):
        achados.extend((m.start(), m.group(1).strip()) for m in rx.finditer(texto))
    achados.sort(key=lambda p: p[0])
    vistos: set[str] = set()
    ordem: list[str] = []
    for _, cod in achados:
        if cod and cod not in vistos:
            vistos.add(cod)
            ordem.append(cod)
    return ordem


def codigos_do_tsv(tsv: str) -> set[str]:
    """Códigos presentes na 11ª coluna das linhas-bilhete do TSV."""
    out: set[str] = set()
    for line in (tsv or "").split("\n"):
        if line.startswith("Data\t"):
            continue          # cabeçalho: a 11ª coluna dele é o rótulo "Código"
        parts = line.split("\t")
        if len(parts) >= 11 and parts[10].strip():
            out.add(parts[10].strip())
    return out


def conferir_cobertura(tsv: str, texto: str | None) -> dict:
    """Bilhetes que estavam no texto-fonte e NÃO voltaram no TSV.

    Motivo (sessão 179): `_extract_tsv_rows` devolve [] quando um chunk responde sem o
    bloco ```tsv — o pedaço inteiro some SEM erro, e `chunks_falhos` (que só conta
    exceção) não acusa. Numa extração real da Superbet, 39 dos 61 bilhetes evaporaram
    e a tela mostrou "✓ 22 novo(s)". Como o gabarito de códigos é determinístico
    (vem do DOM), a perda é detectável sem IA nenhuma.

    Retorna {"esperados": n, "faltantes": [códigos na ordem do texto]}.
    esperados == 0 → casa sem marcador de código: não dá para conferir (no-op).
    """
    esperados = codigos_do_texto(texto)
    if not esperados:
        return {"esperados": 0, "faltantes": []}
    vistos = codigos_do_tsv(tsv)
    return {"esperados": len(esperados),
            "faltantes": [c for c in esperados if c not in vistos]}


def corrigir_codigos_tsv(tsv: str, texto: str | None) -> tuple[str, dict]:
    """Corrige a 11ª coluna (código do bilhete) de cada linha TSV para o ID REAL
    presente no `texto` colado. Cirúrgico e conservador:

      - ID que já bate exatamente com um ID do texto → mantém (reivindica o slot).
      - ID garbled recuperável (gates len/margem/distância + alvo livre) → snap para
        o ID verdadeiro mais próximo.
      - Senão → mantém o que a IA escreveu e conta como "incerto" (nunca inventa).

    Só toca linhas que são bilhete (≥11 colunas TAB e a 11ª preenchida); notas e
    texto livre passam intactos. Sem `texto` ou sem `ID:` no texto → no-op.
    Retorna (tsv_corrigido, {"corrigidos": n, "incertos": m}).
    """
    if not texto:
        return tsv, {"corrigidos": 0, "incertos": 0}
    # Betano (ID: numérico) + Superbet ([Código: alfanumérico]). Numa extração o texto
    # é de uma casa só, então os dois nunca se misturam no mesmo colar.
    reais = _ID_TEXTO_RE.findall(texto) + _ID_SUPERBET_RE.findall(texto) + _ID_BETESPORTE_RE.findall(texto)
    if not reais:
        return tsv, {"corrigidos": 0, "incertos": 0}
    reais_set = set(reais)

    linhas = tsv.split("\n")
    alvos: list[tuple[int, list[str]]] = []   # (índice da linha, colunas) das linhas-bilhete
    for i, line in enumerate(linhas):
        parts = line.split("\t")
        if len(parts) >= 11 and parts[10].strip():
            alvos.append((i, parts))

    claimed: set[str] = set()
    # 1) exatos reivindicam seu ID primeiro (protege contra um garbled roubar um ID
    #    que já é de outra linha por leitura exata).
    pendentes: list[tuple[int, list[str]]] = []
    for i, parts in alvos:
        cod = parts[10].strip()
        if cod in reais_set and cod not in claimed:
            claimed.add(cod)
        else:
            pendentes.append((i, parts))

    corrigidos = incertos = 0
    for i, parts in pendentes:
        cod = parts[10].strip()
        livres = [rid for rid in reais_set if rid not in claimed]
        if not livres:
            incertos += 1
            continue
        dists = sorted((_edit_distance(cod, rid), rid) for rid in livres)
        best_d, best_id = dists[0]
        second_d = dists[1][0] if len(dists) > 1 else 999
        if len(cod) >= _ID_MINLEN and (second_d - best_d) >= _ID_MARGIN and best_d <= _ID_MAXDIST:
            parts[10] = best_id
            linhas[i] = "\t".join(parts)
            claimed.add(best_id)
            corrigidos += 1
        else:
            incertos += 1

    return "\n".join(linhas), {"corrigidos": corrigidos, "incertos": incertos}


def validar_linhas(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separa as linhas com campo financeiro MALFORMADO (presente e ilegível) das
    salváveis, para o `/salvar` gravar as boas e devolver as ruins à UI.

    Rejeita apenas o que é *presente e inválido*: stake/odd que não são número > 0,
    resultado fora de {W,L,V,HW,HL}, ou data ilegível. NÃO rejeita linha só por estar
    INCOMPLETA (campo vazio) — stake/odd/resultado/data vazios são aposta aberta ou
    leitura parcial da IA, sinalizados como aviso (analisar_extracao), não erro.

    Retorna (validas, rejeitadas). Cada rejeitada = {linha, campo, valor, erro, resumo}
    (linha = posição 1-based na lista parseada; resumo identifica o bilhete p/ o operador).
    """
    validas: list[dict] = []
    rejeitadas: list[dict] = []
    for i, row in enumerate(rows, 1):
        problema = None
        for campo in ("stake", "odd"):
            if not valor_monetario_valido(row.get(campo)):
                problema = (campo, row.get(campo), f"{campo} inválido — não é um número maior que zero")
                break
        if problema is None and not resultado_valido(row.get("resultado")):
            problema = ("resultado", row.get("resultado"), "resultado deve ser W, L, V, HW, HL ou vazio")
        if problema is None and not data_valida(row.get("data")):
            problema = ("data", row.get("data"), "data inválida — use DD/MM/AAAA")
        if problema is None:
            validas.append(row)
            continue
        campo, valor, msg = problema
        resumo = " · ".join(
            x for x in [row.get("data"), row.get("aposta"), row.get("descricao")] if x
        )[:80]
        rejeitadas.append({"linha": i, "campo": campo, "valor": valor, "erro": msg, "resumo": resumo})
    return validas, rejeitadas


# ── Análise de confiança da extração (heurística explicável) ──────────────────
# Score de confiança = % médio de campos-chave preenchidos/válidos por bilhete.
# NÃO mexe na IA: lê só as linhas já extraídas. Penaliza categoria incerta
# (`Outros ⚠️`/sinal ⚠) e odd/stake ausentes. `resultado` vazio é bilhete ABERTO
# (esperado) → não penaliza; só conta quando preenchido. Notas = SÓ problemas reais
# (decisão do Feca, sessão 81): nada de parede de notas verdes — quando está tudo
# limpo, devolve uma única nota "ok". Anomalia de stake foi descartada de propósito
# (tipster sai vazio na extração e stakes variam por tipster → média por conta seria
# ruído). A nota livre da IA é fundida no FRONTEND (vem do /extrair, não do /salvar).
def _campo_preenchido(v) -> bool:
    return bool((v or "").strip())


def _aposta_incerta(aposta: str) -> bool:
    a = (aposta or "").strip().lower()
    return ("⚠" in aposta) or a.startswith("outros")


def analisar_extracao(rows: list[dict], duplicatas: dict | None = None) -> dict:
    """Resumo do rail "Análise IA": {confianca, itens, duplicadas, notas}.

    confianca: 0..1 (ou None se lote vazio). notas: lista de
    {tipo: 'info'|'warn'|'ok', n, titulo, texto} — só problemas reais.
    """
    n = len(rows)
    if not n:
        return {"confianca": None, "itens": 0, "duplicadas": 0, "notas": []}

    total_aplic = 0          # campos aplicáveis somados em todos os bilhetes
    total_ok = 0             # campos preenchidos/válidos
    sem_odd = sem_stake = incertos = 0

    for r in rows:
        aposta = (r.get("aposta") or "").strip()
        incerta = _aposta_incerta(aposta)
        odd_ok = _num(r.get("odd")) > 0
        stake_ok = _num(r.get("stake")) > 0
        campos = [
            _campo_preenchido(r.get("data")),
            _campo_preenchido(r.get("esporte")),
            _campo_preenchido(aposta) and not incerta,
            odd_ok,
            stake_ok,
        ]
        # resultado: só é aplicável quando preenchido (bilhete resolvido); vazio =
        # aposta aberta, esperado, não entra no denominador.
        resultado = (r.get("resultado") or "").strip().upper()
        if resultado:
            campos.append(resultado in _RESULTADOS_VALIDOS)
        total_aplic += len(campos)
        total_ok += sum(1 for c in campos if c)
        if not odd_ok:
            sem_odd += 1
        if not stake_ok:
            sem_stake += 1
        if incerta:
            incertos += 1

    confianca = (total_ok / total_aplic) if total_aplic else None

    # Cópias extras (occ>1) — a 1ª ocorrência não é "a duplicata".
    dups = sum(1 for occ_total in (duplicatas or {}).values()
               if isinstance(occ_total, (list, tuple)) and occ_total and occ_total[0] > 1)

    notas = []
    if incertos:
        notas.append({"tipo": "warn", "n": "MERCADO",
                      "titulo": f"{incertos} aposta(s) sem categoria definida",
                      "texto": "Classificadas como <b>Outros ⚠️</b> — confira e ajuste a categoria na grade."})
    if sem_odd:
        notas.append({"tipo": "warn", "n": "ODD",
                      "titulo": f"{sem_odd} bilhete(s) sem odd",
                      "texto": "Odd ausente ou ilegível no print — preencha na grade antes de exportar."})
    if sem_stake:
        notas.append({"tipo": "warn", "n": "STAKE",
                      "titulo": f"{sem_stake} bilhete(s) sem stake",
                      "texto": "Stake ausente — confira o valor apostado no bilhete."})
    if dups:
        notas.append({"tipo": "info", "n": "DUPLICATA",
                      "titulo": f"{dups} possível(is) duplicata(s) no lote",
                      "texto": "Bilhetes idênticos sem ID visível — se vierem de imagens diferentes, confira e delete se necessário."})

    # Conformidade da descrição (checador determinístico, MASTER_DESCRICAO). Warn-only:
    # nunca bloqueia salvar — só sinaliza p/ o operador revisar/re-extrair. É a rede
    # "indo pra frente" contra descrição colapsada (que distorce a dedup).
    desc = resumo_lote(rows)
    desc_total = desc["com_erro"] + desc["com_aviso"]
    if desc_total:
        partes = []
        if desc["com_erro"]:
            partes.append(f"{desc['com_erro']} fora do padrão (separador de confronto, Over/Under em português ou conteúdo proibido)")
        if desc["com_aviso"]:
            partes.append(f"{desc['com_aviso']} de marcador/props <b>sem confronto</b>")
        notas.append({"tipo": "warn", "n": "DESCRIÇÃO",
                      "titulo": f"{desc_total} bilhete(s) com descrição a revisar",
                      "texto": "Confira na grade: " + "; ".join(partes) +
                               ". Descrição incompleta/colapsada distorce a deduplicação — o ideal é re-extrair."})

    if not notas:
        notas.append({"tipo": "ok", "n": "OK",
                      "titulo": "Extração limpa",
                      "texto": f"{n} item(ns) sem pendências — datas, odds, stakes e categorias conferem."})

    return {"confianca": confianca, "itens": n, "duplicadas": dups, "notas": notas}


def _assinatura(row: dict, _counter: int = 1) -> str:
    codigo = row.get("codigo_bilhete", "").strip()
    if codigo:
        raw = "|".join(["ID", row.get("casa", ""), row.get("parceiro", ""), codigo])
    else:
        # Regra do Feca (casa SEM ID): duplicata SÓ quando stake + odd + descrição batem
        # os TRÊS. Qualquer divergência = bilhetes distintos. O `stake` é obrigatório aqui:
        # sem ele, dois bilhetes reais que só diferem no valor apostado (comum — o mesmo
        # mercado apostado com stakes diferentes) colidiam na assinatura e um sobrescrevia
        # o outro (perda silenciosa). `data`/`aposta` seguem no hash como salvaguarda extra
        # (só tornam a chave MAIS restritiva → nunca fundem distintos).
        raw = "|".join([
            row.get("casa", ""), row.get("parceiro", ""),
            row.get("data", ""), row.get("aposta", ""), row.get("descricao", ""),
            row.get("stake", ""), _norm_odd(row.get("odd", "")),
        ])
        if _counter > 1:
            raw += f"|{_counter}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


# Colunas que entram no hash de `_assinatura`. Editar qualquer uma delas invalida a
# assinatura gravada — ver `_assinatura_pos_edicao`.
_SIG_COLS = frozenset({"casa", "parceiro", "data", "aposta", "descricao", "stake", "odd"})


async def _assinatura_pos_edicao(conn, antes, safe: dict, dono: str,
                                 bilhete_id: int) -> str | None:
    """Assinatura que o bilhete deve ter DEPOIS da edição. None = não mexer.

    `atualizar_bilhete` edita colunas que entram no hash (`aposta`, `descricao`, `stake`,
    `odd`, `data`, `casa`, `parceiro`). Sem recalcular, a assinatura fica velha e a
    re-extração do mesmo bilhete gera uma assinatura nova que NÃO colide com ela → o
    UPSERT não dedupa e duplica (mesma família do gap de re-extração sem código).

    Colisão: se o conteúdo final bater com OUTRA linha da mesma conta, escala o `_counter`
    igual ao `upsert_bilhetes` já faz para bilhetes distintos de conteúdo idêntico (regra
    do Feca: sem ID, duplicata só quando stake+odd+descrição batem os três).

    Bilhete COM código não aceita counter — o hash por ID ignora `_counter` — então numa
    colisão devolve None e mantém a assinatura atual (o comportamento de hoje; nunca pior).
    """
    final = {c: (safe.get(c, antes[c]) or "") for c in _SIG_COLS}
    final["codigo_bilhete"] = antes["codigo_bilhete"] or ""
    if _assinatura(final) == antes["assinatura"]:
        return None  # conteúdo do hash não mudou
    tem_codigo = bool(final["codigo_bilhete"].strip())
    for cnt in range(1, 51):
        sig = _assinatura(final, _counter=cnt)
        livre = await conn.fetchval(
            """SELECT NOT EXISTS (
                   SELECT 1 FROM bilhetes
                   WHERE dono = $1 AND casa = $2 AND parceiro = $3
                     AND assinatura = $4 AND id <> $5)""",
            dono, final["casa"], final["parceiro"], sig, bilhete_id)
        if livre:
            # sig == a atual acontece quando a linha já usava counter e o slot dela
            # continua sendo o certo: nada a gravar.
            return None if sig == antes["assinatura"] else sig
        if tem_codigo:
            break  # escalar não sai do lugar: o hash por código ignora `_counter`
    logger.warning(
        "assinatura pós-edição colide para o bilhete %s (dono=%s); mantida a atual — "
        "uma re-extração deste bilhete pode duplicar", bilhete_id, dono)
    return None


async def upsert_bilhetes(
    rows: list[dict], dono: str, confianca: float | None = None,
    origem: str = "extracao", criado_base: datetime | None = None,
    coproprietarios: list[str] | None = None,
) -> tuple[int, int, list[int], list[str], dict]:
    """Retorna (inseridos, atualizados, ids, alertas, duplicatas).

    duplicatas: {str(db_id): [occurrence, total]} — bets suspeitas de duplicidade no lote.
    """
    pool = await get_pool()
    ids: list[int] = []
    alertas: list[str] = []
    inseridos = 0
    atualizados = 0

    # Pré-conta ocorrências de cada base_sig para bets sem ID
    base_sig_totals: dict[str, int] = {}
    for row in rows:
        if not row.get("codigo_bilhete", "").strip():
            bs = _assinatura(row)
            base_sig_totals[bs] = base_sig_totals.get(bs, 0) + 1

    batch_sig_counters: dict[str, int] = {}     # base_sig → contagem atual no lote
    sig_to_first_row: dict[str, int] = {}       # base_sig → índice da 1ª ocorrência
    dup_row_info: dict[int, tuple[int, int]] = {}   # row_idx → (occurrence, total)
    id_per_row: list[int | None] = []           # db_id por posição de row

    async with pool.acquire() as conn:
        # Rede de segurança (camada 2): índice dos bilhetes que JÁ estão no banco COM
        # código, por (casa, parceiro, stake, odd). Serve para avisar quando uma linha
        # que chega SEM código bater com um bilhete já salvo COM código nesta conta —
        # sinal de re-extração que perdeu o ID. A dedup por código não pega (a linha
        # nova não tem código) e a assinatura de conteúdo inclui `data`, que muda ao
        # reprocessar em outro dia. Aqui NÃO apaga nem mescla: só sinaliza (`alertas`).
        coded_por_conta: dict[tuple[str, str, float, str], list[str]] = {}
        contas_sem_cod = {
            (row.get("casa", ""), row.get("parceiro", ""))
            for row in rows if not row.get("codigo_bilhete", "").strip()
        }
        for casa_k, parc_k in contas_sem_cod:
            recs = await conn.fetch(
                """SELECT codigo_bilhete, stake, odd FROM bilhetes
                   WHERE dono = $1 AND casa = $2 AND parceiro = $3
                     AND codigo_bilhete IS NOT NULL AND btrim(codigo_bilhete) <> ''""",
                dono, casa_k, parc_k,
            )
            for rr in recs:
                st = _num(rr["stake"])
                if st <= 0:
                    continue
                k = (casa_k, parc_k, round(st, 2), _norm_odd(rr["odd"] or ""))
                coded_por_conta.setdefault(k, []).append(rr["codigo_bilhete"])

        # Dedup CRUZADA (linhagem supervisor↔operadores): assinaturas que JÁ existem
        # sob um co-proprietário para as contas deste lote. Contas físicas são
        # compartilhadas dentro da linhagem — um supervisor pode repassar ao operador
        # uma conta que usou (ex.: Feca arquiva e o Lava assume). Um bilhete cujo
        # `sig` bate aqui é a MESMA aposta física recapturada do histórico
        # compartilhado; inserir sob o outro dono a contaria duas vezes no painel do
        # supervisor. Auto-escopada: só colide quando casa+parceiro batem EXATAMENTE
        # entre donos (conta genuinamente compartilhada) — contas próprias do operador
        # têm parceiro diferente e nunca entram aqui. Casas com código (Betano) tornam
        # a assinatura (ID|casa|parceiro|codigo) à prova de erro. Inclui arquivados
        # (as antigas do supervisor costumam estar archived=TRUE).
        sig_de_coproprietario: set[str] = set()
        if coproprietarios:
            contas = {(row.get("casa", ""), row.get("parceiro", "")) for row in rows}
            for casa_k, parc_k in contas:
                recs = await conn.fetch(
                    """SELECT assinatura FROM bilhetes
                       WHERE dono = ANY($1) AND casa = $2 AND parceiro = $3""",
                    coproprietarios, casa_k, parc_k,
                )
                for rr in recs:
                    sig_de_coproprietario.add(rr["assinatura"])

        for i, row in enumerate(rows):
            codigo = row.get("codigo_bilhete", "").strip()

            if not codigo:
                base_sig = _assinatura(row)
                total = base_sig_totals.get(base_sig, 1)
                cnt = batch_sig_counters.get(base_sig, 0) + 1
                batch_sig_counters[base_sig] = cnt
                sig = _assinatura(row, _counter=cnt)

                if total > 1:
                    dup_row_info[i] = (cnt, total)
                    if cnt == 1:
                        sig_to_first_row[base_sig] = i
                    else:
                        primeiro = sig_to_first_row[base_sig] + 1  # 1-indexado
                        alertas.append(
                            f"Bilhete {i + 1} idêntico ao bilhete {primeiro} (sem ID visível) — "
                            "se da mesma imagem são apostas distintas (ok); "
                            "se de imagens diferentes pode ser duplicata de scroll — "
                            "verifique e delete se necessário."
                        )

                # Camada 2: a linha chega SEM código mas bate stake+odd com um bilhete
                # já salvo COM código nesta conta? Provável re-extração que perdeu o ID
                # (a dedup por código não pega). Só avisa — não apaga nem mescla.
                st = _num(row.get("stake"))
                if st > 0:
                    k = (row.get("casa", ""), row.get("parceiro", ""),
                         round(st, 2), _norm_odd(row.get("odd") or ""))
                    coincid = coded_por_conta.get(k)
                    if coincid:
                        alertas.append(
                            f"Bilhete {i + 1} sem ID visível bate stake+odd com um "
                            f"bilhete já salvo COM ID (código {coincid[0]}) — provável "
                            "re-extração que perdeu o ID. Confira e delete este se for repetido."
                        )
            else:
                sig = _assinatura(row)

            # Guard da dedup cruzada: se esta assinatura já pertence a um co-proprietário
            # da conta compartilhada, é a MESMA aposta física já planilhada pelo outro
            # dono (histórico anterior ao repasse). Não insere sob este dono — evita a
            # dupla contagem no painel do supervisor. Só sinaliza; não apaga nada.
            if sig in sig_de_coproprietario:
                alertas.append(
                    f"Bilhete {i + 1} já pertence a outro operador desta conta "
                    f"({row.get('casa', '')} / {row.get('parceiro', '')}) — "
                    "histórico anterior ao repasse, ignorado."
                )
                id_per_row.append(None)
                continue

            if codigo:
                # Migração A: normaliza assinatura de linha existente com mesmo código.
                # O guard NOT EXISTS impede mover a linha para uma assinatura que JÁ
                # existe (dono,casa,parceiro,assinatura) — isso violaria a unique e,
                # por estar FORA do try/except do INSERT, abortaria o lote inteiro
                # ("0 exportadas"). Se o destino já existe, a linha antiga é uma
                # duplicata inofensiva: pula a consolidação e deixa o ON CONFLICT
                # abaixo atualizar a linha canônica.
                await conn.execute(
                    """UPDATE bilhetes SET assinatura = $1
                       WHERE casa = $2 AND parceiro = $3
                         AND codigo_bilhete = $4 AND assinatura != $1
                         AND dono = $5
                         AND NOT EXISTS (
                             SELECT 1 FROM bilhetes b2
                             WHERE b2.dono = $5 AND b2.casa = $2
                               AND b2.parceiro = $3 AND b2.assinatura = $1
                         )""",
                    sig, row.get("casa", ""), row.get("parceiro", ""), codigo, dono,
                )
                # Migração B: adota linha sem código que bate em data+aposta+stake+odd
                # (bets importadas via imagem antes do suporte a XLS). Mesmo guard
                # NOT EXISTS da Migração A: só adota se a assinatura de destino estiver
                # livre, evitando colisão não tratada que mataria o lote.
                await conn.execute(
                    """
                    WITH candidate AS (
                        SELECT id FROM bilhetes
                        WHERE casa = $2 AND parceiro = $3
                          AND codigo_bilhete IS NULL
                          AND data = $4 AND aposta = $5 AND stake = $6 AND odd = $7
                          AND dono = $9
                        LIMIT 1
                    )
                    UPDATE bilhetes SET assinatura = $1, codigo_bilhete = $8
                    FROM candidate
                    WHERE bilhetes.id = candidate.id AND bilhetes.assinatura != $1
                      AND NOT EXISTS (
                          SELECT 1 FROM bilhetes b2
                          WHERE b2.dono = $9 AND b2.casa = $2
                            AND b2.parceiro = $3 AND b2.assinatura = $1
                      )
                    """,
                    sig, row.get("casa", ""), row.get("parceiro", ""),
                    row.get("data", ""), row.get("aposta", ""),
                    row.get("stake", ""), row.get("odd", ""), codigo, dono,
                )

            # .upper() canoniza o código (W/L/V/HW/HL). Sem isso, um 'v'/'w' minúsculo
            # (extração/edição) não bate em _RESULTADOS_VALIDOS e o bilhete fica 'aberta'
            # — parece resolvido (badge/PL já upperam) mas conta como "aguardando resultado".
            resultado = row.get("resultado", "").strip().upper() or None
            # Sem odd (linha colapsada) → 'aberta': não entra no feed nem duplica em
            # silêncio até o operador completar a odd (ver estado_extracao).
            extraction_state = estado_extracao(resultado, row.get("odd"))
            # criado_em ancorado na hora de ENVIO (criado_base), com +i µs por linha para
            # manter a ordem interna do lote estritamente crescente — espelha o NOW()-por-
            # linha antigo. None → COALESCE cai no DEFAULT NOW() (sync/import/extensão).
            criado_em_val = criado_base + timedelta(microseconds=i) if criado_base else None
            try:
                rec = await conn.fetchrow(
                    """
                    INSERT INTO bilhetes
                        (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte, tipster,
                         aposta, descricao, stake, odd, resultado,
                         extraction_state, confianca, stake_usd, origem, criado_em)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,
                            COALESCE($18::timestamptz, NOW()))
                    ON CONFLICT (dono, casa, parceiro, assinatura) DO UPDATE SET
                        -- preserva o tipster existente quando o lote vier sem tipster
                        -- (extração/sync sempre mandam ''); só sobrescreve com valor real
                        tipster          = COALESCE(NULLIF(EXCLUDED.tipster, ''), bilhetes.tipster),
                        codigo_bilhete   = COALESCE(bilhetes.codigo_bilhete, EXCLUDED.codigo_bilhete),
                        -- Aposta ABERTA (Betano etc.) sobe sem resultado e vira 'aberta'.
                        -- Quando FECHA, a re-extração (mesmo BetId → mesma assinatura) traz o
                        -- resultado e faz UPSERT: atualiza, nunca duplica. DUAS blindagens:
                        --  1) resultado VAZIO nunca sobrescreve um resultado já gravado
                        --     (uma re-leitura tardia da aba "Em aberto" não rebaixa a linha
                        --      já resolvida de volta p/ 'aberta').
                        --  2) só quando a linha ESTAVA 'aberta' e agora resolve é que os
                        --     campos financeiros (odd/data/stake) são refrescados com a
                        --     verdade da liquidação — vitória com boost passa a odd = Retorno
                        --     ÷ Stake, etc. Linha já resolvida fica intacta. A assinatura por
                        --     código não usa esses campos → o match não quebra.
                        resultado        = COALESCE(NULLIF(EXCLUDED.resultado, ''), bilhetes.resultado),
                        extraction_state = CASE
                            WHEN NULLIF(EXCLUDED.resultado, '') IS NULL
                                 AND NULLIF(bilhetes.resultado, '') IS NOT NULL
                            THEN bilhetes.extraction_state
                            ELSE EXCLUDED.extraction_state END,
                        odd = CASE WHEN bilhetes.extraction_state = 'aberta'
                                   THEN COALESCE(NULLIF(EXCLUDED.odd, ''), bilhetes.odd)
                                   ELSE bilhetes.odd END,
                        data = CASE WHEN bilhetes.extraction_state = 'aberta'
                                    THEN COALESCE(NULLIF(EXCLUDED.data, ''), bilhetes.data)
                                    ELSE bilhetes.data END,
                        stake = CASE WHEN bilhetes.extraction_state = 'aberta'
                                     THEN COALESCE(NULLIF(EXCLUDED.stake, ''), bilhetes.stake)
                                     ELSE bilhetes.stake END,
                        -- backfill do USD em re-sync; nunca apaga um valor já gravado
                        stake_usd        = COALESCE(EXCLUDED.stake_usd, bilhetes.stake_usd),
                        atualizado_em    = NOW()
                    RETURNING id, (xmax = 0) AS was_inserted
                    """,
                    dono, row.get("casa", ""), row.get("parceiro", ""), sig,
                    codigo or None,
                    row.get("data"), row.get("esporte"), row.get("tipster"),
                    row.get("aposta"), row.get("descricao"),
                    row.get("stake"), row.get("odd"), resultado,
                    extraction_state, confianca, row.get("stake_usd"), origem,
                    criado_em_val,
                )
            except asyncpg.UniqueViolationError:
                # Defesa: o ON CONFLICT acima absorve a colisão na quase totalidade dos
                # casos, mas uma corrida entre dois /salvar do mesmo lote (ex.: reenvio
                # durante a extração lenta) pode deixar escapar um unique_violation. Sem
                # este fallback, UMA linha repetida abortaria o lote inteiro ("0 exportadas").
                # Aqui aplicamos manualmente o mesmo UPDATE que o ON CONFLICT faria e
                # seguimos o loop, contando a linha como atualizada.
                rec = await conn.fetchrow(
                    """
                    UPDATE bilhetes SET
                        tipster          = COALESCE(NULLIF($5, ''), tipster),
                        codigo_bilhete   = COALESCE(codigo_bilhete, $6),
                        -- mesmas 2 blindagens do ON CONFLICT acima (aberta→resolvida):
                        resultado        = COALESCE(NULLIF($7, ''), resultado),
                        extraction_state = CASE
                            WHEN NULLIF($7, '') IS NULL AND NULLIF(resultado, '') IS NOT NULL
                            THEN extraction_state ELSE $8 END,
                        odd   = CASE WHEN extraction_state = 'aberta'
                                     THEN COALESCE(NULLIF($9,  ''), odd)   ELSE odd   END,
                        data  = CASE WHEN extraction_state = 'aberta'
                                     THEN COALESCE(NULLIF($10, ''), data)  ELSE data  END,
                        stake = CASE WHEN extraction_state = 'aberta'
                                     THEN COALESCE(NULLIF($11, ''), stake) ELSE stake END,
                        atualizado_em    = NOW()
                    WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND assinatura = $4
                    RETURNING id, FALSE AS was_inserted
                    """,
                    dono, row.get("casa", ""), row.get("parceiro", ""), sig,
                    row.get("tipster"), codigo or None, resultado, extraction_state,
                    row.get("odd"), row.get("data"), row.get("stake"),
                )
            if rec:
                db_id = rec["id"]
                ids.append(db_id)
                id_per_row.append(db_id)
                if rec["was_inserted"]:
                    inseridos += 1
                else:
                    atualizados += 1
            else:
                id_per_row.append(None)

    # Monta mapa duplicatas: str(db_id) → [occurrence, total]
    duplicatas: dict[str, list[int]] = {}
    for row_idx, (occ, total) in dup_row_info.items():
        db_id = id_per_row[row_idx] if row_idx < len(id_per_row) else None
        if db_id is not None:
            duplicatas[str(db_id)] = [occ, total]

    return inseridos, atualizados, ids, alertas, duplicatas


# Colunas capturadas na exclusão e re-inseridas na restauração (undo). Preservam a
# identidade exata do bilhete — sobretudo `assinatura`, para não re-rodar a dedup.
_COLS_RESTAURAR = (
    "casa", "parceiro", "assinatura", "codigo_bilhete", "data", "esporte", "tipster",
    "aposta", "descricao", "stake", "odd", "resultado", "extraction_state",
    "confianca", "stake_usd", "origem",
)


async def deletar_bilhetes(ids: list[int], dono: str) -> list[dict]:
    """Apaga os bilhetes e RETORNA as linhas apagadas (para o undo por toast).

    Antes devolvia só a contagem; agora devolve os dicts com as colunas de
    `_COLS_RESTAURAR`, que o cliente segura para oferecer 'Desfazer'."""
    pool = await get_pool()
    cols = ", ".join(_COLS_RESTAURAR)
    async with pool.acquire() as conn:
        recs = await conn.fetch(
            f"DELETE FROM bilhetes WHERE id = ANY($1) AND dono = $2 RETURNING {cols}",
            ids, dono,
        )
    return [dict(r) for r in recs]


async def restaurar_bilhetes(linhas: list[dict], dono: str) -> int:
    """Re-insere bilhetes apagados (undo). Idempotente: se a linha ainda existir
    (ou colidir na unique), o ON CONFLICT DO NOTHING a ignora. `dono` vem da sessão."""
    if not linhas:
        return 0
    pool = await get_pool()
    restaurados = 0
    async with pool.acquire() as conn:
        for l in linhas:
            rec = await conn.fetchrow(
                """
                INSERT INTO bilhetes
                    (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte, tipster,
                     aposta, descricao, stake, odd, resultado, extraction_state, confianca,
                     stake_usd, origem)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                ON CONFLICT (dono, casa, parceiro, assinatura) DO NOTHING
                RETURNING id
                """,
                dono, l.get("casa", ""), l.get("parceiro", ""), l.get("assinatura"),
                l.get("codigo_bilhete"), l.get("data"), l.get("esporte"), l.get("tipster"),
                l.get("aposta"), l.get("descricao"), l.get("stake"), l.get("odd"),
                l.get("resultado"), l.get("extraction_state") or "aberta",
                l.get("confianca"), l.get("stake_usd"), l.get("origem") or "restauracao",
            )
            if rec:
                restaurados += 1
    return restaurados


async def auto_arquivar(casa: str, parceiro: str, batch_size: int, dono: str) -> int:
    """Arquiva apostas antigas, mantendo max(batch_size, 40) mais recentes visíveis.

    Retorna o número de apostas arquivadas nesta chamada.
    """
    keep = max(batch_size, 40)
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY criado_em DESC) AS rn
                FROM bilhetes
                WHERE casa = $1 AND parceiro = $2 AND dono = $4
            )
            UPDATE bilhetes
            SET archived = CASE WHEN ranked.rn > $3 THEN TRUE ELSE FALSE END
            FROM ranked
            WHERE bilhetes.id = ranked.id
              AND bilhetes.archived != (ranked.rn > $3)
            """,
            casa, parceiro, keep, dono,
        )
    updated = int(result.split()[-1])
    return updated


async def contar_arquivados(casa: str, parceiro: str, dono: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM bilhetes WHERE casa = $1 AND parceiro = $2 AND dono = $3 AND archived = TRUE",
            casa, parceiro, dono,
        )
    return row[0]


async def contar_incompletos(dono: str) -> list[dict]:
    """Conta, por casa+parceiro, bilhetes 'incompletos': sem tipster (azul na sidebar)
    e abertos/sem resultado (âmbar). Inclui arquivados — a pendência existe
    independentemente de o bilhete estar visível na grade. Só retorna grupos com
    pelo menos uma pendência (mantém o payload pequeno)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT casa, parceiro,
                      COUNT(*) FILTER (WHERE tipster IS NULL OR tipster = '') AS sem_tipster,
                      COUNT(*) FILTER (WHERE extraction_state = 'aberta')     AS abertas
               FROM bilhetes
               WHERE dono = $1
               GROUP BY casa, parceiro
               HAVING COUNT(*) FILTER (WHERE tipster IS NULL OR tipster = '') > 0
                   OR COUNT(*) FILTER (WHERE extraction_state = 'aberta') > 0""",
            dono,
        )
    return [dict(r) for r in rows]


def _filtros_bilhetes(dono, casa, parceiro, extraction_state, archived):
    """Monta a cláusula WHERE compartilhada entre a listagem e a contagem."""
    filters, params = [], []
    for col, val in [("dono", dono), ("casa", casa), ("parceiro", parceiro),
                     ("extraction_state", extraction_state)]:
        if val is not None:
            params.append(val)
            filters.append(f"{col} = ${len(params)}")
    if archived == "false":
        filters.append("archived = FALSE")
    elif archived == "true":
        filters.append("archived = TRUE")
    # "all" → sem filtro
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    return where, params


async def list_bilhetes(
    dono: str,
    casa: str | None = None,
    parceiro: str | None = None,
    extraction_state: str | None = None,
    archived: str = "false",   # "false" | "true" | "all"
    limit: int = 500,
    offset: int = 0,
    order: str = "asc",
) -> list[dict]:
    pool = await get_pool()
    where, params = _filtros_bilhetes(dono, casa, parceiro, extraction_state, archived)
    order_sql = "ASC" if order == "asc" else "DESC"
    params.append(limit)
    limit_ph = f"${len(params)}"
    params.append(offset)
    offset_ph = f"${len(params)}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM bilhetes {where} "
            f"ORDER BY criado_em {order_sql}, id {order_sql} LIMIT {limit_ph} OFFSET {offset_ph}",
            *params,
        )
    out = []
    for r in rows:
        d = dict(r)
        # Campo derivado (não persistido): P/L líquido para o Dashboard.
        d["pl"] = calcular_pl(d.get("stake"), d.get("odd"), d.get("resultado"))
        out.append(d)
    return out


async def contar_bilhetes(
    dono: str,
    casa: str | None = None,
    parceiro: str | None = None,
    extraction_state: str | None = None,
    archived: str = "false",
) -> int:
    """Total de bilhetes que casam o filtro (para paginação: "X de Y apostas")."""
    pool = await get_pool()
    where, params = _filtros_bilhetes(dono, casa, parceiro, extraction_state, archived)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(f"SELECT COUNT(*) FROM bilhetes {where}", *params)
    return row[0]


async def casas_com_parceiros(dono: str) -> list[str]:
    """Casas que têm parceiros deste dono — inclui casas inativas importadas (sem
    manual CASA_*.md). Une-se à lista de manuais para a sidebar mostrar tudo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT casa FROM parceiros WHERE dono = $1", dono,
        )
    return [r["casa"] for r in rows]


async def export_bilhetes(dono: str) -> list[dict]:
    """Backup completo: TODAS as linhas do dono, TODAS as colunas, sem limite,
    em ordem cronológica de inserção. Alimenta o export CSV (rede de segurança
    antes de qualquer migração)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM bilhetes WHERE dono = $1 ORDER BY criado_em ASC, id ASC",
            dono,
        )
    return [dict(r) for r in rows]


def _resumir_apostas(rows: list[dict]) -> dict:
    """Agrega P/L, turnover, ROI, win rate, duração e dias ativos de uma lista de
    apostas (dicts com stake/odd/resultado/data). PURA (sem DB) para ser testável —
    é o núcleo de `resumo_conta`. Mesmos filtros de `dashboard_rows`: resultado
    válido, stake>0, P/L numérico (odd ilegível numa vitória → linha excluída),
    data ISO.

    Devolve: apostas (settled + void, contadas em `apostas`), P/L, turnover (exclui
    Void), ROI, win rate, duração (span 1ª→última, em dias) e dias ativos.
    """
    pl = turn = 0.0
    n = settled = wins = 0
    hw = hl = 0  # contagens de HW/HL p/ a fração do win rate (achado #17)
    datas: set[str] = set()
    dmin = dmax = None
    for r in rows:
        resultado = (r.get("resultado") or "").strip().upper()
        if resultado not in _RESULTADOS_VALIDOS:
            continue
        stake = _num(r.get("stake"))
        if stake <= 0:
            continue
        lucro = calcular_pl(r.get("stake"), r.get("odd"), resultado)
        if lucro is None:
            continue
        data_iso = _data_iso(r.get("data"))
        if not data_iso:
            continue
        pl += lucro
        n += 1
        if resultado != "V":
            turn += stake
            settled += 1
            if resultado in ("W", "HW"):
                wins += 1
            if resultado == "HW":
                hw += 1
            elif resultado == "HL":
                hl += 1
        datas.add(data_iso)
        if dmin is None or data_iso < dmin:
            dmin = data_iso
        if dmax is None or data_iso > dmax:
            dmax = data_iso
    roi = (pl / turn * 100) if turn > 0 else 0.0
    # Espelha o wrFrac do front (app.js, achado #17): HW=½ vitória, HL=½ derrota,
    # Void fora do denominador. wins já é W+HW; num = wins−½·hw, den = settled−½·hw−½·hl.
    wr_den = settled - 0.5 * hw - 0.5 * hl
    wr = ((wins - 0.5 * hw) / wr_den * 100) if wr_den > 0 else 0.0
    duracao = 0
    if dmin and dmax:
        duracao = (date.fromisoformat(dmax) - date.fromisoformat(dmin)).days + 1
    return {
        "apostas": n,
        "pl": round(pl, 2),
        "turnover": round(turn, 2),
        "roi": round(roi, 2),
        "win_rate": round(wr, 2),
        "duracao_dias": duracao,
        "dias_ativos": len(datas),
        "primeira": dmin,
        "ultima": dmax,
    }


async def resumo_conta(dono: str, casa: str, parceiro: str) -> dict:
    """Resumo agregado de UMA conta (casa+parceiro) para a faixa de KPIs no topo
    do extrator, incluindo arquivados — números batem com o card da casa no Betting
    Dashboard (mesmos filtros). A matemática vive em `_resumir_apostas` (pura,
    testável); aqui só buscamos as linhas da conta e delegamos.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT stake, odd, resultado, data FROM bilhetes "
            "WHERE dono = $1 AND casa = $2 AND parceiro = $3",
            dono, casa, parceiro,
        )
    return _resumir_apostas([dict(r) for r in rows])


async def dashboard_rows(donos: list[str]) -> list[dict]:
    """Feed do Betting Dashboard no MESMO contrato do Code.gs/Apps Script.

    Monta do Postgres (fonte única) o array que o dashboard client-side consome.
    Recebe uma LISTA de donos — para um DONO supervisor, é ele + os operadores
    dele, consolidando as bases num só feed; cada linha leva o campo `operador`
    (= o dono daquela linha) para o filtro de operador no front. Espelha os
    filtros do getData() da planilha:
      - resultado ∈ {W,L,V,HW,HL};
      - stake > 0;
      - P/L numérico (aposta aberta, P/L None, fica de fora);
      - data conversível para ISO.
    Inclui Polymarket (todas as linhas do banco). `conta`/`fornecedor` saem do
    parceiro "Conta [Fornecedor]"; `lucro` = P/L derivado (calcular_pl).
    """
    out = []
    for dono in donos:
        rows = await export_bilhetes(dono)
        for r in rows:
            resultado = (r.get("resultado") or "").strip().upper()
            if resultado not in _RESULTADOS_VALIDOS:
                continue
            stake = _num(r.get("stake"))
            if stake <= 0:
                continue
            lucro = calcular_pl(r.get("stake"), r.get("odd"), resultado)
            if lucro is None:
                continue
            data_iso = _data_iso(r.get("data"))
            if not data_iso:
                continue
            parceiro = (r.get("parceiro") or "").strip()
            conta, fornecedor = parceiro, ""
            m = _PARCEIRO_RE.match(parceiro)
            if m:
                conta, fornecedor = m.group(1).strip(), m.group(2).strip()
            out.append({
                # id da linha no Postgres — usado pela página de Apostas do dashboard
                # para editar/deletar (PATCH/DELETE /bilhetes/{id}). Linhas da planilha
                # ao vivo (dashboard_rows_ao_vivo) não têm id → chegam sem esta chave e
                # o front trata como não-editável.
                "id": r.get("id"),
                "data": data_iso,
                "esporte": (r.get("esporte") or "").strip(),
                "tipster": (r.get("tipster") or "").strip(),
                "casa": (r.get("casa") or "").strip(),
                "parceiro": parceiro,
                "conta": conta,
                "fornecedor": fornecedor,
                "aposta": (r.get("aposta") or "").strip(),
                "descricao": (r.get("descricao") or "").strip(),
                "stake": stake,
                "odd": _num(r.get("odd")),
                "resultado": resultado,
                "lucro": lucro,
                "operador": dono,
            })
    return out


async def list_tipsters(dono: str) -> list[str]:
    """Tipsters distintos já usados por este dono — alimenta o autocomplete da grade."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT tipster FROM bilhetes "
            "WHERE dono = $1 AND tipster IS NOT NULL AND tipster <> '' "
            "ORDER BY tipster",
            dono,
        )
    return [r["tipster"] for r in rows]


async def list_esportes(dono: str) -> list[str]:
    """Esportes distintos já usados por este dono — alimenta o autocomplete do editor."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT esporte FROM bilhetes "
            "WHERE dono = $1 AND esporte IS NOT NULL AND esporte <> '' "
            "ORDER BY esporte",
            dono,
        )
    return [r["esporte"] for r in rows]


async def get_ativos_tipster(dono: str, codigos: list[str]) -> dict[str, str]:
    """Tipster salvo para posições ativas Polymarket (codigo → tipster), deste dono."""
    if not codigos:
        return {}
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT codigo, tipster FROM polymarket_ativos_tipster "
            "WHERE dono = $1 AND codigo = ANY($2::text[])",
            dono, codigos,
        )
    return {r["codigo"]: r["tipster"] for r in rows}


async def set_ativo_tipster(dono: str, codigo: str, tipster: str) -> None:
    """Salva (ou limpa) o tipster de uma posição ativa Polymarket."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO polymarket_ativos_tipster (dono, codigo, tipster)
               VALUES ($1, $2, $3)
               ON CONFLICT (dono, codigo) DO UPDATE
                   SET tipster = EXCLUDED.tipster, atualizado_em = NOW()""",
            dono, codigo, tipster,
        )


async def limpar_ativos_tipster(dono: str, codigos: list[str]) -> int:
    """Apaga as linhas de tipster de ativas que já migraram para `bilhetes` (a aposta
    resolveu). Sem isso, o carry-over reinjetaria o tipster antigo a cada re-sync,
    sobrescrevendo uma edição feita na grade; e a tabela cresceria sem limite."""
    if not codigos:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM polymarket_ativos_tipster "
            "WHERE dono = $1 AND codigo = ANY($2::text[])",
            dono, codigos,
        )
    return int(result.split()[-1])




# ── Tipsters — cadastro (Perfil de Tipster, Fatia 0) ──────────────────────────
# NÃO confundir com list_tipsters() acima, que devolve os NOMES distintos já usados
# nos bilhetes (autocomplete da grade). As funções abaixo gerem a TABELA `tipsters`
# (o cadastro em si). Espelham o CRUD de parceiros. Ver docs/PLANO_TIPSTER.md.

async def garantir_tipster(dono: str, nome: str) -> None:
    """Auto-cadastro: garante que o tipster existe na tabela no instante em que o nome
    é digitado num bilhete. DO NOTHING → não duplica nem ressuscita um arquivado.
    Best-effort: nunca deve derrubar a escrita do bilhete que a disparou."""
    nome = (nome or "").strip()
    if not nome:
        return
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO tipsters (dono, nome) VALUES ($1, $2) "
                "ON CONFLICT (dono, nome) DO NOTHING",
                dono, nome,
            )
    except Exception:
        logger.exception("auto-cadastro de tipster falhou (não-fatal)")


async def criar_tipster(nome: str, dono: str) -> dict:
    """Cadastro explícito (ou reativação) de um tipster. Espelha criar_parceiro."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tipsters (dono, nome)
            VALUES ($1, $2)
            ON CONFLICT (dono, nome) DO UPDATE SET arquivado = FALSE
            RETURNING id, nome, casas, mercados, obs, arquivado, criado_em
            """,
            dono, nome,
        )
    return dict(row)


async def list_tipsters_cadastro(dono: str, incluir_arquivados: bool = False) -> list[dict]:
    """Tipsters CADASTRADOS (a tabela), com campos de info. `completo` = tem ao menos um
    campo de info preenchido; senão nasce incompleto (sinal (i) no onboarding)."""
    pool = await get_pool()
    filtro = "WHERE dono = $1"
    if not incluir_arquivados:
        filtro += " AND arquivado = FALSE"
    async with pool.acquire() as conn:
        # Poda de órfãos: tipster com 0 bilhetes E nenhuma info é um typo já corrigido na base
        # cuja linha de cadastro ficou pra trás (o backfill do boot só ADICIONA, nunca remove).
        # Pedido do Feca: "typo corrigido → some da lista". Guardado e seguro — nunca apaga quem
        # tem bilhete (o backfill o traria de volta) nem quem tem info curada (some só o lixo,
        # não o trabalho). Não há criação manual de tipster na UI, então 0 bilhetes = sempre órfão.
        await conn.execute(
            "DELETE FROM tipsters t WHERE t.dono = $1 "
            "AND t.casas IS NULL AND t.mercados IS NULL AND t.obs IS NULL AND t.apelidos IS NULL "
            "AND t.dica_stake IS NULL AND t.esportes IS NULL AND t.stake_min IS NULL AND t.stake_max IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM bilhetes b WHERE b.dono = t.dono AND b.tipster = t.nome)",
            dono)
        rows = await conn.fetch(
            f"SELECT id, nome, casas, mercados, obs, stake_min, stake_max, apelidos, "
            f"dica_stake, esportes, arquivado, criado_em "
            f"FROM tipsters {filtro} ORDER BY nome ASC",
            dono,
        )
    out = []
    for r in rows:
        d = dict(r)
        d["completo"] = bool(d.get("casas") or d.get("mercados") or d.get("obs")
                             or d.get("apelidos") or d.get("dica_stake") or d.get("esportes")
                             or d.get("stake_min") is not None
                             or d.get("stake_max") is not None)
        out.append(d)
    return out


async def arquivar_tipster(tipster_id: int, dono: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE tipsters SET arquivado = TRUE WHERE id = $1 AND dono = $2", tipster_id, dono
        )
    return result.split()[-1] == "1"


async def reativar_tipster(tipster_id: int, dono: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE tipsters SET arquivado = FALSE WHERE id = $1 AND dono = $2", tipster_id, dono
        )
    return result.split()[-1] == "1"


async def atualizar_tipster_info(tipster_id: int, dono: str, casas: str | None,
                                 mercados: str | None, obs: str | None,
                                 stake_min=None, stake_max=None,
                                 apelidos: str | None = None,
                                 dica_stake: str | None = None,
                                 esportes: str | None = None) -> bool:
    """Preenche os campos de info do perfil (casas, mercados, observações, dica de stake +
    os campos de detecção da Fase B: faixa de stake e apelidos/marca d'água).
    Regra: `None` mantém o valor atual; para os campos de texto string vazia LIMPA; para
    stake_min/stake_max, `""`/valor ilegível → NULL (via _num_or_none)."""
    sets, params = [], []
    for col, val in (("casas", casas), ("mercados", mercados), ("obs", obs),
                     ("apelidos", apelidos), ("dica_stake", dica_stake),
                     ("esportes", esportes)):
        if val is not None:
            params.append(val.strip() or None)
            sets.append(f"{col} = ${len(params)}")
    for col, val in (("stake_min", stake_min), ("stake_max", stake_max)):
        if val is not None:                       # "" → _num_or_none → None → limpa (NULL)
            params.append(_num_or_none(val))
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return False
    params.append(tipster_id)
    id_ph = len(params)
    params.append(dono)
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            f"UPDATE tipsters SET {', '.join(sets)} WHERE id = ${id_ph} AND dono = ${len(params)}",
            *params,
        )
    return result.split()[-1] == "1"


# ── Casa dedicada (registro + curadoria) ──────────────────────────────────────
# Casa-feudo: casa usada por 1 (ou 2) tipster(s) na operação do dono. A sugestão nasce
# da PUREZA observada nos rótulos HUMANOS (exclui 'sugerido' → sem circularidade). Estas
# funções só montam o registro e a curadoria; o matcher NÃO usa ainda (Etapa 1). Ver STATUS.
CASA_MIN_VOL = 8       # volume mínimo da casa p/ ter sugestão confiável
CASA_SHARE = 0.10      # tipster só é candidato a dono se ocupa ≥10% das apostas da casa
CASA_COVER = 0.85      # os 1-2 donos precisam cobrir ≥85% do volume (senão a cauda = multi)


async def casas_visao(dono: str) -> list[dict]:
    """Para cada casa vista nos bilhetes do dono, devolve a evidência de pureza (top
    tipster + share + volume + nº de tipsters), a SUGESTÃO de casa-feudo e a config atual
    (se já curada). Ordena por volume. READ-ONLY sobre os bilhetes."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT casa, tipster, COUNT(*) AS n FROM bilhetes "
            "WHERE dono = $1 AND tipster IS NOT NULL AND tipster <> '' "
            "AND (origem_tipster IS DISTINCT FROM 'sugerido') "
            "GROUP BY casa, tipster", dono)
        cfg_rows = await conn.fetch(
            "SELECT casa, modo, tipsters, origem FROM casa_config WHERE dono = $1", dono)
        ativos = await conn.fetch(
            "SELECT nome FROM tipsters WHERE dono = $1 AND arquivado = FALSE", dono)
    ativos_set = {r["nome"] for r in ativos}
    cfg = {r["casa"]: {"modo": r["modo"], "tipsters": r["tipsters"], "origem": r["origem"]} for r in cfg_rows}
    por_casa: dict[str, dict] = {}
    for r in rows:
        casa = (r["casa"] or "").strip()
        if not casa:
            continue
        d = por_casa.setdefault(casa, {"total": 0, "dist": {}})
        d["total"] += r["n"]
        d["dist"][(r["tipster"] or "").strip()] = r["n"]
    out = []
    for casa, d in por_casa.items():
        total = d["total"]
        dist = sorted(d["dist"].items(), key=lambda x: -x[1])
        top_nome, top_n = dist[0]
        # Sugestão de feudo: donos = tipsters ATIVOS com share individual ≥ CASA_SHARE (corta a
        # cauda), no máximo os 2 maiores. Só é 'dedicada' se esses 1-2 cobrem ≥ CASA_COVER do
        # volume; senão a cauda é grande = casa compartilhada → 'multi'. Ex.: Bet365 tem 2 acima
        # de 10% mas juntos <30% → multi; BETesporte é 99% Peixe → dedicada.
        donos = [nome for nome, n in dist if nome in ativos_set and n / total >= CASA_SHARE][:2]
        cobertura = sum(d["dist"][nm] for nm in donos) / total if donos else 0
        if total < CASA_MIN_VOL:
            sug_modo, sug_tipsters = None, []            # pouco dado → sem sugestão, Feca decide
        elif donos and cobertura >= CASA_COVER:
            sug_modo, sug_tipsters = "dedicada", donos
        else:
            sug_modo, sug_tipsters = "multi", []
        c = cfg.get(casa)
        out.append({
            "casa": casa, "total": total, "n_tipsters": len(d["dist"]),
            "top": top_nome, "top_share": round(100 * top_n / total),
            "sugestao_modo": sug_modo, "sugestao_tipsters": sug_tipsters,
            "modo": c["modo"] if c else None,             # None = ainda não curada
            "tipsters": c["tipsters"] if c else "",
            "origem": c["origem"] if c else None,         # 'sharpen' | 'custom' | None (não curada)
        })
    out.sort(key=lambda x: -x["total"])
    return out


async def salvar_casa_config(dono: str, casa: str, modo: str, tipsters: str,
                             origem: str = "custom") -> bool:
    """Upsert da curadoria de uma casa. modo='dedicada' exige 1-2 tipsters; 'multi' zera a
    lista. `origem` = 'sharpen' (aplicada da sugestão) | 'custom' (editada à mão). Chave
    (dono, casa). Retorna False se o input for inválido."""
    casa = (casa or "").strip()
    modo = (modo or "").strip().lower()
    origem = (origem or "custom").strip().lower()
    if not casa or modo not in ("dedicada", "multi") or origem not in ("sharpen", "custom"):
        return False
    if modo == "dedicada":
        tips_list = [t.strip() for t in (tipsters or "").split(",") if t.strip()]
        if not (1 <= len(tips_list) <= 2):
            return False
        tips = ",".join(tips_list)
    else:
        tips = ""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO casa_config (dono, casa, modo, tipsters, origem, atualizado_em) "
            "VALUES ($1, $2, $3, $4, $5, NOW()) "
            "ON CONFLICT (dono, casa) DO UPDATE SET modo = $3, tipsters = $4, origem = $5, atualizado_em = NOW()",
            dono, casa, modo, tips, origem)
    return True


async def renomear_tipster(tipster_id: int, novo_nome: str, dono: str) -> dict:
    """Renomeia o tipster E propaga aos bilhetes (que o referenciam por NOME em
    bilhetes.tipster). Espelha renomear_parceiro. Colisão respeita UNIQUE (dono, nome):
    se o novo nome já existe, recusa e explica — fundir dois tipsters é decisão manual
    (reatribuir os bilhetes), não um efeito colateral silencioso do rename."""
    novo_nome = (novo_nome or "").strip()
    if not novo_nome:
        return {"ok": False, "motivo": "Nome vazio."}
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT nome FROM tipsters WHERE id = $1 AND dono = $2", tipster_id, dono
            )
            if not row:
                return {"ok": False, "motivo": "Tipster não encontrado."}
            antigo = row["nome"]
            if antigo == novo_nome:
                return {"ok": True, "bilhetes_atualizados": 0}
            existe = await conn.fetchval(
                "SELECT 1 FROM tipsters WHERE dono = $1 AND nome = $2 AND id <> $3",
                dono, novo_nome, tipster_id,
            )
            if existe:
                return {"ok": False, "motivo": "Já existe um tipster com esse nome."}
            await conn.execute(
                "UPDATE tipsters SET nome = $1 WHERE id = $2 AND dono = $3",
                novo_nome, tipster_id, dono,
            )
            res = await conn.execute(
                "UPDATE bilhetes SET tipster = $1 WHERE dono = $2 AND tipster = $3",
                novo_nome, dono, antigo,
            )
            # Propaga também para a escada de unidade (chaveada por nome).
            await conn.execute(
                "UPDATE tipster_unidade SET tipster = $1 WHERE dono = $2 AND tipster = $3",
                novo_nome, dono, antigo,
            )
    return {"ok": True, "bilhetes_atualizados": int(res.split()[-1])}


# ── Escada de unidade (Perfil de Tipster, Fatia 1) ────────────────────────────
# As funções PURAS (unidade_vigente, pl_em_unidades) vivem lá em cima, junto de
# calcular_pl. Estas são só os wrappers de banco. Ver docs/PLANO_TIPSTER.md §P1.

async def get_escada_unidade(dono: str, tipster: str) -> list[dict]:
    """Escada de valor-da-unidade no tempo de um tipster (degraus ordenados)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, vigente_desde, valor FROM tipster_unidade "
            "WHERE dono = $1 AND tipster = $2 ORDER BY vigente_desde ASC",
            dono, tipster,
        )
    return [dict(r) for r in rows]


async def set_unidade(dono: str, tipster: str, vigente_desde: str, valor) -> dict:
    """Insere/atualiza um degrau (a partir de `vigente_desde`, 1u = `valor` reais).
    Valida data e valor > 0. Upsert por (dono, tipster, vigente_desde)."""
    tipster = (tipster or "").strip()
    if not tipster:
        return {"ok": False, "motivo": "Tipster não informado."}
    di = _data_iso(vigente_desde)
    if not di:
        return {"ok": False, "motivo": "Data inválida (use DD/MM/AAAA)."}
    v = _num_or_none(valor)
    if v is None or v <= 0:
        return {"ok": False, "motivo": "Valor da unidade deve ser maior que zero."}
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO tipster_unidade (dono, tipster, vigente_desde, valor)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (dono, tipster, vigente_desde)
               DO UPDATE SET valor = EXCLUDED.valor
               RETURNING id, vigente_desde, valor""",
            dono, tipster, di, v,
        )
    return {"ok": True, "segmento": dict(row)}


async def remover_unidade(unidade_id: int, dono: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM tipster_unidade WHERE id = $1 AND dono = $2", unidade_id, dono
        )
    return result.split()[-1] == "1"


async def resultado_em_unidades(dono: str, tipster: str) -> dict:
    """P/L de um tipster em UNIDADES, usando a escada dele (via pl_em_unidades). Sem
    escada, cai na stake média das apostas resolvidas do PRÓPRIO tipster (fallback) e
    marca usou_fallback. NOTA: o PLANO_TIPSTER sugere como default a média GLOBAL do
    cliente; aqui uso a do próprio tipster (self-contido) — trocar é só mudar o fallback."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT data, stake, odd, resultado FROM bilhetes "
            "WHERE dono = $1 AND tipster = $2", dono, tipster,
        )
        esc = await conn.fetch(
            "SELECT vigente_desde, valor FROM tipster_unidade "
            "WHERE dono = $1 AND tipster = $2", dono, tipster,
        )
    escada = [dict(r) for r in esc]
    linhas, stakes = [], []
    for r in rows:
        pl = calcular_pl(r["stake"], r["odd"], r["resultado"])
        if pl is None:
            continue
        di = _data_iso(r["data"])
        if di is None:
            continue
        linhas.append({"pl": pl, "data": di})
        s = _num(r["stake"])
        if s > 0:
            stakes.append(s)
    fallback = (sum(stakes) / len(stakes)) if (not escada and stakes) else None
    res = pl_em_unidades(linhas, escada, unidade_fallback=fallback)
    res["pl_reais"] = round(sum(ln["pl"] for ln in linhas), 2)
    res["tem_escada"] = bool(escada)
    return res


async def get_escadas_todas(dono: str) -> dict:
    """Todas as escadas do dono, agrupadas por tipster. O front computa o resultado em
    unidades sobre as linhas JÁ FILTRADAS do dashboard (respeita data/esporte/casa) — por
    isso entregamos as escadas cruas, não o u pronto. Payload pequeno (1 linha por degrau);
    a maioria dos tipsters não tem escada e cai no fallback de média (calculado no cliente)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT tipster, vigente_desde, valor FROM tipster_unidade WHERE dono = $1 "
            "ORDER BY tipster, vigente_desde", dono)
    out: dict = {}
    for r in rows:
        out.setdefault(r["tipster"], []).append(
            {"vigente_desde": r["vigente_desde"], "valor": r["valor"]})
    return out


# ── Parceiros ─────────────────────────────────────────────────────────────────

async def criar_parceiro(casa: str, nome: str, dono: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO parceiros (dono, casa, nome)
            VALUES ($1, $2, $3)
            ON CONFLICT (dono, casa, nome) DO UPDATE SET arquivado = FALSE
            RETURNING id, casa, nome, arquivado, criado_em
            """,
            dono, casa, nome,
        )
    return dict(row)


async def list_parceiros(dono: str, casa: str | None = None, incluir_arquivados: bool = False) -> list[dict]:
    pool = await get_pool()
    params = [dono]
    filters = [f"dono = ${len(params)}"]
    if casa is not None:
        params.append(casa)
        filters.append(f"casa = ${len(params)}")
    if not incluir_arquivados:
        filters.append("arquivado = FALSE")
    where = "WHERE " + " AND ".join(filters)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, casa, nome, arquivado, criado_em FROM parceiros {where} ORDER BY criado_em ASC",
            *params,
        )
    return [dict(r) for r in rows]


async def arquivar_parceiro(parceiro_id: int, dono: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE parceiros SET arquivado = TRUE WHERE id = $1 AND dono = $2", parceiro_id, dono
        )
    return result.split()[-1] == "1"


def _correcoes_diff(antes, safe: dict) -> list[tuple]:
    """Pares (campo, antigo, novo) dos campos que de fato mudaram. Puro/testável.
    `antes` = valores atuais (Record ou dict); `safe` = valores novos já filtrados.
    None e string vazia contam como iguais (não é correção)."""
    out = []
    for campo, novo in safe.items():
        antigo = antes.get(campo)
        if (antigo or "") == (novo or ""):
            continue
        out.append((campo, antigo, novo))
    return out


async def _registrar_correcoes(conn, bilhete_id: int, dono: str, antes, safe: dict) -> None:
    """Grava em `correcoes` cada campo alterado (semente do cache aprendido — Fase 3).
    NUNCA falha a edição: qualquer erro aqui é engolido e logado."""
    try:
        casa, desc = antes.get("casa"), antes.get("descricao")
        for campo, antigo, novo in _correcoes_diff(antes, safe):
            await conn.execute(
                "INSERT INTO correcoes (bilhete_id, dono, casa, campo, "
                "valor_anterior, valor_novo, descricao) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                bilhete_id, dono, casa, campo, antigo, novo, desc)
    except Exception:
        logger.exception("registro de correção falhou (não-fatal)")


async def atualizar_bilhete(bilhete_id: int, campos: dict, dono: str) -> bool:
    _EDITAVEIS = {"data", "esporte", "tipster", "casa", "parceiro",
                  "aposta", "descricao", "stake", "odd", "resultado"}
    safe = {k: v for k, v in campos.items() if k in _EDITAVEIS}
    if not safe:
        return False
    # Canoniza o resultado para maiúscula ANTES de gravar e de derivar o estado: digitar
    # 'v' precisa virar 'V' no banco, senão fica 'aberta' e conta como "aguardando resultado".
    if "resultado" in safe:
        safe["resultado"] = (safe["resultado"] or "").strip().upper()
    pool = await get_pool()
    async with pool.acquire() as conn:
        # snapshot ANTES do update: registra a correção (rótulo→antigo→novo) E fornece
        # resultado/odd atuais p/ recomputar o estado quando só um dos dois é editado.
        # Defensivo: se o snapshot falhar, a edição segue normalmente.
        antes = None
        try:
            antes = await conn.fetchrow(
                "SELECT * FROM bilhetes WHERE id = $1 AND dono = $2", bilhete_id, dono)
        except Exception:
            logger.exception("snapshot p/ correção falhou (não-fatal)")
        sets, params = [], []
        for col, val in safe.items():
            params.append(val)
            sets.append(f"{col} = ${len(params)}")
        # Recalcula extraction_state quando resultado OU odd muda, com o valor FINAL de
        # cada um (novo se editado, senão o já gravado). Assim completar a odd de uma
        # aposta 'aberta' (sem odd) promove p/ 'resolvida'; apagar a odd rebaixa.
        if ("resultado" in safe or "odd" in safe) and antes is not None:
            res_final = safe.get("resultado", antes["resultado"])
            odd_final = safe.get("odd", antes["odd"])
            params.append(estado_extracao(res_final, odd_final))
            sets.append(f"extraction_state = ${len(params)}")
        elif "resultado" in safe:  # snapshot falhou: regra antiga (só resultado)
            params.append("resolvida" if safe["resultado"] in _RESULTADOS_VALIDOS else "aberta")
            sets.append(f"extraction_state = ${len(params)}")

        # Procedência do rótulo de tipster (Fase 0): grava origem_tipster quando o tipster
        # muda. Sem origem declarada → 'humano' (só o botão de sugestão manda 'sugerido').
        # Tipster limpo (vazio) → NULL. origem_tipster ∉ _SIG_COLS → não mexe na assinatura.
        if "tipster" in safe:
            _tip = (safe["tipster"] or "").strip()
            params.append((campos.get("origem_tipster") or "humano") if _tip else None)
            sets.append(f"origem_tipster = ${len(params)}")

        # Ponto de retorno SEM assinatura: fallback se a corrida abaixo estourar a unique.
        sets_base, params_base = list(sets), list(params)

        # Recalcula a assinatura quando a edição toca o hash — senão a linha fica com a
        # assinatura velha e uma re-extração do mesmo bilhete duplica.
        if antes is not None and not _SIG_COLS.isdisjoint(safe):
            nova_sig = await _assinatura_pos_edicao(conn, antes, safe, dono, bilhete_id)
            if nova_sig:
                params.append(nova_sig)
                sets.append(f"assinatura = ${len(params)}")

        async def _exec(sets_: list, params_: list) -> str:
            p = list(params_)
            p.append(bilhete_id)
            id_ph = len(p)
            p.append(dono)
            return await conn.execute(
                f"UPDATE bilhetes SET {', '.join(sets_)}, atualizado_em = NOW() "
                f"WHERE id = ${id_ph} AND dono = ${len(p)}", *p)

        try:
            result = await _exec(sets, params)
        except asyncpg.UniqueViolationError:
            # Corrida: alguém ocupou a assinatura entre a checagem e o UPDATE. A edição do
            # usuário não pode falhar por isso — regrava sem tocar na assinatura.
            logger.warning("assinatura pós-edição colidiu em corrida no bilhete %s; "
                           "edição aplicada mantendo a assinatura atual", bilhete_id)
            result = await _exec(sets_base, params_base)
        ok = result.split()[-1] == "1"
        if ok and antes is not None:
            await _registrar_correcoes(conn, bilhete_id, dono, antes, safe)
    # Cadastro automático: editar o tipster de um bilhete faz o tipster existir na base.
    if ok and safe.get("tipster"):
        await garantir_tipster(dono, safe["tipster"])
    return ok


async def set_casa_dominio(dono: str, casa: str, dominio: str) -> None:
    """Guarda o domínio de uma casa (por dono) para o favicon. Upsert idempotente.
    Domínio vazio vira NULL (cai no fallback do faviconUrl)."""
    if not casa.strip():
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO casas_meta (dono, casa, dominio) VALUES ($1, $2, $3)
               ON CONFLICT (dono, casa)
               DO UPDATE SET dominio = EXCLUDED.dominio, atualizado_em = NOW()""",
            dono, casa.strip(), (dominio or "").strip() or None)


async def get_casas_dominios(dono: str) -> dict:
    """Mapa casa→domínio do dono (só casas com domínio definido)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT casa, dominio FROM casas_meta WHERE dono = $1 AND dominio IS NOT NULL", dono)
    return {r["casa"]: r["dominio"] for r in rows}


async def get_custo_store(dono: str) -> dict | None:
    """Custos do dono (Custo por Tipster + Custos Gerais) — ver database.custo_store.
    Retorna None se o dono AINDA NÃO tem registro (servidor "vazio" → o front sabe
    que precisa importar do navegador). custo_tipster = {tipster:{"YYYY-MM":val}};
    custo_geral = [{id,tipo,values}]. Espelha get_casas_dominios. JSONB volta como
    str no asyncpg (sem codec) → json.loads."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT custo_tipster, custo_geral FROM custo_store WHERE dono = $1", dono)
    if row is None:
        return None
    ct = row["custo_tipster"]
    cg = row["custo_geral"]
    if isinstance(ct, str):
        ct = json.loads(ct)
    if isinstance(cg, str):
        cg = json.loads(cg)
    return {"custo_tipster": ct or {}, "custo_geral": cg or []}


async def salvar_custo_store(dono: str, custo_tipster: dict, custo_geral: list) -> None:
    """Upsert do blob de custos do dono. Substitui o registro inteiro — o front
    sempre manda o estado completo (como o localStorage fazia). Espelha
    salvar_casa_config. Passa JSON como texto + cast ::jsonb (sem codec global)."""
    ct = json.dumps(custo_tipster if isinstance(custo_tipster, dict) else {})
    cg = json.dumps(custo_geral if isinstance(custo_geral, list) else [])
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO custo_store (dono, custo_tipster, custo_geral, atualizado_em) "
            "VALUES ($1, $2::jsonb, $3::jsonb, NOW()) "
            "ON CONFLICT (dono) DO UPDATE SET custo_tipster = EXCLUDED.custo_tipster, "
            "custo_geral = EXCLUDED.custo_geral, atualizado_em = NOW()",
            dono, ct, cg)


async def get_custo_conta(dono: str) -> dict | None:
    """Custo por conta/fornecedor do dono ({"fornecedor||casa": numero}) — coluna
    custo_conta de custo_store. Retorna None se o dono não tem registro nenhum. O
    row pode existir (do import de tipster/geral) com custo_conta vazio; a rota
    decide `existe` pela NÃO-vacuidade do dict. JSONB→str no asyncpg → json.loads."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT custo_conta FROM custo_store WHERE dono = $1", dono)
    if row is None:
        return None
    v = row["custo_conta"]
    if isinstance(v, str):
        v = json.loads(v)
    return {"custo_conta": v or {}}


async def salvar_custo_conta(dono: str, custo_conta: dict) -> None:
    """Upsert do custo por conta/fornecedor, tocando SÓ a coluna custo_conta (não
    mexe em custo_tipster/custo_geral). Front manda o estado completo. Linha nova
    nasce com os outros custos no default da coluna ('{}'/'[]')."""
    cc = json.dumps(custo_conta if isinstance(custo_conta, dict) else {})
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO custo_store (dono, custo_conta, atualizado_em) "
            "VALUES ($1, $2::jsonb, NOW()) "
            "ON CONFLICT (dono) DO UPDATE SET custo_conta = EXCLUDED.custo_conta, atualizado_em = NOW()",
            dono, cc)


async def set_tipster_bulk(ids: list[int], tipster: str, dono: str) -> int:
    """Atribui o mesmo tipster a várias apostas de uma vez (1 UPDATE atômico).
    Só toca linhas do próprio dono. Retorna quantas foram atualizadas."""
    if not ids:
        return 0
    # Bulk é operação MANUAL → procedência 'humano' (tipster vazio → NULL). Fase 0.
    origem = "humano" if (tipster or "").strip() else None
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE bilhetes SET tipster = $1, origem_tipster = $4, atualizado_em = NOW() "
            "WHERE id = ANY($2) AND dono = $3",
            tipster, ids, dono, origem,
        )
    n = int(result.split()[-1])
    if n:
        # Cadastro automático: o tipster passa a existir na base ao ser atribuído.
        await garantir_tipster(dono, tipster)
    return n


async def reativar_parceiro(parceiro_id: int, dono: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE parceiros SET arquivado = FALSE WHERE id = $1 AND dono = $2", parceiro_id, dono
        )
    return result.split()[-1] == "1"


async def renomear_parceiro(parceiro_id: int, novo_nome: str, dono: str) -> dict:
    """Renomeia a conta E propaga o novo nome aos bilhetes dela (os bilhetes referenciam
    o parceiro por NOME — `bilhetes.casa + bilhetes.parceiro` —, então sem isto as apostas
    ficariam órfãs). Tudo numa transação. Retorna {ok, motivo?, bilhetes_atualizados}."""
    novo_nome = (novo_nome or "").strip()
    if not novo_nome:
        return {"ok": False, "motivo": "Nome vazio."}
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT casa, nome FROM parceiros WHERE id = $1 AND dono = $2", parceiro_id, dono
            )
            if not row:
                return {"ok": False, "motivo": "Conta não encontrada."}
            casa, antigo = row["casa"], row["nome"]
            if antigo == novo_nome:
                return {"ok": True, "bilhetes_atualizados": 0}
            # Colisão: já existe outra conta com esse nome nesta casa (viola UNIQUE).
            existe = await conn.fetchval(
                "SELECT 1 FROM parceiros WHERE dono = $1 AND casa = $2 AND nome = $3 AND id <> $4",
                dono, casa, novo_nome, parceiro_id,
            )
            if existe:
                return {"ok": False, "motivo": "Já existe uma conta com esse nome nesta casa."}
            await conn.execute(
                "UPDATE parceiros SET nome = $1 WHERE id = $2 AND dono = $3",
                novo_nome, parceiro_id, dono,
            )
            res = await conn.execute(
                "UPDATE bilhetes SET parceiro = $1 WHERE dono = $2 AND casa = $3 AND parceiro = $4",
                novo_nome, dono, casa, antigo,
            )
    return {"ok": True, "bilhetes_atualizados": int(res.split()[-1])}


async def get_codigos_existentes(codigos: list[str], dono: str) -> set[str]:
    """Retorna subset de codigos que já existem no banco (deste dono)."""
    if not codigos:
        return set()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT codigo_bilhete FROM bilhetes WHERE codigo_bilhete = ANY($1::text[]) AND dono = $2",
            codigos, dono,
        )
    return {row["codigo_bilhete"] for row in rows}


async def get_codigos_resolvidos(codigos: list[str], dono: str) -> set[str]:
    """Retorna subset de codigos já salvos E liquidados (extraction_state = 'resolvida').

    Usado no pré-dedup de texto (Betano): pula bilhetes que já estão no banco como
    resolvidos, mas NÃO pula os salvos como 'aberta' — assim uma aposta que estava
    em aberto (vinda de print) e agora aparece liquidada no texto ainda é processada
    para atualizar o resultado.
    """
    if not codigos:
        return set()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT codigo_bilhete FROM bilhetes
               WHERE codigo_bilhete = ANY($1::text[])
                 AND extraction_state = 'resolvida'
                 AND dono = $2""",
            codigos, dono,
        )
    return {row["codigo_bilhete"] for row in rows}


# ── Log de uso de tokens (observabilidade de custo) ───────────────────────────
# Preço USD por MTok (input, output, cache write 5m, cache read). Fonte: tabela de
# preços da API Anthropic. Ao mudar o preço, atualize aqui — o custo já gravado
# permanece congelado (foi calculado no ato da extração).
_PRECOS = {
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_write": 3.75},
    "claude-opus-4-8":   {"input": 5.0, "output": 25.0, "cache_read": 0.50, "cache_write": 6.25},
}
_PRECO_PADRAO = _PRECOS["claude-sonnet-4-6"]


def custo_usd(modelo: str, tk: dict) -> float:
    """Custo em USD de um lote de tokens para um modelo (preço por MTok / 1e6)."""
    p = _PRECOS.get(modelo, _PRECO_PADRAO)
    return (
        tk.get("input", 0) * p["input"]
        + tk.get("output", 0) * p["output"]
        + tk.get("cache_read", 0) * p["cache_read"]
        + tk.get("cache_write", 0) * p["cache_write"]
    ) / 1_000_000


async def registrar_uso(dono: str, casa: str, modelo: str, chunks: int,
                        n_itens: int, tokens: dict) -> None:
    """Grava uma linha de uso por extração. Fire-and-forget: nunca derruba o
    stream (erros são só logados)."""
    try:
        custo = custo_usd(modelo, tokens)
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO uso_tokens
                     (dono, casa, modelo, chunks, n_itens, input, output, cache_read, cache_write, custo_usd)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
                dono, casa, modelo, int(chunks or 1), int(n_itens or 0),
                int(tokens.get("input", 0)), int(tokens.get("output", 0)),
                int(tokens.get("cache_read", 0)), int(tokens.get("cache_write", 0)), custo,
            )
    except Exception:
        logger.warning("registrar_uso falhou (uso não gravado)", exc_info=True)


async def uso_resumo(dono: str, dias: int = 30, todos: bool = False) -> dict:
    """Resumo de uso/custo dos últimos `dias`. Se `todos`, agrega TODOS os donos
    (visão da carteira inteira, p/ o dono do projeto) e inclui quebra por dono."""
    pool = await get_pool()
    janela = f"{int(dias)} days"
    async with pool.acquire() as conn:
        if todos:
            filtro, args = "criado_em >= NOW() - $1::interval", (janela,)
        else:
            filtro, args = "dono = $2 AND criado_em >= NOW() - $1::interval", (janela, dono)

        total = await conn.fetchrow(
            f"""SELECT COUNT(*) extracoes, COALESCE(SUM(n_itens),0) itens,
                       COALESCE(SUM(input),0) input, COALESCE(SUM(output),0) output,
                       COALESCE(SUM(cache_read),0) cache_read, COALESCE(SUM(cache_write),0) cache_write,
                       COALESCE(SUM(custo_usd),0) custo_usd
                FROM uso_tokens WHERE {filtro}""", *args)
        por_casa = await conn.fetch(
            f"""SELECT casa, COUNT(*) extracoes, COALESCE(SUM(n_itens),0) itens,
                       COALESCE(SUM(custo_usd),0) custo_usd
                FROM uso_tokens WHERE {filtro}
                GROUP BY casa ORDER BY custo_usd DESC""", *args)
        por_dia = await conn.fetch(
            f"""SELECT date_trunc('day', criado_em)::date dia, COUNT(*) extracoes,
                       COALESCE(SUM(n_itens),0) itens, COALESCE(SUM(custo_usd),0) custo_usd
                FROM uso_tokens WHERE {filtro}
                GROUP BY dia ORDER BY dia""", *args)
        por_dono = []
        if todos:
            por_dono = await conn.fetch(
                f"""SELECT dono, COUNT(*) extracoes, COALESCE(SUM(n_itens),0) itens,
                           COALESCE(SUM(custo_usd),0) custo_usd
                    FROM uso_tokens WHERE {filtro}
                    GROUP BY dono ORDER BY custo_usd DESC""", *args)

    d = dict(total)
    itens = d["itens"] or 0
    d["custo_por_item_usd"] = (d["custo_usd"] / itens) if itens else 0.0
    return {
        "dias": int(dias), "escopo": "todos" if todos else dono,
        "total": d,
        "por_casa": [dict(r) for r in por_casa],
        "por_dia": [dict(r) for r in por_dia],
        "por_dono": [dict(r) for r in por_dono],
    }

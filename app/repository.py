import hashlib
import logging
import re
from datetime import date, datetime, timezone

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


async def upsert_bilhetes(
    rows: list[dict], dono: str, confianca: float | None = None,
    origem: str = "extracao",
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

            resultado = row.get("resultado", "").strip() or None
            extraction_state = "resolvida" if resultado in _RESULTADOS_VALIDOS else "aberta"
            try:
                rec = await conn.fetchrow(
                    """
                    INSERT INTO bilhetes
                        (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte, tipster,
                         aposta, descricao, stake, odd, resultado,
                         extraction_state, confianca, stake_usd, origem)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                    ON CONFLICT (dono, casa, parceiro, assinatura) DO UPDATE SET
                        -- preserva o tipster existente quando o lote vier sem tipster
                        -- (extração/sync sempre mandam ''); só sobrescreve com valor real
                        tipster          = COALESCE(NULLIF(EXCLUDED.tipster, ''), bilhetes.tipster),
                        codigo_bilhete   = COALESCE(bilhetes.codigo_bilhete, EXCLUDED.codigo_bilhete),
                        resultado        = EXCLUDED.resultado,
                        extraction_state = EXCLUDED.extraction_state,
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
                        resultado        = $7,
                        extraction_state = $8,
                        atualizado_em    = NOW()
                    WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND assinatura = $4
                    RETURNING id, FALSE AS was_inserted
                    """,
                    dono, row.get("casa", ""), row.get("parceiro", ""), sig,
                    row.get("tipster"), codigo or None, resultado, extraction_state,
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
        datas.add(data_iso)
        if dmin is None or data_iso < dmin:
            dmin = data_iso
        if dmax is None or data_iso > dmax:
            dmax = data_iso
    roi = (pl / turn * 100) if turn > 0 else 0.0
    wr = (wins / settled * 100) if settled > 0 else 0.0
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


async def atualizar_bilhete(bilhete_id: int, campos: dict, dono: str) -> bool:
    _EDITAVEIS = {"data", "esporte", "tipster", "casa", "parceiro",
                  "aposta", "descricao", "stake", "odd", "resultado"}
    safe = {k: v for k, v in campos.items() if k in _EDITAVEIS}
    if not safe:
        return False
    sets, params = [], []
    for col, val in safe.items():
        params.append(val)
        sets.append(f"{col} = ${len(params)}")
    if "resultado" in safe:
        es = "resolvida" if (safe["resultado"] or "").strip() in _RESULTADOS_VALIDOS else "aberta"
        params.append(es)
        sets.append(f"extraction_state = ${len(params)}")
    params.append(bilhete_id)
    id_ph = len(params)
    params.append(dono)
    sql = (f"UPDATE bilhetes SET {', '.join(sets)}, atualizado_em = NOW() "
           f"WHERE id = ${id_ph} AND dono = ${len(params)}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(sql, *params)
    return result.split()[-1] == "1"


async def set_tipster_bulk(ids: list[int], tipster: str, dono: str) -> int:
    """Atribui o mesmo tipster a várias apostas de uma vez (1 UPDATE atômico).
    Só toca linhas do próprio dono. Retorna quantas foram atualizadas."""
    if not ids:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE bilhetes SET tipster = $1, atualizado_em = NOW() "
            "WHERE id = ANY($2) AND dono = $3",
            tipster, ids, dono,
        )
    return int(result.split()[-1])


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

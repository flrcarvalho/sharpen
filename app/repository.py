import hashlib

import asyncpg

from database import get_pool

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


def _num(v) -> float:
    """Converte número ("1.234,50" / "1,81" / "75.2606") para float.

    Duas convenções coexistem no histórico:
      - BR com vírgula decimal: "1.234,50" → ponto é milhar, vírgula é decimal.
      - Odd calculada com ponto decimal: "75.26066..." (múltiplas Betano, s50),
        sem vírgula nenhuma → o ponto JÁ é o separador decimal.

    Regra: se há vírgula, ela manda (ponto = milhar). Sem vírgula, o ponto é
    decimal e deve ser preservado — removê-lo transformava "75.26" em 7526...,
    estourando o P/L derivado. Confirmado no banco: 5 odds nesse formato, 0 stakes.
    Devolve 0.0 se ilegível.
    """
    if v is None:
        return 0.0
    s = str(v).strip().rstrip(".")  # remove reticências/ponto solto ao final
    if not s:
        return 0.0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")  # padrão BR: ponto = milhar
    # sem vírgula: o ponto (se houver) já é decimal — não mexe
    try:
        return float(s)
    except ValueError:
        return 0.0


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
    o = _num(odd)
    valor = {
        "W":  s * o,
        "L":  0.0,
        "V":  s,
        "HW": (s / 2) * o + (s / 2),
        "HL": s / 2,
    }[res]
    return round(valor - s, 2)


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


def _assinatura(row: dict, _counter: int = 1) -> str:
    codigo = row.get("codigo_bilhete", "").strip()
    if codigo:
        raw = "|".join(["ID", row.get("casa", ""), row.get("parceiro", ""), codigo])
    else:
        raw = "|".join([
            row.get("casa", ""), row.get("parceiro", ""),
            row.get("data", ""), row.get("aposta", ""), row.get("descricao", ""),
            _norm_odd(row.get("odd", "")),
        ])
        if _counter > 1:
            raw += f"|{_counter}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


async def upsert_bilhetes(
    rows: list[dict], dono: str, confianca: float | None = None
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
                         extraction_state, confianca, stake_usd)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
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
                    extraction_state, confianca, row.get("stake_usd"),
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


async def deletar_bilhetes(ids: list[int], dono: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM bilhetes WHERE id = ANY($1) AND dono = $2", ids, dono
        )
    return int(result.split()[-1])


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


async def contar_pendentes(dono: str) -> list[dict]:
    """Conta bilhetes ainda não copiados (copy_state='pendente') por casa+parceiro.

    Inclui arquivados — 'pendente' significa 'não copiado para a planilha',
    independentemente de o bilhete estar visível na grade ou arquivado.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT casa, parceiro, COUNT(*) AS pendentes
               FROM bilhetes
               WHERE dono = $1 AND copy_state = 'pendente'
               GROUP BY casa, parceiro""",
            dono,
        )
    return [dict(r) for r in rows]


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


def _filtros_bilhetes(dono, casa, parceiro, copy_state, extraction_state, archived):
    """Monta a cláusula WHERE compartilhada entre a listagem e a contagem."""
    filters, params = [], []
    for col, val in [("dono", dono), ("casa", casa), ("parceiro", parceiro),
                     ("copy_state", copy_state), ("extraction_state", extraction_state)]:
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
    copy_state: str | None = None,
    extraction_state: str | None = None,
    archived: str = "false",   # "false" | "true" | "all"
    limit: int = 500,
    offset: int = 0,
    order: str = "asc",
) -> list[dict]:
    pool = await get_pool()
    where, params = _filtros_bilhetes(dono, casa, parceiro, copy_state, extraction_state, archived)
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
    copy_state: str | None = None,
    extraction_state: str | None = None,
    archived: str = "false",
) -> int:
    """Total de bilhetes que casam o filtro (para paginação: "X de Y apostas")."""
    pool = await get_pool()
    where, params = _filtros_bilhetes(dono, casa, parceiro, copy_state, extraction_state, archived)
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


async def marcar_copiada(ids: list[int], dono: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE bilhetes SET copy_state = 'copiada', atualizado_em = NOW() WHERE id = ANY($1) AND dono = $2",
            ids, dono,
        )
    return int(result.split()[-1])


async def marcar_pendente(ids: list[int], dono: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE bilhetes SET copy_state = 'pendente', atualizado_em = NOW() WHERE id = ANY($1) AND dono = $2",
            ids, dono,
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


async def reativar_parceiro(parceiro_id: int, dono: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE parceiros SET arquivado = FALSE WHERE id = $1 AND dono = $2", parceiro_id, dono
        )
    return result.split()[-1] == "1"


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

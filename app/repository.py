import hashlib

from database import get_pool

# Colunas do TSV (índices 0–9)
_COLS = ["data", "esporte", "tipster", "casa", "parceiro",
         "aposta", "descricao", "stake", "odd", "resultado"]

_RESULTADOS_VALIDOS = {"W", "L", "V", "HW", "HL"}


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


def _assinatura(row: dict) -> str:
    codigo = row.get("codigo_bilhete", "").strip()
    if codigo:
        # ID único do bilhete disponível: usa como chave primária de dedup
        raw = "|".join(["ID", row.get("casa", ""), row.get("parceiro", ""), codigo])
    else:
        # Sem ID: usa conteúdo completo (casa + parceiro + data + aposta + descricao + odd)
        raw = "|".join([
            row.get("casa", ""), row.get("parceiro", ""),
            row.get("data", ""), row.get("aposta", ""), row.get("descricao", ""),
            row.get("odd", ""),
        ])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


async def upsert_bilhetes(
    rows: list[dict], confianca: float | None = None
) -> tuple[int, int, list[int], list[str]]:
    """Retorna (inseridos, atualizados, ids, alertas)."""
    pool = await get_pool()
    ids: list[int] = []
    alertas: list[str] = []
    inseridos = 0
    atualizados = 0
    # Rastreia hashes sem ID no lote atual para detectar sobreposição de prints
    seen_no_id: dict[str, int] = {}  # hash → índice da primeira ocorrência

    async with pool.acquire() as conn:
        for i, row in enumerate(rows):
            codigo = row.get("codigo_bilhete", "").strip()
            sig = _assinatura(row)

            # Detecção de sobreposição de prints (apenas quando não há ID)
            if not codigo:
                content_key = "|".join([
                    row.get("casa", ""), row.get("parceiro", ""),
                    row.get("data", ""), row.get("descricao", ""), row.get("odd", ""),
                ])
                ck_hash = hashlib.sha256(content_key.encode()).hexdigest()[:16]
                if ck_hash in seen_no_id:
                    primeiro = seen_no_id[ck_hash] + 1
                    alertas.append(
                        f"Bilhete {i + 1} idêntico ao bilhete {primeiro} (sem ID visível) — "
                        "possível sobreposição de prints. Verifique e delete o duplicado se necessário."
                    )
                else:
                    seen_no_id[ck_hash] = i

            if codigo:
                # Migração A: normaliza assinatura de linha existente com mesmo código
                await conn.execute(
                    """UPDATE bilhetes SET assinatura = $1
                       WHERE casa = $2 AND parceiro = $3
                         AND codigo_bilhete = $4 AND assinatura != $1""",
                    sig, row.get("casa", ""), row.get("parceiro", ""), codigo,
                )
                # Migração B: adota linha sem código que bate em data+aposta+stake+odd
                # (bets importadas via imagem antes do suporte a XLS)
                await conn.execute(
                    """
                    WITH candidate AS (
                        SELECT id FROM bilhetes
                        WHERE casa = $2 AND parceiro = $3
                          AND codigo_bilhete IS NULL
                          AND data = $4 AND aposta = $5 AND stake = $6 AND odd = $7
                        LIMIT 1
                    )
                    UPDATE bilhetes SET assinatura = $1, codigo_bilhete = $8
                    FROM candidate
                    WHERE bilhetes.id = candidate.id AND bilhetes.assinatura != $1
                    """,
                    sig, row.get("casa", ""), row.get("parceiro", ""),
                    row.get("data", ""), row.get("aposta", ""),
                    row.get("stake", ""), row.get("odd", ""), codigo,
                )

            resultado = row.get("resultado", "").strip() or None
            extraction_state = "resolvida" if resultado in _RESULTADOS_VALIDOS else "aberta"
            rec = await conn.fetchrow(
                """
                INSERT INTO bilhetes
                    (casa, parceiro, assinatura, codigo_bilhete, data, esporte, tipster,
                     aposta, descricao, stake, odd, resultado,
                     extraction_state, confianca)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                ON CONFLICT (casa, parceiro, assinatura) DO UPDATE SET
                    tipster          = EXCLUDED.tipster,
                    codigo_bilhete   = COALESCE(bilhetes.codigo_bilhete, EXCLUDED.codigo_bilhete),
                    resultado        = EXCLUDED.resultado,
                    extraction_state = EXCLUDED.extraction_state,
                    atualizado_em    = NOW()
                RETURNING id, (xmax = 0) AS was_inserted
                """,
                row.get("casa", ""), row.get("parceiro", ""), sig,
                codigo or None,
                row.get("data"), row.get("esporte"), row.get("tipster"),
                row.get("aposta"), row.get("descricao"),
                row.get("stake"), row.get("odd"), resultado,
                extraction_state, confianca,
            )
            if rec:
                ids.append(rec["id"])
                if rec["was_inserted"]:
                    inseridos += 1
                else:
                    atualizados += 1
    return inseridos, atualizados, ids, alertas


async def deletar_bilhetes(ids: list[int]) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM bilhetes WHERE id = ANY($1)", ids
        )
    return int(result.split()[-1])


async def list_bilhetes(
    casa: str | None = None,
    parceiro: str | None = None,
    copy_state: str | None = None,
    extraction_state: str | None = None,
    limit: int = 500,
    order: str = "asc",
) -> list[dict]:
    pool = await get_pool()
    filters, params = [], []

    for col, val in [("casa", casa), ("parceiro", parceiro),
                     ("copy_state", copy_state), ("extraction_state", extraction_state)]:
        if val is not None:
            params.append(val)
            filters.append(f"{col} = ${len(params)}")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    order_sql = "ASC" if order == "asc" else "DESC"
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM bilhetes {where} ORDER BY criado_em {order_sql} LIMIT ${len(params)}",
            *params,
        )
    return [dict(r) for r in rows]


async def marcar_copiada(ids: list[int]) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE bilhetes SET copy_state = 'copiada', atualizado_em = NOW() WHERE id = ANY($1)",
            ids,
        )
    return int(result.split()[-1])


async def marcar_pendente(ids: list[int]) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE bilhetes SET copy_state = 'pendente', atualizado_em = NOW() WHERE id = ANY($1)",
            ids,
        )
    return int(result.split()[-1])


# ── Parceiros ─────────────────────────────────────────────────────────────────

async def criar_parceiro(casa: str, nome: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO parceiros (casa, nome)
            VALUES ($1, $2)
            ON CONFLICT (casa, nome) DO UPDATE SET arquivado = FALSE
            RETURNING id, casa, nome, arquivado, criado_em
            """,
            casa, nome,
        )
    return dict(row)


async def list_parceiros(casa: str | None = None, incluir_arquivados: bool = False) -> list[dict]:
    pool = await get_pool()
    filters, params = [], []
    if casa is not None:
        params.append(casa)
        filters.append(f"casa = ${len(params)}")
    if not incluir_arquivados:
        filters.append("arquivado = FALSE")
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, casa, nome, arquivado, criado_em FROM parceiros {where} ORDER BY criado_em ASC",
            *params,
        )
    return [dict(r) for r in rows]


async def arquivar_parceiro(parceiro_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE parceiros SET arquivado = TRUE WHERE id = $1", parceiro_id
        )
    return result.split()[-1] == "1"


async def atualizar_bilhete(bilhete_id: int, campos: dict) -> bool:
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
    sql = f"UPDATE bilhetes SET {', '.join(sets)}, atualizado_em = NOW() WHERE id = ${len(params)}"
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(sql, *params)
    return result.split()[-1] == "1"


async def reativar_parceiro(parceiro_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE parceiros SET arquivado = FALSE WHERE id = $1", parceiro_id
        )
    return result.split()[-1] == "1"


async def get_codigos_existentes(codigos: list[str]) -> set[str]:
    """Retorna subset de codigos que já existem no banco."""
    if not codigos:
        return set()
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT codigo_bilhete FROM bilhetes WHERE codigo_bilhete = ANY($1::text[])",
            codigos,
        )
    return {row["codigo_bilhete"] for row in rows}

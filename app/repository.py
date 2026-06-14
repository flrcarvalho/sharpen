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
        if row["data"].lower() in ("data", "date"):
            continue
        rows.append(row)
    return rows


def _assinatura(row: dict) -> str:
    raw = "|".join([
        row.get("casa", ""), row.get("parceiro", ""),
        row.get("data", ""), row.get("aposta", ""), row.get("descricao", ""),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


async def upsert_bilhetes(rows: list[dict], confianca: float | None = None) -> int:
    pool = await get_pool()
    count = 0
    async with pool.acquire() as conn:
        for row in rows:
            sig = _assinatura(row)
            resultado = row.get("resultado", "").strip() or None
            extraction_state = "resolvida" if resultado in _RESULTADOS_VALIDOS else "aberta"
            await conn.execute(
                """
                INSERT INTO bilhetes
                    (casa, parceiro, assinatura, data, esporte, tipster,
                     aposta, descricao, stake, odd, resultado,
                     extraction_state, confianca)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                ON CONFLICT (casa, parceiro, assinatura) DO UPDATE SET
                    resultado        = EXCLUDED.resultado,
                    extraction_state = EXCLUDED.extraction_state,
                    atualizado_em    = NOW()
                """,
                row.get("casa", ""), row.get("parceiro", ""), sig,
                row.get("data"), row.get("esporte"), row.get("tipster"),
                row.get("aposta"), row.get("descricao"),
                row.get("stake"), row.get("odd"), resultado,
                extraction_state, confianca,
            )
            count += 1
    return count


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

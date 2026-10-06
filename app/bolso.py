"""Bolso por moeda: o câmbio da operação (s398, passo 6 do `docs/PLANO_MOEDA_POR_CONTA.md`).

Decisões do Feca com o Gabriel (06/10/2026):

- **A verdade é a moeda da conta.** O R$ de cada aposta é o da cotação do dia em que ela foi
  FEITA, e por isso o P/L de apostas (e o ROI de tipster e de método) não sofre com o câmbio.
- **O câmbio é da MOEDA do dono, não da casa.** Todas as casas e corretoras numa moeda formam
  um bolso só: o USDT que sai da casa A, passa pela Binance e entra na casa B nunca deixou de
  ser USDT. Transferência dentro do bolso não é evento de câmbio; só a TAXA dela é.
- **Enquanto é moeda, o câmbio está "no papel"** (muda todo dia). **Só a venda por real
  realiza**, declarada pelo dono na corretora, e daí em diante o valor trava.

Cada bolso guarda QUANTIDADE e CUSTO EM R$, por custo médio:

    entrada sem compra declarada (saldo inicial, depósito sem origem)  + qtd   + qtd × cotação do dia
    compra declarada (paguei R$ X, recebi Y)                           + Y     + X
    aposta liquidada                                                   + P/L   + P/L × cotação da aposta
    ajuste                                                             ± v     ± v × cotação do dia
    transferência casa ⇄ corretora                                     nada    nada
    taxa da transferência                                              − taxa  − taxa × médio  (custo)
    saída do bolso (saque sem destino, transferência fora da janela)   − v     − v × médio
    venda declarada (vendi Y, recebi R$ X)                             − Y     − Y × médio;  realizado = X − Y × médio

    câmbio no papel = quantidade × cotação de hoje − custo em R$

PURO: sem banco e sem rede. Quem chama carrega as cotações e passa `cot_dia(moeda, iso)`.

O que NÃO é exato, e a tela tem de dizer: saque SEM destino tira dinheiro do bolso sem dizer
para onde foi (sai pelo custo médio, e o câmbio daquela parte não se mede); dia sem cotação
entra pelo custo médio do momento e é contado em `n_sem_cotacao`.
"""
from __future__ import annotations

# Ordem dentro do MESMO dia: o que entra antes do que sai, para uma saída do dia não
# encontrar o bolso vazio e sair por um médio que ainda não existe.
_ORDEM = {"entrada": 0, "compra": 0, "pl": 1, "ajuste": 1, "transf": 2, "saida": 3, "venda": 3}
_EPS = 1e-9


def _iso(d) -> str:
    if d is None:
        return ""
    return d.isoformat() if hasattr(d, "isoformat") else str(d)[:10]


def janelas_corretora(corretora_movs: list[dict]) -> dict[tuple, str]:
    """(corretora_id, moeda) → data do saldo inicial (o corte da corretora naquela moeda).
    Sem saldo inicial a janela é aberta (''): a corretora nasceu vazia e tudo conta."""
    out: dict[tuple, tuple] = {}
    for m in corretora_movs:
        if m.get("tipo") != "inicial":
            continue
        k = (m["corretora_id"], (m.get("moeda") or "").upper())
        chave = (_iso(m.get("data")), m.get("id") or 0)
        if k not in out or chave > out[k]:
            out[k] = chave
    return {k: v[0] for k, v in out.items()}


def saldos_corretoras(corretora_movs: list[dict], transferencias: list[dict]) -> dict[tuple, float]:
    """(corretora_id, moeda) → saldo na moeda. Só conta o que está dentro da janela da
    corretora naquela moeda; o saldo inicial é o ponto de partida.

    `transferencias`: os lançamentos de Caixa com `corretora_id` (saque com destino entra
    `valor − taxa`; depósito com origem sai `valor + taxa`), com a moeda da conta."""
    jan = janelas_corretora(corretora_movs)
    ini_id: dict[tuple, int] = {}
    for m in corretora_movs:
        k = (m["corretora_id"], (m.get("moeda") or "").upper())
        if m.get("tipo") == "inicial" and _iso(m.get("data")) == jan.get(k):
            ini_id[k] = max(ini_id.get(k, 0), m.get("id") or 0)
    saldo: dict[tuple, float] = {}
    for m in corretora_movs:
        k = (m["corretora_id"], (m.get("moeda") or "").upper())
        d, v, tipo = _iso(m.get("data")), float(m.get("valor") or 0.0), m.get("tipo")
        if tipo == "inicial":
            if (m.get("id") or 0) == ini_id.get(k):
                saldo[k] = saldo.get(k, 0.0) + v
            continue
        if d < jan.get(k, ""):
            continue
        sinal = -1.0 if tipo == "venda" else 1.0
        saldo[k] = saldo.get(k, 0.0) + sinal * v
    for t in transferencias:
        k = (t["corretora_id"], (t.get("moeda") or "").upper())
        if _iso(t.get("data")) < jan.get(k, ""):
            continue
        v, taxa = float(t.get("valor") or 0.0), float(t.get("taxa") or 0.0)
        if t.get("tipo") == "saque":
            saldo[k] = saldo.get(k, 0.0) + (v - taxa)
        elif t.get("tipo") == "deposito":
            saldo[k] = saldo.get(k, 0.0) - (v + taxa)
    return {k: round(v, 2) for k, v in saldo.items()}


def _eventos(contas: list[dict], corretora_movs: list[dict],
             transferencias: list[dict]) -> list[dict]:
    """Junta os dois lados num fluxo só de eventos do bolso, cada um com a moeda.

    A transferência é PAREADA quando os dois lados estão dentro das suas janelas (a Caixa da
    casa ligada e o lançamento depois do corte dela; a corretora depois do saldo inicial dela
    naquela moeda): aí ela não move o bolso, só a taxa. Com um lado só dentro, o dinheiro
    entra ou sai do bolso por aquele lado, porque o outro já está embutido num saldo
    inicial."""
    jan = janelas_corretora(corretora_movs)
    ev: list[dict] = []
    da_casa: set = set()
    for c in contas:
        moeda = (c.get("moeda") or "BRL").upper()
        if moeda == "BRL" or not c.get("ligada"):
            continue
        for e in c.get("eventos") or []:
            if e.get("mov_id") is not None:
                da_casa.add(e["mov_id"])
    for c in contas:
        moeda = (c.get("moeda") or "BRL").upper()
        if moeda == "BRL" or not c.get("ligada"):
            continue
        for e in c.get("eventos") or []:
            tipo, v, d = e["tipo"], float(e.get("valor") or 0.0), _iso(e.get("data"))
            base = {"moeda": moeda, "data": d, "origem": c.get("rotulo") or ""}
            if tipo == "inicial":
                ev.append({**base, "tipo": "entrada", "qtd": v})
            elif tipo == "pl":
                ev.append({**base, "tipo": "pl", "qtd": v, "cot": e.get("cot")})
            elif tipo == "ajuste":
                ev.append({**base, "tipo": "ajuste", "qtd": v})
            elif tipo in ("deposito", "saque"):
                cid = e.get("corretora_id")
                par = cid is not None and d >= jan.get((cid, moeda), "")
                taxa = float(e.get("taxa") or 0.0)
                if par:
                    ev.append({**base, "tipo": "transf", "qtd": 0.0, "taxa": taxa})
                elif tipo == "deposito":
                    ev.append({**base, "tipo": "entrada", "qtd": v})
                else:
                    ev.append({**base, "tipo": "saida", "qtd": v,
                               "sem_destino": cid is None})
    for t in transferencias:
        moeda = (t.get("moeda") or "").upper()
        cid, d = t["corretora_id"], _iso(t.get("data"))
        if d < jan.get((cid, moeda), "") or t.get("mov_id") in da_casa:
            continue
        v, taxa = float(t.get("valor") or 0.0), float(t.get("taxa") or 0.0)
        base = {"moeda": moeda, "data": d, "origem": t.get("rotulo") or ""}
        if t.get("tipo") == "saque":
            ev.append({**base, "tipo": "entrada", "qtd": v - taxa})
        elif t.get("tipo") == "deposito":
            ev.append({**base, "tipo": "saida", "qtd": v + taxa, "sem_destino": False})
    for m in corretora_movs:
        moeda = (m.get("moeda") or "").upper()
        k = (m["corretora_id"], moeda)
        d, v, tipo = _iso(m.get("data")), float(m.get("valor") or 0.0), m.get("tipo")
        base = {"moeda": moeda, "data": d, "origem": m.get("rotulo") or ""}
        if tipo == "inicial":
            if d == jan.get(k):
                ev.append({**base, "tipo": "entrada", "qtd": v})
            continue
        if d < jan.get(k, ""):
            continue
        if tipo == "compra":
            ev.append({**base, "tipo": "compra", "qtd": v, "brl": float(m.get("valor_brl") or 0.0)})
        elif tipo == "venda":
            ev.append({**base, "tipo": "venda", "qtd": v, "brl": float(m.get("valor_brl") or 0.0),
                       "obs": m.get("obs") or ""})
        elif tipo == "ajuste":
            ev.append({**base, "tipo": "ajuste", "qtd": v})
    return ev


def montar_bolsos(contas: list[dict], corretora_movs: list[dict],
                  transferencias: list[dict], cot_dia, cot_hoje: dict) -> dict[str, dict]:
    """O bolso de cada moeda do dono. Ver o cabeçalho do módulo para a régua.

    `contas`: as contas de casa, cada uma com `moeda`, `ligada` (Caixa ativa), `banca` (na
    moeda) e `eventos` (de `repository._caixa_projetar(..., eventos=[])`). Conta em outra
    moeda SEM Caixa não entra (o saldo dela não é conhecido) e é contada.
    `cot_dia(moeda, iso)` → R$ por unidade naquele dia, ou None. `cot_hoje[moeda]` idem, hoje.
    """
    bolsos: dict[str, dict] = {}

    def b(moeda):
        return bolsos.setdefault(moeda, {
            "moeda": moeda, "qtd": 0.0, "custo_brl": 0.0,
            "realizado_brl": 0.0, "taxas_brl": 0.0,
            "realizados": [], "taxas": [],
            "n_sem_destino": 0, "qtd_sem_destino": 0.0, "n_sem_cotacao": 0,
            "contas": 0, "contas_sem_caixa": 0, "saldo_casas": 0.0, "saldo_corretoras": 0.0,
        })

    for c in contas:
        moeda = (c.get("moeda") or "BRL").upper()
        if moeda == "BRL":
            continue
        x = b(moeda)
        if c.get("ligada"):
            x["contas"] += 1
            x["saldo_casas"] += float(c.get("banca") or 0.0)
        else:
            x["contas_sem_caixa"] += 1
    for (cid, moeda), v in saldos_corretoras(corretora_movs, transferencias).items():
        b(moeda)["saldo_corretoras"] += v

    eventos = _eventos(contas, corretora_movs, transferencias)
    eventos.sort(key=lambda e: (e["data"], _ORDEM.get(e["tipo"], 9)))
    for e in eventos:
        x = b(e["moeda"])
        q = e["qtd"]

        def medio():
            if x["qtd"] > _EPS:
                return x["custo_brl"] / x["qtd"]
            c = cot_dia(e["moeda"], e["data"])
            return c or 0.0

        def preco_do_dia():
            c = cot_dia(e["moeda"], e["data"])
            if not c:
                x["n_sem_cotacao"] += 1
                return medio()
            return c

        t = e["tipo"]
        if t == "entrada":
            x["custo_brl"] += q * preco_do_dia()
            x["qtd"] += q
        elif t == "compra":
            x["custo_brl"] += e["brl"]
            x["qtd"] += q
        elif t == "pl":
            cot = float(e.get("cot") or 0.0) or preco_do_dia()
            x["custo_brl"] += q * cot
            x["qtd"] += q
        elif t == "ajuste":
            x["custo_brl"] += q * preco_do_dia()
            x["qtd"] += q
        elif t == "transf":
            taxa = float(e.get("taxa") or 0.0)
            if taxa > 0:
                brl = taxa * medio()
                x["custo_brl"] -= brl
                x["qtd"] -= taxa
                x["taxas_brl"] += brl
                x["taxas"].append({"data": e["data"], "brl": round(brl, 2),
                                   "qtd": round(taxa, 2), "origem": e["origem"]})
        elif t == "saida":
            x["custo_brl"] -= q * medio()
            x["qtd"] -= q
            if e.get("sem_destino"):
                x["n_sem_destino"] += 1
                x["qtd_sem_destino"] += q
        elif t == "venda":
            custo = q * medio()
            ganho = e["brl"] - custo
            x["custo_brl"] -= custo
            x["qtd"] -= q
            x["realizado_brl"] += ganho
            x["realizados"].append({"data": e["data"], "brl": round(ganho, 2),
                                    "qtd": round(q, 2), "recebido": round(e["brl"], 2),
                                    "origem": e["origem"]})

    for moeda, x in bolsos.items():
        hoje = cot_hoje.get(moeda)
        x["cot_hoje"] = hoje
        x["medio"] = round(x["custo_brl"] / x["qtd"], 6) if x["qtd"] > _EPS else None
        x["valor_brl"] = round(x["qtd"] * hoje, 2) if hoje else None
        x["papel_brl"] = round(x["qtd"] * hoje - x["custo_brl"], 2) if hoje else None
        for k in ("qtd", "custo_brl", "realizado_brl", "taxas_brl", "qtd_sem_destino",
                  "saldo_casas", "saldo_corretoras"):
            x[k] = round(x[k], 2)
        # O bolso tem de fechar com o que as casas e as corretoras dizem ter. Se não fecha,
        # algum lado do mesmo dinheiro ficou fora de uma janela (o que a tela avisa).
        x["fecha"] = abs(x["qtd"] - (x["saldo_casas"] + x["saldo_corretoras"])) < 0.05
    return bolsos

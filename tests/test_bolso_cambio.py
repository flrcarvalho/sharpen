"""Bolso de câmbio por moeda (s398, passo 6 do `docs/PLANO_MOEDA_POR_CONTA.md`).

Decisões do Feca com o Gabriel (06/10/2026): verdade na moeda da conta; aposta pela cotação
do dia em que foi feita; corretoras com transferência e taxa; o câmbio é da MOEDA do dono e
só realiza na venda por real.

O que este arquivo prova, executando o código real (`app/bolso.py` e
`repository._caixa_projetar` com `eventos`):

A. o exemplo que abriu a frente: 100 USDT a 5, aposta de odd 2 ganha a 5, USDT a 4,5 hoje
   → apostas +R$ 500, câmbio no papel −R$ 100, o bolso vale R$ 900;
B. transferência casa → corretora com os dois lados na janela NÃO move o bolso, só a taxa
   (que sai pelo custo médio e vira custo);
C. a venda realiza contra o custo MÉDIO, nunca contra a cotação do dia;
D. saque sem destino sai pelo médio e é contado; transferência com um lado fora da janela
   entra ou sai do bolso pelo lado que está dentro;
E. compra declarada entra pelo R$ pago; dia sem cotação entra pelo médio e é contado;
F. no mesmo dia, o que entra vem antes do que sai;
G. a Caixa entrega ao bolso a MESMA janela da projeção: o saldo do corte com o que estava
   preso, só os lançamentos depois do corte, e o P/L de cada aposta com a cotação dela.

O que NÃO está coberto: o SQL do `cambio_visao` (só o CI com banco) e a tela.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
BOLSO = RAIZ / "app" / "bolso.py"
REPO = RAIZ / "app" / "repository.py"

COT = {("USDT", "2026-10-01"): 5.0, ("USDT", "2026-10-02"): 5.0,
       ("USDT", "2026-10-03"): 5.2, ("USDT", "2026-10-04"): 5.1,
       ("USDT", "2026-10-05"): 4.8}


def cot_dia(moeda, iso):
    return COT.get((moeda, iso))


HOJE = {"USDT": 4.5}


def conta(eventos, banca, ligada=True, moeda="USDT", rotulo="Betpanda · Feca"):
    return {"moeda": moeda, "ligada": ligada, "banca": banca, "eventos": eventos,
            "rotulo": rotulo}


def _falhas_bolso(mod) -> list[str]:
    f = []

    def chk(cond, msg):
        if not cond:
            f.append(msg)

    def mb(*a):
        try:
            return mod.montar_bolsos(*a)
        except Exception as e:  # mutação que quebra também é detectada
            f.append("erro: " + repr(e))
            return {"USDT": {}}

    # A. o exemplo do Feca
    # A aposta foi FEITA com o USDT a 5 e o evento é do dia 03 (5,2): manda a cotação dela.
    a = mb([conta([{"tipo": "inicial", "data": "2026-10-01", "valor": 100.0},
                   {"tipo": "pl", "data": "2026-10-03", "valor": 100.0, "cot": 5.0}], 200.0)],
           [], [], cot_dia, HOJE)["USDT"]
    chk(a.get("qtd") == 200.0 and a.get("custo_brl") == 1000.0, f"A: 200 USDT custando R$ 1.000: {a}")
    chk(a.get("valor_brl") == 900.0 and a.get("papel_brl") == -100.0, f"A: vale 900, papel −100: {a}")
    chk(a.get("realizado_brl") == 0.0, "A: nada realizado sem venda")
    chk(a.get("fecha") is True, "A: o bolso fecha com a banca da casa")

    # B. transferência pareada com taxa
    base = [{"tipo": "inicial", "data": "2026-10-01", "valor": 200.0}]
    saque = {"tipo": "saque", "data": "2026-10-03", "valor": 50.0, "mov_id": 9,
             "corretora_id": 3, "taxa": 1.0}
    tr = [{"mov_id": 9, "corretora_id": 3, "tipo": "saque", "data": "2026-10-03",
           "valor": 50.0, "taxa": 1.0, "moeda": "USDT"}]
    b = mb([conta(base + [saque], 150.0)], [], tr, cot_dia, HOJE)["USDT"]
    chk(b.get("qtd") == 199.0, f"B: só a taxa sai do bolso: {b.get('qtd')}")
    chk(b.get("custo_brl") == 995.0, f"B: a taxa sai pelo médio (5), não pela cotação do dia (5,2): {b.get('custo_brl')}")
    chk(b.get("taxas_brl") == 5.0 and len(b.get("taxas") or []) == 1, f"B: a taxa vira custo: {b.get('taxas_brl')}")
    chk(b.get("saldo_corretoras") == 49.0 and b.get("fecha") is True, f"B: chegou 49 na corretora: {b}")

    # C. venda realiza contra o médio
    venda = [{"id": 1, "corretora_id": 3, "tipo": "venda", "data": "2026-10-04", "moeda": "USDT",
              "valor": 49.0, "valor_brl": 230.0}]
    c = mb([conta(base + [saque], 150.0)], venda, tr, cot_dia, HOJE)["USDT"]
    chk(c.get("realizado_brl") == -15.0, f"C: 230 − 49 × 5 = −15: {c.get('realizado_brl')}")
    chk(c.get("qtd") == 150.0 and c.get("custo_brl") == 750.0, f"C: sobra 150 a 5: {c}")
    chk(c.get("saldo_corretoras") == 0.0 and c.get("fecha") is True, "C: a corretora zera")

    # D. saque sem destino e transferência com um lado fora da janela
    d = mb([conta(base + [{"tipo": "saque", "data": "2026-10-03", "valor": 50.0, "mov_id": 8}],
                  150.0)], [], [], cot_dia, HOJE)["USDT"]
    chk(d.get("n_sem_destino") == 1 and d.get("qtd_sem_destino") == 50.0, "D: saque sem destino é contado")
    chk(d.get("custo_brl") == 750.0, f"D: e sai pelo médio: {d.get('custo_brl')}")
    ini_depois = [{"id": 2, "corretora_id": 3, "tipo": "inicial", "data": "2026-10-04",
                   "moeda": "USDT", "valor": 49.0}]
    d2 = mb([conta(base + [saque], 150.0)], ini_depois, tr, cot_dia, HOJE)["USDT"]
    chk(d2.get("n_sem_destino") == 0, "D: destino fora da janela não é 'sem destino'")
    chk(d2.get("qtd") == 199.0 and d2.get("saldo_corretoras") == 49.0 and d2.get("fecha") is True,
        f"D: o lado da corretora entra pelo saldo inicial dela: {d2}")
    chk(abs(d2.get("custo_brl", 0) - (1000.0 - 250.0 + 49.0 * 5.1)) < 0.01,
        f"D: sai pelo médio na casa e entra pela cotação do dia na corretora: {d2.get('custo_brl')}")
    sem_caixa = mb([conta([], 0.0, ligada=False)], [], tr, cot_dia, HOJE)["USDT"]
    chk(sem_caixa.get("contas_sem_caixa") == 1, "D: conta sem Caixa é contada")
    chk(sem_caixa.get("qtd") == 49.0 and abs(sem_caixa.get("custo_brl", 0) - 49.0 * 5.2) < 0.01,
        f"D: casa sem Caixa → a corretora recebe pela cotação do dia: {sem_caixa}")
    antes_do_ini = mb([conta([], 0.0, ligada=False)], ini_depois, tr, cot_dia, HOJE)["USDT"]
    chk(antes_do_ini.get("qtd") == 49.0 and abs(antes_do_ini.get("custo_brl", 0) - 49.0 * 5.1) < 0.01,
        f"D: transferência anterior ao saldo inicial da corretora já está nele: {antes_do_ini}")

    # E. compra declarada e dia sem cotação
    compra = [{"id": 3, "corretora_id": 3, "tipo": "compra", "data": "2026-10-02", "moeda": "USDT",
               "valor": 100.0, "valor_brl": 530.0}]
    e = mb([], compra, [], cot_dia, HOJE)["USDT"]
    chk(e.get("custo_brl") == 530.0 and e.get("qtd") == 100.0, f"E: a compra entra pelo R$ pago: {e}")
    e2 = mb([conta(base + [{"tipo": "deposito", "data": "2026-09-01", "valor": 10.0, "mov_id": 7}],
                   210.0)], [], [], cot_dia, HOJE)["USDT"]
    chk(e2.get("n_sem_cotacao") == 1, "E: dia sem cotação é contado")

    # F. ordem no mesmo dia: a entrada vem antes da saída. Uma compra antes (médio 6) faz o
    # médio do dia (5,33) diferir do de ontem: sair antes de entrar daria outro custo.
    antes = [{"id": 4, "corretora_id": 3, "tipo": "compra", "data": "2026-09-30", "moeda": "USDT",
              "valor": 100.0, "valor_brl": 600.0}]
    f_ = mb([conta([{"tipo": "saque", "data": "2026-10-01", "valor": 50.0, "mov_id": 1},
                    {"tipo": "inicial", "data": "2026-10-01", "valor": 200.0}], 150.0)],
            antes, [], cot_dia, HOJE)["USDT"]
    chk(abs(f_.get("custo_brl", 0) - (1600.0 - 50.0 * 1600.0 / 300.0)) < 0.01,
        f"F: o saque do dia sai pelo médio depois da entrada do dia: {f_.get('custo_brl')}")

    # BRL fica fora
    chk("BRL" not in mb([conta([{"tipo": "inicial", "data": "2026-10-01", "valor": 5.0}], 5.0,
                               moeda="BRL")], [], [], cot_dia, HOJE), "conta em R$ não tem bolso")
    return f


def _falhas_caixa(mod) -> list[str]:
    """G: os eventos que a Caixa entrega são a janela DELA."""
    f = []

    def chk(cond, msg):
        if not cond:
            f.append(msg)

    movs = [
        {"id": 1, "tipo": "inicial", "data": "2026-10-02", "valor": 100.0,
         "abertas_corte": [21], "criado_em": "2026-10-02T10:00:00"},
        {"id": 2, "tipo": "deposito", "data": "2026-10-01", "valor": 30.0, "criado_em": "x"},
        {"id": 3, "tipo": "saque", "data": "2026-10-03", "valor": 40.0, "corretora_id": 5,
         "taxa": 1.0, "criado_em": "x"},
        {"id": 4, "tipo": "conferencia", "data": "2026-10-03", "valor": 1.0, "criado_em": "x"},
    ]
    apostas = [
        {"id": 21, "stake": "50,00", "stake_orig": 10.0, "moeda": "USDT", "cotacao": 5.0,
         "odd": "2,00", "resultado": "W", "data": "03/10/2026"},
        {"id": 22, "stake": "52,00", "stake_orig": 10.0, "moeda": "USDT", "cotacao": 5.2,
         "odd": "3,00", "resultado": "L", "data": "04/10/2026"},
        {"id": 23, "stake": "50,00", "stake_orig": 10.0, "moeda": "USDT", "cotacao": 5.0,
         "odd": "2,00", "resultado": "W", "data": "01/10/2026"},
    ]
    ev = []
    try:
        res = mod._caixa_projetar(movs, apostas, "USDT", "Betpanda", ev)
    except Exception as e:
        return ["erro: " + repr(e)]
    tipos = sorted(e["tipo"] for e in ev)
    chk(tipos == ["inicial", "pl", "pl", "saque"], f"G: eventos da janela: {tipos}")
    ini = [e for e in ev if e["tipo"] == "inicial"]
    chk(ini and ini[0]["valor"] == 110.0 and ini[0]["data"] == "2026-10-02",
        f"G: o corte entra com o que estava preso (100 + 10): {ini}")
    sq = [e for e in ev if e["tipo"] == "saque"]
    chk(sq and sq[0]["corretora_id"] == 5 and sq[0]["taxa"] == 1.0 and sq[0]["mov_id"] == 3,
        f"G: o saque leva a corretora e a taxa: {sq}")
    pls = sorted((e["valor"], e["cot"]) for e in ev if e["tipo"] == "pl")
    chk(pls == [(-10.0, 5.2), (10.0, 5.0)], f"G: P/L na moeda com a cotação da aposta: {pls}")
    total = sum(e["valor"] * (-1 if e["tipo"] == "saque" else 1) for e in ev)
    chk(abs(total - res["banca"]) < 0.01, f"G: os eventos somam a banca ({total} × {res['banca']})")
    return f


def _carregar(path: Path, nome: str):
    spec = importlib.util.spec_from_file_location(nome, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bolso():
    sys.path.insert(0, str(RAIZ / "app"))
    import bolso
    assert _falhas_bolso(bolso) == []


def test_caixa_entrega_a_janela_ao_bolso():
    import repository
    assert _falhas_caixa(repository) == []


MUTACOES_BOLSO = [
    ("a transferência pareada move o bolso",
     '                par = cid is not None and d >= jan.get((cid, moeda), "")',
     '                par = False'),
    ("a taxa sai pela cotação do dia",
     '                brl = taxa * medio()', '                brl = taxa * preco_do_dia()'),
    ("a venda realiza contra a cotação do dia",
     '            custo = q * medio()', '            custo = q * preco_do_dia()'),
    ("a aposta entra pela cotação do dia, não pela dela",
     '            cot = float(e.get("cot") or 0.0) or preco_do_dia()', '            cot = preco_do_dia()'),
    ("no mesmo dia a saída vem antes",
     '_ORDEM = {"entrada": 0, "compra": 0, "pl": 1, "ajuste": 1, "transf": 2, "saida": 3, "venda": 3}',
     '_ORDEM = {"entrada": 4, "compra": 0, "pl": 1, "ajuste": 1, "transf": 2, "saida": 3, "venda": 3}'),
    ("a janela da corretora é ignorada",
     '        if d < jan.get((cid, moeda), "") or t.get("mov_id") in da_casa:',
     '        if t.get("mov_id") in da_casa:'),
    ("o saque sem destino não é contado",
     '                x["n_sem_destino"] += 1', '                pass'),
    ("a compra entra pela cotação do dia",
     '            x["custo_brl"] += e["brl"]', '            x["custo_brl"] += q * preco_do_dia()'),
    ("dia sem cotação não é contado",
     '                x["n_sem_cotacao"] += 1', '                pass'),
    ("a corretora perde a taxa da transferência",
     '            saldo[k] = saldo.get(k, 0.0) + (v - taxa)', '            saldo[k] = saldo.get(k, 0.0) + v'),
    ("o papel usa o custo médio em vez da cotação de hoje",
     '        x["papel_brl"] = round(x["qtd"] * hoje - x["custo_brl"], 2) if hoje else None',
     '        x["papel_brl"] = 0.0'),
]

MUTACOES_CAIXA = [
    ("o corte entra sem o que estava preso",
     '                        "valor": out["inicial"] + out["preso_corte"]})',
     '                        "valor": out["inicial"]})'),
    ("o P/L vai sem a cotação da aposta",
     '                            "cot": a.get("cotacao")})', '                            "cot": None})'),
    ("o saque perde a corretora",
     '                            "mov_id": m.get("id"), "corretora_id": m.get("corretora_id"),',
     '                            "mov_id": m.get("id"), "corretora_id": None,'),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES_BOLSO, ids=[m[0] for m in MUTACOES_BOLSO])
def test_mutacoes_do_bolso_sao_detectadas(tmp_path, titulo, de, para):
    src = BOLSO.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única ({src.count(de)})"
    alvo = tmp_path / "bolso_mutado.py"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    assert _falhas_bolso(_carregar(alvo, "bolso_mutado")), f"a mutação «{titulo}» passou despercebida"


@pytest.mark.parametrize("titulo,de,para", MUTACOES_CAIXA, ids=[m[0] for m in MUTACOES_CAIXA])
def test_mutacoes_da_caixa_sao_detectadas(tmp_path, titulo, de, para):
    src = REPO.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única ({src.count(de)})"
    alvo = tmp_path / "repository_mutado.py"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    assert _falhas_caixa(_carregar(alvo, "repository_mutado")), f"a mutação «{titulo}» passou despercebida"

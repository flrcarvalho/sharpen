"""Checador determinístico de conformidade da coluna Descrição.

Fonte de verdade: `global/MASTER_DESCRICAO_2026.md` (§3 separadores, §4/§5 confronto,
§11 Over/Under em inglês, §12.1 sufixo+confronto OBRIGATÓRIOS p/ marcador/props,
§17 conteúdo proibido, §19 validação final).

É a rede "indo pra frente": roda SEM IA, sem custo, em microssegundos. Usado (a) nos
testes (`tests/test_descricao.py` + `golden_set/descricoes.jsonl`) como backtest de
regressão, e (b) como aviso suave no fluxo de extração (`analisar_extracao`) — nunca
bloqueia salvar; só sinaliza pro operador revisar.

Filosofia: ALTA PRECISÃO (poucos falsos positivos). Só marca o que o MASTER declara
proibido/obrigatório de forma inequívoca. Regras que não dá pra checar deterministicamente
(confronto inventado, ordem das seleções) ficam de fora — são responsabilidade da IA.

`checar_descricao(aposta, descricao) -> list[Problema]`  (lista vazia = conforme).
Cada Problema tem `nivel` ('erro' | 'aviso'), `regra` (slug) e `msg` (texto pt-BR).
"""
import re
from typing import NamedTuple


class Problema(NamedTuple):
    nivel: str   # 'erro' (viola o MASTER) | 'aviso' (permitido, mas suspeito)
    regra: str   # slug curto p/ agrupar/testar
    msg: str     # texto legível pro operador


# Famílias em que o confronto é OBRIGATÓRIO (MASTER_DESCRICAO §12.1/§12.2/§12.3):
# jogador-para-marcar, assistência e player props. Nelas, descrição sem [Confronto]
# colapsa bilhetes distintos → é o bug que a recuperação pós-SharpenUp atacou.
_FAMILIA_CONFRONTO_OBRIG = ("anytime", "marcador", "assist", "player", "props")

# Grupos entre colchetes = confrontos (no MASTER, colchete só embrulha confronto).
_RE_CONFRONTO = re.compile(r"\[([^\[\]]*)\]")
# Separadores de confronto PROIBIDOS (§5): x, vs, @, hífen — com espaços laterais.
_RE_SEP_ERRADO = re.compile(r"\s(vs|x|@|-)\s", re.IGNORECASE)
# Over/Under em português (§11): tem de vir em inglês.
_RE_OU_PT = re.compile(r"\b(mais de|menos de|acima de|abaixo de)\b", re.IGNORECASE)
# Conteúdo proibido (§17): dinheiro, data, hora.
_RE_DINHEIRO = re.compile(r"R\$|\bUS\$", re.IGNORECASE)
_RE_DATA = re.compile(r"\b\d{1,2}/\d{1,2}(/\d{2,4})?\b")
_RE_HORA = re.compile(r"\b\d{1,2}:\d{2}\b")


def _familia_marcador_props(aposta: str) -> bool:
    a = (aposta or "").strip().lower()
    return any(k in a for k in _FAMILIA_CONFRONTO_OBRIG)


def checar_descricao(aposta: str, descricao: str) -> list[Problema]:
    """Valida uma descrição contra o MASTER_DESCRICAO. Vazio = conforme.

    Não levanta exceção. Descrição vazia devolve [] (linha incompleta é tratada por
    `analisar_extracao`/`validar_linhas`, não aqui).
    """
    d = (descricao or "").strip()
    if not d:
        return []

    problemas: list[Problema] = []

    # ── ERROS (violam o MASTER de forma inequívoca) ──────────────────────────
    # §3: separadores proibidos entidade↔mercado.
    if "|" in d:
        problemas.append(Problema("erro", "separador-proibido", "usa '|' — separador entidade↔mercado é ' - ' (§3)"))
    if "  " in d:
        problemas.append(Problema("erro", "espaco-duplo", "tem espaço duplo — proibido (§3)"))

    # §17: conteúdo proibido na descrição.
    if _RE_DINHEIRO.search(d):
        problemas.append(Problema("erro", "conteudo-proibido", "contém valor monetário (R$/US$) — proibido na descrição (§17)"))
    if _RE_DATA.search(d):
        problemas.append(Problema("erro", "conteudo-proibido", "contém data — proibido na descrição (§17)"))
    if _RE_HORA.search(d):
        problemas.append(Problema("erro", "conteudo-proibido", "contém horário — proibido na descrição (§17)"))

    # §11: Over/Under tem de estar em inglês.
    if _RE_OU_PT.search(d):
        problemas.append(Problema("erro", "over-under-pt", "Over/Under em português — converter p/ inglês (§11)"))

    # §4/§5: cada confronto [A v B] com separador ' v '. Colchete com separador errado = erro.
    confrontos = _RE_CONFRONTO.findall(d)
    for c in confrontos:
        tem_v = re.search(r"\sv\s", c) is not None
        if not tem_v and _RE_SEP_ERRADO.search(c):
            problemas.append(Problema("erro", "confronto-separador", f"confronto [{c}] usa separador errado — só ' v ' (§5)"))
        elif not tem_v:
            problemas.append(Problema("aviso", "confronto-malformado", f"confronto [{c}] sem ' v ' — conferir (§4)"))

    # ── AVISOS (permitido como fallback, mas suspeito de colapso) ─────────────
    # §8+§12.1: marcador/props SEM confronto = fallback raro. Sinaliza p/ revisão.
    if not confrontos and _familia_marcador_props(aposta):
        problemas.append(Problema("aviso", "sem-confronto", "marcador/props sem [Confronto] — obrigatório salvo fallback raro (§12.1)"))

    return problemas


def resumo_lote(rows: list[dict]) -> dict:
    """Agrega o checador sobre um lote extraído. Devolve contagens p/ o rail de avisos.

    {com_erro, com_aviso, exemplos: [ {linha, aposta, descricao, problemas:[msg,...]} ]}.
    'linha' é 1-based na lista recebida. Só os 5 primeiros exemplos (o rail é enxuto).
    """
    com_erro = com_aviso = 0
    exemplos: list[dict] = []
    for i, r in enumerate(rows, 1):
        probs = checar_descricao(r.get("aposta", ""), r.get("descricao", ""))
        if not probs:
            continue
        tem_erro = any(p.nivel == "erro" for p in probs)
        if tem_erro:
            com_erro += 1
        else:
            com_aviso += 1
        if len(exemplos) < 5:
            exemplos.append({
                "linha": i,
                "aposta": r.get("aposta", ""),
                "descricao": r.get("descricao", ""),
                "problemas": [p.msg for p in probs],
            })
    return {"com_erro": com_erro, "com_aviso": com_aviso, "exemplos": exemplos}

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
import unicodedata
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


# ── Fidelidade ao bloco cru (s302) ────────────────────────────────────────────
# O checador acima olha a FORMA da descrição. Esta metade olha a PROCEDÊNCIA: a
# descrição pertence mesmo ao bilhete daquele código?
#
# O caso que abriu a regra (s302, Betfair O/…/0001941): o robô mandou
# `Norwich x Burnley · Mais/Menos de 3,5 Cartões` e a IA gravou
# `Matthew Dennant [Norwich v Burnley]`, esporte Dardos, categoria ML — a seleção do
# bilhete VIZINHO no mesmo chunk. A linha é impecável de forma: separador certo, sem
# conteúdo proibido, confronto bem formado com ' v '. `checar_descricao` passa nela
# sem um arranhão, e nada mais no sistema comparava a linha com o texto que a gerou.
#
# A conferência é possível porque a tradução NÃO INVENTA NOME. Ela traduz rótulo de
# mercado (`Mais de` → `Over`), canoniza separador e escolhe categoria — mas time,
# jogador e competição são copiados. Então: **todo nome próprio da descrição tem de
# existir no bloco cru daquele código**. O mesmo vale para a LINHA da aposta (o
# decimal do handicap/total): `Under 1.5 Rounds` num bilhete cujo bloco não contém
# `1.5` é número inventado, e número inventado muda o que foi apostado.
#
# ALTA PRECISÃO por desenho, medido sobre a sombra inteira (1.058 bilhetes com linha
# no banco, 11 casas): 1.051 passam. Das 7 reprovações, 6 eram erro real de conteúdo.
# É gate de AVISO e de repescagem — nunca bloqueia salvar.
#
# O QUE ELE NÃO PEGA, e está aqui escrito para o verde não virar promessa falsa:
#   • troca entre bilhetes que compartilham os mesmos nomes (duas apostas no mesmo
#     jogo trocadas entre si passam: os nomes existem nos dois blocos);
#   • rótulo de mercado traduzido para a categoria errada (`Vence o 3º Set` virando
#     ML) — ali nenhum token é estranho ao bloco, só falta um. É o buraco que a regra
#     de período do `MASTER_DESCRICAO §12.8` fecha, por outro caminho;
#   • bilhete sem código: sem código não há bloco para comparar, e a função devolve [].

# Vocabulário que a TRADUÇÃO introduz legitimamente — vem do MASTER, não da casa.
# Palavra daqui nunca é cobrada do bloco cru. Manter enxuto: cada entrada é um nome
# que o gate deixa de conferir.
_VOCAB_TRADUCAO = frozenset("""
over under v e de do da no na o a em por com sem ao aos das dos
gols gol cartoes cartao escanteios escanteio pontos ponto sets set games game
rounds round chutes chute assistencias assistencia rebotes rebote roubos faltas
triplos cestas aces quarto quartos tempo periodo half inning corridas wickets
batidas handicap mais menos acima abaixo total totais individual equipe ambos
nenhum nenhuma sim nao race primeiro segundo terceiro ultimo proximo marcar
marcador vencedor vence empate casa fora visitante mandante prorrogacao
penaltis penalties tie breaks vitoria derrota submissao nocaute decisao dupla
chance resultado impedimentos outros classificacao finalizacoes desarmes defesas
legs metade feminino masculino women men am reb ast pts min
""".split())

# Tokens alfabéticos de 3+ letras. Hífen, apóstrofo, `&` e ponto ficam DENTRO do
# token: `Al-Hilal`, `Brighton & Hove`, `St Patrick's` são um nome, não três.
_RE_TOKEN_NOME = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'&.\-]{2,}")
# Só o decimal: é a LINHA da aposta. Inteiro solto fica de fora — a tradução o
# introduz legitimamente (`Segundo Tempo` → `2º Tempo`, `Race 7`).
_RE_DECIMAL = re.compile(r"\d+[.,]\d+")


def _fold(s: str) -> str:
    """Minúscula, sem acento, com as três aspas agudas unificadas.

    O acento agudo tipográfico é armadilha real: a Pinnacle escreve `St Patrick´s`
    (U+00B4) e a IA devolve `St Patrick's` (U+0027). Sem unificar, o gate acusa nome
    inventado num bilhete perfeito.
    """
    s = (s or "").replace("\u00b4", "'").replace("\u2019", "'").replace("`", "'")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _no_bloco(token: str, bloco: str) -> bool:
    """O token aparece no bloco cru, tolerando as variações que a casa faz no NOME.

    Três tolerâncias, todas medidas na sombra e todas necessárias — tirar qualquer
    uma reintroduz falso positivo em bilhete correto:
      • hífen com espaços: a 1xBet escreve `Ararat - Armênia`, a IA `Ararat-Armênia`;
      • hífen ausente: `Al-Ahli` × `Al Ahli`;
      • plural: a 1xBet escreve `Tiro de meta`, a IA `Tiros de Meta`.
    """
    if token in bloco:
        return True
    if "-" in token and (token.replace("-", " - ") in bloco or token.replace("-", " ") in bloco):
        return True
    for sufixo in ("es", "s"):
        if token.endswith(sufixo) and len(token) > len(sufixo) + 2:
            if token[: -len(sufixo)] in bloco:
                return True
    return False


def checar_fidelidade(descricao: str, bruto: str) -> list[Problema]:
    """A descrição pertence ao bilhete cujo bloco cru é `bruto`? Vazio = pertence.

    Função PURA, sem I/O, microssegundos. `bruto` vazio devolve [] — sem bloco não há
    o que comparar, e calar é a resposta certa (o gate nunca inventa suspeita).
    """
    d = (descricao or "").strip()
    b = (bruto or "").strip()
    if not d or not b:
        return []

    fb = _fold(b)
    fb_num = fb.replace(",", ".")
    problemas: list[Problema] = []

    fora = []
    for tok in _RE_TOKEN_NOME.findall(d):
        ft = _fold(tok)
        if ft in _VOCAB_TRADUCAO or _no_bloco(ft, fb):
            continue
        if ft not in fora:
            fora.append(tok)
    if fora:
        problemas.append(Problema(
            "erro", "nome-fora-do-bloco",
            "nome não existe no bilhete: " + ", ".join(f"'{t}'" for t in fora[:5])
            + " — descrição pode ser de OUTRO bilhete"))

    linhas = []
    for num in _RE_DECIMAL.findall(d):
        if num.replace(",", ".") not in fb_num and num not in linhas:
            linhas.append(num)
    if linhas:
        problemas.append(Problema(
            "erro", "linha-fora-do-bloco",
            "linha da aposta não existe no bilhete: " + ", ".join(f"'{n}'" for n in linhas[:5])))

    return problemas

"""Fase 7 (s438; Feca, 01/11/2026): TODA exclusão de aposta passa pela lixeira.

A tela de Extração apagava de vez (`deletar_bilhetes`): em 31/10 a Shuffle inteira do Gabriel
sumiu assim, sem rastro, e com ela a prova do que estava errado na base (a Caixa de 17/10 tinha
divergido US$ 556). Este gate lê o código do app (AST, sem banco) e falha se aparecer um
`DELETE FROM bilhetes` fora das funções que GUARDAM a linha:
  • `repository._mover_para_lixeira` (Extração, "Desfazer análise", linha única, Polymarket);
  • `repository.excluir_bilhetes_lote` (Base Completa / Em Aberto, `lixeira_bilhetes`);
  • `repository.excluir_parceiro` (a conta inteira, `lixeira_contas`).
E confere que as duas exclusões que apagavam de vez passam pela função da lixeira.

Não cobre: os scripts de `scripts/` (imports que se refazem, reparos com dump próprio), fora
desta fase por decisão pendente do Feca; o comportamento no banco (harness,
`test_repository_db.py`, bloco "Fase 7").
"""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
PERMITIDAS = {"_mover_para_lixeira", "excluir_bilhetes_lote", "excluir_parceiro"}


def _funcoes_com_delete() -> dict[str, set[str]]:
    """{arquivo: nomes das funções cujo corpo tem uma string com `DELETE FROM bilhetes`}."""
    out: dict[str, set[str]] = {}
    for arq in sorted(APP.glob("*.py")):
        arvore = ast.parse(arq.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for sub in ast.walk(no):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                        and "DELETE FROM bilhetes" in " ".join(sub.value.split()):
                    out.setdefault(arq.name, set()).add(no.name)
    return out


def test_nenhum_delete_de_aposta_fora_da_lixeira():
    achadas = _funcoes_com_delete()
    fora = {a: f - PERMITIDAS for a, f in achadas.items() if f - PERMITIDAS}
    assert fora == {}, f"DELETE FROM bilhetes sem lixeira: {fora}"
    assert achadas.get("repository.py", set()) <= PERMITIDAS


def _corpo(nome: str) -> ast.AST:
    arvore = ast.parse((APP / "repository.py").read_text(encoding="utf-8"))
    return next(n for n in ast.walk(arvore)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nome)


def _chama(nome: str, alvo: str) -> bool:
    return any(isinstance(n, ast.Call) and getattr(n.func, "id", None) == alvo
               for n in ast.walk(_corpo(nome)))


def test_as_exclusoes_da_tela_e_da_polymarket_passam_pela_lixeira():
    assert _chama("deletar_bilhetes", "_mover_para_lixeira")
    assert _chama("remover_bilhetes_supersedidos", "_mover_para_lixeira")


def test_a_funcao_da_lixeira_guarda_na_mesma_instrucao():
    sqls = [n.value for n in ast.walk(_corpo("_mover_para_lixeira"))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    sqls += ["".join(p.value for p in n.values if isinstance(p, ast.Constant))
             for n in ast.walk(_corpo("_mover_para_lixeira")) if isinstance(n, ast.JoinedStr)]
    assert any("DELETE FROM bilhetes" in s and "INSERT INTO lixeira_bilhetes" in s for s in sqls)

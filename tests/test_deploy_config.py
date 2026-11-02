"""s438 (Extra, queda de 25/10/2026): o deploy da Railway só recebe tráfego depois do startup.

Sem `healthcheckPath` a Railway mandava as requisições para o container novo ainda travado no
`init_db`. O teste confere o arquivo e que a rota existe e não depende do banco nem de login.
Não cobre: o comportamento da Railway em si (só a config que ela lê).
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _deploy() -> str:
    txt = (RAIZ / "railway.toml").read_text(encoding="utf-8")
    m = re.search(r"^\[deploy\]\s*$(.*?)(?=^\[|\Z)", txt, re.M | re.S)
    assert m, "railway.toml sem seção [deploy]"
    return m.group(1)


def test_railway_tem_healthcheck_no_healthz():
    dep = _deploy()
    assert re.search(r'^healthcheckPath\s*=\s*"/healthz"\s*$', dep, re.M)


def test_healthcheck_timeout_cobre_o_pior_caso_do_init_db():
    import ast
    src = (RAIZ / "app" / "database.py").read_text(encoding="utf-8")
    val = {}
    for no in ast.parse(src).body:
        if isinstance(no, ast.Assign) and isinstance(no.targets[0], ast.Name) \
                and no.targets[0].id in ("DDL_LOCK_TIMEOUT", "DDL_TENTATIVAS", "DDL_PAUSA"):
            val[no.targets[0].id] = ast.literal_eval(no.value)
    lock_s = float(val["DDL_LOCK_TIMEOUT"].rstrip("s"))
    pior = val["DDL_TENTATIVAS"] * (lock_s + val["DDL_PAUSA"])
    m = re.search(r"^healthcheckTimeout\s*=\s*(\d+)\s*$", _deploy(), re.M)
    assert m and int(m.group(1)) > pior, f"healthcheckTimeout precisa passar de {pior:.0f} s"


def test_healthz_existe_sem_auth_e_sem_banco():
    src = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    m = re.search(r'@app\.get\("/healthz"\)\s*\nasync def healthz\(\):\s*\n(.*?)\n\n', src, re.S)
    assert m, "rota /healthz sumiu ou ganhou dependência (Depends) na assinatura"
    corpo = m.group(1)
    assert "get_pool" not in corpo and "conn" not in corpo

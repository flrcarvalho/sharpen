"""Backup do Postgres de produção, com PROVA DE RESTORE.

Por que este script existe: até a s373 não havia backup nenhum do banco. Nem
`pg_dump`, nem job, nem snapshot documentado. O único caminho de volta era a
`lixeira_contas`, que cobre UMA conta excluída pela tela e vive 7 dias. Com
25.726 apostas migradas e a base de 16 donos, abrir o cadastro público sem dump
é apostar a base inteira no primeiro `DELETE` mal escrito.

**Dump que ninguém restaurou é arquivo, não backup.** Por isso o modo `--provar`
não é opcional no ritual: ele restaura o dump num banco LOCAL descartável e
compara `count(*)` tabela a tabela contra a origem. Sem essa comparação a única
coisa provada é que o arquivo existe.

Uso:
    python scripts/backup_postgres.py                  → só o dump (rápido, sem prova)
    python scripts/backup_postgres.py --provar         → dump + restore local + comparação
    python scripts/backup_postgres.py --provar-arquivo _backups/postgres/x.dump
                                                       → prova um dump que já existe
    python scripts/backup_postgres.py --listar         → o que já está gravado
    python scripts/backup_postgres.py --podar 10       → mantém os 10 mais recentes

Onde grava: `_backups/postgres/` (gitignored), ou o que estiver em
`SHARPEN_BACKUP_DIR`. **Não usa `Planilhador/Backups/`** de propósito: aquela
pasta é o snapshot de arquivo-antes-de-editar da invariante #4, é podada a cada
poucas sessões, e um dump de banco no meio dela seria apagado pela faxina.

⚠️ TRÊS TRAVAS, e as três recusam em vez de avisar:
  1. O restore só aceita alvo em **localhost/127.0.0.1**. Mesma família da trava
     do `TEST_DATABASE_URL` no `conftest.py`: o `.env` desta máquina carrega a
     URL de PRODUÇÃO, e um restore apontado para lá escreveria por cima da base
     viva.
  2. O banco de prova tem nome prefixado (`sharpen_prova_`) e é criado e
     derrubado pelo próprio script. Ele nunca restaura sobre banco preexistente.
  3. Nenhuma URL, senha ou host é impressa em lugar nenhum. O relatório fala de
     tabelas e contagens, nunca de credencial.

Requisitos: `pg_dump`/`pg_restore`/`psql` (o script acha o Postgres instalado e
usa a MAIOR versão disponível — a 9.3 que sobrou na máquina do Feca não fala com
servidor moderno) e, para `--provar`, um Postgres local de pé.
"""
import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - ambiente sem python-dotenv
    load_dotenv = None

_RAIZ = Path(__file__).resolve().parents[1]
if load_dotenv:
    load_dotenv(_RAIZ / ".env")

PREFIXO_PROVA = "sharpen_prova_"
_LOCAIS = {"localhost", "127.0.0.1", "::1", ""}


# ── Localizar as ferramentas do Postgres ─────────────────────────────────────

def _bin_postgres() -> Path:
    """Pasta `bin` do Postgres de MAIOR versão instalada.

    Procurar no PATH não basta nesta máquina: o PATH não tem nenhum, e há duas
    instalações em `Program Files` (17 e 9.3). Escolher a errada dá um erro de
    protocolo que não se parece nada com "versão velha".
    """
    from shutil import which
    achado = which("pg_dump")
    if achado:
        return Path(achado).parent

    candidatos: list[tuple[int, Path]] = []
    for raiz in (Path(r"C:\Program Files\PostgreSQL"),
                 Path(r"C:\Program Files (x86)\PostgreSQL")):
        if not raiz.is_dir():
            continue
        for d in raiz.iterdir():
            binario = d / "bin" / "pg_dump.exe"
            if binario.exists():
                m = re.match(r"^(\d+)", d.name)
                candidatos.append((int(m.group(1)) if m else 0, d / "bin"))
    if not candidatos:
        raise SystemExit(
            "pg_dump não encontrado. Instale o cliente do PostgreSQL ou ponha-o no PATH."
        )
    candidatos.sort(key=lambda t: t[0], reverse=True)
    return candidatos[0][1]


_BIN = None


def _ferramenta(nome: str) -> str:
    global _BIN
    if _BIN is None:
        _BIN = _bin_postgres()
    exe = _BIN / (nome + (".exe" if os.name == "nt" else ""))
    if not exe.exists():
        raise SystemExit(f"{nome} não encontrado em {_BIN}.")
    return str(exe)


# ── URLs ─────────────────────────────────────────────────────────────────────

def _url_producao() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SystemExit(
            "DATABASE_URL ausente. Ela vive no .env da raiz (nunca no git).")
    return url


def _url_prova_base() -> str:
    """Servidor LOCAL onde o dump será restaurado para conferência."""
    return os.environ.get(
        "SHARPEN_BACKUP_PROVA_URL",
        "postgresql://postgres@localhost:5432/postgres").strip()


def _host_de(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _exigir_local(url: str) -> None:
    """Trava 1: restore só em localhost. Recusa, nunca avisa."""
    host = _host_de(url)
    if host not in _LOCAIS:
        raise SystemExit(
            "RECUSADO: o alvo do restore não é local. A prova de restore só roda "
            "contra um Postgres em localhost — o .env desta máquina aponta para "
            "PRODUÇÃO, e restaurar lá por engano escreveria por cima da base viva."
        )


def _trocar_banco(url: str, banco: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, "/" + banco, p.query, p.fragment))


def _nome_do_banco(url: str) -> str:
    return urlsplit(url).path.lstrip("/") or "?"


# ── Execução ─────────────────────────────────────────────────────────────────

def _rodar(args: list[str], entrada: str | None = None) -> subprocess.CompletedProcess:
    """Roda um binário do Postgres. A saída de erro é devolvida crua para quem
    chamou decidir; nada aqui imprime a linha de comando, que carrega a URL.

    ⚠️ `-w` em TUDO (`--no-password`). Sem ele o `psql`/`pg_dump` abre um prompt
    de senha e **fica esperando para sempre** quando a conexão precisa de senha
    que o ambiente não tem. Medido nesta máquina: o comando não falhou, travou.
    Backup que trava às 3h é pior que backup que falha, porque nada avisa e o
    arquivo daquele dia simplesmente não existe. Com `-w` vem
    `fe_sendauth: no password supplied` na hora, que é um erro legível.
    """
    if args and Path(args[0]).stem in {"psql", "pg_dump", "pg_restore"}:
        args = [args[0], "-w", *args[1:]]
    return subprocess.run(
        args, input=entrada, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _contagens(url: str) -> dict[str, int]:
    """`count(*)` de cada tabela do schema `public`, via psql.

    Uma consulta só, montada por `string_agg`: percorrer tabela a tabela abriria
    N conexões contra o proxy do Railway, que é justamente o que a regra "peça a
    FAIXA" do CLAUDE.md manda evitar.
    """
    sql = """
        SELECT coalesce(string_agg(
                 format('SELECT %L AS t, count(*) AS n FROM public.%I', tablename, tablename),
                 ' UNION ALL '), '') FROM pg_tables WHERE schemaname='public';
    """
    r = _rodar([_ferramenta("psql"), url, "-tAq", "-c", sql.strip()])
    if r.returncode != 0:
        raise SystemExit("Falha ao listar as tabelas:\n" + (r.stderr or "").strip())
    consulta = (r.stdout or "").strip()
    if not consulta:
        return {}
    r = _rodar([_ferramenta("psql"), url, "-tAq", "-F", "|", "-c", consulta])
    if r.returncode != 0:
        raise SystemExit("Falha ao contar as linhas:\n" + (r.stderr or "").strip())
    saida: dict[str, int] = {}
    for linha in (r.stdout or "").splitlines():
        linha = linha.strip()
        if not linha or "|" not in linha:
            continue
        tabela, _, n = linha.rpartition("|")
        saida[tabela] = int(n)
    return saida


def _pasta_backup() -> Path:
    p = Path(os.environ.get("SHARPEN_BACKUP_DIR", str(_RAIZ / "_backups" / "postgres")))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _tamanho(caminho: Path) -> str:
    n = caminho.stat().st_size
    for unidade in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidade == "GB":
            return f"{n:.1f} {unidade}" if unidade != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} GB"


# ── Dump ─────────────────────────────────────────────────────────────────────

def dumpar() -> Path:
    url = _url_producao()
    pasta = _pasta_backup()
    carimbo = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    alvo = pasta / f"sharpen_{carimbo}.dump"
    parcial = alvo.with_suffix(".dump.parcial")

    print(f"Origem: banco '{_nome_do_banco(url)}' (host não impresso)")
    print(f"Gravando em: {alvo}")
    t0 = time.time()
    # Formato CUSTOM (-Fc): comprimido, e o pg_restore consegue restaurar tabela a
    # tabela a partir dele. `--no-owner`/`--no-acl` para o dump restaurar num
    # servidor local onde o papel `postgres` do Railway não existe.
    r = _rodar([_ferramenta("pg_dump"), url, "-Fc", "--no-owner", "--no-acl",
                "-f", str(parcial)])
    if r.returncode != 0:
        if parcial.exists():
            parcial.unlink()
        erro = (r.stderr or "").strip()
        # O `pg_dump` se RECUSA a dumpar servidor mais novo que ele, e a mensagem
        # crua ("aborting because of server version mismatch") não diz o que fazer.
        # Medido na s373: produção é 18.6 e o cliente desta máquina era 17.10, então
        # o backup não existia por falta de UM instalador. Erro que não diz o gesto
        # seguinte vira pendência parada.
        if "version mismatch" in erro:
            m_srv = re.search(r"server version:\s*([\d.]+)", erro)
            m_cli = re.search(r"pg_dump version:\s*([\d.]+)", erro)
            srv = m_srv.group(1) if m_srv else "?"
            cli = m_cli.group(1) if m_cli else "?"
            raise SystemExit(
                f"O cliente do Postgres é VELHO demais para esta base.\n"
                f"  servidor (produção): {srv}\n"
                f"  pg_dump local:       {cli}   ({_BIN})\n\n"
                f"O pg_dump nunca dumpa servidor mais novo que ele. Instale o cliente "
                f"{srv.split('.')[0]}.x (basta 'Command Line Tools' no instalador do "
                f"PostgreSQL) e rode de novo: o script escolhe sozinho a maior versão "
                f"instalada.\nA conexão está OK — ele chegou ao servidor e leu a versão.")
        raise SystemExit("pg_dump falhou:\n" + erro)

    # Só vira `.dump` depois de terminar. Arquivo com o nome final é arquivo
    # íntegro: um dump interrompido que mantivesse o nome definitivo seria
    # encontrado num incidente e restaurado como se estivesse completo.
    parcial.rename(alvo)
    print(f"Dump concluído em {time.time() - t0:.1f}s · {_tamanho(alvo)}")
    return alvo


# ── Prova de restore ─────────────────────────────────────────────────────────

def provar(dump: Path) -> bool:
    """Restaura o dump num banco local descartável e compara com a origem.

    Devolve True só se TODA tabela tiver a mesma contagem dos dois lados.
    """
    if not dump.exists():
        raise SystemExit(f"Arquivo não encontrado: {dump}")

    base_local = _url_prova_base()
    _exigir_local(base_local)                      # trava 1
    banco = PREFIXO_PROVA + datetime.now().strftime("%Y%m%d%H%M%S")
    if not banco.startswith(PREFIXO_PROVA):        # trava 2 (paranoia explícita)
        raise SystemExit("RECUSADO: banco de prova sem o prefixo obrigatório.")
    url_prova = _trocar_banco(base_local, banco)
    _exigir_local(url_prova)

    print(f"\nProva de restore em banco local descartável: {banco}")
    r = _rodar([_ferramenta("psql"), base_local, "-v", "ON_ERROR_STOP=1",
                "-c", f'CREATE DATABASE "{banco}"'])
    if r.returncode != 0:
        erro = (r.stderr or "").strip()
        if "no password supplied" in erro or "authentication failed" in erro:
            raise SystemExit(
                "O Postgres LOCAL pede senha e o script não a tem.\n"
                "Aponte-o com a senha do seu Postgres local (nunca a de produção):\n\n"
                '  $env:SHARPEN_BACKUP_PROVA_URL = '
                '"postgresql://postgres:<SENHA_LOCAL>@localhost:5432/postgres"\n\n'
                "Ele só é usado para criar e derrubar o banco descartável da prova.\n"
                "Detalhe do servidor: " + erro)
        raise SystemExit(
            "Não consegui criar o banco de prova. O Postgres local está de pé?\n" + erro)

    try:
        r = _rodar([_ferramenta("pg_restore"), "-d", url_prova,
                    "--no-owner", "--no-acl", "-j", "2", str(dump)])
        # pg_restore devolve != 0 por AVISO (extensão ausente, papel inexistente).
        # Quem decide é a comparação de linhas abaixo, não o código de saída — mas
        # o texto do erro vai para a tela, porque é onde se lê o motivo real.
        if r.returncode != 0:
            print("  (pg_restore terminou com avisos; a comparação abaixo é quem decide)")
            for linha in (r.stderr or "").strip().splitlines()[:8]:
                print("    " + linha)

        print("  Contando linhas na ORIGEM…")
        origem = _contagens(_url_producao())
        print("  Contando linhas na CÓPIA…")
        copia = _contagens(url_prova)

        tabelas = sorted(set(origem) | set(copia))
        if not tabelas:
            print("\nFALHA: nenhuma tabela encontrada dos dois lados.")
            return False

        larg = max(len(t) for t in tabelas)
        divergentes = []
        print(f"\n  {'tabela'.ljust(larg)}  {'origem':>10}  {'cópia':>10}")
        for t in tabelas:
            a, b = origem.get(t), copia.get(t)
            marca = "OK" if a == b else "DIVERGE"
            if a != b:
                divergentes.append(t)
            print(f"  {t.ljust(larg)}  {str(a if a is not None else '—'):>10}"
                  f"  {str(b if b is not None else '—'):>10}  {marca}")

        total_origem = sum(origem.values())
        print(f"\n  {len(tabelas)} tabela(s) · {total_origem:,} linha(s) na origem"
              .replace(",", "."))
        if divergentes:
            print("\nFALHA: divergência em " + ", ".join(divergentes))
            print("O dump NÃO está provado. Não abra a torneira com este backup.")
            return False
        print("\nPROVADO: o dump restaura e bate linha a linha com a origem.")
        return True
    finally:
        # O banco de prova sempre sai, mesmo se a comparação estourar: deixá-lo
        # para trás encheria o disco a cada rodada e, pior, o próximo run acharia
        # um banco `sharpen_prova_*` e ninguém saberia de qual dump ele veio.
        _rodar([_ferramenta("psql"), base_local, "-c",
                f'DROP DATABASE IF EXISTS "{banco}" WITH (FORCE)'])
        print(f"Banco de prova {banco} removido.")


# ── Inventário ───────────────────────────────────────────────────────────────

def listar() -> list[Path]:
    dumps = sorted(_pasta_backup().glob("sharpen_*.dump"), reverse=True)
    if not dumps:
        print(f"Nenhum dump em {_pasta_backup()}.")
        return []
    print(f"{len(dumps)} dump(s) em {_pasta_backup()}:\n")
    for d in dumps:
        idade = (time.time() - d.stat().st_mtime) / 86400
        print(f"  {d.name}  {_tamanho(d):>10}  {idade:.1f} dia(s)")
    return dumps


def podar(manter: int) -> None:
    dumps = sorted(_pasta_backup().glob("sharpen_*.dump"), reverse=True)
    sobra = dumps[manter:]
    if not sobra:
        print(f"Nada a podar: {len(dumps)} dump(s), teto {manter}.")
        return
    for d in sobra:
        d.unlink()
        print(f"  removido {d.name}")
    print(f"Mantidos os {min(manter, len(dumps))} mais recentes.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Backup do Postgres com prova de restore.")
    ap.add_argument("--provar", action="store_true",
                    help="depois do dump, restaura num banco local e compara")
    ap.add_argument("--provar-arquivo", metavar="DUMP",
                    help="prova um dump já existente, sem gerar outro")
    ap.add_argument("--listar", action="store_true", help="lista os dumps gravados")
    ap.add_argument("--podar", type=int, metavar="N",
                    help="mantém só os N dumps mais recentes")
    a = ap.parse_args()

    if a.listar:
        listar()
        return 0
    if a.podar is not None:
        podar(a.podar)
        return 0
    if a.provar_arquivo:
        return 0 if provar(Path(a.provar_arquivo)) else 1

    dump = dumpar()
    if a.provar:
        return 0 if provar(dump) else 1
    print("\nDump gerado SEM prova de restore. Rode com --provar antes de confiar nele.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

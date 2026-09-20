# Runbook — Backup do Postgres (e a prova de que ele volta)

> Procedimento de produção. O dump é **leitura**: não mexe na base viva.
> A prova de restore acontece num banco **local descartável**, nunca em produção.
> Ferramenta: [`scripts/backup_postgres.py`](../scripts/backup_postgres.py).

## Por que isto existe

Até a s373 não havia backup nenhum do banco: nem `pg_dump`, nem job agendado, nem
snapshot documentado. O único caminho de volta era a `lixeira_contas`, que cobre
**uma** conta excluída pela tela e vive 7 dias. Com 25.726 apostas migradas da
planilha e a base de 16 donos, abrir o cadastro público sem dump é apostar a base
inteira no primeiro `DELETE` mal escrito.

**Dump que ninguém restaurou é arquivo, não backup.** É por isso que o modo
`--provar` existe e por isso que ele é o gate, não o dump.

## Pré-requisitos (uma vez só)

1. **Cliente do PostgreSQL** instalado. O script acha sozinho a **maior** versão
   em `C:\Program Files\PostgreSQL` (nesta máquina, a 17.10). A 9.3 que sobrou
   ali não fala com servidor moderno, e escolher a errada dá um erro de protocolo
   que não se parece nada com "versão velha".
2. **`DATABASE_URL` no `.env`** da raiz, apontando para o host **público** do
   Railway (o `.internal` só resolve de dentro da rede deles). O `.env` está no
   `.gitignore` e nunca foi commitado.
3. **Um Postgres local de pé**, só para a prova. Se ele pede senha:

   ```powershell
   $env:SHARPEN_BACKUP_PROVA_URL = "postgresql://postgres:<SENHA_LOCAL>@localhost:5432/postgres"
   ```

   É a senha do Postgres **da sua máquina**, nunca a de produção. O script só a
   usa para `CREATE DATABASE` e `DROP DATABASE` do banco descartável.

## O ritual

```powershell
python scripts/backup_postgres.py --provar
```

Faz, nesta ordem: dump de produção → restaura num banco local `sharpen_prova_<carimbo>`
→ conta as linhas dos **dois lados, tabela a tabela** → derruba o banco de prova.

Saída esperada no fim:

```
PROVADO: o dump restaura e bate linha a linha com a origem.
```

Qualquer outra coisa **não é backup**. Se aparecer `DIVERGE` em alguma tabela, o
arquivo não serve e não adianta guardá-lo.

Outros modos:

| Comando | O que faz |
|---|---|
| `python scripts/backup_postgres.py` | só o dump, rápido, **sem prova** |
| `python scripts/backup_postgres.py --provar-arquivo <dump>` | prova um dump que já existe |
| `python scripts/backup_postgres.py --listar` | inventário do que está gravado |
| `python scripts/backup_postgres.py --podar 10` | mantém os 10 mais recentes |

## Onde os dumps ficam

`_backups/postgres/` na raiz (gitignored), ou o que estiver em `SHARPEN_BACKUP_DIR`.

**Não é `Planilhador/Backups/`**, e isso é de propósito: aquela pasta é o snapshot
de arquivo-antes-de-editar da invariante #4, é podada a cada poucas sessões, e um
dump de banco no meio dela seria apagado pela faxina junto com o resto.

> ⚠️ **Backup na mesma máquina cobre erro humano, não perda de máquina.** Um dump
> em `_backups/` protege contra `DELETE` errado, migração ruim e deploy que
> corrompe dado. **Não** protege contra o HD morrer. Copiar o dump provado para
> fora da máquina é o passo que fecha isso, e hoje ele é manual.

## As três travas, e por que elas recusam em vez de avisar

1. **O restore só aceita alvo em `localhost`/`127.0.0.1`.** Mesma família da trava
   do `TEST_DATABASE_URL` no `conftest.py`: o `.env` desta máquina carrega a URL de
   **produção**, e um restore apontado para lá escreveria por cima da base viva.
   Provado por mutação: apontando para um host remoto o script para com `RECUSADO`
   antes de abrir conexão.
2. **O banco de prova nasce com o prefixo `sharpen_prova_`** e é criado e derrubado
   pelo próprio script, sempre. Ele nunca restaura sobre banco preexistente, e o
   `DROP` está num `finally` — banco de prova esquecido no disco viraria um segundo
   `sharpen_prova_*` que ninguém sabe de qual dump veio.
3. **Nenhuma URL, senha ou host é impressa.** O relatório fala de tabela e contagem.

## Duas armadilhas medidas

**`-w` em todo binário do Postgres.** Sem ele o `psql`/`pg_dump` abre prompt de
senha e **fica esperando para sempre** quando o ambiente não tem a credencial.
Medido nesta máquina: o comando não falhou, travou. Backup que trava às 3h é pior
que backup que falha, porque nada avisa e o arquivo daquele dia simplesmente não
existe. Com `-w` o erro chega em 0,6s e é legível.

**O arquivo só recebe o nome final depois de terminar.** O dump é escrito como
`.dump.parcial` e renomeado no fim. Um dump interrompido que já tivesse o nome
definitivo seria encontrado num incidente e restaurado como se estivesse completo.

## Num incidente: restaurar de verdade

O script **não** restaura em produção, de propósito. O caminho é manual e com
cabeça fria:

1. **Pare a torneira antes.** Suspenda os cadastros novos no `/admin` para o
   estrago não crescer enquanto você decide.
2. **Prove o dump que você vai usar** (`--provar-arquivo`) antes de encostar em
   produção. Restaurar um dump não conferido em cima de uma base meio quebrada
   troca um problema conhecido por dois.
3. **Decida o escopo.** Quase nunca a resposta é "restaurar tudo": o dano costuma
   ser uma tabela ou um dono. O formato `custom` (`-Fc`) permite
   `pg_restore -t <tabela>` a partir do mesmo arquivo.
4. **Restaure numa cópia primeiro**, confira o que voltou, e só então leve para
   produção com o que você já viu funcionando.
5. Se o que se perdeu foi **uma conta excluída pela tela**, o caminho é outro e é
   mais barato: [`scripts/restaurar_conta_lixeira.py`](../scripts/restaurar_conta_lixeira.py),
   dentro dos 7 dias.

## Cadência

| Momento | O quê |
|---|---|
| **Antes de abrir o cadastro público** | `--provar`, e o resultado colado no `STATUS.md` |
| **Antes de todo deploy com `ALTER TABLE`** | `--provar`. Rollback de container não volta schema |
| **Diário, na semana de lançamento** | `--provar` (manual, ver pendência abaixo) |
| **Semanal, depois** | `--provar` + `--podar 14` |

> **Pendência conhecida:** a cadência é **manual** hoje. Agendar (tarefa do Windows
> ou job no Railway) é trabalho separado, e enquanto não existir, backup depende de
> alguém lembrar. Está no `BACKLOG.md`.

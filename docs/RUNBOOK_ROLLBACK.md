# Runbook — Voltar atrás quando o deploy quebra

> Procedimento de emergência. Escrito para ser lido às 22h com o site fora do ar,
> então a ordem importa mais que a explicação.
> Backup do banco: [`RUNBOOK_BACKUP_POSTGRES.md`](RUNBOOK_BACKUP_POSTGRES.md).

## Primeiro: é o código ou é o dado?

São dois desastres diferentes e o remédio é oposto. Trinta segundos aqui evitam
uma hora de conserto errado.

| Sintoma | Provável | Vá para |
|---|---|---|
| Site não abre, erro 500 em tudo, `/healthz` não responde | **código** | [Voltar o deploy](#voltar-o-deploy) |
| Site abre, mas uma tela quebra ou mostra número errado | **código** | [Voltar o deploy](#voltar-o-deploy) |
| Site abre e funciona, mas sumiu ou corrompeu dado | **dado** | [`RUNBOOK_BACKUP_POSTGRES.md`](RUNBOOK_BACKUP_POSTGRES.md#num-incidente-restaurar-de-verdade) |
| Captura de uma casa parou | **nem um nem outro** | `/sharpenup-diagnostico` |

O teste de 5 segundos: `https://www.sharpen.bet/healthz` deve devolver `{"ok":true}`.
Ele não toca o banco e não exige login, então responde mesmo com o resto quebrado.
Se ele responde e o site não abre, o processo está de pé e o defeito é de aplicação,
não de container.

## Voltar o deploy

O deploy dispara no `git push` para a `main` (invariante #8). Há **dois** caminhos de
volta, e eles têm velocidades diferentes.

### Caminho A — redeploy da versão anterior (rápido, sem build)

**Este é o caminho da emergência.** Não passa por build, então volta em menos de um
minuto.

1. Abra o Railway → projeto **victorious-generosity** → serviço **extrator**.
2. Aba **Deployments**.
3. Ache o último deploy que estava bom (olhe o horário e a mensagem de commit).
4. No menu de três pontinhos dele → **Redeploy**.
5. Espere ficar `Active` e confira o `/healthz`.

> ⚠️ **O CLI do Railway NÃO faz isto.** `railway deployment redeploy` reimplanta a
> **última** implantação, que é justamente a quebrada. Voltar para uma versão anterior
> é ação de painel. Conferido na v5.8.0: os subcomandos são `list`, `up` e `redeploy`,
> e nenhum aceita um id de deploy antigo.

> ⚠️ **Nunca use `railway down`.** Ele **remove** a implantação mais recente em vez de
> voltar para a anterior, e o resultado é o serviço sem nada rodando.

### Caminho B — desfazer no git (mais lento, mas é o que fica no histórico)

Use quando o incidente já passou e você quer que a `main` deixe de conter o defeito.
Passa por build, então leva alguns minutos.

```powershell
git log --oneline -10                  # ache o commit culpado
git revert <sha>                       # cria um commit que DESFAZ aquele
git push
```

`revert` cria um commit novo que desfaz o anterior. **Nunca use `reset --hard` + force
push** numa branch já publicada: o outro terminal tem a mesma `main`, e reescrever
histórico pushado é o caso #8 do `docs/CASOS.md` acontecendo de novo.

Com **duas sessões abertas**, o `revert` pode arrastar arquivo alheio se o commit
culpado misturou trabalho. Confira com `git show --stat` antes de pushar.

## O que voltar o deploy NÃO desfaz

Três coisas, e são elas que transformam "voltei a versão" em "continua quebrado".

### 1. O banco — medido, e a notícia é boa

O `init_db()` roda a **cada boot** (`main.py`, no `lifespan`) e executa o `SCHEMA_SQL`
inteiro. Ou seja: **todo deploy migra o banco sozinho**, sem passo manual.

Medido no `app/database.py`, contando as formas de DDL:

| Forma | Ocorrências |
|---|---|
| `CREATE TABLE IF NOT EXISTS` | 18 |
| `ADD COLUMN IF NOT EXISTS` | 24 |
| `CREATE INDEX IF NOT EXISTS` | 9 |
| `CREATE UNIQUE INDEX IF NOT EXISTS` | 1 |
| `DROP COLUMN IF EXISTS` | 1 (`bilhetes.copy_state`, migração antiga) |
| `DROP CONSTRAINT IF EXISTS` | 2 (troca da unique antiga pela versão com `dono`) |
| `SET NOT NULL` · `DROP TABLE` · `ALTER COLUMN … TYPE` · DDL sem guarda | **0** |

**Tudo é idempotente**, e é isso que torna o rollback seguro hoje: rodar o mesmo boot
dez vezes não muda nada, a versão antiga ignora as colunas que a nova criou, e nenhuma
coluna ficou obrigatória.

> ⚠️ **Quase tudo é aditivo; DOIS pontos não são.** Os `DROP CONSTRAINT IF EXISTS`
> derrubam a unique pré-multiusuário (`bilhetes_casa_parceiro_assinatura_key` e
> `parceiros_casa_nome_key`) para recriá-la com `dono` junto. Um rollback para uma versão
> **anterior ao multiusuário** encontraria o banco sem a restrição que ela espera. Nenhum
> deploy plausível volta tão longe, mas é o único ponto do schema em que "voltar o
> código" não é simétrico.

> ⚠️ **Esta é uma medição DATADA, e por isso virou gate:**
> `tests/test_schema_aditivo.py` quebra o CI se entrar um `SET NOT NULL`, um `DROP TABLE`,
> um `ALTER COLUMN … TYPE`, um `TRUNCATE` ou qualquer DDL sem guarda. O gate não proíbe a
> migração: obriga a conversa. Quando o CI quebrar ali, **tire um backup provado**
> (`python scripts/backup_postgres.py --provar`), escreva aqui o caminho de volta daquele
> deploy e só então libere.
>
> O gate tem uma rede contra si mesmo (`test_o_gate_esta_mesmo_lendo_o_schema`), porque a
> primeira versão dele foi um **falso verde**: ela limpava docstrings do arquivo, e como o
> `SCHEMA_SQL` É uma triple-quoted string, apagava o schema inteiro e inspecionava vazio.
> Dez testes verdes, oito mutações escapando. Provado por mutação: **10/10 detectadas**.

### 2. O SharpenUp já instalado

A extensão é distribuída **manualmente**, sem loja. Voltar o servidor volta o `.zip` que
a rota `/extensao` oferece, mas **não alcança o que já está instalado na máquina de cada
tester**. Se a quebra for da extensão, o caminho é avisar o grupo e pedir reinstalação.
Não existe volta remota.

### 3. O dado que entrou errado enquanto estava quebrado

Voltar o código para de produzir dado errado; não conserta o que já foi gravado. Isso é
trabalho de script de reparo, com ensaio e olho humano, como o
`scripts/corrigir_boost_lottu_s371.py`.

## Depois de voltar

1. **Diga ao grupo `Sharpen - Testers` que voltou.** Quem ficou sem o site precisa saber
   que pode usar de novo. Regra da casa: perguntar ao Feca antes de enviar, com a
   mensagem pronta ([`RUNBOOK_AVISO_TESTERS.md`](RUNBOOK_AVISO_TESTERS.md)).
2. **Registre no `STATUS.md`** o que quebrou e o que voltou. Rollback não anotado vira
   um mistério na sessão seguinte.
3. **Só então conserte de verdade**, com gate. Voltar é estancar, não é consertar.

## O ensaio — e por que ele não é opcional

**Procedimento de emergência que nunca foi executado é ficção.** O Caminho A depende de
um botão de painel que ninguém desta equipe clicou ainda, e a hora de descobrir que ele
está noutro lugar não é com o site fora do ar.

Ensaie uma vez, num horário morto:

1. Confira que o site está bom (`/healthz` e uma tela qualquer).
2. Railway → extrator → Deployments → pegue o deploy **anterior** → Redeploy.
3. Cronometre quanto leva até ficar `Active`.
4. Confira o `/healthz` e uma tela.
5. Volte para o deploy mais novo pelo mesmo caminho.
6. **Anote aqui embaixo** o tempo e qualquer diferença entre o que está escrito e o que
   a tela do Railway mostra de verdade.

### Registro dos ensaios

| Data | Quem | Tempo até `Active` | Observações |
|---|---|---|---|
| _(pendente)_ | | | **Nunca ensaiado.** Até esta linha ser preenchida, o Caminho A é teoria. |

# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-13 (sessao 355: **a base do SharkTrack entrou DENTRO da base viva do Diogo, e o trabalho de verdade foi o NOME.** O pedido do Feca: *"preciso importar a base do diogo dentro da base q ele vem utilizando... precisa ser feito um trabalho com o nome das casas e principalmente com o nome dos tipsters dele"*, com o exemplo `araujo` / `ARAUJO` / `Araujo` sendo tudo o mesmo. **O ESTADO MEDIDO ANTES:** 891 bilhetes vivos, todos `origem='extracao'` do SharpenUp, de 07/09 a 13/09, com o tipster em MINUSCULO; o export do SharkTrack traz 6.410 linhas de 24/06 a 06/09, em duas caixas. **Zero sobreposicao de periodo: o import para exatamente onde a captura comeca. TRES DECISOES DO FECA:** Title Case em tudo (renomeando tambem o que ja estava no banco), nenhum merge semantico (`pei` segue separado de `peixe`) e conta `SharkTrack` para toda linha, porque o export nao tem coluna de titular. **O ACHADO QUE JUSTIFICOU A SESSAO INTEIRA: o `_CASA_MAP` do importador criaria QUATRO casas paralelas.** Ele foi escrito na s255 sem medir, e `casa` e TEXTO em 7 tabelas: `Rei do Pitaco` nao existe em lugar nenhum da base (0 linhas) e levaria 48 bilhetes; `VixeBet` tambem nao (o Diogo ja tem 8 em `Vixebet`); `Sportingbet` idem, contra `SportingBet` (467). Faltavam `bet mgm` (`BetMGM`, 864), `ice bet` (`icebet`, 76, e a grafia MINUSCULA e a que existe) e `bateubet` (`Bateu`, 136 contra 2). **Cada linha do mapa agora carrega a contagem que a autorizou.** **O NOME DO TIPSTER VIVE EM TRES LUGARES, e o terceiro e o que se esquece:** `bilhetes.tipster`, `tipsters.nome` (o que o matcher le) e as **CHAVES** de `custo_store.custo_tipster` / `custo_tipster_meta`. Renomear os dois primeiros e deixar o terceiro para tras e o caso *tipster cobrado e ineditavel* do `CLAUDE.md`. As 22 chaves do Diogo estavam todas sem valor lancado, entao o rename foi barato; a proxima base nao tera essa sorte. **UM MODULO, NAO DUAS FUNCOES:** `scripts/tipster_nomes.py` e a fonte unica que o import e o rename consultam. Dois normalizadores separados concordam hoje e divergem no primeiro acento, e ai o tipster nasce partido de novo (mesma razao de o `parseNum` do dashboard ser um so). A regra de desempate esta escrita e provada pelo dado: dentro do grupo (casefold + sem acento) **vence a variante ACENTUADA mais frequente**, porque o acento e informacao que a digitacao sem acento perdeu, e o contrario nunca e verdade. Hoje nao ha nenhum caso de acento divergente na base do Diogo; a regra existe para o `Araujo` do proximo export. **O de-para ficou num JSON versionado** (`scripts/tipsters_diogo_map.json`, 79 grafias -> 45 tipsters), que e onde um merge de APELIDO entra depois sem tocar em codigo. Merge de apelido nunca e inferido: dois apelidos parecidos podem ser duas pessoas. **DEFEITO DO IMPORTADOR QUE SO APARECE AGORA:** ele ancorava `criado_em` em `NOW()`, escrito quando a base do Diogo estava vazia. Com captura ao vivo rodando, isso jogaria as 6.410 linhas historicas para o TOPO do feed, acima dos bilhetes de hoje. Passou a ancorar na data da aposta, com a posicao dentro do dia como desempate. **DOIS ESPORTES FORA DO VOCABULARIO, corrigidos junto por serem o mesmo problema:** `Counter-Strike 2` (5 linhas) virou `E-Sports` como manda o `MASTER_ESPORTES §7`; `Automobilismo` (1 linha) **NAO** virou F1, porque o bilhete e `CBPS Azul - Lagomar` / `Total de Pontos` / `Liga de Ascenso`, ou seja o rotulo mente na origem, e traduzir rotulo que mente e inventar o dado. Ele cai em `Outro`. **RESULTADO, conferido no banco DEPOIS de gravar:** 7.301 bilhetes (6.410 import + 891 captura), turnover R$ 1.855.101,42, P/L +R$ 158.728,54, ROI 8,56%, identicos ao ensaio; 45 grafias de tipster e **nenhuma comecando em minuscula**; 26 casas e nenhuma paralela; o topo do feed continua sendo a captura de hoje. Residuo: 9 linhas em `Outros` (0,14%), 63 em esporte `Outro` (1%), 1 sem odd. A Caixa do Diogo esta desligada (0 movimentos), entao nada de `abertas_corte` foi tocado. **FORA DO ESCOPO, de proposito:** as contas reais do Diogo seguem intactas, e a conta `SharkTrack` (25 casas) nao puxa o custo de aquisicao delas para 24/06, que e o que aconteceria se o historico fosse atribuido as contas verdadeiras. **AS DUAS PENDENCIAS FECHARAM NA PROPRIA SESSAO, as duas com o Feca decidindo:** (1) **`Pei` e `Peixe` sao DUAS PESSOAS** (*"Pei e Pei mesmo. Tem o Pei, tem o Peixe"*), entao nao ha merge de apelido a fazer. Isso e a prova de que semelhanca de grafia nunca autoriza merge: um normalizador ingenuo juntaria os dois e apagaria um tipster inteiro, em silencio. Caixa e acento o modulo une sozinho; apelido so por declaracao humana, e o lugar dela e o JSON. (2) **A CAPTURA VIRA A FONTE UNICA** (*"ele vai importar so no sharpen agora"*): o SharkTrack deixa de ser exportado e o que esta no banco como `origem='import'` passa a ser **historico congelado**, exatamente o desfecho que a regra *Planilha e bot escrevem na MESMA serie de codigo* ja prescrevia. Com isso some o unico risco estrutural que sobrava, o de dois escritores para a mesma aposta a partir de 07/09, que **nao teriam como deduplicar entre si** (contas diferentes: `SharkTrack` de um lado, a conta real do outro). `teste`, `teste bask`, `fix`, `dark`, `dynamite` e `vini` ficam na base verbatim, sem decisao, e nenhum deles atrapalha nada.)

_Anterior: 2026-09-13 (sessao 354: **FATIA 1 do `/realtrial` — a carteira de demonstracao saiu das bases reais, anonimizada e com o porte pela metade.** O pedido do Feca: *"qual a chance de a gnt ter um perfil fake e q funcione... pegar minha carteira, e carteira do jonathan e fazer um mix"*, para mostrar o Sharpen em video sem abrir conta, fornecedor e tipster de ninguem. **QUATRO DECISOES DELE, registradas:** (1) mix REAL anonimizado, e nao a base sintetica que ja existe em `scripts/demo/` — *"a ideia e mostrar numeros reais, downdraws reais etc, porem sem revelar quem e oq"*; (2) 5 prints + 5 capturas do SharpenUp **por pessoa**, *"a ideia eh ver o funcionamento e nao usar"*; (3) o endereco e `www.sharpen.bet/realtrial`, ou seja **dentro do app de producao**, nao um subdominio separado; (4) escalar a stake, delegada a mim (*"se vc acha q o ideal... manda ver"*). **TRES ACHADOS DE ARQUITETURA que barateiam a Fatia 3:** o SharpenUp funciona **sem mudar uma linha** (`extensor/config.js` ja aponta para `https://www.sharpen.bet` e autentica por cookie, entao cookie de trial no mesmo dominio faz a captura cair sozinha); `dashboard_rows(donos: list[str])` ja agrega LISTA de donos, que e o mecanismo supervisor/operador e serve de uniao "base compartilhada + dado do visitante" sem inventar nada; e `_client_ip` + janela em memoria no `/login` ja resolvem o teto por IP, com o cuidado do X-Forwarded-For feito. **O ISOLAMENTO E O PONTO QUE NAO PODE FALHAR:** o visitante usa o SharpenUp na casa DELE, com as apostas reais dele. Dono efemero por visitante, senao o proximo a entrar ve a carteira do anterior — vazamento com o agravante de ser gente que se quer conquistar. **A REGUA DA ANONIMIZACAO:** troca identidade (conta, e-mail, fornecedor, tipster, codigo de bilhete), **preserva o evento** (casa, esporte, categoria canonica, descricao, odd, resultado, data) e escala **todo** dinheiro por 0,5. Categoria NAO se troca: nao identifica ninguem e trocar quebraria matcher, Atribuicao por Casa e as telas de mercado. O fator 0,5 foi escolhido por preservar a REDONDEZA da stake (100->50, 250->125), que e sinal que o matcher usa; fator quebrado apagaria a assinatura. Fator unico em stake + custo + faixa do tipster **juntos** — escalar metade seria a familia do *blindar metade dos campos*. **MEDIDO ANTES DE DECIDIR:** Feca 35.962 apostas / R$ 7,43 mi / ROI 4,34%, Jonathan 12.923 / R$ 1,89 mi / ROI 2,00%. Somados dao **ROI 3,60%** e nenhum dos dois numeros e de ninguem, o que ja e metade da protecao. **Minha recomendacao de recortar em maio foi REVERTIDA pela propria medicao:** o recorte custava 16 mil apostas e quase metade do ROI (2,22% contra 3,60%), porque o 1o quadrimestre do Feca e o mais forte; o "degrau" de volume em maio le como operacao que cresceu. **63 das 90 contas do Jonathan tem E-MAIL REAL no nome** (as do Feca usam `Nome [Fornecedor]` em 179 de 180) — o dado mais identificavel da base, e virou item de falha dura na conferencia. **RESULTADO:** 48.899 bilhetes, turnover R$ 4,73 mi, P/L R$ 170 mil, ROI e win rate identicos aos reais. **QUATRO DEFEITOS MEUS, todos pegos por medicao e nenhum por leitura:** (1) **loop infinito** na 1a rodada — com codigo de bilhete a assinatura e `ID|casa|parceiro|codigo` e **ignora o `_counter`**, entao procurar contador livre nunca termina; hoje o codigo nasce unico e colisao ali **aborta**; (2) o codigo ficticio nao era deterministico (sorteava a cada chamada), o que faria o mesmo bilhete deixar de ser o mesmo e a dedup por ID parar; (3) **31 bilhetes tem codigo de 1-2 caracteres**, espaco de 10 e 100 valores; (4) **nome ficticio colidindo com nome real** — existem um tipster "Duplo" e outro "MARLON" e as duas palavras estavam nos pools, gerando *"Duplo Alto"* e *"Marlon Alves"*; em vez de tirar dois nomes a mao, o `Anonimizador` passou a **recusar na geracao** qualquer ficticio que contenha nome real, o que fecha a familia para a proxima base. **E UM QUINTO, que so apareceu na prova por mutacao:** um comando meu de edicao calculou intervalo invertido (`ini > fim`) e **duplicou 212 linhas** em vez de mover — `transformar` ficou definida DUAS vezes, a segunda vencendo. `py_compile` passa (duplicar funcao e sintaxe valida) e os testes passavam, porque eu estava mutando **codigo morto**. Foi a mutacao escapando que denunciou. **A VARREDURA DE VAZAMENTO acusou 24 nomes e 21 eram inocentes:** um tipster "Beta" casando dentro de "Betano" 8.372 vezes, "Samu" em "Samuel Silvera", "Nine" em "Moknine", e "Feca" casando dentro do **hash hexadecimal** da assinatura. Substring solta nao serve; hoje exige limite de PALAVRA e separa dois regimes — campo anonimizado com tolerancia ZERO, descricao tolerando so nome que e palavra publica (`_NOMES_PUBLICOS`, 21 excecoes declaradas com o motivo medido: o esporte Badminton, o jogador Marlon Tolic, o time Moriyama Samurai). **Os TRES culpados de verdade eram rotulo interno escrito no lugar do evento** (`Arrudex 1/2/3`, `Multipla So Chutes`, `Pessoal`) e agora sao trocados pelo ficticio do tipster. **GATE: `tests/test_realtrial_export.py`, 30 provas e 7 de 8 mutacoes detectadas.** A 8a **escapa de proposito e esta documentada como inocua**: para um molde de k letras e m digitos ha 26^k x 10^m saidas e no maximo esse tanto de codigos reais com aquela forma, entao o espaco nunca esgota e a extensao de molde e defesa redundante — inventar assercao para ela seria fabricar verde. **ACHADO LATERAL, que nao e da demo:** o Feca **nao tem linha nenhuma em `custo_store`** (nem geral, nem por tipster, nem por conta) e `fornecedor_preco` esta vazia para todos; o custo dele provavelmente nunca saiu do `localStorage`. Foi para o `BACKLOG`. **ONDE ESTA:** `scripts/realtrial/exportar.py` (so leitura de producao, grava JSON) e o par `Backups/realtrial/export.json` + `export.chave.json`, este ultimo a chave que desfaz a anonimizacao inteira — `Backups/` e gitignored, entao nenhum dos dois vai para o git. **E O FECA MANDOU OLHAR AS DESCRICOES — rendeu o maior achado da sessao.** *"se quiser verificar as descricoes, podemos achar algo"*. A conferencia so procurava nome CONHECIDO (tipster, conta, fornecedor), entao era cega para o que nao esta em lista nenhuma. Duas varreduras novas, as duas pela FORMA: descricao sem forma de evento (sem confronto entre colchetes, sem ` v `, sem ` // `) e marcas de dado pessoal (e-mail, @handle, URL, CPF, telefone, username de dono). **Zero e-mail, zero URL, zero CPF.** Mas o casador de telefone acusou 410 ocorrencias que eram **codigo de bilhete escrito DENTRO da descricao** — `Multipla - #291310574`, `Simples - #291367894`, e alguns em que o numero E' a descricao inteira (`291543248.0`). Anonimizar so a COLUNA `codigo_bilhete` deixava esse elo intacto, e e' ele que casa a linha publica com o bilhete real na casa. **E a primeira correcao pegou so METADE:** eu troquei o que existia na coluna (63 bilhetes) e continuei cego para o identificador que **nunca virou coluna** (**495 bilhetes**) — a IA leu o numero do print e o deixou so no texto. A regra passou a ser por FORMA: todo token so-digitos com 7+ caracteres e' identificador (odd, linha, placar e minuto tem 1 a 4). Alfanumerico segue trocado so quando bate com codigo conhecido, senao mutilaria nome de jogador de e-sports (`4ikibabmoni`). **Segundo achado:** `Multipla Germano` e `Aposta para cadastrar o custo do grupo` — rotulo interno com nome de DONO do sistema, categoria que a lista de tipster/conta nunca cobriu. Virou troca **FRACA**, valida so em descricao sem forma de evento: dos 324 casos de username na descricao, **322 eram ATLETA** (Jonathan David, Gabriel Diallo, Diogo Spencer) e trocar ali destruiria o evento. A forma e' o unico discriminador honesto. **Medido depois: 63 -> 0, 495 -> 0, 2 -> 0**, com os tres numeros conferidos por `grep` literal no arquivo. **Gate subiu para 41 provas e 11 de 12 mutacoes** (a 12a e a inocua documentada). Entre elas, uma que so existe por causa deste achado: tirar a **passada 1** (traduzir todo codigo ANTES de limpar descricao) — o codigo de um bilhete aparece no texto de outro, e montar o mapa na mesma passada deixaria de fora todo codigo ainda nao visto, em silencio. **FATIA 2 NO AR, na mesma sessao: a conta `realtrial` existe no banco.** 48.899 bilhetes, 270 contas, 110 tipsters e os custos, com ROI 3,59% e turnover R$ 4.726.937 conferidos DEPOIS de gravar, contra o que foi mandado. `scripts/realtrial/importar.py`, com **ensaio como padrao** e tres travas: dono de destino tem de ser exatamente `realtrial`, recusa gravar se ja houver dado (sem `--recriar`) e tudo numa transacao so. **O Feca calibrou o esforco e estava certo:** *"sao milhares e milhares de apostas q ninguem vai ler e so entender como funciona o sistema... vamos ter um produto entregue, sem necessariamente ser 100%"* — a caca a vazamento parou e a entrega andou. **DOIS DEFEITOS, os dois uteis:** (1) `ON CONFLICT (casa, parceiro, assinatura)` estourou `InvalidColumnReferenceError` no meio da gravacao, porque a constraint REAL inclui o dono (`UNIQUE (dono, casa, parceiro, assinatura)`); o `database.py` mostra o CREATE TABLE original e a migracao acrescentou depois. **Eu tinha conferido as COLUNAS no banco e supus a CONSTRAINT pelo arquivo** — a transacao salvou (rollback limpo, tudo voltou a zero). (2) o conferidor pos-gravacao marcou `!!` em tipsters (110 de 133) num comportamento CORRETO: o mapa de tipster e' global de proposito, entao os 23 que Feca e Jonathan assinam em comum viram um ficticio so. O alvo passou a ser nomes DISTINTOS. **Conexao com retry:** o Railway oscila (medido: timeout em 25s, conexao em 3,9s na seguinte) e sem isso uma gravacao de 48 mil linhas morre por hipo de rede. **FORA do import, de proposito:** `caixa_mov` (o `abertas_corte` guarda IDS de bilhete e os ids mudam no import — e' o caso do script que inflou a projecao em R$ 10.477) e a linha em `usuarios` (sessao e login sao da Fatia 3; conta logavel antes da hora so aumenta superficie). **PROXIMO PASSO: a Fatia 3 (rota `/realtrial`, sessao efemera, purga de 7 dias), a 4 (creditos 5+5 com teto por IP) e a 5 (trava de escrita na base compartilhada). **SEGUE ABERTO E E DO FECA:** 21 bilhetes datados no futuro ficaram como estao (aposta em futuro e legitima); se ele quiser, corta.)

_Anterior: 2026-09-13 (sessao 353: **o bilhete #62 do So Chutes virou 7 linhas onde cabiam 4, e o que fez a zona foi um argumento que o comando jogou fora calado.** Tres correcoes no `sharpen-bot`; nada no repo do Planilhador foi tocado. **O CASO:** a bet365 juntou as duas selecoes do mesmo jogo num bloco `Criar Aposta` (Judd + Augusto, 5,50) e o cupom fechou em 12,65 (5,50 x 2,30 do Navarro). A tripla saiu certa, porque ela COBRE o cupom; as tres duplas que a legenda pedia nao sao derivaveis de cupom sem preco por perna, e duas ficaram SEM ODD, **com o aviso certo no apoio**. O tipster entao republicou as duplas como bilhetes proprios (#63 @6,32, #64 @4,83, #65 @5,50, este ultimo o proprio bloco) e editou a legenda do #62 para so a tripla. **As tres duplas do #62 continuaram na planilha**, duplicadas: medido no banco, 7 linhas onde cabiam 4, **-0,70u de P/L contado duas vezes** e 3u de turnover a mais. **A TENTATIVA DE CONSERTO E O DEFEITO 1:** `/anular #62 1` e `/anular #62 2`. O regex nao era ancorado e nao olhava o resto da linha (`/\/anular?\s*#?(\d+)/`): leu o 62, descartou o ` 1` **em silencio** e anulou o bilhete INTEIRO. O segundo disse *ja esta anulado*, o `/desanular #62` devolveu tudo, inclusive o que ele queria fora. O comando do caso e o `/anularparcial`, e nada no caminho apontava para ele. **DEFEITO 2, a outra metade:** o aviso de `divergenciasNaoAplicadas` (`src/recompor.js`) dizia *use /anular #N se o bilhete todo caiu* para UMA aposta que saiu da legenda. Aviso que nomeia o comando errado e pior que aviso nenhum, porque parece instrucao. **DEFEITO 3, achado ao medir o print seguinte:** `0,25 tripla`, sem o `u`, nao so perdia a stake (a tripla nao era montada e, como a legenda *nao pediu*, nao havia divergencia para avisar) como caia no `extrairCorrecoesOdd` e virava **correcao de odd 0,25 na multipla**, que transforma green em prejuizo. Agora o `u` e opcional, com duas guardas: linha que fala de ODD nao e linha de stake, e o numero tem de vir ANTES da palavra (depois dela e a odd da casa, `tripla 10.68`). **A posicao e o unico discriminador, e os dois lados usam a mesma.** **O DADO foi consertado pelo Feca, nao por script:** `/anularparcial #62` no apoio, conferido no banco (sobraram `dnxML-T` 0,25u @12,65 L, `dpHvv-D1` W @2,30, `dpH6g-D1` L @4,83 e `dpHBG-D1` L @5,50). Apagar no Postgres nao serviria: o registro do bot seguiria com as apostas VIVAS e a proxima marcacao as ressuscitaria, que e a razao de o `apostasVivas` existir. **GATES: 5, 5 e 5 mutacoes, todas detectadas**, com os blocos RECORTADOS do `index.js` real. No terceiro **uma mutacao escapou na primeira rodada e o buraco era do TESTE**: faltava o caso *stake numa linha, `odd min` na outra*, que e o que prova que a guarda de odd e por LINHA e nao pelo texto inteiro. **ETIQUETA:** os tres commits saem marcados `s352` porque a sessao paralela (Fatia 2 dos Custos) ja ocupava o numero no STATUS quando eles foram escritos; historico pushado nao se reescreve, mesmo precedente da s351. Commits `65517aa`, `2a945bb`, `1abf762` em `Downloads/BOTS/sharpen-bot`, branch `master`, deploy automatico. **DECISAO DO FECA, registrada para nao ser desfeita por engano:** dupla de MESMO JOGO planilhada com a odd de PRODUTO esta certa e **nao leva aviso**. Proposto o aviso com os numeros na mesa (Haaland 1,83 x Sesko 2,60 = 4,758 contra o medido no #62: 2,75 x 2,10 = 5,775 de produto e 5,50 pagos pela casa) e ele recusou: *isso aqui ta certo*. Quando a odd real importar, o caminho e humano e ja existe (`/atualizaodd`, ou postar a combinacao como bilhete proprio). **Nenhuma regra nova para o `CLAUDE.md`** (que segue 1,3 KB acima do teto): as tres regras vivem no comentario do codigo do bot, o lugar canonico delas, igual a s351. **PROXIMO PASSO:** o proximo bilhete do So Chutes fecha a prova no ar. O teste dubla a visao, entao ele prova a montagem e nao prova a leitura do print; o que se confere e uma legenda sem o `u` virando aposta e um `/anular #N <coisa>` sendo recusado.)




> **Histórico completo das sessões 332 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 342)

> **Sessão longa, de custo e do tradutor.** O registro durável está nos planos; isto aqui
> é o mapa para retomar.

### O que entrou no ar hoje

| | Onde está |
|---|---|
| Estudo de custo **remedido** | [`ESTUDO_PRECIFICACAO_2026 §7`](docs/ESTUDO_PRECIFICACAO_2026.md) |
| **Barreira de recaptura**, Fases 0 e 1 | [`PLANO_BARREIRA_RECAPTURA.md`](docs/PLANO_BARREIRA_RECAPTURA.md) (novo) |
| O gate do tradutor **trocado** | [`PLANO_TRADUTOR §II.9`](docs/PLANO_TRADUTOR_DETERMINISTICO.md) |
| Decisões **A e B** do Feca, aplicadas | `MASTER_DESCRICAO §10.1` e **§10.1.1** · `MASTER_OUTPUT §19` |

### O achado que reorganiza a frente

**Em 76,7% das releituras a IA descreveu de forma diferente algo que ela mesma já tinha
descrito.** No maior mercado da base a mesma seleção saiu de **doze** jeitos. O teto de
acerto de qualquer tradutor determinístico contra esse juiz é **~23%**.

E a causa não é a casa (a entrada é byte a byte idêntica) nem só o buraco do MASTER. A
instabilidade segue **quantas decisões o modelo precisa tomar para montar a frase**:

| A descrição exige | Instável |
|---|---|
| Copiar um nome | 18% |
| Montar com linha meia (**tem** template) | 42% |
| Montar com linha partida (sem template) | **100%** |

> **Descrição montada por modelo estocástico não converge para um formato só, por melhor
> que fique o MASTER.** Só compor em código elimina. O tradutor ganhou com isso uma
> segunda justificativa que não depende do preço da API: **ele é o que dá formato único
> ao dado.**

### Onde o tradutor está

| | |
|---|---|
| Cobertura na Bet365 | **68,0%** (7.606 de 11.186) |
| **Conformidade com o MASTER** | **100,0%** contra 67,1% da IA |
| Maior buraco de cobertura | `mercado desconhecido`, 1.644 bilhetes |

### O PRÓXIMO PASSO, concreto

**Ampliar o mapa com a régua nova.** Ela mudou o jogo: rótulo que eu rejeitei na s334 por
"divergir 98% da IA" pode estar certo. Já reavaliei os 10 podados e **dois voltaram**
(`total de pontos`, `corrida - handicap`); os outros quatro têm agora motivo nomeado no
próprio `app/tradutor.py`, logo abaixo do mapa. Falta rodar a mesma reavaliação nos
**1.644 bilhetes de `mercado desconhecido`**, que é onde está o volume.

O script que produz a lista de trabalho está descrito no `PLANO_TRADUTOR §II.8`; ele
casa cada rótulo desconhecido com a maioria da IA e a frequência.

### O que depende do Feca

`BACKLOG §3.8`, decisões **C** (prop de SIM/NÃO, ~100 leituras) e **D** (escopo de tempo,
~60). São pequenas perto das ~5.700 que A e B resolveram, mas destravam quatro rótulos
que hoje estão de fora com motivo escrito.

### Três hipóteses de custo que MORRERAM medidas

Estão no `BACKLOG §3.10`, e valem por poupar a próxima sessão de tentar de novo: aparato
editorial no prompt (**US$ 0,76/mês**), fatiar esportes por casa (**US$ 7,30**), e cortar
o preâmbulo do output (**o modelo não aceita prefill de assistente**; sobra US$ 9/mês pelo
`stop_sequences`). **Os masters estão densos, não inchados.**

### Duas coisas que não são minhas e ficaram vermelhas

- **`CLAUDE.md` está em 65,4 KB, acima do teto de 65.** Veio commitado em `db5b77c` /
  `cea574b`. Pela regra do próprio arquivo, o conserto é mover **caso** para o
  `docs/CASOS.md`, nunca subir o teto.
- **`test_changelog` com 3 falhas:** o `extensor/manifest.json` está numa versão sem nota
  de changelog. Resolve rodando o `scripts/avisar_testers.py`.

---

## Sessão 344 — as 298 de 2025 saíram, e o que impede elas de voltarem

### O que estava errado

A 1ª captura da Betbra (s343) gravou **411 bilhetes de uma vez**, e **298 eram de 2025**
(01/06 a 31/10). A Betbra é a **única** casa deste dono com bilhete daquele ano: toda a
base dele começa em 2026. A exportação da casa trouxe o histórico inteiro junto.

### A metade que faltava: apagar não bastava

`extensor/bda_inject.js` varre **3 anos** por desenho (`DIAS_HISTORICO = 1095`), e o
`lookbackDias` do painel só é respeitado quando pede **mais**. Isso é deliberado desde a
s299, quando a janela curta fez o robô trazer 21 de 418 bilhetes da Bolsa.

Consequência: a próxima captura reencontra os mesmos 298 códigos e regrava tudo, sem erro
nenhum. **Exclusão sem corte dura até a varredura seguinte**, que é a mesma família do
"volta pela CASA, nunca pelo banco". E não havia nada no sistema segurando isso:
`lixeira_bilhetes` é snapshot de reparo, ninguém a consulta no `/salvar`.

### Onde o corte ficou, e por quê

No **`/extrair`**, não na extensão. Dois motivos:

| | |
|---|---|
| O inject é **compartilhado** com a Bolsa de Aposta e vale para todo dono | encurtar o horizonte lá quebraria a casa que ele existe para proteger |
| Aqui a régua é por **(dono, casa)** e roda **antes da IA** | o bloco cortado não paga leitura, não vira TSV e não chega ao `/salvar` |

Régua em `main._CORTE_HISTORICO`, um mapa de par exato: **Feca × Betbra, nada anterior a
01/01/2026**. Casa nenhuma entra ali sem decisão escrita.

Três decisões de leitura, todas com gate próprio:

- A data que manda é a do **EVENTO**, a mesma que decide a coluna Data. Ler a colocação
  cortaria aposta feita em dezembro para jogo de janeiro.
- Bloco **sem data legível FICA** (fail-open). Esconder bilhete é o modo de falha caro,
  porque ninguém reclama do que não apareceu; um a mais para a IA é o que a barreira de
  recaptura já devolve.
- A contagem tem **balde próprio** na tela (`fora_corte`), nunca somada em `xls_skipped`:
  "já salva" afirma que existe uma linha no banco, e esta nunca existiu.

### O que saiu da base

Aplicado **depois** de conferir o deploy no ar (o `/static/index.html` de produção já
servia o campo novo), por `scripts/excluir_historico_fora_do_corte.py`, que lê a régua do
próprio `_CORTE_HISTORICO` em vez de repetir a data.

| | |
|---|---|
| Movidas para `lixeira_bilhetes` | **298**, motivo nomeado, snapshot JSONB |
| Saiu da base | R$ 10.125,25 de turnover · **+R$ 5.262,25 de P/L** |
| Restam na Betbra do Feca | **113**, todas de 2026 |
| Bilhete de 2025 em qualquer casa dele | **zero** |
| Contas dos outros 4 donos na Betbra | intactas |

### Gates

`tests/test_corte_historico.py`: 16 casos sobre blocos **reais** da `sombra_rotulos`,
**6 de 7 mutações detectadas**. A 7ª é inócua (o log some) e está registrada como tal.

A mutação nº 5 é a que interessa: **a chamada removida da rota**. Sem ela o corte fica
verde e inútil, que é como uma regra sem gate morre neste repo.

863 passed / 36 skipped · `check-tokens` verde · `index.html` renderizado headless sem
erro de script.

### Pendente

**Validar ao vivo:** recapturar a Betbra e conferir que as 298 não voltam. É o único teste
que fecha isto, porque o gate lê o fonte da rota, não a executa ponta a ponta.

> **Duas sessões no mesmo `index.html`.** O 1º commit levou junto o selo de captura que a
> outra sessão estava escrevendo no arquivo. Corrigido **antes do push**: o blob do índice
> foi trocado por uma versão com só os meus hunks, e o trabalho dela seguiu intacto no
> working copy. O `git show --stat` é o que acusa isso, e ele só serve se for lido.

---

## Sessão 343 — Betbra: a casa espelho e o cupom que virava múltipla falsa

### A casa

A **Betbra** entrou na captura como **casa espelho da Bolsa de Aposta** — é a mesma
plataforma com outra marca. Medido no navegador, lendo o `src` real dos dois iframes:
rotas de casca idênticas (`/b/exchange` · `/fbook`), Exchange LayBack em
`mexchange.betbra.bet.br` (cookie, 0 parâmetros) e Sportsbook msjxk em
`prod20454-176166310.msjxk.com` (`operatorToken` na URL). **Zero inject novo, zero
formatador novo:** os dois já derivavam o endereço de `location`.

**O único bloqueio real era o `match` do manifest**, preso em `*.bolsadeaposta.bet.br` —
o `bda_inject` nunca subiria em `mexchange.betbra.bet.br`. O Sportsbook já vinha coberto
pelo curinga `*://*.msjxk.com/*`.

Volume: **403 ofertas no Exchange** (mai/2025 → set/2026, varridas em 29 chamadas com zero
erro) e 7 liquidadas + 3 abertas no Sportsbook.

### O achado: `Selections` não é a lista do que foi apostado

No Criador de Apostas (bet builder) o Sportsbook manda, dentro do MESMO array: as **pernas
soltas**, cada uma com a odd de mercado dela — que não foi apostada —, e uma entrada
**agregada** do cupom (`MarketTypeId: "QA0"`), com a odd do conjunto e os textos das pernas
concatenados por ` | `. Quem diz o que entrou é **`MappedSelections`**, uma lista de índices.

O código lia todas. Uma aposta de **4,61** virava uma múltipla de **26,72** (1,13 × 2,30 ×
2,23 × 4,61) — **sem erro nenhum, e com o P/L continuando certo**, porque a odd do bilhete
vem de outro campo. Errariam só turnover, ROI e a assinatura de stake do matcher. Mesma
família de "a stake que era do vizinho, com o P/L intacto" (s311).

Medido em **10 de 10** bilhetes: a odd bate com o produto das *mapped* em 10/10 e com o
produto de todas em **0/10**.

> **O defeito atravessou o recon da Bolsa sem aparecer.** Lá `MappedSelections` é sempre
> `[0]` com uma seleção só: as duas leituras coincidem. O caso da Bolsa fica **verde com ou
> sem a correção** — falso verde do tipo 2 do `CLAUDE.md` ("o dado sintético não exerce a
> regra"), e está escrito no cabeçalho dos dois arquivos.

**Decisões de formato**, todas contra a tela: a ordem das pernas vem do **texto agregado**
(o array traz outra ordem — o `SelectionId` da agregada é `0VS0|2|1`); a perna de um cupom
**não tem odd própria** no bloco (publicá-la seria oferecer à IA um número que parece conta
feita e não é); e o tipo virou `Criador de Apostas (bet builder — N seleções do MESMO jogo,
odd única do cupom)`, nunca "Múltipla", que mentiria em três frentes.

### O boost, que a Bolsa tinha como "não confirmado"

`ClientOdds` é a odd **com** boost e `DbTrueOdds` da agregada é a **sem**. A tela risca a
segunda e estampa a primeira (`2.89 → 3.36`). A odd que vale é a `ClientOdds` do bilhete —
200 × 3,36 = 672 = "Retorno Total" da tela. A regra global de W (`retorno ÷ stake`) absorve
o boost sozinha; o percentual **não** se deduz do `Campaigns[].Type` (1,32 e 1,16 medidos em
tipos diferentes).

### Gates

| | |
|---|---|
| Harness | **28 casos, 447 bilhetes** — verde |
| Mutação | **5 de 5 detectadas** pelo caso Betbra · **0 de 5** pelo caso Bolsa |
| `audit_sharpenup` / `audit_casas` / `audit_changelog` | sem FAIL |
| `pytest` | 826 passed / 36 skipped |
| Manifest | 0.7.10 → **0.7.11**, aviso publicado no grupo (`message_id 3380`) |

As 5 mutações confirmam por medição o que o cabeçalho do caso dizia por dedução: **a fixture
da Bolsa não protege esta regra.** Sem o caso da Betbra, a correção teria entrado parecendo
coberta.

### Duas coisas medidas antes de registrar

**A grafia.** `_CASA_DISPLAY` é retroativo, e o código já tinha duas grafias divergentes
(`import_arrudex_xlsx.py` grava `Betbra`, `import_dashboard_xlsx.py` grava `BetBra`). No
banco só existe **`Betbra`**, em todas as cinco tabelas onde `casa` é texto: 5 contas, 158
bilhetes, 1 em `casas_meta`, 23 em `correcoes`, 1 em `uso_tokens`. A decisão do Feca
("Betbra para todos") confirmou a base.

**As séries de código são por CASA, não por plataforma.** Exchange da Betbra: 7–8 dígitos.
Exchange da Bolsa: 9. Mesma plataforma, contadores independentes — **comprimento de código
não diz de que casa o bilhete é**.

### Pendente

**Validação ao vivo**, que não fecha sem o operador: recarregar a extensão, **Ctrl+Shift+R
na aba da Betbra** (recarregar a extensão não re-injeta em aba já aberta) e **F5 no
dashboard** (a casa nova não aparece no seletor numa aba que já estava aberta).

**Sem cobertura automatizada no harness, e portanto ainda dependentes de teste ao vivo:**
`SUPERBET` e `BETESPORTE` — nenhuma das duas tocada por este diff.

**Não provado nesta casa** (medido, não suposto): `lay` (403 de 403 são `back`),
cashout/Retirada, freebet, `push_win`/`push_lose`, casamento parcial no Exchange, e
`MappedSelections` com 2+ índices (múltipla de eventos diferentes).

---

---

## 1. O que estamos construindo

A base de conhecimento (masters) do scanner de bets. Camada **global** (regra única, muda devagar) + camada **por casa** (traduz cada casa para a língua global). A saída final é **TSV**.

---

## 2. Invariantes (não se quebram)

1. O app **lê** os masters, **nunca escreve** neles. Mudança de regra = diff revisado por humano + commit. Git é a porta de aprovação.
2. O arquivo de casa **traduz** a casa para a língua global; **não redefine** regra global.
3. **Cálculo é global, localização é da casa.** Ex.: "W → Retorno÷Stake" é global; "o retorno está no campo PRÊMIO" é da Superbet.
4. Nenhuma regra nova é aplicada sozinha. Propor como diff, esperar aprovação.

---

## 3. Estrutura-alvo do repo

```
/global/                 (autoridade única — 6 masters)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/                  (1 arquivo por casa — traduz, nunca redefine)
    CASA_MODELO.md         (gabarito — 15 seções)
    CASA_BET365.md
    CASA_BETANO.md
    CASA_BETESPORTE.md
    CASA_BETFAIR.md
    CASA_BETNACIONAL.md
    CASA_BOLSADEAPOSTA.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_NOVIBET.md        (plataforma própria BlueBrown — replay que ALARGA o filtro)
    CASA_PINNACLE.md
    CASA_PITACO.md         (ex-"Rei do Pitaco" — gRPC-Web/protobuf; 2 grafias, 1 manual)
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_JONBET.md
    CASA_BETBOOM.md        (espelho técnico da Jonbet — mesmo motor BetBy/sptpub)
    CASA_VAIDEBET.md
    CASA_ESPORTIVA.md      (espelho técnico da VaideBet — mesmo motor Altenar/BIA)
    CASA_JOGODEOURO.md     (3ª casa Altenar — captura na TELA CHEIA do histórico)
    CASA_BETPIX365.md      (4ª casa Altenar — a casa NÃO chama o endpoint que ela precisa)
    CASA_ESTRELABET.md     (5ª casa Altenar — a mais lisa na tela; o gateway recusa credencial)
    CASA_STAKE.md          (mesma Kambi da KTO, mas REST próprio — captura NÃO é espelho)
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (guias, referências, ADRs, planos VIVOS — índice em docs/README.md)
    CASOS.md               (os casos que originaram as regras do CLAUDE.md; não auto-carregado)
    HISTORICO.md           (índice) → historico/  (6 partições por faixa de sessão)
    arquivo/               (o que virou registro; índice em arquivo/README.md)
CLAUDE.md                  (regras vinculantes)
STATUS.md                  (este arquivo — estado atual + as 3 últimas sessões)
BACKLOG.md                 (tudo que está aberto)
```

**Um arquivo, uma pergunta** (invariante #10), com gate em `python tools/check_docs.py`.

Os 6 MASTER_*.md vivem em `/global/`; as **28** casas em `/casas/` (Polymarket por API, as demais por IA/texto), mais o gabarito `CASA_MODELO.md`.

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Identidade na tabela `usuarios` do Postgres via cache em memória (s233 — Fase 1 do `docs/PLANO_MULTIUSUARIO_2026.md`); os dicts de `app/auth.py` são a SEMENTE. Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway (o seed leva ao banco no boot); base nasce vazia sem migration. Suspender no banco (`status`) revoga login E sessão em ≤60s.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Base do `SoChutes` (s224):** 23.199 apostas all-time do tipster Só Chutes (17/09/2024 → 27/07/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` (Bet365/Superbet/Betano; casa não informada entrou como Bet365 — decisão do Feca). **Stake em UNIDADES** (1u = 1; o P/L do dashboard é o P/L em unidades: +1.381,29u). Script idempotente: `scripts/import_sochutes_xlsx.py`. O planilhamento novo é do **bot Sharpen** (repo próprio `BOTS/sharpen-bot`, ver s223), que desde a **s251** roda 24/7 no Railway — serviço `sharpen-bot`, no mesmo projeto do app, com o estado em volume próprio. Ele escreve nesta base por `/salvar` + `/bilhetes/tipster`: **mudança no contrato dessas rotas quebra o bot em silêncio.**
- **Base do `Flurray` / tipster Fleury (s260):** 473 apostas (11/06 → 09/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 4 casas (Bet365, Betano, Superbet, BetMGM). Base de **nicho**: 100 % mercados de finalização no futebol. **Stake em UNIDADES** (1u = 1; P/L +122,30u sobre 447,80u de turnover). Script idempotente: `scripts/import_fleury_xlsx.py`. **⚠️ A marca é `Fleury` e o username é `Flurray`** — o `dono` é sempre o username; a ponte entre os dois é o `TIPSTERS_PUBLICOS`. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/fleury`** (3ª do sistema).
- **Base do `passapano` / tipster PassaTips VIP (s273):** 911 apostas (02/06 → 17/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 7 casas (Bet365, Betano, Betnacional, Betvip, Estrela Bet, Novibet, Suprema Bet). Base **multiesporte**: 20 esportes, de futebol e tênis a polo aquático e críquete. **Stake em UNIDADES** (1u = 1; P/L +90,20u sobre 1.102,61u de turnover liquidado). Script idempotente: `scripts/import_passatips_xlsx.py`. **⚠️ A marca é `PassaTips VIP` e o username é `passapano`** — mesmo caso do Fleury. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/passatipsvip`** (5ª do sistema). O planilhamento novo é do **bot Sharpen** (4º tenant, `passatips`) — **1º perfil sem visão**, porque a legenda dele já traz tudo.
- **Casas:** 28 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **25 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210), **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`), BetNacional, Jonbet (BetBy/sptpub, s248), **Betboom** (s250 — **espelho da Jonbet**: mesmo motor BetBy, mesmo `jb_inject.js`) **Pitaco** (s270 — plataforma própria, **gRPC-Web/protobuf binário**, replay puro) **Novibet** (s271 — plataforma própria BlueBrown, replay puro que **alarga o filtro** da tela: ela pede 24 h e só as fechadas) e **Estrela Bet** (s303 — **5ª casa Altenar**, mesmo `vb_inject.js`; a mais lisa na TELA e a única cujo gateway **recusa `credentials:"include"`**). **Dois pares de espelho, zero código duplicado** — o inject casa por caminho de API, nunca por host, e é isso que faz a casa seguinte da mesma plataforma custar registro em vez de implementação.
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências

> **As pendências mudaram de casa.** Elas moram em **[`BACKLOG.md`](BACKLOG.md)**, na raiz —
> organizadas por natureza (bloqueado por humano · por amostra · decisão do Feca · dívida
> técnica medida · planos com fase aberta · não medido), com as marcas
> **VIVA / NÃO-MEDIDA / HUMANA** da varredura da s261 preservadas.
>
> Motivo: o §5 tinha **51 KB** e ficava atrás de 124 KB de changelog. Quatro arquivos
> disputavam o papel de "onde o projeto está" e três descreviam o projeto de julho. Ver
> [`docs/FAXINA_PROPOSTA.md`](docs/FAXINA_PROPOSTA.md).
>
> **Pendência nova vai para o `BACKLOG.md`, nunca para cá** (invariante #10 do `CLAUDE.md`).
> Gate: `python tools/check_docs.py`.

As três mais quentes de hoje, com o resto no `BACKLOG.md`:

1. **`apps_script/Code_LavaFatuch.gs` expõe a base do Fatuch sem autenticação nenhuma.**
   `doGet(e)` na linha 95, zero token ou segredo no arquivo — e é a fronteira que alimenta o
   `app/planilha_viva.py`, a base financeira **ao vivo** de um cliente. Qualquer um com a URL
   lê. Medido em 06/09. → `BACKLOG §4.3`, e é sessão própria.

2. **PassaTips: 3 passos humanos para fechar o buraco do #259, e a ORDEM importa.**
   Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
   (`resultado` não é congelado). O `/anular #259` **apaga** a linha `Under 1.5 cartões
   Elche`, então o tipster tem de repostar **antes**. → `BACKLOG §1`.

3. **Polymarket ainda mistura `entry_odd` e `realized_odd`** (`AUDITORIA_2026 #32`).
   `_calc_odd` (`app/polymarket.py:894`) devolve um número só, e o próprio comentário da
   `:987` admite "odd de entrada, **ou** a efetiva na liquidação". É o maior risco quant
   aberto e mexe em P/L. → `BACKLOG §4.1`.

---

## 6. Rodar / produção

**App em produção:** `https://sharpen.bet/` (www.sharpen.bet → Railway)

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/sharpen`, renomeado de `extrator` na sessão 129). Deploy automático via Railway conectado ao GitHub — push dispara deploy.

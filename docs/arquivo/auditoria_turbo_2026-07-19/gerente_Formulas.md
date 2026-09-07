## Formulas

**Veredito da area:** Precisa atencao — o nucleo de dinheiro (P/L) esta solido e correto, mas o indice composto "Nivel de Solidez" tem dois modos de falha reais e o backtest de tipster nao mede o que promete.

**Top 3 acoes prioritarias:**
- **Corrigir a Solidez para nao selar perdedor como "Baixa" e nao inflar edge trivial** (achados criticos): hoje um book grande e perdedor nunca cai de 0,40, e +0,5% de yield sobre 25.726 apostas vira "Muito Alta". Risco direto de o CEO/usuario ler seguranca onde nao ha.
- **Alinhar o Win Rate do extrator (backend) a meia-ponderacao do dashboard**: a mesma conta com HW/HL exibe percentuais diferentes nas duas telas, contradizendo o proprio docstring. O fix #27 da auditoria ficou so no front.
- **Reabrir o metodo do backtest de tipster antes da Fase 1**: ele nao faz o split temporal que o proprio plano exige e nao mede Jonathan/Lava — justamente as carteiras que provariam overfit ao Feca.

### Achados criticos e altos (detalhados)

**1. Solidez sela perdedor como "Baixa" — nunca "Muito Baixa" (medio/confirmado)** — `app.js:253-261`
Dois dos quatro componentes (sAmostra 20% + sVar 20%) sao agnosticos a lucro. Um tipster que perde consistentemente, com muitas apostas (>=1000) e odd media baixa (<=3), floreia sAmostra=1 e sVar=1 → score = (0+0+2+2)/10 = 0,40 = "Baixa", por pior que seja o prejuizo. A Solidez nao penaliza prejuizo estrutural.
**Acao:** gate de rentabilidade — se P/L ou yield <= 0, forcar "Muito Baixa"; ou rebaixar drasticamente o peso de amostra/odd quando o resultado e negativo. [esforco: pequeno]

**2. Solidez infla para edge economicamente trivial (baixo/plausivel)** — `app.js:253-261`
O indice recompensa o tamanho da amostra duas vezes (sEdge via p-value e sAmostra crescem ambos com n). Significancia estatistica nao e significancia pratica: +0,5% de yield sobre base enorme dispara p<0,001 e n>=1000 e atinge 5/10 antes de folga e odd, podendo ser selado como "Muito Alta".
**Acao:** separar "forca do sinal" de "tamanho de amostra" — usar p-value so como gate de confiabilidade e pontuar a qualidade pelo yield/edge com magnitude economica (IC do yield acima de limiar pratico). Adicionar disclaimer "Solidez alta ≠ edge grande". [esforco: medio]

**3. Win Rate diverge entre extrator e dashboard (medio/nao-verificado)** — `repository.py:1107-1115`
`_resumir_apostas` conta HW como vitoria cheia (wins += 1 para W e HW; win_rate = wins/settled), enquanto o front usa `wrFrac` (HW = ½ vitoria, HL = ½ derrota). A mesma conta com HW/HL mostra percentuais distintos nas duas telas, contradizendo o docstring de `resumo_conta` (repository.py:1135). A auditoria #27 aplicou a meia-ponderacao so no frontend.
**Acao:** alinhar `_resumir_apostas` a formula canonica do wrFrac (numerador W + ½·HW; denominador encerradas − ½·HW − ½·HL, excluindo V) ou extrair para ponto unico compartilhado. Reabrir o item #27 da AUDITORIA_2026.md. [esforco: pequeno]

**4. Backtest de tipster nao faz split temporal treino/teste (baixo/plausivel)** — `backtest_matcher.py:143-183`
O plano manda "treina no passado, testa no bloco recente" (PLANO_INTELIGENCIA_TIPSTER §5/§10B). O script avalia a janela recente contra o cadastro atual inteiro, sem split. Inofensivo hoje (v4/v5 e 100% declarativo), mas o script e a regua canonica — quando a Fase 1 somar pseudo-contagens de historico observado sobre a tabela inteira, a regua vaza dado futuro e infla a metrica.
**Acao:** refatorar o harness para split temporal real (ordenar por tempo, congelar conhecimento ate um corte, testar so nos posteriores) antes de plugar historico; assertar que nenhuma contagem seja construida sobre bilhetes com data >= corte. [esforco: medio]

**5. Holdout temporal e estruturalmente impossivel: assinatura declarada nao tem era (medio/plausivel)** — `backtest_matcher.py:86-100`
O cadastro (dica_stake/esportes/mercados/casas) e um unico snapshot sem vigencia, mas a convencao do tipster muda no tempo (Arrudex final6→final0 em fev; Peixe adota final6 so em jun). Aplicar a convencao de hoje a bilhetes de qualquer idade e vazamento de informacao futura; mesmo com janela de 14 dias, o cadastro pode ter sido ajustado a mao olhando esses bilhetes (in-sample). A metrica reportada e otimista por construcao.
**Acao:** reconhecer no doc que regua honesta exige assinatura datada (a imagem da escada de unidade) e derivar a assinatura por era do historico observado. Enquanto isso, rotular a saida como "avaliacao in-sample / otimista", nao "linha de base holdout". [esforco: grande]

**6. Carteiras importadas (Jonathan/Lava) invisiveis ou degeneradas no backtest (medio/nao-verificado)** — `backtest_matcher.py:13-16`
O filtro usa `criado_em`, que em base importada de uma vez e constante (= data do import): janela retorna N=0 e a carteira e pulada, ou cai a base inteira sem ordenacao temporal. A razao de existir da regua multi-carteira e flagrar overfit ao Feca — ela silenciosamente nao mede 2 das 4 carteiras, exatamente as que testariam generalizacao.
**Acao:** usar a coluna `data` (evento) como eixo temporal quando `criado_em` for constante, ou detectar base importada (variancia ~0) e trocar de eixo. Sem isso, remover Jonathan/Lava da tabela de saida para nao passar falsa cobertura. [esforco: medio]

### Achados medios e baixos (resumidos em tabela)

| # | Sev | Achado | Local | Acao | Esforco |
|---|---|---|---|---|---|
| 7 | medio | p-value e Monte Carlo assumem apostas i.i.d.; apostas reais sao correlacionadas → p-value otimista e cauda de drawdown (p95/p99) subestimada | `app.js:215-240` | Block/cluster bootstrap por evento/dia onde houver ID; no minimo documentar direcao do vies no tooltip | grande |
| 8 | medio | BASE_BANK=100000 fixo torna o Drawdown % arbitrario e nao comparavel entre donos | `app.js:149-161` | Parametrizar banca por dono (ou derivar do turnover); ate la rotular "sobre banca de referencia R$100k" | medio |
| 9 | medio | MDD agregado por dia esconde drawdown intradiario (limite inferior); convive com calcTopoDrawdown linha-a-linha (resolucoes diferentes) | `app.js:149-161` | Unificar num unico motor bet-a-bet ordenado por data+hora; documentar aproximacao sem hora | medio |
| 10 | medio | Unidade de fallback usa media das stakes filtradas na tela → "u" nao comparavel entre views; divergencia tripla front/backend/plano | `app.js:28-33` | Fixar 1u de fallback na media all-time do tipster (ou global do cliente), independente do filtro; sinalizar aproximacao na UI | pequeno |
| 11 | baixo | p-value testa yield COM Void, mas o ROI exibido e SEM Void → o numero testado nao e o exibido | `app.js:215` | Excluir Void do calculo do p-value, ou explicitar que o teste inclui Void | trivial |
| 12 | baixo | sFolga usa DD medio simulado (xmdd) mas comparte o benchmark >5 do Recovery Factor real (MDD real) → satura em 1 e nao discrimina | `app.js:254-258` | Usar o mesmo denominador (MDD real) na sFolga ou recalibrar limiares; alinhar rotulos | pequeno |
| 13 | baixo | Peso de stake (25) domina esporte (10) e casa (5) → pode sugerir tipster com um unico sinal fraco | `index.html:4787-4813` | Ja planejado p/ Fase 1; enquanto v5, medir no backtest a precisao dos bilhetes sugeridos SO por stake | pequeno |
| 14 | baixo | Precisao penalizada por casos insoluveis: bilhetes de tipster arquivado (real ∉ ativos) entram no denominador como miss garantido | `backtest_matcher.py:170-183` | Condicionar precisao a real ∈ ativos (usar `com_perfil`); excluir/separar pares arquivados da matriz | trivial |
| 15 | info | Arredondamento por linha antes da soma gera drift de centavos vs SUM da planilha (Σ round vs round Σ); sub-R$1 na maioria | `repository.py:110` | Expor P/L nao-arredondado para o somatorio se paridade exata for requisito; senao documentar como diferenca aceita | pequeno |
| 16 | info | Dead code "wins" conta HW cheio (residuo do bug #27), definido 3x e nunca usado — armadilha se religado a UI | `performance.js:405` | Remover as tres declaracoes mortas | trivial |
| 17 | info | Divergencia de nomenclatura do matcher: backtest diz "v4", index.html e plano dizem "v5" | `backtest_matcher.py:1-9` | Padronizar a etiqueta de versao em codigo/docstring/plano numa fonte unica | trivial |

### Pontos positivos (o que esta bem feito)

- **P/L centralizado numa unica funcao espelhando o SWITCH da planilha** (`repository.py:70-110`): todo P/L do sistema deriva de `calcular_pl` (campo nunca persistido). As cinco formulas (W/L/V/HW/HL) e a subtracao Valor−stake batem exatamente com MASTER_RESULTADO_2026 §5. HW/HL e cashout (160/40) conferidos, zero divergencia backend↔JS. Modelo certo — manter.
- **Odd sempre com precisao plena no calculo, com guard** (`repository.py:98-102`): `_num_or_none` preserva precisao total (inclusive ponto-decimal das multiplas Betano), truncando so no display — cumpre a regra primordial da odd. Odd ilegivel/≤0 em W/HW devolve None (linha aberta) em vez de virar vitoria −stake.
- **Win rate fraciona HW/HL corretamente** (`app.js:136-140`): a divida #10/#27 esta de fato resolvida no front — `wrFrac` trata HW=½ e HL=½, com fallback anti-NaN. Falta so alinhar o backend (achado #3).
- **Motor bootstrap-t e Monte Carlo bem construidos e deterministicos** (`app.js:215-240`): p-value studentizado com residuos centrados no nulo, correcao +1/(sims+1), RNG semeado (mesmo numero entre abas), cache O(n) e Web Worker, 10.000 simulacoes. A limitacao e a premissa i.i.d., nao a implementacao.
- **Disclaimers honestos nos tooltips** (`overview.js:299`): p-value rotulado "indicador heuristico... nao e prova estatistica nem recomendacao", Monte Carlo "estimativa... nao aconteceu", Solidez "indice composto". Estender esses disclaimers aos dois modos de falha da Solidez (achados #1 e #2).
- **Matematica de unidades correta, honesta e bem testada** (`repository.py:113-167`): cada bilhete dividido pela unidade vigente na sua data (funcao-degrau), preservando o resultado real em "u" sem reprocessar o passado; datas normalizadas para ISO; boa cobertura em `test_unidades.py`.
- **Backtest exclui procedencia 'sugerido'** (`backtest_matcher.py:163-167`): cumpre a regra de ouro do treino (nunca aprender da propria sugestao); `origem_tipster` gravado com default 'humano' num unico ponto de wiring.
- **Port do matcher para o backtest e fiel ao runtime** (`backtest_matcher.py:57-141`): reproduz linha a linha a logica do index.html (veto, distintividade ≤2, folga 7, dono unico dispensa folga, casa-feudo). A regua mede o codigo realmente deployado — pre-condicao para o backtest ter valor. Ao evoluir, extrair a logica para modulo unico consumido por runtime e backtest.
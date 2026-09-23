# eval_zeroshot — harness de regressão da extração "modo cego"

Mede quanto o modelo acerta a **categoria de aposta** vendo o rótulo cru da casa,
**sem** o arquivo de tradução (`casas/CASA_*.md`). É a rede de medição da frente
worldwide: antes de mexer no prompt de extração (Fase 1+), rode isto para saber
se regrediu. Contexto e plano: [`../../docs/PLANO_EXTRACAO_WORLDWIDE.md`](../../docs/PLANO_EXTRACAO_WORLDWIDE.md).

## Como funciona

O gabarito sai dos próprios §9 ("Mapa de mercados") das casas — pares
`rótulo cru → categoria global` já confirmados por humano. O modelo recebe **só os
6 `global/MASTER_*.md`** (taxonomia) e tenta remapear cada rótulo. Comparamos com o gold.

## Rodar

Tudo é controlado por variáveis de ambiente, e o **default de cada uma reproduz a rodada de
julho**: `EVAL_SUFIXO=""` · `EVAL_MODEL=claude-sonnet-4-6` · `EVAL_THINKING=disabled` ·
`EVAL_MAX_TOKENS=4000` · `EVAL_TEMPERATURE` vazio.

```
# 1) extrai o gabarito e a entrada do modelo
EVAL_SUFIXO=_v2 python tools/eval_zeroshot/extrair_pares.py
#    -> pares_v2.json (gabarito) + labels_input_v2.tsv (entrada)
#    SEM o sufixo ele reescreveria o gabarito de JULHO — não faça isso.

# 2) rodar um modelo sobre labels_input.tsv em MODO CEGO e salvar preds.tsv
#    (indice <TAB> categoria). O modelo só pode ler global/MASTER_*.md;
#    é PROIBIDO abrir qualquer casas/CASA_*.md (invalidaria o teste).
#    Duas formas:
#      a) app/ com ANTHROPIC_API_KEY no .env (mesmo Sonnet de produção), ou
#      b) um agente Claude com a taxonomia global (como na 1ª rodada).

# 3) pontua
EVAL_SUFIXO=_v2 python tools/eval_zeroshot/pontuar.py
#    -> RESULTADO_v2.txt + resumo no stdout
```

## Métricas

- **Acerto de categoria** (alvo): match após normalizar a anotação do gold
  (`Anytime (descr. - 2+ Gols)` → `Anytime`; `Outros ⚠️` → `Outros`). É o que importa.
- **Match cru**: string exata (subconta, por causa das anotações). Objetivo, secundário.
- **Erro silencioso**: categoria errada **e** não sinalizada. É o que faz mal — a meta é minimizar.
- **Falha segura**: modelo respondeu `Outros` (incerteza) → cairia no amarelo pro usuário. Não é silencioso.
- **Alucinação**: predição fora da lista oficial da §3 → o guardrail de enum (Fase 1) mata.

## ⚠️ O REGIME desta bancada: `thinking` DESLIGADO

**Toda rodada roda com `thinking: {"type": "disabled"}`** (`EVAL_THINKING`, default `disabled`).
Não é detalhe de implementação, é o que torna a comparação válida — e quem mudar isso sem ler
aqui vai comparar **regimes** achando que compara **modelos**.

- **Por que existe:** o `run_blind.py` de julho nunca passava `thinking`, porque o modelo da
  época não pensava. O Sonnet 5 pensa por padrão e `max_tokens` é o teto **total**: ele gastou
  4000 — e depois 16000 — inteiros raciocinando, devolveu `stop_reason=max_tokens` com
  `content=['thinking']` e **zero bloco de texto**. A bancada leu 282 `<VAZIO>` e cuspiu
  **0% com 282 alucinações**. Subir o teto não conserta: o pensamento adaptativo preenche o
  que houver.
- **Por que desligado e não `effort: low`:** com o 4.6 sem pensar e o 5 pensando, toda diferença
  de acerto fica inseparável de *"um pensou e o outro não"*. Desligado é o único regime que os
  três modelos aceitam igual (medido: 282/282 linhas nos três).
- **O preço disso, e ele é real:** desligar thinking pode penalizar mais um modelo desenhado
  para pensar. **A comparação abaixo é válida NESTE regime e não fora dele.**

**`temperature` não é o caminho para determinismo, e não é nem opção.** Foi **removido** no
Sonnet 5 e no Opus 5 (400 `invalid_request_error`); só a geração anterior aceita. E onde
aceita **não determina**: 3 rodadas de Sonnet 4.6 com `temperature=0` deram 257/256/257, com
2 a 3 predições diferentes entre si. **A dispersão desta bancada se MEDE com N amostras.**

## Resultado — 2026-09-23 (sessão 384), gabarito `pares_v2.json`

**282 pares de 33 casas, 35 categorias** (34 arquivos varridos; a `BETESPORTE` ainda não tem §9 com mercado confirmado), N=5 por modelo, `thinking` desligado.
Desvio é o da amostra; a faixa é média ± 2 desvios (conservadora, N pequeno).

| Modelo | média | desvio | pior | melhor | erro silenc. (méd.) | alucin. | US$/rodada | US$/par |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Opus 5** | **92,2%** | 1,00 pp | 256/282 | 262/282 | **18,6** | 0 | 0,4018 | 0,00142 |
| **Sonnet 4.6** | **91,1%** | 0,30 pp | 256/282 | 258/282 | 25,0 | 0 | 0,1899 | 0,00067 |
| **Sonnet 5** | **87,4%** | 0,96 pp | 243/282 | 249/282 | 25,0 | 0 | **0,1606** | **0,00057** |

**Leitura, e ela para onde o desvio manda:**

- **Opus 5 × Sonnet 4.6: INDISTINGUÍVEL.** As faixas se cruzam ([90,2–94,2] × [90,5–91,7]) e
  os brutos também (256 aparece nos dois). Não ordene os dois com esta bancada.
- **Opus 5 > Sonnet 5** e **Sonnet 4.6 > Sonnet 5**: aqui as faixas **não** se tocam.
- Opus 5 comete **menos erro silencioso** (18,6 contra 25,0), que é a métrica que faz mal.
- **Zero alucinação** nos três, em 15 rodadas.

> ⚠️ **Pergunta aberta, e ela decide a leitura acima:** o Sonnet 5 sai atrás **neste regime**,
> com o pensamento desligado. Ninguém mediu ainda o mesmo conjunto com `EVAL_THINKING=adaptive`.
> Até isso existir, *"Sonnet 5 é pior nesta tarefa"* é **conclusão do regime**, não do modelo.

## Registro histórico — 2026-07-12 (sessão 132), gabarito `pares.json`

> **Isto é registro datado, não métrica corrente.** Ficou por dois meses na tabela de
> métricas como se fosse medida estável, e não era: **tirada única, sem temperatura fixada,
> sem thinking configurado, contra um gabarito de 13 casas que a taxonomia já ultrapassou.**

`preds.tsv` guarda a saída do **Sonnet 4.6** de então, sobre 110 rótulos de 13 casas:
**107/110 = 97,3%** de acerto de categoria, match cru 90,0%, 1 erro silencioso, 2 falhas
seguras, 0 alucinações.

**O que a s384 descobriu ao tentar reproduzir:**

1. **`pontuar.py` sobre os arquivos commitados reproduz exato** (107/110, byte a byte). A
   pontuação é determinística.
2. **A bancada, não.** O mesmo `claude-sonnet-4-6`, no mesmo gabarito, em modo cego, devolveu
   **104/110**. Seis das 110 predições mudaram.
3. **O gabarito de julho está VENCIDO em pelo menos um par:** o `#27 'Total de Faltas'` tem
   gold `Outros ⚠️ (nicho)` porque em 12/07 não havia categoria. A **`Faltas` foi criada
   depois**. Hoje o modelo responde `Faltas`, que é certo, e a bancada conta como erro.
4. **110 pares não separam 97% de 94%.** IC95 de Wilson: 97,3% → [92,3–99,1]; 94,5% →
   [88,6–97,5]. McNemar exato sobre as discordâncias: **p = 0,375**.

**Os dois gabaritos convivem de propósito.** `pares.json` é a prova do que se mediu em julho;
`pares_v2.json` é o conjunto corrente. `extrair_pares.py` **nunca** sobrescreve o antigo.

## Ressalvas (não superinterpretar)

1. Testa **categorização**, não OCR/locale/stake/odd.
2. Rótulos do §9 são mais limpos que OCR real (viés otimista); mas o modelo vê só o
   rótulo, sem o resto do bilhete que produção vê (viés pessimista) → se cancelam.
3. O gold vem do §9 e às vezes traz rótulos não-canônicos; a normalização cuida das
   anotações, mas trate o número como **direcional**, não nota de prova.

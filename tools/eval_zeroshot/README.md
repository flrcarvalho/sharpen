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

```
# 1) extrai o gabarito e a entrada do modelo
python tools/eval_zeroshot/extrair_pares.py
#    -> pares.json (gabarito) + labels_input.tsv (entrada)

# 2) rodar um modelo sobre labels_input.tsv em MODO CEGO e salvar preds.tsv
#    (indice <TAB> categoria). O modelo só pode ler global/MASTER_*.md;
#    é PROIBIDO abrir qualquer casas/CASA_*.md (invalidaria o teste).
#    Duas formas:
#      a) app/ com ANTHROPIC_API_KEY no .env (mesmo Sonnet de produção), ou
#      b) um agente Claude com a taxonomia global (como na 1ª rodada).

# 3) pontua
python tools/eval_zeroshot/pontuar.py
#    -> RESULTADO.txt + resumo no stdout
```

## Métricas

- **Acerto de categoria** (alvo): match após normalizar a anotação do gold
  (`Anytime (descr. - 2+ Gols)` → `Anytime`; `Outros ⚠️` → `Outros`). É o que importa.
- **Match cru**: string exata (subconta, por causa das anotações). Objetivo, secundário.
- **Erro silencioso**: categoria errada **e** não sinalizada. É o que faz mal — a meta é minimizar.
- **Falha segura**: modelo respondeu `Outros` (incerteza) → cairia no amarelo pro usuário. Não é silencioso.
- **Alucinação**: predição fora da lista oficial da §3 → o guardrail de enum (Fase 1) mata.

## Resultado registrado (Fase 0 — 2026-07-12, sessão 132)

`preds.tsv` guarda a saída da 1ª rodada (Sonnet, modo cego, 110 rótulos de 13 casas):

| Métrica | Valor |
|---|---|
| Acerto de categoria | **94,5%** (104/110) |
| Match cru | 90,0% (99/110) |
| Erro silencioso | **3,6%** (4/110) — todos nicho obscuro |
| Falha segura (pred=Outros) | 2/110 |
| Alucinação | **0/110** (`Corridas` É categoria §3 válida — baseball) |

## Ressalvas (não superinterpretar)

1. Testa **categorização**, não OCR/locale/stake/odd.
2. Rótulos do §9 são mais limpos que OCR real (viés otimista); mas o modelo vê só o
   rótulo, sem o resto do bilhete que produção vê (viés pessimista) → se cancelam.
3. O gold vem do §9 e às vezes traz rótulos não-canônicos; a normalização cuida das
   anotações, mas trate o número como **direcional**, não nota de prova.

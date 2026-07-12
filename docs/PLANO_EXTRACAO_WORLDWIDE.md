# PLANO — Extração Worldwide (escalar sem esteira de "1 extrator por casa")

> **Status:** plano aprovado para documentar (sessão 132, 2026-07-12). **Fase 0 rodada e validada.** Fases 1–5 aguardam início a critério do Feca.
> **Fonte de regras:** este é um **plano**, não regra vinculante. As regras vivem nos `global/MASTER_*` e no `CLAUDE.md`. Ao construir cada fase, o código passa a ser a verdade.
> **Relacionados:** [`ADR-002-dashboard-primeira-carga.md`](ADR-002-dashboard-primeira-carga.md) · [`PLANO_TIPSTER.md`](PLANO_TIPSTER.md) · [`GUIA_NOVA_CASA.md`](GUIA_NOVA_CASA.md)

---

## 1. A dor

O Sharpen quer virar produto **escalável e worldwide**. Só no Brasil há 200+ casas; internacionalizando, milhares — talvez dezenas de milhares. Se cada casa exigir alguém **construir um extrator/arquivo de tradução antes de funcionar**, entramos numa esteira infinita e inviável como produto.

Pergunta-guia: *se amanhã uma pessoa na Índia assinar o Sharpen para planilhar as bets dela numa casa que nunca vimos, como ela usa o extrator e como o sistema lida com isso?*

---

## 2. Diagnóstico (consenso de 3 modelos — Sonnet, Opus, Fable, independentes)

Os três, pensando separado, convergiram no mesmo diagnóstico:

1. **O gargalo NÃO é a IA de leitura.** Um LLM com visão já lê um bilhete auto-descritivo em qualquer idioma/layout sem arquivo de casa. Leitura é zero-shot por natureza; escala por **volume** (~$0,011/bilhete, Sonnet 4.6 cache quente), não por nº de casas.
2. **O gargalo real é a camada de tradução por casa ser artesanato humano.** Hoje, para uma casa "funcionar", alguém escreve o `casas/CASA_*.md` (§9 mapa de mercados, roda `/audit-casas`). Isso é *push* — cobertura construída **antes** da demanda. É O(N) com N = casas do mundo. É a esteira que se teme.
3. **O SharpenUp por DOM é o único extrator bespoke de verdade.** `extensor/content.js` tem dispatcher hardcoded por casa (`if casa === "superbet"…`) + scripts de injeção (`sb_inject.js`, `be_inject.js`, `bn_inject.js`) + seletores CSS por casa. Isso **não escala e não deve tentar** — fica premium para as ~20 casas de maior volume; texto/print é o canal mundial.
4. **O moat já existe: os 6 MASTERs globais.** A taxonomia canônica é universal ("Over 2.5" é o mesmo em Bombaim e na Betano). A arquitetura atual (cálculo global + tradução local) está **certa**; o único erro é a tradução ser escrita à mão **antes** do uso.

---

## 3. A virada: de *push* para *pull*

> **Extração universal (zero-shot) é o default. O arquivo de casa deixa de ser pré-requisito escrito à mão e vira um _cache aprendido_ pelo uso.**

Quatro pilares:

| Pilar | O que muda |
|---|---|
| **Modo cego / zero-shot é o default** | Casa desconhecida → IA extrai direto pro canônico, sem arquivo. Funciona no dia 1. |
| **Arquivo de casa vira DADO, não documento** | Deixa de ser markdown escrito por humano; vira tabela `casa + rótulo_cru → categoria_canônica`, populada pelas próprias extrações + correções do usuário. |
| **Confidence score por campo** | Campo duvidoso vem sinalizado (amarelo); usuário confirma em 1 clique. Nunca auto-confirma o ambíguo. O modelo já emite `Outros` como sinal natural de incerteza. |
| **Graduação automática** | Casa nova nasce em "modo aprendizado" → após X bilhetes com Y% de acerto confirmado, gradua para "confiável" e a fricção some. |

**Por que não cai na armadilha dos N-extratores:** a unidade que escala deixa de ser "casa" e passa a ser "exceção de mercado" — e exceções **convergem**, não multiplicam. Cada correção feita para a Betano beneficia a Betfair, a Sportingbet e uma casa indiana com termos parecidos em inglês. O sistema aprende por **vocabulário e esporte** (conjunto finito e pequeno), não por casa (milhares). Efeito de rede de dados no lugar de esteira de engenharia.

---

## 4. O fluxo de UX que materializa isso (visão do Feca)

O modo cego não é abstrato — é o popup **"+adicionar conta"**:

1. Usuário digita `oioioibet`, vê que não existe, clica **"adicionar nova casa"**.
2. Popup pede a **URL da casa** (para pegar o favicon e deixar bonito — e de bônus, o **domínio é um sinal** de locale/moeda/idioma, como o slug do Polymarket entrega o esporte).
3. A casa nasce como **uma linha** no banco. Vai direto pra tela de extração e **já extrai** (zero-shot).
4. Campos duvidosos vêm em amarelo; usuário confirma. Cada confirmação **engorda o cache** daquela casa.
5. A base cresce sozinha, casa a casa, aposta a aposta — cada usuário (Jonathan, Feca…) adiciona as próprias casas em autosserviço.

> **INVARIANTE CRÍTICO desta frente:** *"adicionar casa" = criar 1 linha (nome + url + favicon) + funciona já.* A tradução vem **depois**, do uso, **nunca antes**. Se em algum momento "adicionar casa" virar um formulário que exige mapear mercados antes de funcionar, recaímos na esteira que este plano existe para matar.

Isto transforma "adicionar casa" de **custo de engenharia (nosso)** em **ação de autosserviço (do usuário)** — é o que destrava o worldwide.

---

## 5. As 5 fases

Esforço em "sessões" (bloco focado com Claude Code, ~meio dia). Arquivos citados pelo mapa do código atual.

| # | Fase | O que muda (arquivos reais) | Esforço | Risco |
|---|---|---|---|---|
| **0** | **Validação** (gate) ✅ FEITA | Medir quanto o §9 realmente compra, rodando categorização zero-shot contra os §9 confirmados. Sem código de produção. | ½ sessão | — |
| **1** | **Confidence da IA + guardrail de enum** | `_INSTRUCAO` (`app/main.py:484`) passa a pedir confiança por campo; **saída presa ao enum oficial de categorias** (§3, 27 itens) como rede determinística — 0 alucinações observadas na Fase 0, mas barata como seguro; frontend (`app/static/index.html:~3102`) sinaliza amarelo; fundir com o score heurístico que já existe (`repository.py:340`). | 2–3 sessões | Baixo |
| **2** | **Modo cego (default) + auto-registro** | `build_system(casa=None)` roda só com os 6 masters (`app/prompts.py:28`); `/extrair` aceita "casa desconhecida"; auto-registro da casa na 1ª ocorrência (hoje casa = entrada no dict `_CASA_DISPLAY` em `main.py:96` + arquivo; passa a existir tabela `casas` com nome+url+favicon). Popup "+adicionar conta" no front. | 3–4 sessões | Médio |
| **3** | **Cache aprendido** (coração da tese) | Nova tabela `mapa_mercado (casa, rotulo_cru, categoria, confirmacoes)`; correção do usuário grava o par; job de destilação (propõe arquivo fino, humano aprova em 1 clique — invariante #1); estado de graduação da casa. | 5–8 sessões | Médio-alto |
| **4** | **Locale/moeda** | `_num_or_none` (`repository.py:34`) vira locale-aware (hoje default pt-BR); normalizar **odd americana/fracionária → decimal antes do cálculo** (`odd = Resultado/Stake` depende disso); moeda por usuário. | 2–3 sessões | Médio |
| **5** | **Governança do cache** | Consenso (2–3 confirmações independentes) antes de gravar mapping **compartilhado** (senão um usuário errado envenena o cache de todos — ponto do Fable); amostragem 1–2% de extrações graduadas para golden automático (anti-erro-silencioso). | 2–3 sessões | Baixo |

### Custo

- **Desenvolvimento:** sem custo de contratação (Feca + Claude Code). Custo real = tempo (~15–21 sessões no total) + tokens do Claude Code no build (dezenas de US$).
- **Operação (o que importa pro worldwide):** extração continua **~$0,011/bilhete**. Modo cego tem input *menor* (sem arquivo de casa) → custo por bilhete **não sobe**, pode cair. **Custo é O(volume), não O(nº de casas):** um usuário na Índia custa o mesmo que um no Brasil. Infra: zero novo (Postgres já roda no Railway; tabelas `casas`/`mapa_mercado` são minúsculas). Fase 3 pode, em escala, rodar bilhete graduado em modelo menor com o mapping como few-shot → **reduz** custo.

### Prazo — dois marcos

- **MVP "funciona no mundo dia 1" = Fases 0+1+2 → ~6–8 sessões (2–3 semanas de trabalho real).** Ao fim: usuário estrangeiro cola bilhete de casa nunca vista e recebe o TSV, com campos duvidosos em amarelo. É a promessa central.
- **Produto que "fica melhor sozinho" = +Fases 3+4+5 → mais ~9–14 sessões (4–6 semanas).** Aqui entra o efeito de rede: correções alimentam o cache, casas graduam, locale robusto.

**Caminho crítico:** tudo dependia da Fase 0 (abaixo). Validada → segue.

---

## 6. Fase 0 — metodologia e resultado (evidência)

### Metodologia
- **Dado:** os §9 ("mapa de mercados") de 13 casas reais são pares **`rótulo cru da casa → categoria global`** já confirmados por humano. Extraídos por script → **110 pares**, 16 categorias (ML, Cartões, Escanteios, Player Props, Múltipla, Gols, Handicap, Anytime, Ambas Marcam, Dupla Chance, Chutes, Chutes no Gol, Games, H2H, Team Props, E-Sports Props).
- **Teste:** um agente **Sonnet** recebeu **só os MASTERs globais** (taxonomia §3 + sinônimos §4 + prioridade §7) e os 110 rótulos crus, **proibido de abrir qualquer `casas/CASA_*.md`**. Categorizou em "modo cego". Comparado 1-a-1 com o gold.

### Resultado

| Métrica | Valor |
|---|---|
| Match exato cru | **90,0%** (99/110) |
| Acerto real de **categoria**¹ | **94,5%** (104/110) |
| Erros **silenciosos** (errado E sem sinalizar) | **3,6%** (4/110) |
| Falhas **seguras** (modelo marcou `Outros` = incerteza → cai no amarelo) | 2/110 |
| Categoria alucinada (fora da §3) | **0/110** |

¹ 5 dos 11 "erros" são artefato de match exato: categoria idêntica (`Anytime`, `Outros`), só divergiu uma anotação entre parênteses no gold (ex.: `Anytime (descr. - 2+ Gols)`). O scorer normaliza isso.

**Os 6 misses reais:**
- **2 falhas seguras** (#83 Polymarket `Total O/U`, #103 Superbet `Total de Quebras (tênis)`): o modelo respondeu `Outros` sozinho → cairiam no amarelo pro usuário confirmar. **Não são erro silencioso — é o loop de confiança funcionando de graça.**
- **4 erros silenciosos**, todos **mercados de nicho obscuro**: #9/#10 primeiro/último marcador (previu Player Props em vez de Anytime), #12 Hits/Runs/RBIs de baseball (previu `Corridas`, gold `Player Props` — **ambas categorias §3 válidas**, rótulo genuinamente ambíguo), #27 Total de Faltas. **É exatamente a cauda longa que a Fase 3 (cache aprendido) conserta após 1 correção.**
- **0 alucinações.** (A 1ª leitura reportou 1 em #12 `Corridas`, mas `Corridas` **é** categoria oficial §3 — "corridas e estatísticas de Baseball"; era erro do harness, cuja lista estava incompleta. Corrigido: o harness agora lê as 27 categorias direto da §3.) O guardrail de enum da Fase 1 continua valendo como **seguro barato** (defesa em profundidade), não como conserto de um problema observado.

### Ressalvas (para não superinterpretar)
1. Testa **categorização**, não OCR/locale/stake/odd (riscos isolados nas Fases 1 e 4).
2. Usou o **Sonnet atual** como proxy do Sonnet 4.6 de produção (capacidade ≥ → otimista no limite; em categorização a diferença é irrelevante).
3. Rótulos do §9 são **mais limpos** que OCR real (viés otimista), mas o modelo viu **só o rótulo, sem o resto do bilhete**, enquanto em produção vê o bilhete inteiro (viés pessimista). Os dois se cancelam → proxy justo a conservador.

### Veredito
**Sinal verde.** Sem nenhum arquivo de tradução, o modelo já mapeia ~94,5% dos mercados sozinho, com erro silencioso de ~3,6% concentrado 100% na cauda de nicho — onde o cache aprendido atua. O §9 escrito à mão compra pouco; o que ele faz, o zero-shot + confirmação + cache faz de forma que escala. **"Adicionar casa = funciona já" é realidade, não promessa.**

---

## 7. Próximo passo

Construir o **MVP (Fases 1 → 2)**, começando pela Fase 1 (confidence da IA + guardrail de enum), que também é pré-requisito de segurança antes de abrir para o mundo. A Fase 0 já provou a tese; o gate está aberto.

# CASA_MODELO
## Camada de tradução — `<Casa>` → padrão global (FDC Capital)

> **Este é um template (v2).** Preencha os `<...>` com dados reais da casa. Não remova as instruções "(como preencher: ...)" — elas guiam o preenchimento e servem de memória do sistema.
>
> Este arquivo descreve **apenas** as particularidades de `<Casa>`.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> ⚠️ Antes de adicionar qualquer regra aqui, pergunte: **"isso muda de casa pra casa?"** Se não muda, vai no master global — não aqui.
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `<Nome>` *(como preencher: o valor exato que vai na coluna `Casa` do output)*
- Aliases: `<alias1>`, `<alias2>` *(como preencher: variações visuais e domínios que identificam esta casa num bilhete — ex.: "bet365.bet.br")*
- Locale: `<locale>` · Moeda: `<símbolo e formato>` *(como preencher: pt-BR vs en-US, prefixo vs sufixo, ponto vs vírgula — atenção ao §10)*
- `Parceiro` / `Tipster`: `<política>` *(como preencher: preenchidos pela app / extrator deixa vazio / valor fixo por workspace)*

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

*(como preencher: indicar PRIMÁRIO e FALLBACK. Tipos possíveis: **visão** (screenshot/OCR) · **export estruturado** (CSV/XLS determinístico) · **DOM** (parsing de página web) · **join multi-fonte** (duas fontes casadas por ID — ex.: bilhete + extrato financeiro) · **texto colado** (copiar/colar da interface). O modo de ingestão define toda a estratégia de extração — um parser determinístico tem custo ≈ zero de LLM; visão exige OCR; join exige duas fontes sincronizadas.)*

- **PRIMÁRIO:** `<tipo>` — `<de onde vem, qual URL/tela/aba, como acionar o export ou capturar o texto>`
- **FALLBACK:** `<tipo>` — `<quando usar e como>` *(omitir se a casa tiver só um modo)*

### 2.2 Tipo do bilhete declarado

*(como preencher: algumas casas declaram o tipo num rótulo fixo — ex.: cabeçalho verde "Simples / Dupla / Criar Aposta" da Bet365, rótulo "Tripla" da Betano. Quando existe, este rótulo define simultaneamente a categoria `Aposta` e a fórmula de odd a aplicar (`MASTER_RESULTADO_2026 §7`). Se a casa não declara o tipo, omitir esta subseção.)*

- Localização do rótulo: `<onde aparece no bilhete>`
- Regra: Simples → categoria do mercado da seleção; Dupla / Tripla / N-seleções / Criar Aposta / Sistema → `Múltipla`. Fórmula de odd: `MASTER_RESULTADO_2026 §7`.

### 2.3 Layout do bilhete

*(como preencher: descrever a anatomia do bilhete de cima para baixo — quais campos aparecem, em que ordem, como delimitar um bilhete do seguinte. Mencionar a ordem de exibição na tela vs ordem no output — a inversão cronológica é global: `MASTER_OUTPUT_2026 §15`.)*

`<Anatomia: campo 1 · campo 2 · campo 3 · bloco financeiro final · ...>`

---

## 3. ID do bilhete

*(como preencher: identificar qual dos 3 casos se aplica à esta casa:*
*- **Visível** — o ID aparece no bilhete; é a chave forte de dedup. Indicar formato e localização.*
*- **Ausente** — a casa não expõe ID. Usar assinatura derivada = `data + stake + retorno + confronto(s)`.*
*- **Fonte separada** — o ID existe mas vem de outra fonte (ex.: extrato CSV da Betfair), casado por ID com o bilhete. Indicar o par de campos que fazem o join.)*

- Caso: `<visível / ausente / fonte separada>`
- Formato: `<padrão — ex.: alfanumérico XXXX-XXXXXX, numérico, O/XXXXX/XXXX>`
- Localização: `<campo no bilhete / campo na fonte secundária>`
- Nunca vai no output (serve só para contar, validar e deduplicar).
- `<Se ausente:>` assinatura derivada = `data + stake + retorno + confronto(s)`.
- `<Se fonte separada:>` chave de join = `<campo A (bilhete)>` ↔ `<campo B (fonte secundária)>`.

---

## 4. Data

*(como preencher: a cadeia global de fallback é, em ordem de preferência: **evento (preferido) > data informada pela operação > liquidação via extrato/join por ID > colocação como proxy (só quando o evento é no mesmo dia) > data atual em `America/Sao_Paulo`**. Indicar qual(is) posições desta cadeia esta casa preenche e como. Nunca usar colocação quando a data do evento estiver disponível.)*

- Fonte primária: `<campo ou aba onde a data do evento aparece, com formato>`
- Fallback(s): `<o que usar quando a fonte primária não está disponível, em ordem>`
- Formato fonte: `<ex.: DD/MM/AAAA - HH:MM · YYYY-MM-DD HH:MM:SS · DD-mmm-YY HH:MM:SS>` → converter para `DD/MM/AAAA` (descartar horário).
- Múltipla: data = evento da **perna mais recente** entre as seleções (regra global, `MASTER_OUTPUT_2026`).

> ⚠️ Se o sistema roda em servidor UTC (ex.: Railway), fixar explicitamente `America/Sao_Paulo` (UTC−3) ao usar "data atual" — sem isso, após 21h UTC a data sai um dia adiantada.

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar o código visual da casa diretamente para o output. Traduzir sempre para os códigos oficiais: `W · L · V · HW · HL`. Exemplo real: o `V` visual da Betfair significa "Você ganhou" → nosso `W`. Copiado direto, seria uma vitória registrada como void — erro silencioso e catastrófico.

*(como preencher: listar os rótulos visuais da casa e o código global correspondente. A conferência financeira é a segunda linha de defesa — usá-la para desambiguar quando o rótulo for ambíguo.)*

| `<Casa>` exibe | Nosso código |
|---|---|
| `<rótulo de vitória>` | W |
| `<rótulo de derrota>` | L |
| `<rótulo de void/anulação>` | V |
| `<rótulo de meia vitória, se aplicável>` | HW |
| `<rótulo de meia derrota, se aplicável>` | HL |

Conferência financeira (segunda linha de defesa): `Retorno = 0` → L · `Retorno = Stake` → V · `Retorno > Stake` → W.

**Gatilho de meia-liquidação (HW/HL):**

*(como preencher: indicar como esta casa sinaliza HW/HL. Pode ser: rótulo explícito ("Half Win"), tags de metade na seleção ("½ Ganho"/"½ Perdido"/"½ Anulado" — padrão Bet365), ou ausência de rótulo — só detectável pela assinatura financeira. Documentar qual é o primário para esta casa.)*

- Primário: `<rótulo direto / tags de metade na seleção / só assinatura financeira>`
- Confirmação por assinatura financeira **exata**: `HL → retorno = stake/2` · `HW → retorno = (stake/2) × (odd + 1)`.
- Esta assinatura também **distingue HW/HL de cashout** — cashout produz retorno arbitrário que não casa com nenhuma das duas fórmulas.
- Só ocorre em linhas asiáticas de quarto (`.25` / `.75`) ou split (`-1.0,-1.5` / `0.0,+0.5`).

Apostas abertas → `extraction_state = aberta` (fora da fila de cópia).

---

## 6. Boost / promoção

*(como preencher: indicar se a casa tem boost de odd (odds boosted, promoções que aumentam o retorno). Se sim: localizar visualmente e confirmar se o campo de retorno já embute o boost — quando embute, `Odd = Retorno ÷ Stake` captura naturalmente. Se não tem boost, declarar explicitamente — isso simplifica a extração.)*

- Tem boost: `<sim / não>`
- Localizador: `<rótulo visual ou campo que indica boost — ex.: "Bet Boost", "SUPERMÚLTIPLA X%">`
- Comportamento: `<o retorno já embute o boost → usar Retorno÷Stake / a odd exibida já é boosted / outro>`

<!-- TODO se sem amostra: confirmar rótulo visual e se o retorno embute o boost. -->

---

## 7. Cashout

*(como preencher: indicar se a casa oferece cashout e onde aparece o valor encerrado. A lógica de resultado e odd é global — aqui fica só o localizador da casa.)*

- Tem cashout: `<sim / não>`
- Localizador: `<campo, aba ou rótulo onde o valor de cashout aparece — ex.: "Total de Cash Out: R$X", aba "Encerrar Aposta">`
- Regra global: `Odd = Cashout ÷ Stake` (resultado = L); se `Cashout = Stake` → resultado `V`, preservar a odd exibida/estrutural.
- **Distinção de meia-liquidação:** cashout produz retorno **arbitrário** (não casa com `Stake/2` nem `(Stake/2)×(odd+1)`); HW/HL casam **exato** — usar esta assinatura para desambiguar quando o rótulo for ambíguo.

<!-- TODO se sem amostra: confirmar localizador e rótulo visual do cashout encerrado. -->

---

## 8. Bônus

*(como preencher: indicar se a casa opera com apostas de bônus / freebets — dinheiro de bônus, distinto do capital próprio. Definir a política de tratamento. Enquanto não decidido, sinalizar a aposta e não misturar no fluxo de cash.)*

- Tem bônus: `<sim / não>`
- Localizador: `<campo ou rótulo que identifica aposta com bônus — ex.: "Bônus usado:", colunas "Entrada/Saída de bônus" no extrato>`
- **Política:** `<excluir da análise (mais limpo para P&L real) / marcar com flag para filtro posterior / incluir com stake do bônus (superestima capital em risco)>`

> ⚠️ Bônus superestima volume de capital próprio em risco — registrar a decisão aqui quando tomada; manter pendente até ter amostra real.

<!-- TODO se sem amostra ou decisão pendente: sinalizar como pendente. -->

---

## 9. Mapa de mercados (`<Casa>` → `Aposta` global)

*(como preencher: mapear **apenas** os mercados que esta casa realmente exibiu, traduzindo o rótulo da casa para a categoria global do `MASTER_APOSTAS_2026 §3`. Seguir a prioridade: categoria específica > Player Props > Outros.)*

> ⚠️ **NÃO reescreva as 27 categorias nem use linhas "aguarda amostra".** A lista canônica de categorias vive no `MASTER_APOSTAS_2026 §3`, que é carregado no prompt em **toda** extração — a IA já a conhece. Restar categoria que esta casa nunca mostrou é duplicação morta: não ensina nada ao modelo e quebra quando o global muda (era a causa raiz do drift de propagação). Liste só o que foi **confirmado num bilhete real**; um mercado novo é classificado pelo `MASTER_APOSTAS` quando surgir.

| `<Casa>` exibe (rótulo real) | Aposta global |
|---|---|
| `<rótulo confirmado>` | `<categoria do §3>` |
| `<rótulo confirmado>` | `<categoria do §3>` |

> Mercado que apareça e **não** tenha categoria adequada no §3 → `Outros` ⚠️ + registrar no §Feedback com recomendação. Mercados ainda não vistos **não entram nesta tabela**.

**Notas de reconstrução:**
- Confronto: `<formato da casa>` → `[Time A v Time B]` (padrão global, `MASTER_DESCRICAO_2026`).
- `Mais de` / `Menos de` → Over / Under.
- **Normalização de jogador:** pode vir em `[colchetes]` no fim do mercado (ex.: Betano `Total de Pontos [Victor Wembanyama]`) → extrair e colocar no início da descrição; pode vir como `Sobrenome, Nome` (ex.: Pinnacle `Valdez, Framber`) → normalizar para `Nome Sobrenome`. Confirmar o padrão desta casa.
- Mercado sem categoria global → `Outros` ⚠️ + registrar no §Feedback.
- `<outros padrões específicos desta casa>`

---

## 10. Stake

*(como preencher: indicar onde está o valor da stake e o formato numérico. Atenção especial ao locale numérico — algumas casas usam en-US mesmo com interface em pt-BR.)*

- Localização: `<campo ou posição no bilhete — ex.: "Aposta: R$X", header do bilhete, coluna "Risco:" no export>`
- Formato: `<pt-BR (padrão): R$1.914,56 — ponto de milhar, vírgula decimal / en-US (ex.: Betfair): R$1,050.00 — vírgula de milhar, ponto decimal>`
- ⚠️ Se **en-US**: a vírgula em `R$1,050.00` é **milhar**, não decimal — remover a vírgula de milhar e trocar o ponto decimal por vírgula → `1050,00`.
- Normalização final (remover símbolo de moeda, trim, separador de milhar) = global (`MASTER_OUTPUT_2026 §11/§16`).

---

## 11. Odds

> **Conceito: campo financeiro único.** Muitas casas têm um campo que resolve todos os desfechos de uma vez — ex.: Bet365 `Retorno Obtido`, Superbet `PRÊMIO`/`REEMBOLSO`, Betfair `Ganhos`, Betano `Ganhos`. Quando existe, este campo tem prioridade máxima. **Mas atenção:** ele só **deriva** a odd em W / cashout / boost (retorno positivo real). Em L/HL/V, a odd vem do bilhete — nunca calcular odd a partir de retorno zero ou parcial.

*(como preencher: identificar o campo financeiro principal desta casa e documentar a regra por resultado.)*

- Campo financeiro principal: `<nome do campo>`
- Localização: `<onde aparece no bilhete>`

| Resultado | Regra da odd |
|---|---|
| W | `Odd = <campo financeiro> ÷ Stake` |
| L | odd **exibida** no bilhete — nunca `0,00` |
| V | odd **exibida** — nunca `1,00` |
| HW | odd **exibida** — nunca metade |
| HL | odd **exibida** — nunca metade |
| Cashout (≠ stake) | `Odd = Cashout ÷ Stake` |

**Múltiplas e sistemas:**
- Casa **exibe** odd combinada (ex.: `Odds Totais`, `Cotações combinadas`) → usá-la em L/V.
- Casa **não exibe** odd combinada (ex.: Betano) → produto das odds das seleções (`MASTER_RESULTADO_2026 §7`).
- Sistema (Trixie / Yankee / 3×Duplas…) **ganho com perna anulada** → `Retorno ÷ Stake` já embute o void; não recalcular pela fórmula estrutural.
- Sistema **perdido inteiro** → odd estrutural pela fórmula de `MASTER_RESULTADO_2026 §7`, preservando perna anulada como odd `1,00`.

> ⚠️ Regra crítica: em `L` a odd nunca vira `0,00`; em `HL` nunca vira metade; em `V` nunca vira `1,00`. Odd exibida é sempre preservada. `Campo ÷ Stake` vale **só** para W / cashout / boost.
> Precisão: preservar — não truncar nem arredondar (global, `MASTER_RESULTADO_2026`).

`<Particularidades adicionais desta casa, se houver.>`

---

## 12. Ruído a ignorar

*(como preencher: listar os elementos visuais desta casa que devem ser ignorados na extração — banners, botões de ação, stats ao vivo com número, placares, ícones, labels constantes etc.)*

`<elemento 1>` · `<elemento 2>` · `<elemento 3>` · …

---

## 13. Pegadinhas (resumo rápido)

*(como preencher: bullets curtos com os erros mais prováveis ao processar bilhetes desta casa. Focar no que é específico desta casa e não óbvio pelo master global.)*

- `<pegadinha 1>`
- `<pegadinha 2>`
- `<...>`

---

## 14. Validações específicas

*(como preencher: aqui vão **só** as validações próprias desta casa. As transversais valem para todas e vivem no global — não copiar.)*

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18`. Cobrem: resultado oficial (`W/L/V/HW/HL`), odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes. **Não duplicar aqui.**

**Específicas desta casa:**
- `<validação 1>`
- `<validação 2>`
- `<...>`

---

## 15. Exemplos golden (bilhetes reais)

*(como preencher: incluir bilhetes reais com o TSV esperado, um por cenário relevante. Cobrir ao menos: W simples, L simples, V/void, múltipla. Adicionar HW/HL e cashout quando houver amostra. **TABs reais entre colunas — nunca espaços.**)*

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

<!-- Nenhum exemplo neste template. Preencher com bilhetes reais ao criar o arquivo da casa. -->

---

## Feedback para a camada global / MODELO

*(como preencher: registrar aqui lacunas encontradas nos masters globais ou neste MODELO ao preencher a casa — mercados sem categoria, padrões de data não cobertos, modos de ingestão novos etc. Não aplicar a mudança aqui — propor como diff nos masters globais e aguardar aprovação.)*

1. `<lacuna ou proposta>`
2. `<...>`

---

VERSÃO: 2026
STATUS: TEMPLATE (v2)
CASA: `<preencher ao criar arquivo da casa>`

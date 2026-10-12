# PROJETO FICHA SHARPEN: tirar a IA do caminho da aposta

> **Dono:** Feca · **Aberto em:** 2026-10-11 · **Ritmo:** acelerado ao máximo, dia a dia, sem meses.
> **Origem:** mapa independente do Sharpen (Fase 1), em
> `C:\Users\Fernando\Downloads\FDC Capital\Auditorias\mapa_2026-10\claude\` (somente leitura: é
> auditoria, não se edita).
> **Projeto independente.** Ele nasce do mapa e das decisões do Feca de 11/10, e de nada mais. Planos
> antigos em `docs/` (`PLANO_*.md`) **não são fonte** deste projeto e não devem ser usados para decidir
> nada aqui. Se algum fato antigo parecer útil, ele só entra depois de reconferido no código ou no banco
> de hoje.

---

## 1. O que é, em português simples

Hoje toda aposta capturada pela extensão faz uma volta inútil:

```
ficha organizada da casa → vira TEXTO → IA paga reescreve como tabela → 8 fiscais por regex
corrigem o que a IA copiou → tabela é lida de novo → banco
```

O projeto troca isso por:

```
ficha da casa → extensão monta a FICHA SHARPEN (formato único) → manda só o que é novo ou mudou
→ servidor grava na hora, números direto da fonte → termo de mercado nunca visto vai para uma fila
→ IA barata classifica o TERMO uma vez, em lote → dicionário → nunca mais é pago
```

**Princípio:** a IA nunca toca em número e nunca fica no caminho da aposta.

---

## 2. Por que (números de produção, medidos em 11/10/2026)

| Fato | Valor | Prova |
|---|---|---|
| Custo por extração, Sonnet 4.6 → Sonnet 5 | US$ 0,22 → **US$ 0,45** | `uso_tokens` por modelo |
| Fatia da conta que é a IA **escrevendo** (Sonnet 5) | **69%** (provável "pensamento" ligado por padrão) | `uso_tokens`; `app/main.py:2113-2116` sem parâmetro de pensamento |
| Escrita por pedaço, 4.6 → 5 | 1.509 → **6.103 tokens** | `uso_tokens` |
| Manual enviado a cada pedaço | ~76 mil tokens, **96% fixo** | `count_tokens` |
| Do manual geral, quanto é só "padrão" (esporte, categoria, descrição) | **73%** (46.482 de 63.907 tokens) | `count_tokens` por arquivo |
| Colunas que a IA escreve e o código sobrescreve depois | **6 de 11** (stake, odd, resultado, código, casa, conta) | `app/repository.py:717,1241`; `app/main.py:4100-4123` |
| Leituras pagas por aposta desde 21/09 | **1,65** (DEX Sport: 6,44) | `sombra_rotulos` |
| Gasto com IA de Feca + Gabriel, 01 a 11/10 | **US$ 94,46** | `uso_tokens` |
| Tempo de uma extração | 60 a 190 s | logs do extrator |

Detalhe e prova de tudo: `Auditorias\mapa_2026-10\claude\MAPA.md` e a página "Viagem de uma aposta"
(cópia em [`referencias/viagem-de-uma-aposta.html`](referencias/viagem-de-uma-aposta.html)).

---

## 3. Decisões do Feca (valem como lei do projeto)

1. **Objetivo:** reduzir o custo de IA. Railway fica fora.
2. **Números não podem errar.** Odd, stake e resultado têm que ser 100% exatos. "O Sharpen é um sistema
   financeiro das apostas."
3. **Descrição pode variar.** "Se ele entregar uma palavra diferente na descrição, não importa."
   A descrição não é critério de nada neste projeto.
4. **Começar pelas casas em uso em outubro** (bases do Feca e do Gabriel). **Bet365 fica fora por
   enquanto.**
5. **DEX Sport e Shuffle:** as correções do porteiro (maiúsculas) já estão em andamento em outra frente.
6. **Base antiga importada** é necessária e fica como histórico fora do padrão.
7. **Ritmo:** não temos meses. Tudo acelerado ao máximo.
8. **Prioridade (11/10):** a Ficha vem **antes** da Fase 2 da blueprint.
9. **Arquivos centrais (11/10):** enquanto o projeto estiver ativo, só a sessão dele mexe em `app/main.py` e
   `app/repository.py` (`docs/ESTRUTURA_DO_TIME.md`). A Ficha entra em módulo novo, com um único ponto de
   registro da rota.
10. **Critério de virada (11/10):** pelo menos 30 apostas **liquidadas** comparadas; aberta não conta
    (`03_REGUA_NUMEROS.md §4`).
11. **Odd (11/10):** aberta usa a odd calculada pelas pernas; resolvida usa retorno ÷ stake. Ajustes em
    discussão no `DIARIO.md`.
12. **As 249 apostas antigas do furo de 0,005 não serão corrigidas (11/10).** Item fechado.

---

## 4. O caminho (os dois unidos)

**Regra que une os dois:** só se aperta um parafuso do processo atual se ele custar menos de um dia
**ou** sobreviver ao sistema novo. O resto do processo atual não recebe mais investimento.

| Do processo atual (fica) | Por quê |
|---|---|
| Reduzir ou desligar o "pensamento" do Sonnet 5 | uma linha; corta ~metade da conta enquanto as casas migram |
| Sombra no `claude-haiku-5-5` (variável `SOMBRA_MODELO`) | mantém o experimento a ~1/10 do custo |
| Régua de números (`app/sombra_numeros.py`, em construção) | vira o juiz da virada de cada casa |
| `sombra_rotulos` (53 mil pares bloco × decisão da IA) | vira a semente do dicionário |
| Os 22 ouvintes (`extensor/*_inject.js`) e a bancada (`extensor/harness/fixtures/`) | são a fundação |

| Do processo atual (não recebe mais esforço) | Por quê |
|---|---|
| Trava de extração sobreposta, pedaços maiores, troca de titular para Haiku | morrem na migração |
| Manuais MASTER / CASA | encolhem sozinhos quando a IA sai do caminho; editar invalida cache |

---

## 5. Cronograma acelerado (dias corridos a partir da aprovação da Ficha)

| Dia | Entrega | Pronto quando |
|---|---|---|
| **D0** | Feca aprova a Ficha Sharpen ([`01_FICHA_SHARPEN.md`](01_FICHA_SHARPEN.md)) e a ordem das casas ([`02_CASAS_OUTUBRO.md`](02_CASAS_OUTUBRO.md)) | perguntas do §9 da Ficha respondidas |
| **D1** | Pensamento reduzido no Sonnet 5 + sombra no Haiku 5.5 (caminho velho) · rota nova de recebimento da Ficha **em modo sombra** (grava à parte, não em `bilhetes`) | régua mede o caminho velho sem regressão de número |
| **D1-D2** | Adaptador **DEX Sport** (fixture `dexsport.tickets.json`) + harness | caso verde, e vermelho por mutação |
| **D2-D3** | Família **1xBet**: Megapari, PariPesa, SapphireBet, 1xBit · **BetConstruct**: MyStake | idem |
| **D3-D4** | Família **BetBy**: Betpanda, Duel, Betfury, Betcoin · **Altenar**: BetMartini, Betrebels, Vavada, Kikobet · **Shuffle** | idem |
| **D2-D5** | Extensão publicando Ficha + texto juntos (o caminho velho segue mandando) · dicionário semeado | Fichas chegando de verdade na tabela sombra |
| **D4-D7** | **Virada da DEX Sport** pela régua ([`03_REGUA_NUMEROS.md`](03_REGUA_NUMEROS.md)) | 100% dos números iguais ou divergência explicada |
| **D5-D10** | Virada das demais famílias, uma a uma | idem |
| **depois** | Prints, PDF, texto colado e bot passam a gerar Ficha via IA de visão com saída estruturada | — |

Atraso não muda a ordem: muda a data. Cada virada é uma chave por casa, reversível na hora.

---

## 6. Como se trabalha neste projeto

- Siga o [`CLAUDE.md`](../../CLAUDE.md) do repositório e as regras do Feca: uma tarefa por vez, **proponha,
  espere aprovação, execute**; backup antes de sobrescrever; pt-BR; PowerShell 5.1.
- Nada de commit, push ou deploy sem o Feca mandar.
- Todo número novo entra no [`DIARIO.md`](DIARIO.md) com a consulta ou o arquivo:linha que o prova.
- **Outra sessão pode estar mexendo no repo.** Antes de editar `app/main.py`, `app/repository.py` ou
  `app/database.py`, rode `git status` e confirme com o Feca.
- Banco de produção: só leitura para medir. Escrita só pelo app publicado.
- Não editar manuais (`global/`, `casas/`) neste projeto.

---

## 7. Arquivos

| Arquivo | Para quê |
|---|---|
| [`INICIAR.md`](INICIAR.md) | o prompt para abrir uma sessão nova e continuar de onde parou |
| [`01_FICHA_SHARPEN.md`](01_FICHA_SHARPEN.md) | especificação da Ficha Sharpen (rascunho para aprovação) |
| [`02_CASAS_OUTUBRO.md`](02_CASAS_OUTUBRO.md) | casas em uso em outubro, famílias, fixtures, custo e ordem |
| [`03_REGUA_NUMEROS.md`](03_REGUA_NUMEROS.md) | o juiz da virada de cada casa |
| [`04_DICIONARIO.md`](04_DICIONARIO.md) | como o vocabulário sai da IA e vai para uma tabela |
| [`DIARIO.md`](DIARIO.md) | o que foi feito a cada dia, com prova |
| `referencias/` | a página "Viagem de uma aposta" e o prompt original da sombra de números |

---

## 8. Estado

- [x] Mapa do que existe (Fase 1) · 11/10
- [x] Revisão do processo com o Feca · 11/10
- [x] D0: Ficha aprovada · 11/10 (respostas no §9 de `01_FICHA_SHARPEN.md`)
- [x] Sombra no Haiku 5.5 · 11/10, feita por outra frente (s407, commit `e2427d4`)
- [ ] D1: pensamento reduzido + rota sombra
- [ ] Adaptadores: DEX · 1xBet · BetConstruct · BetBy · Altenar · Shuffle
- [ ] Viradas: DEX · Megapari · MyStake · Betpanda · Duel · BetMartini · Shuffle · demais

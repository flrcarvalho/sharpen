# MASTER_OUTPUT_2026
## Estrutura Oficial do TSV — Extrações de Apostas (2026)

Este documento define o formato final obrigatório do TSV gerado pelos GPTs de extração de apostas.

Ele é a fonte única de verdade para:
- estrutura da planilha
- ordem das colunas
- separador oficial
- validação estrutural

Todos os GPTs devem obedecer exatamente este padrão.

---

# 1. Estrutura Oficial das Colunas

A saída do extrator deve conter exatamente as seguintes colunas:

```text
Data
Esporte
Tipster
Casa
Parceiro
Aposta
Descrição
Stake
Odd
Resultado
```

A ordem das colunas é imutável.

---

# 2. Proibição de Colunas Extras

Nenhum GPT pode criar colunas adicionais.

É expressamente proibido adicionar colunas como:

```text
Tipo
PRE
Status
Liga
Campeonato
Mercado
Evento
```

Se qualquer coluna extra aparecer, o TSV deve ser considerado inválido.

**Exceção — Código (11ª coluna interna):** o app de extração pode solicitar explicitamente uma 11ª coluna chamada `Código` com o ID/código do bilhete visível no print. Quando essa coluna aparecer na instrução da chamada, emiti-la **não viola esta regra** — ela é interna ao sistema, usada só para deduplicação no banco de dados, e nunca vai para a planilha do usuário.

---

# 3. Separador de Colunas

O TSV deve utilizar exclusivamente:

```text
TAB (U+0009, \t)
```

Nunca utilizar:
- `;`
- `,`
- pipes (`|`)
- múltiplos espaços
- alinhamento visual

Exemplo válido (colunas separadas por TAB):

```text
12/03/2026	Basquete		Betano		Player Props	Anthony Davis - 10+ Rebotes [LAL Lakers v CHI Bulls]	400,00	2,35	W
```

---

# 3.1 Regra Crítica — TSV Literal

A serialização final deve utilizar TAB real (U+0009) entre colunas.

Nunca:
- alinhar visualmente
- utilizar pseudo-colunas
- utilizar múltiplos espaços
- utilizar markdown tabelado
- compactar whitespace
- substituir TAB por espaços

Cada linha deve ser serializada literalmente como:

```text
valor	valor	valor
```

(os espaços entre "valor" acima são TABs reais)

Exemplo inválido:

```text
12/03/2026 Basquete Betano Player Props ...
```

Mesmo que visualmente pareça separado.

---

# 4. Formato da Data

Formato obrigatório:

```text
DD/MM/AAAA
```

Exemplo:

```text
12/03/2026
```

Regras:
- ignorar horário
- nunca usar ISO
- nunca usar formato americano
- em apostas múltiplas: usar a data da perna mais recente

---

## 4.1 Data de Referência (Hoje / Ontem / Amanhã)

A camada de app fornece a **data de referência da captura** no campo `data_referencia`.

Regra obrigatória:
- `Hoje` → data de referência fornecida
- `Ontem` → data de referência − 1 dia
- `Amanhã` → data de referência + 1 dia

**Nunca** resolver datas relativas contra o horário de processamento do modelo.
**Nunca** usar o cabeçalho de criação do bilhete como referência de "Hoje".

A data de referência viaja junto com as imagens na camada de app para suportar processamento assíncrono (captura ontem + processamento hoje = "Hoje" ainda é ontem).

---

# 5. Esporte

A coluna Esporte deve seguir exatamente o padrão definido em:

```text
MASTER_ESPORTES_2026
```

Nenhum GPT pode inventar novos esportes.

---

# 6. Tipster

Campo livre.

Se não houver informação:

```text
campo vazio
```

Nunca preencher automaticamente.

---

# 7. Casa

Deve conter o nome padronizado da casa — **primeira letra maiúscula, demais minúsculas**.

Exemplos válidos:

```text
Betano
Bet365
Pinnacle
Superbet
Novibet
Betfair
```

> **Convenção de duas camadas:**
> - **TSV (saída da IA):** grafia com primeira letra maiúscula — `Superbet`, `Bet365`, etc.
> - **Banco de dados:** o backend normaliza automaticamente para ALL-CAPS — `SUPERBET`, `BET365`, etc.
>
> A IA **nunca** precisa identificar a casa: o usuário a seleciona antes da extração. O campo Casa no TSV apenas confirma o nome canônico para rastreabilidade.

---

# 8. Parceiro

Campo livre.

Se não existir parceiro:

```text
campo vazio
```

---

# 9. Aposta

A coluna Aposta deve usar exclusivamente categorias existentes no arquivo:

```text
MASTER_APOSTAS_2026
```

Nunca criar categorias novas.

Exemplos válidos:

```text
Player Props
Anytime
Assistência
ML
Handicap
Gols
Múltipla
```

---

# 10. Descrição

A coluna Descrição deve seguir exatamente o padrão definido em:

```text
MASTER_DESCRICAO_2026
```

Ela deve conter:
- mercado
- entidade
- confronto

Nunca incluir:
- odds
- stake
- resultado
- placar
- ID da aposta

---

# 11. Stake

A stake deve ser retornada como valor numérico com vírgula decimal.

Exemplos:

```text
100,00
507,00
12,50
```

Regras:
- remover símbolo de moeda
- remover separador de milhar
- sempre usar vírgula decimal

---

# 12. Odd

A odd deve usar:

```text
vírgula decimal
```

Exemplos:

```text
2,35
1,87
10,50
```

## 12.1 Separador decimal — regra inquebrável

A odd usa **SEMPRE vírgula**, **JAMAIS ponto**.

Toda odd **calculada** (divisão `Retorno ÷ Stake` ou produto das pernas de uma múltipla) sai
do cálculo com **ponto** decimal. Esse ponto **deve** ser convertido em vírgula **antes** de
escrever a célula.

```text
CORRETO:  75,26066666666666   ·   8,580978   ·   127,672839
ERRADO:   75.26066666666666   ·   8.580978   ·   127.672839
```

> **Motivo:** a planilha (locale pt-BR) interpreta o ponto como separador de **milhar**.
> Uma odd `8.580978` é remontada como `8.580.978,00` e a aposta fica corrompida.

## 12.2 Precisão — regra inquebrável

Preservar a **precisão total**: nunca arredondar nem truncar para 2 casas. Usar quantas casas
decimais forem necessárias (até 12). Nunca usar reticências (`...` / `…`) — escrever todos os
dígitos significativos e parar no último dígito real. Vale tanto para odd lida quanto calculada
(divisão ou produto). Ver `MASTER_RESULTADO_2026 §5.2.1` e `§7.2`.

As regras oficiais de:
- cashout
- void
- HW
- HL
- odds recalculadas

estão definidas em:

```text
MASTER_RESULTADO_2026
```

---

# 13. Resultado

A coluna Resultado deve utilizar exclusivamente os códigos:

```text
W
L
V
HW
HL
```

Significados:

```text
W  → aposta vencedora
L  → aposta perdida
V  → aposta anulada / void
HW → half win
HL → half loss
```

Nunca escrever:

```text
Green
Red
Void
Half Win
Half Loss
Ganhou
Perdida
```

---

# 14. Regra de Cashout

Quando houver cashout com valor diferente da stake, o extrator deve ajustar a odd.

Regra:

```text
Odd = Retorno / Stake
```

Exemplo:

```text
Stake = 100
Retorno = 160
Odd = 1,60
```

Isso garante compatibilidade com a planilha.

---

# 15. Ordem das Apostas

A ordenação do output **não é universal** — cada casa tem sua própria regra.

Consultar obrigatoriamente o **§2 do arquivo da casa** (`CASA_*.md`) para saber:
- se a ordem das imagens/texto deve ser mantida ou invertida
- qual ponta do input corresponde ao bilhete mais antigo

A planilha exige sempre **mais antigo → mais recente** na saída final.
A regra por casa define como chegar nessa ordem a partir do input recebido.

---

# 16. Trim Obrigatório

Todos os campos devem ser normalizados automaticamente.

Remover:
- espaços no início
- espaços no final
- espaços invisíveis

Nunca gerar:

```text
[TAB] valor [TAB]
```

Sempre gerar:

```text
[TAB]valor[TAB]
```

---

# 17. Validação Estrutural Crítica

Antes da serialização final validar obrigatoriamente:

- todas as linhas possuem exatamente 10 colunas de saída (Data…Resultado); se a instrução solicitar `Código` como 11ª coluna interna, ela pode estar presente — não é erro
- nenhum campo deslocou posição
- Esporte nunca pode ocupar coluna Aposta
- Aposta nunca pode ocupar coluna Descrição
- Descrição nunca pode ocupar Stake
- Stake/Odd/Resultado devem permanecer nas 3 colunas finais

Se qualquer deslocamento estrutural ocorrer:
- invalidar a linha
- nunca serializar TSV quebrado

---

# 18. Validação Final do TSV

Antes de retornar o TSV, o GPT deve validar:

1. número de linhas = número de apostas detectadas
2. nenhuma coluna extra foi criada (exceto `Código` se solicitada pela instrução — ver §2)
3. ordem cronológica correta
4. separador TAB (U+0009)
5. decimal com `,`
6. categorias válidas de aposta
7. esporte válido
8. resultado válido
9. exatamente 10 colunas por linha (Data…Resultado); `Código` como 11ª coluna interna é permitida quando solicitada

Se qualquer validação falhar, o TSV deve ser considerado inválido.

---

VERSÃO: 2026  
STATUS: ATIVO  
USO: GPTs de extração de apostas

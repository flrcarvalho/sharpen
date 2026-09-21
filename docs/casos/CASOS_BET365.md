# Casos da captura SharpenUp — bet365

> Partição de [`../CASOS.md`](../CASOS.md) por assunto, aberta quando ele encostou no
> teto de 60 KB do `check_docs.py`. **Teto é sinal de partição, não de excesso: caso não
> se apaga.** Caso novo de captura da bet365 entra AQUI, não lá.

> ⚠️ Daqui de dentro, todo caminho relativo sobe um nível: `../CASOS.md`, `../../casas/`.

---

## O muro que parecia da casa e era do histórico do navegador — bet365, 2026-09-20

A extração da bet365 travava no meio e o operador "reconectava" para seguir. A explicação em
vigor vinha da s184: *"a `confirmation` dá 500 sob rajada no namespace D0"*. Dela saíram a
folga de 900 ms entre bilhetes, o teto de 9 s e os dois retries com bounce no hash.

**Nada disso era verdade, e ninguém nunca tinha medido o status das respostas.**

### O que a medição mostrou

Um gravador no `b3_inject.js` carimbou cada requisição com status HTTP e duração:

| | |
|---|---|
| `confirmation` numa sessão | **473, todas 200** |
| `summary` na mesma sessão | **133, todas 200** |
| mediana do 1º bloco de 50 | 422 ms |
| mediana do ÚLTIMO bloco de 50 | **391 ms** |
| 500, 429 ou 403 | **zero** |

A casa não só nunca recusou: ficou **mais rápida** no fim da rodada. Não há cota nem punição
por rajada. E a cauda do gravador, no instante da travada, mostra o absurdo:

```
nav  FALHOU  9145 ms
conf 200      394 ms   ← a casa respondeu, rápido
nav  FALHOU  9017 ms
conf 200      178 ms   ← e de novo
```

### A causa

Cada detalhe era aberto com `location.hash = rota`, e **toda atribuição ao hash empilha uma
entrada no histórico do navegador**. Passadas ~420 entradas, o roteador da página da bet365
para de reagir à troca de rota: a `confirmation` continua voltando 200, mas sempre do **mesmo**
bilhete, e o `esperarCodigo` estoura o teto em todos os seguintes.

Reproduzido duas vezes no mesmo dia, em sessões independentes: quebrou na **435ª** navegação e
na **417ª**. Depois disso, 100% de falha e zero recuperação.

**"Reconectar" não cura**, e era essa a parte cara: o operador reconectava, o robô recomeçava,
e cada bilhete restante consumia 9 s para produzir nada. Só recarregar a página cura.

O conserto é `location.replace(rota)`, que navega sem empilhar. Nos três lugares que mexiam no
hash: a navegação, o bounce do retry e a volta para a lista.

### Os três defeitos que o diagnóstico errado escondia

- **A folga de 900 ms virou 60% do custo por bilhete** (1.523 ms medidos: 617 de navegação
  real, 906 de espera nossa) para proteger de uma rajada que nunca incomodou ninguém.
- **Passada que não termina não grava memória.** O `b3Lembrar` só rodava no fim do laço, e
  recarregar a página no meio — o gesto natural de quem vê a captura travada — matava a rodada
  antes disso: **435 bilhetes detalhados, ~15 minutos de `confirmation` paga, perdidos.**
- **O retry com bounce nunca teve chance.** Existia para renovar um token vencido que nunca
  estava vencido.

> **Sintoma para reconhecer isto noutro campo:** o remoto responde **200 e rápido**, e mesmo
> assim o seu laço conta falha. Quando o erro que você registra é um **timeout SEU**, e não um
> status do outro lado, a culpa quase nunca é do outro lado. Registre o status da resposta
> antes de escrever a teoria — aqui foram anos de teoria construída sobre um 500 que nunca
> aconteceu.

## A memória indexada pela VISÃO, não pela aposta — bet365, 2026-09-20

Varrendo um período de 1049 bilhetes já planilhados em ~95%, o driver registrou
`alvos 1038 · pulados 0`: a memória `b3Detalhes` não reconheceu **um** bilhete.

A causa está documentada no próprio arquivo desde sempre, sem ninguém ter ligado as pontas: o
`ID` do `summary` é **da visão**, não da aposta. As últimas 24h vêm no namespace `D1`, as 48h e
o Intervalo de Datas vêm no `D0`. A memória é indexada por esse `ID`.

Medido com as duas visões carregadas com cinco minutos de diferença, em 269 entradas:

```
TP 20260921002749000
  D0  id=49911954609          code=YR5088082431I  stake=160,00
  D1  id=3152534307690061594  code=YR5088082431I  stake=160,00
```

**O mesmo código de comprovante.** São 189 apostas reais aparecendo como 269 entradas, com
**77 duplicatas entre visões**: bilhetes que acabaram de pagar `confirmation` e pagaram de novo.

Dentro do mesmo namespace a memória funciona bem (numa passada seguinte: `alvos 282 ·
pulados 425`). **O desperdício mora só na fronteira entre visões.**

O campo estável é o **`TP`** (carimbo de tempo do bilhete), idêntico nas duas visões em 6 de 6
pares conferidos por código. Ele **não é único sozinho**: nas mesmas 269 entradas, 3 `TP` se
repetiram dentro da mesma visão, que é aposta feita no mesmo segundo. Precisa do desempatador
que o projeto já usa para dedup sem id — stake e odd, ambos no `summary`, de graça.

> **Sintoma para reconhecer isto noutro campo:** uma memória que nunca acerta, num universo
> onde você sabe que quase tudo já foi visto. Antes de suspeitar da memória, pergunte se a
> **chave** dela pertence ao dado ou à consulta que o trouxe. Id de listagem é da listagem.

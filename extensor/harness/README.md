# Harness da captura (SharpenUp)

Roda o **código real** da extensão — os `*_inject.js` e os formatadores do `content.js`,
lidos do repo, não uma cópia — contra **payloads reais salvos** em `fixtures/`. Sem
navegador, sem rede, em menos de 1 segundo.

```powershell
node extensor/harness/run.mjs          # todos os casos
node extensor/harness/run.mjs kto      # só a KTO
```

Exit 1 em qualquer falha. **Rode antes de todo commit que toque `*_inject.js` ou um
`formatTicket*`.**

---

## Por que existe

Até a s192, todo harness era montado no scratchpad e jogado fora no fim da sessão
(bet365 na s178, KTO na s192). Consequências medidas:

- cada casa nova reconstruía o andaime do zero — trabalho repetido, toda vez;
- **nenhuma regressão ficava travada**: o parser da bet365 quebrou em três sessões
  seguidas (`02` lido como perna, `04` ignorado, `TP=00010101…` virando 01/01/0001) e
  nada acusou antes do teste ao vivo;
- a validação morria junto com o payload — o único lugar onde as armadilhas de cada
  casa estavam registradas era a prosa do STATUS.

Aqui o andaime é permanente e **casa nova = um arquivo em `casos/` + um `fixtures/*.json`**.

---

## Anatomia

| Arquivo | Papel |
|---|---|
| `sandbox.mjs` | Mundo MAIN falso (fetch/XHR/postMessage) + carregador do `content.js` |
| `run.mjs` | Descobre `casos/*.mjs`, roda, imprime, exit 1 na falha |
| `casos/<casa>.mjs` | O que se espera de cada bilhete da fixture daquela casa |
| `fixtures/<casa>.*.json` | Payload REAL capturado da casa (F12 → Network → Copy response) |

`carregarContent()` roda o `content.js` **inteiro** num DOM/`chrome` dublados e devolve
`pegar(nome)` — enxerga qualquer função interna do arquivo, inclusive os `formatTicket*`.
Nada precisa ser exportado e **nada é recortado por comentário** (o harness antigo fatiava
o arquivo por marcador de comentário e quebrava a cada edição de comentário).

`rodarInject()` entrega a fixture como se fosse a resposta da casa e **também exercita o
replay**: a URL de cada requisição passa pelo `responder`, então dá para simular paginação
devolvendo páginas diferentes e provar que o loop termina.

---

## Adicionar uma casa

1. **Salvar a fixture.** Na casa, F12 → Network → a requisição da lista de bilhetes →
   *Copy response* → `fixtures/<casa>.<endpoint>.json`.
   Guarde uma amostra que cubra os casos que doem: **1 aberta, 1 perdida, 1 ganha, 1 com
   boost, 1 múltipla/bet builder**. Anonimize se houver nome/CPF no payload.
2. **Escrever `casos/<casa>.mjs`** espelhando `casos/kto.mjs`: exporta `casa` e uma função
   `rodar()` que devolve `{falhas: string[], testes: number}`.
3. **Conferir cada valor esperado contra o que a PRÓPRIA CASA renderiza na tela** — não
   contra o que o código produz. O harness trava a leitura correta, não o comportamento atual.
4. Rodar. Depois **quebrar de propósito** um valor esperado e conferir que o caso falha —
   harness que nunca falha não protege nada.

> As expectativas são a documentação executável das armadilhas da casa. Toda armadilha
> descoberta em produção deve virar uma linha aqui — senão ela volta.

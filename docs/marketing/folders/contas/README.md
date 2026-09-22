# Folder da tela Contas

Encarte de uma página para apresentar a aba **Contas** ao grupo `Sharpen - Testers`.
Saída: `folder-contas.png` (3120 × 5952, ~1,4 MB — o limite do Telegram por foto é 10 MB).

## De onde vêm os números e os nomes

**Os números são da operação do Feca** (decisão dele, 22/09/2026): 184 contas inativas,
mediana de 10 dias, custo de R$ 74.284, múltiplo de 4,65×, e a Superbet com 58 contas.
**Os nomes de conta e de fornecedor são fictícios** — `marianalopes203040`, `KaR1515`,
`MV`, `TopPro`, `Leandro`. Nenhuma conta de ninguém aparece aqui, e o rodapé do folder
diz isso.

A tela, o markup e o CSS são os **reais**: o `capturar_recortes.mjs` abre a aba no
`servidor_demo` e troca só os VALORES no DOM. Não é um desenho da tela, é a tela.

> **Por que não usar o dado do demo direto:** no `dados_demo.py` as 102 contas são
> **todas ativas** e apostam o período inteiro, então o histograma sai com quatro faixas
> zeradas e o painel `Últimas contas` sem mediana. Um folder assim ensinaria a tela
> errado. Consertar o gerador (simular limitação) é o caminho certo se este folder
> precisar ser refeito muitas vezes — ficou fora por tempo.

## Como refazer

```
python scripts/demo/servidor_demo.py 8655
node docs/marketing/folders/contas/capturar_recortes.mjs <pasta> 8655
node docs/marketing/folders/contas/renderizar_folder.mjs <pasta>
```

O primeiro grava os três recortes (`recorte-geral`, `recorte-lista`, `recorte-casa`) e o
`pos.json`; o segundo monta o `folder-contas.png` a partir do `folder.html`.

**O `pos.json` existe para as chamadas numeradas não ficarem no chute:** ele guarda a
posição de cada alvo em % do recorte, medida no DOM. Ao refazer, confira se os `left`/
`top` das `.bolha` no `folder.html` ainda batem com ele.

## Três armadilhas medidas

- **`cnToggle` repinta a tela inteira**, então abrir o drill desfaz a injeção nas fichas.
  Daí `injetarFichas` ser função e rodar **duas vezes**.
- **Trocar o nome da casa não troca o favicon.** O chip sai de `mkHouseChip`/`casaCell`,
  e renomear só o texto deixou a Superbet com o ícone da Bet365. Regenere o chip.
- **O recorte da casa começa na FICHA**, não na seção: o cabeçalho "Por casa" e a legenda
  da barra já são o recorte do meio, e repeti-los alongou o folder em 113px sem dizer
  nada novo.

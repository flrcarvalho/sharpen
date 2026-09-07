# -*- coding: utf-8 -*-
"""Planilha o ATRASO do canal `Grego Tips - VIP` — as apostas que ele parou de
registrar no tracker, da msg **969** (01/09/2026 22:04) até a última do export
(msg 1110, 06/09/2026 15:51).

⚠️ **Este script NÃO lê planilha. A fonte são os PRINTS do canal.**
`import_grego_csv.py` importou as 956 linhas do tracker, que param em
`GV202609-32` (lote entrado à mão em 01/09 23:28–23:35). Daí em diante ele
publicou no canal e não planilhou. O Feca apontou a fronteira
(`t.me/c/3928624343/969`) e ela confere: nenhum dos bilhetes daqui aparece no CSV.

── De onde vem cada campo ────────────────────────────────────────────────────

Export `ChatExport_2026-09-06`: 142 mensagens a partir da 969, **79 com aposta**
(as 3 que têm `%` sem print são aviso de stake — `2.25% Betano`), **195 linhas de
aposta**. Os 79 prints foram lidos um a um; a transcrição está no bloco `DADOS`
abaixo, uma seção por mensagem.

    stake      → legenda da mensagem (`1.50%`), em unidades como o resto da base
    resultado  → marca na PRÓPRIA linha da legenda: ✔️/✅ = W · ❌ = L ·
                 ⌛ ou SEM marca = **aberta** (decisão do Feca: ele completa à mão)
    odd        → o PRINT. Só 29 das 195 linhas trazem odd escrita na legenda
    seleção    → o PRINT. **67 linhas (34 %) têm legenda cega** (`1.50%`, sem
                 nome): sem o print elas não existiriam
    confronto  → o PRINT. O tracker nunca teve essa coluna
    casa       → host do link da mensagem, conferido contra o nome no rodapé:
                 batem em 100 % das 66 mensagens que têm os dois

── O pareamento stake ↔ seleção, que é onde isso costuma errar em silêncio ───

Legenda fora de ordem põe o valor certo na aposta errada **sem o total mudar**
(regra do `CLAUDE.md`, medida no Soh Props). Aqui há três conferências, e todas
foram usadas:

1. **A caixa de valor do print traz o R$ igual ao `%` da legenda.** bet365 e
   Betano imprimem a stake; nas mensagens em que ela aparece, ela bate exata
   (ex.: msg 990 → R$ 2,00 / 0,50 / 0,50 / 0,25 = `2.00% / 0.50% / 0.50% / 0.25%`).
2. **A escada de odd.** Limiar maior = odd maior = stake menor. Uma inversão
   salta aos olhos.
3. **O nome, quando a legenda o traz** — e ele MANDA sobre a posição. Na msg 986
   a legenda está fora de ordem (`+2`, `+4`, `+3`) enquanto o print está em
   ordem; quem parear por posição erra duas das três.

E para a combinada, o produto das pernas confere a odd do cupom: msg 1085 dá
`1.95 × 1.98 × 2.50 = 9.65` exato, msg 1036 dá `4.75 × 6.60 = 31.35` exato. Onde
o cupom é `Criar Aposta` da Betano o produto fica ACIMA da odd paga (a casa corta
a combinação do mesmo jogo) — aí vale o número do print, nunca o produto.

── Descrição no formato do MASTER (decisão do Feca, 06/09/2026) ──────────────

As 956 linhas do tracker são o título cru dele, sem confronto, porque a fonte não
tinha mais nada. **Aqui o print tem tudo**, e a descrição sai no
`MASTER_DESCRICAO §2`: `Entidade - Mercado [Confronto]`, com `v` no confronto
(§5), ` - ` como separador (§3) e a conversão obrigatória `Mais de 2.5 → Over 2.5`
(§11).

**A forma da linha segue a CASA, não uma normalização minha** (§10.1 × §10.2): a
Betano e o BetMGM vendem o mercado discreto (`3+ Chutes`) e a bet365 e a Superbet
o contínuo (`Over 2.5 Chutes`). São o mesmo mercado, e o MASTER dá template
separado para cada forma — reescrever uma na outra seria inventar apresentação.

`Anytime` de 1+ vai **sem sufixo** (`Lucas Copado [Wolfsburg v Cottbus]`, §12.1).
Recorte de período vira sufixo antes do confronto (`2+ Chutes 1º Tempo`, §12.10).
Combinada usa ` // `, o único separador de seleção do sistema (#19).

── O que é MÚLTIPLA aqui ─────────────────────────────────────────────────────

São 30 linhas, e três coisas diferentes caem nelas:

- **`Criar Aposta` / bet builder do mesmo jogo** (Betano, bet365). O print às
  vezes mostra só o cupom, e a legenda o chama pela perna que interessa a ele
  (msg 1080: legenda `Dest +1 Chutes`, print `Guus Til 1+ // Dest 1+` @1.85).
  Três linhas de legenda para três itens do print, na ordem — a 1ª é o cupom.
- **Dupla/Tripla/Quadra de jogos diferentes**, com as pernas listadas como
  simples na mesma mensagem.
- **Cupom que a legenda NÃO menciona não entra.** Nas msgs 1046 e 1055 o print
  mostra o construtor montado, mas a legenda declara duas SIMPLES com odd
  própria (`1.25% @2,42❌ | 1.25% @1.95✔️`) — são duas apostas, não um cupom.

`esporte = Múltiplos` só quando a combinada tem **3+ seleções de jogos
diferentes** (`MASTER_ESPORTES §2`): são 2 casos (msgs 1021 e 1085). Dupla de
dois jogos e cupom do mesmo jogo ficam em `Futebol`.

── Divergências entre legenda e print (todas anotadas, nenhuma silenciosa) ───

- **msg 1062** — legenda `@3.5`, print `3.60`. É **W**, então a odd entra no P/L:
  vale o print, e ele se prova sozinho (`Retornos Potenciais R$4,50 ÷ R$1,25 =
  3,60`). A legenda é arredondamento dele.
- **msg 1057** — legenda `@1.39`, print `2.22` no cupom. É **L** (a odd não muda
  o P/L). Fica a da legenda, que é o que ele mandou planilhar, e a divergência
  sai no relatório.
- **msg 1029** — legenda diz `Cuzão Tackles +4`, print diz `3+`. Vale o print
  (fonte da casa). A msg 1030 confirma que ele escreve `+4` para o `4+`.
- **msg 1108** — legenda diz `+3 FG Nico`, print diz `2+`. O produto fecha com o
  print (`2.27 × 2.87 = 6.51 ≈ 6.60`), então vale o print.
- **msg 1022** — a tripla tem odd `32.9` declarada na legenda e o produto das 3
  pernas dá `31.36`. Fica a declarada (é a que ele pegou); anotada.
- **msg 997** — `1.5% @1.2u plan`: ele declara a stake de novo, em `u`, e o `plan`
  é "planilhar". Vale **1,20**, que é a instrução explícita. Odd 6,50, a
  **aumentada** da Betfair (6,00 riscado ao lado) — mesma regra do Rogerin: o
  bônus é pago por fora e a odd exibida subestimaria a vitória.

── Numeração, origem e idempotência ──────────────────────────────────────────

Códigos `GV202609-33` em diante, continuando a série do tracker — e é isso que
faz o UPSERT reconhecer a linha se ela voltar por outro caminho
(`_assinatura` = `ID|casa|parceiro|codigo`).

⚠️ **`origem='extracao'`, não `'import'`.** O `import_grego_csv.py` apaga
`WHERE dono=… AND origem='import'` antes de reescrever: com a mesma origem, um
reimport do tracker levaria estas 195 linhas junto, em silêncio. E a idempotência
DAQUI é por **faixa de código** (`DELETE … WHERE codigo_bilhete = ANY(...)`), que
não depende de origem nenhuma e não encosta no que o bot vier a escrever.

⚠️ **Rodar este script DEPOIS de um reimport do tracker**, se algum dia houver:
a ordem importa só para os códigos, e eles não colidem (33+ contra 1–32).

⚠️ **O contador do bot tem de subir para além do ÚLTIMO código daqui** antes da
primeira aposta pelo bot — hoje `GV202609-227`. Planilha, este script e o bot
escrevem na MESMA série.

Uso:
    python scripts/import_grego_canal_s325.py --dono gregozxrd
    python scripts/import_grego_canal_s325.py --dono gregozxrd --go
"""
import argparse
import asyncio
import datetime as dt
import hashlib
import os
import re
from collections import Counter

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
PARCEIRO = 'Padrão'
TIPSTER = 'Grego Tips - VIP'
PREFIXO = 'GV'
ORIGEM = 'extracao'          # NÃO 'import' — ver docstring
INICIO = 33                  # o tracker parou em GV202609-32
VALID = {'W', 'L', 'V', 'HW', 'HL'}

# Contagem CEGA das marcas nas legendas das 79 mensagens (regex sobre o export,
# sem olhar print nenhum). O relatório confronta a leitura dos prints com isto —
# ver o gate em `relatorio`. Medido em 06/09/2026 sobre `ChatExport_2026-09-06`.
EMOJI_NO_EXPORT = {'❌': 73, '✔️': 40, '⌛': 15, 'sem marca': 68}

# ── Transcrição dos 79 prints ────────────────────────────────────────────────
# Cabeçalho de seção:  # <nn> <msg> <dd/mm/aaaa do EVENTO> <Casa>
# Linha de aposta:     S|entidade|mercado|confronto|odd|stake|marca[|MU]
#                      M|descrição da combinada|(vazio)|confronto|odd|stake|marca[|MU]
# marca: W · L · A (aberta: ⌛ ou sem marca na legenda)
# `MU` no fim = esporte `Múltiplos` (3+ seleções de JOGOS diferentes, §2)
DADOS = """
# 01 969 01/09/2026 BetMGM
S|Elias, Rafael||Yokohama F Marinos v Kyoto Sanga FC|2.88|1.50|L
S|Marcelo Ryan||Shimizu S-Pulse v FC Tokyo|2.70|1.25|L
S|Hummet, Deniz||V-Varen Nagasaki v Gamba Osaka|2.62|1.25|A
S|Leo Ceara||Mito Hollyhock v Kashima Antlers|2.15|1.75|W
M|Elias, Rafael [Yokohama F Marinos v Kyoto Sanga FC] // Marcelo Ryan [Shimizu S-Pulse v FC Tokyo] // Hummet, Deniz [V-Varen Nagasaki v Gamba Osaka] // Leo Ceara [Mito Hollyhock v Kashima Antlers]|||43.80|0.25|A|MU

# 02 971 02/09/2026 Bet365
S|Matteo Dagasso|Over 1.5 Chutes|Udinese v Venezia|2.75|1.50|L
S|Matteo Dagasso|Over 2.5 Chutes|Udinese v Venezia|6.50|0.75|L
S|Matteo Dagasso|Over 3.5 Chutes|Udinese v Venezia|17.00|0.25|L

# 03 974 02/09/2026 Betano
S|Thierry Correia|1+ Chutes|Udinese v Venezia|2.07|1.75|W
S|Thierry Correia|2+ Chutes|Udinese v Venezia|6.40|1.00|L

# 04 976 02/09/2026 Betano
M|Tyreece Campbell 2+ Chutes // Over 0.5 Gols||West Bromwich Albion v Charlton|1.70|1.50|W
S|Tyreece Campbell|3+ Chutes|West Bromwich Albion v Charlton|2.85|0.50|A
S|Tyreece Campbell|4+ Chutes|West Bromwich Albion v Charlton|5.70|0.50|A

# 05 977 02/09/2026 Betano
S|Kareem Tunde|1+ Chutes no Gol|West Bromwich Albion v Charlton|1.72|1.25|W
S|Kareem Tunde|2+ Chutes no Gol|West Bromwich Albion v Charlton|4.50|0.50|A

# 06 978 02/09/2026 Betano
S|Josh Coburn|3+ Chutes|Millwall FC v Wrexham FC|2.20|1.50|L
S|Josh Coburn|4+ Chutes|Millwall FC v Wrexham FC|4.10|0.50|L

# 07 979 02/09/2026 Betano
M|Isaac Price 3+ Chutes // Isaac Price 1+ Chutes no Gol||West Bromwich Albion v Charlton|1.82|1.75|W
S|Isaac Price|4+ Chutes|West Bromwich Albion v Charlton|2.35|0.75|W
S|Isaac Price|5+ Chutes|West Bromwich Albion v Charlton|4.00|0.50|A

# 08 980 02/09/2026 BetMGM
S|Carrascal, Jorge|3+ Chutes|Flamengo v Mirassol|1.80|1.50|L
S|Carrascal, Jorge|4+ Chutes|Flamengo v Mirassol|3.10|0.50|L
S|Carrascal, Jorge|5+ Chutes|Flamengo v Mirassol|5.50|0.50|L

# 09 982 03/09/2026 Betano
S|Francesco Ruocco|2+ Chutes|US Palermo v Mantova FC|1.85|2.00|A
S|Francesco Ruocco|3+ Chutes|US Palermo v Mantova FC|3.60|1.00|A
S|Francesco Ruocco|4+ Chutes|US Palermo v Mantova FC|7.60|0.50|A

# 10 984 03/09/2026 Betano
S|Ettore Gliozzi|2+ Chutes|US Palermo v Mantova FC|1.72|3.00|W
S|Ettore Gliozzi|3+ Chutes|US Palermo v Mantova FC|3.15|1.25|W
S|Ettore Gliozzi|4+ Chutes|US Palermo v Mantova FC|6.50|0.50|L

# 11 986 03/09/2026 Betano
S|Mattia Compagnon|2+ Chutes|Cagliari v Hellas Verona|1.95|2.00|A
S|Mattia Compagnon|3+ Chutes|Cagliari v Hellas Verona|3.95|0.50|A
S|Mattia Compagnon|4+ Chutes|Cagliari v Hellas Verona|8.50|1.00|A

# 12 988 02/09/2026 Betano
S|Ramon Rique|2+ Chutes|Vitória v Vasco da Gama|2.75|1.25|L
S|Ramon Rique|3+ Chutes|Vitória v Vasco da Gama|6.80|0.50|L
S|Ramon Rique|4+ Chutes|Vitória v Vasco da Gama|14.50|0.50|L

# 13 990 02/09/2026 Bet365
S|Renato Kayzer|Over 2.5 Chutes|Vitória v Vasco da Gama|2.10|2.00|L
S|Renato Kayzer|Over 3.5 Chutes|Vitória v Vasco da Gama|3.75|0.50|L
S|Renato Kayzer|Over 4.5 Chutes|Vitória v Vasco da Gama|7.00|0.50|L
S|Renato Kayzer|Over 5.5 Chutes|Vitória v Vasco da Gama|15.00|0.25|L

# 14 992 03/09/2026 Betano
S|Fahem Benaissa|1+ Chutes|US Palermo v Mantova FC|1.87|1.50|L
S|Fahem Benaissa|2+ Chutes|US Palermo v Mantova FC|5.20|0.50|L
S|Fahem Benaissa|3+ Chutes|US Palermo v Mantova FC|14.00|0.25|L

# 15 994 03/09/2026 Betano
S|Benjamin Andre|2+ Faltas Sofridas|Toulouse FC v Lille|2.07|1.50|W
S|Benjamin Andre|3+ Faltas Sofridas|Toulouse FC v Lille|4.40|0.50|W
S|Benjamin Andre|4+ Faltas Sofridas|Toulouse FC v Lille|9.50|0.50|L

# 16 996 03/09/2026 Betano
S|Santiago Hidalgo|1+ Chutes no Gol|Toulouse FC v Lille|1.70|1.25|W
S|Santiago Hidalgo|2+ Chutes no Gol|Toulouse FC v Lille|4.35|0.50|W

# 17 997 03/09/2026 Betfair
S|Ethan Mbappe||Toulouse v Lille|6.50|1.20|L

# 18 999 03/09/2026 Betano
S|Andres Antanon|2+ Chutes|Real Sociedad v Celta de Vigo|2.32|1.50|L
S|Andres Antanon|3+ Chutes|Real Sociedad v Celta de Vigo|5.20|0.50|L
S|Andres Antanon|4+ Chutes|Real Sociedad v Celta de Vigo|11.50|0.50|L

# 19 1003 04/09/2026 Betano
S|Andreas Skov Olsen|2+ Chutes|Istanbul Basaksehir FK v Galatasaray|1.88|1.50|A
S|Andreas Skov Olsen|3+ Chutes|Istanbul Basaksehir FK v Galatasaray|3.70|0.50|A
S|Andreas Skov Olsen|4+ Chutes|Istanbul Basaksehir FK v Galatasaray|7.90|0.50|A

# 20 1005 04/09/2026 Bet365
S|Chris Fuhrich|Over 0.5 Faltas Cometidas|VfB Stuttgart v Köln|2.50|1.50|A
S|Chris Fuhrich|Over 1.5 Faltas Cometidas|VfB Stuttgart v Köln|9.00|0.50|A

# 21 1007 04/09/2026 Bet365
S|Jahmai Simpson-Pusey|Over 0.5 Faltas Cometidas|VfB Stuttgart v Köln|2.00|1.50|A
S|Jahmai Simpson-Pusey|Over 1.5 Faltas Cometidas|VfB Stuttgart v Köln|6.00|0.50|A

# 22 1009 04/09/2026 Betano
S|Gideon Mensah|2+ Desarmes|VfB Stuttgart v 1. FC Köln|1.83|1.50|A
S|Gideon Mensah|3+ Desarmes|VfB Stuttgart v 1. FC Köln|3.55|0.50|A
S|Gideon Mensah|4+ Desarmes|VfB Stuttgart v 1. FC Köln|7.50|0.50|A
S|Gideon Mensah|5+ Desarmes|VfB Stuttgart v 1. FC Köln|14.50|0.25|A

# 23 1011 04/09/2026 Betano
S|Nicolás Tagliafico|2+ Faltas Cometidas|Lyon v AJ Auxerre|3.20|2.00|A
S|Nicolás Tagliafico|3+ Faltas Cometidas|Lyon v AJ Auxerre|8.00|0.50|A

# 24 1012 04/09/2026 Betano
S|Nicolás Tagliafico|2+ Faltas Sofridas|Lyon v AJ Auxerre|3.55|1.25|A
S|Nicolás Tagliafico|3+ Faltas Sofridas|Lyon v AJ Auxerre|9.25|0.50|A

# 25 1013 04/09/2026 Betano
M|Nicolás Tagliafico 2+ Faltas Cometidas // Nicolás Tagliafico 2+ Faltas Sofridas||Lyon v AJ Auxerre|11.75|0.50|A

# 26 1014 04/09/2026 Betano
M|Nicolás Tagliafico 3+ Faltas Sofridas // Nicolás Tagliafico 3+ Faltas Cometidas||Lyon v AJ Auxerre|70.00|0.25|A

# 27 1018 04/09/2026 Bet365
S|Gustav Marcussen||Vejle v Vendsyssel FF|3.00|1.25|A
S|Donavan Bagou||Hobro IK v Hvidovre IF|2.62|1.75|A
M|Gustav Marcussen [Vejle v Vendsyssel FF] // Donavan Bagou [Hobro IK v Hvidovre IF]|||7.87|0.50|A

# 28 1021 04/09/2026 BetMGM
S|Schalk, Alex||Helmond Sport v VVV Venlo|3.40|1.25|A
S|Quispel, Freddy||FC Emmen v FC Volendam|3.50|1.50|A
S|Soumano, Moussa||RKC Waalwijk v NAC Breda|2.80|1.50|A
M|Schalk, Alex [Helmond Sport v VVV Venlo] // Quispel, Freddy [FC Emmen v FC Volendam] // Soumano, Moussa [RKC Waalwijk v NAC Breda]|||33.32|0.25|A|MU

# 29 1022 04/09/2026 BetMGM
S|Pugno, Diego||Almere City FC v Jong Ajax Amsterdam|2.80|1.25|A
S|Unuvar, Emre||Almere City FC v Jong Ajax Amsterdam|3.20|1.50|A
S|Kania, Julian||Heracles Almelo v De Graafschap|3.50|1.25|A
M|Pugno, Diego // Unuvar, Emre [Almere City FC v Jong Ajax Amsterdam] // Kania, Julian [Heracles Almelo v De Graafschap]|||32.90|0.25|A

# 30 1023 04/09/2026 Betano
S|Achraf Hakimi|2+ Chutes|Paris Saint-Germain v Monaco|1.82|1.25|W
S|Achraf Hakimi|3+ Chutes|Paris Saint-Germain v Monaco|3.50|0.50|W

# 31 1024 04/09/2026 Betano
S|Maghnes Akliouche|3+ Chutes|Paris Saint-Germain v Monaco|1.91|1.75|W
S|Maghnes Akliouche|4+ Chutes|Paris Saint-Germain v Monaco|3.30|0.75|A
S|Maghnes Akliouche|5+ Chutes|Paris Saint-Germain v Monaco|6.20|0.50|A

# 32 1025 04/09/2026 Betano
S|Federico Valverde|1+ Chutes no Gol|Bétis v Real Madrid|1.78|1.25|W
S|Federico Valverde|2+ Chutes no Gol|Bétis v Real Madrid|4.75|0.50|A

# 33 1029 05/09/2026 Betano
S|Matthieu Udol|2+ Desarmes|Lens v FC Lorient|2.05|2.00|L
S|Michał Skóraś|2+ Desarmes|Lens v FC Lorient|2.62|2.50|L
S|Michael Cuisance|3+ Desarmes|Lens v FC Lorient|2.70|1.50|A
M|Matthieu Udol 2+ Desarmes // Michał Skóraś 2+ Desarmes // Michael Cuisance 3+ Desarmes||Lens v FC Lorient|13.50|0.50|L

# 34 1030 05/09/2026 Betano
S|Michał Skóraś|3+ Desarmes|Lens v FC Lorient|6.30|1.00|L
S|Michael Cuisance|4+ Desarmes|Lens v FC Lorient|5.30|0.50|A
S|Matthieu Udol|3+ Desarmes|Lens v FC Lorient|4.25|1.00|L
M|Michał Skóraś 3+ Desarmes // Michael Cuisance 4+ Desarmes // Matthieu Udol 3+ Desarmes||Lens v FC Lorient|110.00|0.25|A

# 35 1031 05/09/2026 Betano
S|Michał Skóraś|4+ Desarmes|Lens v FC Lorient|13.50|0.50|L
S|Matthieu Udol|4+ Desarmes|Lens v FC Lorient|9.25|0.50|L
M|Michał Skóraś 4+ Desarmes // Matthieu Udol 4+ Desarmes||Lens v FC Lorient|120.00|0.25|L

# 36 1034 05/09/2026 Betano
S|Saul Coco|1+ Faltas Sofridas|Fiorentina v Torino|2.10|1.50|W
S|Saul Coco|2+ Faltas Sofridas|Fiorentina v Torino|6.60|0.50|L

# 37 1035 05/09/2026 Betano
S|Diego Gomez|2+ Faltas Cometidas|Brighton & Hove Albion v Leeds United|2.18|1.25|W
S|Diego Gomez|3+ Faltas Cometidas|Brighton & Hove Albion v Leeds United|4.75|0.50|L
S|Diego Gomez|4+ Faltas Cometidas|Brighton & Hove Albion v Leeds United|10.50|0.25|L

# 38 1036 05/09/2026 Betano
M|Diego Gomez 3+ Faltas Cometidas [Brighton & Hove Albion v Leeds United] // Saul Coco 2+ Faltas Sofridas [Fiorentina v Torino]|||31.35|0.25|L

# 39 1037 05/09/2026 Bet365
S|Mamadou Kone|Over 1.5 Chutes|Lens v Lorient|1.83|1.75|W
S|Mamadou Kone|Over 2.5 Chutes|Lens v Lorient|3.50|0.50|L
S|Mamadou Kone|Over 3.5 Chutes|Lens v Lorient|8.00|0.50|L

# 40 1042 05/09/2026 Bet365
S|Lucas Copado||Wolfsburg v Cottbus|4.50|1.25|W

# 41 1044 05/09/2026 Betano
S|Timothy Noor Ouma|1+ Chutes|Stoke City v Charlton|1.93|1.50|L
S|Timothy Noor Ouma|2+ Chutes|Stoke City v Charlton|5.60|0.50|L

# 42 1046 05/09/2026 Betano
S|Joe Willock|2+ Faltas Cometidas|Newcastle United v AFC Bournemouth|2.42|1.25|L
S|Nico Gonzalez|2+ Faltas Cometidas|Newcastle United v AFC Bournemouth|1.95|1.25|W

# 43 1048 05/09/2026 Betano
S|Alieu Eybi Njie|1+ Chutes no Gol|Fiorentina v Torino|2.00|1.25|A
S|Alieu Eybi Njie|2+ Chutes no Gol|Fiorentina v Torino|5.90|0.50|A

# 44 1049 05/09/2026 Bet365
S|Michael Kayode|Marcar de Cabeça|Brentford v Sunderland|81.00|0.25|L

# 45 1050 05/09/2026 Bet365
S|Konstantinos Karetsas|Jogador a Dar Assistência|TSG Hoffenheim v Borussia Dortmund|4.50|1.50|L

# 46 1052 05/09/2026 Bet365
S|Adam Daghim|Over 1.5 Chutes|TSG Hoffenheim v Borussia Dortmund|1.83|1.50|W
S|Adam Daghim|Over 2.5 Chutes|TSG Hoffenheim v Borussia Dortmund|3.50|0.50|W
S|Adam Daghim|Over 3.5 Chutes|TSG Hoffenheim v Borussia Dortmund|7.00|0.50|L

# 47 1053 05/09/2026 Bet365
S|Julian Ryerson|Over 0.5 Chutes|TSG Hoffenheim v Borussia Dortmund|2.62|1.25|L

# 48 1055 05/09/2026 Betano
S|Ezechiel Banzuzi|2+ Faltas Sofridas|Werder Bremen v RB Leipzig|2.67|1.25|W
S|Neil El Aynaoui|2+ Faltas Cometidas|Werder Bremen v RB Leipzig|2.90|1.25|L

# 49 1057 05/09/2026 Betano
M|Nico O'Reilly 1+ Faltas Cometidas // Elliot Anderson 1+ Faltas Cometidas||Manchester City v Coventry City|1.39|1.50|L
S|Nico O'Reilly|2+ Faltas Cometidas|Manchester City v Coventry City|3.80|1.00|A

# 50 1059 05/09/2026 Betano
S|Iliman Ndiaye|2+ Desarmes|Manchester City v Coventry City|2.02|1.50|W
S|Iliman Ndiaye|3+ Desarmes|Manchester City v Coventry City|4.15|0.50|W
S|Iliman Ndiaye|4+ Desarmes|Manchester City v Coventry City|9.00|0.50|W

# 51 1060 05/09/2026 Betano
S|Kaito Mizuta|2+ Chutes|Le Havre AC v Brestois|1.80|1.50|A
S|Kaito Mizuta|3+ Chutes|Le Havre AC v Brestois|3.45|0.50|A
S|Kaito Mizuta|4+ Chutes|Le Havre AC v Brestois|7.30|0.25|A

# 52 1062 05/09/2026 Bet365
S|Yaser Asprilla||Sporting Gijón v Girona|3.60|1.25|W

# 53 1063 05/09/2026 Bet365
S|Abraham Marcus|Over 0.5 Chutes no Gol|Estrela Amadora v FC Famalicão|2.25|1.25|W
S|Abraham Marcus|Over 1.5 Chutes no Gol|Estrela Amadora v FC Famalicão|9.00|0.50|L

# 54 1065 05/09/2026 Betano
S|Luciano Valente|2+ Chutes|NEC Nijmegen v Feyenoord|2.07|1.50|W
S|Luciano Valente|3+ Chutes|NEC Nijmegen v Feyenoord|4.30|0.75|L
S|Luciano Valente|4+ Chutes|NEC Nijmegen v Feyenoord|9.50|0.50|L

# 55 1067 05/09/2026 Bet365
M|Florian Thauvin Marcar a Qualquer Momento // Jean-Victor Makengo Over 0.5 Chutes||Lens v Lorient|3.00|1.50|L

# 56 1069 05/09/2026 Bet365
S|Christian Wagner||Helsingborg v Sandvikens IF|3.00|1.25|W
S|Alexander Johansson||Helsingborg v Sandvikens IF|3.20|1.50|L

# 57 1071 05/09/2026 Betano
S|Robin Gosens|2+ Faltas Cometidas|FC Schalke 04 v Bayern de Munique|3.10|1.25|W
S|Konrad Laimer|2+ Faltas Cometidas|FC Schalke 04 v Bayern de Munique|3.75|1.50|W
M|Robin Gosens 2+ Faltas Cometidas // Konrad Laimer 2+ Faltas Cometidas||FC Schalke 04 v Bayern de Munique|11.75|0.50|W

# 58 1073 05/09/2026 Bet365
S|Chiquinho|Over 1.5 Chutes|Alverca v SC Braga|2.10|1.50|A
S|Toni Tamarit|Over 0.5 Chutes|Alverca v SC Braga|2.25|1.00|L
S|Figueiredo|Over 1.5 Chutes|Alverca v SC Braga|1.90|1.50|L
M|Chiquinho Over 1.5 Chutes // Toni Tamarit Over 0.5 Chutes // Figueiredo Over 1.5 Chutes||Alverca v SC Braga|7.50|0.50|L

# 59 1074 05/09/2026 Bet365
S|Figueiredo|Over 2.5 Chutes|Alverca v SC Braga|3.75|0.75|L
S|Chiquinho|Over 2.5 Chutes|Alverca v SC Braga|4.33|0.50|A
S|Toni Tamarit|Over 1.5 Chutes|Alverca v SC Braga|8.00|0.50|L
M|Figueiredo Over 2.5 Chutes // Chiquinho Over 2.5 Chutes // Toni Tamarit Over 1.5 Chutes||Alverca v SC Braga|67.00|0.25|A

# 60 1076 05/09/2026 Superbet
S|Kodai Sano|Over 1.5 Chutes|Ajax Amsterdam v PSV Eindhoven|2.52|1.50|L
S|Kodai Sano|Over 2.5 Chutes|Ajax Amsterdam v PSV Eindhoven|5.00|0.50|L
S|Kodai Sano|Over 3.5 Chutes|Ajax Amsterdam v PSV Eindhoven|11.00|0.50|L

# 61 1080 05/09/2026 Betano
M|Guus Til 1+ Chutes // Sergiño Dest 1+ Chutes||AFC Ajax v PSV Eindhoven|1.85|2.00|W
S|Sergiño Dest|2+ Chutes|AFC Ajax v PSV Eindhoven|4.35|0.75|L
S|Sergiño Dest|3+ Chutes|AFC Ajax v PSV Eindhoven|11.50|0.50|L

# 62 1081 05/09/2026 Betano
M|Kodai Sano 3+ Chutes // Sergiño Dest 2+ Chutes||AFC Ajax v PSV Eindhoven|22.00|0.50|L

# 63 1082 05/09/2026 Betano
S|Sergiño Dest|2+ Chutes 1º Tempo|AFC Ajax v PSV Eindhoven|10.50|0.50|L
S|Kodai Sano|2+ Chutes 1º Tempo|AFC Ajax v PSV Eindhoven|6.50|0.50|L
M|Sergiño Dest 2+ Chutes 1º Tempo // Kodai Sano 2+ Chutes 1º Tempo||AFC Ajax v PSV Eindhoven|60.00|0.25|L

# 64 1083 05/09/2026 Betano
M|Kodai Sano 3+ Chutes 1º Tempo // Sergiño Dest 2+ Chutes 1º Tempo||AFC Ajax v PSV Eindhoven|150.00|0.25|A

# 65 1085 05/09/2026 Betano
S|Pathe Mboup|2+ Faltas Cometidas|Le Havre AC v Brestois|1.95|1.50|W
S|Alexandre Lauray|2+ Faltas Cometidas|Nice v Le Mans UC 72|1.98|1.50|L
S|Pape Gueye|2+ Faltas Cometidas|Villarreal CF v Deportivo A Coruña|2.50|1.50|W
M|Pathe Mboup 2+ Faltas Cometidas [Le Havre AC v Brestois] // Alexandre Lauray 2+ Faltas Cometidas [Nice v Le Mans UC 72] // Pape Gueye 2+ Faltas Cometidas [Villarreal CF v Deportivo A Coruña]|||9.65|0.50|L|MU

# 66 1086 05/09/2026 Betano
S|Pathe Mboup|3+ Faltas Cometidas|Le Havre AC v Brestois|3.95|1.00|W
S|Pathe Mboup|4+ Faltas Cometidas|Le Havre AC v Brestois|8.50|0.50|L

# 67 1090 05/09/2026 BetMGM
S|Duarte, Bruno|3+ Chutes|Fluminense v Vasco da Gama|1.91|2.00|A
S|Duarte, Bruno|4+ Chutes|Fluminense v Vasco da Gama|3.40|1.00|A
S|Duarte, Bruno|5+ Chutes|Fluminense v Vasco da Gama|6.00|0.50|A
S|Duarte, Bruno|6+ Chutes|Fluminense v Vasco da Gama|11.00|0.50|A

# 68 1093 06/09/2026 Betano
S|Bukayo Saka|3+ Chutes|Arsenal v Chelsea|2.27|1.50|W
S|Bukayo Saka|4+ Chutes|Arsenal v Chelsea|4.05|0.50|W
S|Bukayo Saka|5+ Chutes|Arsenal v Chelsea|8.25|0.50|L

# 69 1095 06/09/2026 Betano
S|Giorgi Kochorashvili|2+ Chutes|Espanyol v Sevilha FC|3.80|1.25|A
S|Giorgi Kochorashvili|3+ Chutes|Espanyol v Sevilha FC|10.00|0.50|A

# 70 1097 06/09/2026 Betano
S|Gabriel Suazo|2+ Faltas Cometidas|Espanyol v Sevilha FC|2.42|1.75|A
S|Gabriel Suazo|3+ Faltas Cometidas|Espanyol v Sevilha FC|5.60|0.50|A

# 71 1098 06/09/2026 Betano
S|Omar El Hilali|2+ Faltas Cometidas|Espanyol v Sevilha FC|2.32|1.50|A
S|Omar El Hilali|3+ Faltas Cometidas|Espanyol v Sevilha FC|5.20|0.75|A

# 72 1100 06/09/2026 Bet365
S|Giorgi Kochorashvili|Over 1.5 Faltas Cometidas|Espanhol v Sevilha|1.90|1.75|A
S|Giorgi Kochorashvili|Over 2.5 Faltas Cometidas|Espanhol v Sevilha|4.00|0.75|A

# 73 1101 06/09/2026 Betano
M|Gabriel Suazo 2+ Faltas Cometidas // Giorgi Kochorashvili 2+ Faltas Cometidas // Omar El Hilali 2+ Faltas Cometidas||Espanyol v Sevilha FC|9.75|0.50|A

# 74 1102 06/09/2026 Betano
M|Omar El Hilali 3+ Faltas Cometidas // Gabriel Suazo 3+ Faltas Cometidas // Giorgi Kochorashvili 3+ Faltas Cometidas||Espanyol v Sevilha FC|90.00|0.25|A

# 75 1104 06/09/2026 Betano
S|Diego Moreira|2+ Chutes|Juventus FC v AC Milan|3.15|1.75|A
S|Diego Moreira|3+ Chutes|Juventus FC v AC Milan|7.90|0.75|A
S|Diego Moreira|4+ Chutes|Juventus FC v AC Milan|16.50|0.25|A

# 76 1106 06/09/2026 Betano
S|Kerim Alajbegovic|3+ Chutes|Juventus FC v AC Milan|2.27|1.50|A
S|Kerim Alajbegovic|4+ Chutes|Juventus FC v AC Milan|4.30|0.50|A

# 77 1108 06/09/2026 Betano
S|Kerim Alajbegovic|2+ Faltas Sofridas|Juventus FC v AC Milan|2.27|1.50|A
S|Nico Gonzalez|2+ Faltas Sofridas|Juventus FC v AC Milan|2.87|1.75|A
M|Kerim Alajbegovic 2+ Faltas Sofridas // Nico Gonzalez 2+ Faltas Sofridas||Juventus FC v AC Milan|6.60|0.50|A

# 78 1109 06/09/2026 Betano
S|Kerim Alajbegovic|3+ Faltas Sofridas|Juventus FC v AC Milan|5.10|0.50|A
S|Nico Gonzalez|3+ Faltas Sofridas|Juventus FC v AC Milan|7.20|0.50|A
M|Kerim Alajbegovic 3+ Faltas Sofridas // Nico Gonzalez 3+ Faltas Sofridas||Juventus FC v AC Milan|37.00|0.25|A

# 79 1110 06/09/2026 Betano
S|Jorginho|1+ Chutes no Gol|Remo v Flamengo|3.15|1.25|A
S|Jorginho|2+ Chutes no Gol|Remo v Flamengo|12.50|0.50|A
"""

_CAB = re.compile(r'^#\s+(\d+)\s+(\d+)\s+(\d{2}/\d{2}/\d{4})\s+(.+)$')


def carregar() -> list[dict]:
    rows: list[dict] = []
    bloco = None
    for bruta in DADOS.strip().splitlines():
        linha = bruta.strip()
        if not linha:
            continue
        cab = _CAB.match(linha)
        if cab:
            bloco = {'n': int(cab.group(1)), 'msg': int(cab.group(2)),
                     'data': cab.group(3), 'casa': cab.group(4).strip()}
            continue
        if linha.startswith('#'):
            continue
        if bloco is None:
            raise SystemExit(f'linha de aposta antes do cabeçalho: {linha!r}')
        p = linha.split('|')
        if len(p) not in (7, 8):
            raise SystemExit(f'linha malformada ({len(p)} campos): {linha!r}')
        tipo, ent, merc, conf, odd, stake, marca = p[:7]
        esp = p[7] if len(p) == 8 else ''
        if tipo not in ('S', 'M'):
            raise SystemExit(f'tipo inválido {tipo!r}: {linha!r}')
        if marca not in ('W', 'L', 'A'):
            raise SystemExit(f'marca inválida {marca!r}: {linha!r}')
        rows.append({
            **bloco,
            'tipo': tipo, 'entidade': ent.strip(), 'mercado': merc.strip(),
            'confronto': conf.strip(), 'odd': odd.strip(),
            'stake': stake.strip(), 'marca': marca,
            'esporte': 'Múltiplos' if esp == 'MU' else 'Futebol',
        })
    return rows


def descricao(r: dict) -> str:
    """`MASTER_DESCRICAO §2`: Entidade - Mercado [Confronto].
    Anytime de 1+ vai sem sufixo de mercado (§12.1). Combinada de jogos
    diferentes já carrega o confronto de cada perna e não leva o de fora."""
    conf = f' [{r["confronto"]}]' if r['confronto'] else ''
    if r['tipo'] == 'M':
        return f'{r["entidade"]}{conf}'.strip()
    if not r['mercado']:
        return f'{r["entidade"]}{conf}'.strip()
    return f'{r["entidade"]} - {r["mercado"]}{conf}'.strip()


# `MASTER_APOSTAS §1`: a categoria registra o OBJETO. Aqui o objeto está escrito
# no mercado que a casa imprimiu — não há adivinhação a fazer.
def categoria(r: dict) -> str:
    if r['tipo'] == 'M':
        return 'Múltipla'
    m = r['mercado'].lower()
    if not m or 'marcar' in m:
        return 'Anytime'                    # inclui "Marcar de Cabeça"
    if 'assistência' in m or 'assistencia' in m:
        return 'Assistência'
    if 'chutes no gol' in m:
        return 'Chutes no Gol'
    if 'chutes' in m:
        return 'Chutes'
    if 'faltas' in m:
        return 'Faltas'
    if 'desarmes' in m:
        return 'Desarmes'
    raise SystemExit(f'mercado sem categoria: {r["mercado"]!r} (msg {r["msg"]})')


def numerar(rows: list[dict]) -> list[dict]:
    """Continua a série do tracker. As 195 são todas de setembro."""
    for i, r in enumerate(rows):
        mes = dt.datetime.strptime(r['data'], '%d/%m/%Y').strftime('%Y%m')
        if mes != '202609':
            raise SystemExit(f'linha fora de setembro: {r["data"]} (msg {r["msg"]})')
        r['codigo'] = f'{PREFIXO}{mes}-{INICIO + i}'
        r['_dt'] = dt.datetime.strptime(r['data'], '%d/%m/%Y')
    return rows


def assinatura(r: dict) -> str:
    """Idêntica a repository._assinatura com código: ID|casa|parceiro|codigo."""
    raw = '|'.join(['ID', r['casa'], PARCEIRO, r['codigo']])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _f(v):
    try:
        return float(str(v).replace(',', '.'))
    except (TypeError, ValueError):
        return None


def fmt_stake(v) -> str:
    n = _f(v)
    return '' if n is None else f'{n:.2f}'.replace('.', ',')


def fmt_odd(v) -> str:
    n = _f(v)
    if n is None or n <= 0:
        return ''
    s = repr(float(n))
    return (s[:-2] if s.endswith('.0') else s).replace('.', ',')


def resultado(r: dict) -> str:
    return '' if r['marca'] == 'A' else r['marca']


def estado_extracao(res: str, odd: str) -> str:
    if res not in VALID:
        return 'aberta'
    if res in ('W', 'HW'):
        return 'resolvida' if (_f(odd.replace(',', '.')) or 0) > 0 else 'aberta'
    return 'resolvida'


def pl(r: dict):
    s = _f(r['stake']) or 0.0
    o = _f(r['odd'])
    res = resultado(r)
    if res == 'L':
        return -s
    if res == 'W':
        return s * (o - 1)
    return None            # aberta não tem P/L


def carregar_env():
    for line in open(ENV_PATH, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ---------- escrita ----------
async def gravar(rows: list[dict], dono: str):
    import asyncpg
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    codigos = [r['codigo'] for r in rows]
    casas = sorted({r['casa'] for r in rows})

    conn = await asyncpg.connect(url, command_timeout=120)
    try:
        u = await conn.fetchrow(
            'SELECT username, status FROM usuarios WHERE username = $1', dono)
        if not u:
            raise SystemExit(f'✋ ABORTADO — username {dono!r} não existe.')
        if u['status'] != 'ativo':
            raise SystemExit(f'✋ ABORTADO — {dono!r} está {u["status"]!r}.')
        print(f'  dono conferido: {dono} | status={u["status"]}')

        # A fronteira é uma afirmação sobre o mundo, então é conferida: nenhum
        # código desta faixa pode existir, e o tracker tem de parar em -32.
        ja = await conn.fetch(
            'SELECT codigo_bilhete, origem, descricao FROM bilhetes '
            'WHERE dono=$1 AND codigo_bilhete = ANY($2::text[])', dono, codigos)
        if ja:
            print(f'\n  {len(ja)} código(s) desta faixa JÁ existem — serão '
                  f'substituídos (idempotência por faixa de código):')
            for c in ja[:5]:
                print(f"    {c['codigo_bilhete']} | {c['origem']} | {c['descricao'][:45]}")
        ultimo = await conn.fetchval(
            "SELECT MAX(CAST(split_part(codigo_bilhete,'-',2) AS INT)) FROM bilhetes "
            "WHERE dono=$1 AND codigo_bilhete LIKE 'GV202609-%' AND origem='import'", dono)
        print(f'  último código do tracker (origem=import): GV202609-{ultimo}')
        if ultimo is not None and ultimo >= INICIO:
            raise SystemExit(
                f'✋ ABORTADO — o tracker já vai até -{ultimo} e este script começa '
                f'em -{INICIO}. Ajuste INICIO ou confira a fronteira.')
    finally:
        await conn.close()

    registros = [(
        dono, r['casa'], PARCEIRO, assinatura(r), r['codigo'],
        r['data'], r['esporte'], TIPSTER, categoria(r), descricao(r),
        fmt_stake(r['stake']), fmt_odd(r['odd']), resultado(r) or None,
        estado_extracao(resultado(r), fmt_odd(r['odd'])),
        None, None, ORIGEM,
    ) for r in rows]

    last_err = None
    for tentativa in range(1, 4):
        try:
            conn = await asyncpg.connect(url, command_timeout=120)
            try:
                async with conn.transaction():
                    # Idempotência por FAIXA DE CÓDIGO — não por origem. Assim
                    # este script não encosta nas 956 do tracker nem no que o bot
                    # vier a escrever.
                    apagadas = await conn.execute(
                        'DELETE FROM bilhetes WHERE dono=$1 AND codigo_bilhete = ANY($2::text[])',
                        dono, codigos)
                    print(f'  [tentativa {tentativa}] limpou faixa anterior: {apagadas}')
                    await conn.executemany(
                        """
                        INSERT INTO bilhetes
                            (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte,
                             tipster, aposta, descricao, stake, odd, resultado,
                             extraction_state, confianca, stake_usd, origem)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                        ON CONFLICT (dono, casa, parceiro, assinatura) DO NOTHING
                        """, registros)
                    for casa in casas:
                        await conn.execute(
                            'INSERT INTO parceiros (dono, casa, nome) VALUES ($1,$2,$3) '
                            'ON CONFLICT (dono, casa, nome) DO NOTHING',
                            dono, casa, PARCEIRO)
                    # o feed ordena por criado_em DESC; ancora na data para o
                    # atraso entrar DEPOIS das 956 do tracker, em ordem
                    await conn.execute(
                        """
                        WITH ordered AS (
                            SELECT id, ROW_NUMBER() OVER (ORDER BY id ASC) AS rn,
                                   COUNT(*) OVER () AS total
                            FROM bilhetes WHERE dono=$1 AND codigo_bilhete = ANY($2::text[])
                        )
                        UPDATE bilhetes b
                        SET criado_em = NOW() - ((o.total - o.rn) * INTERVAL '1 second')
                        FROM ordered o WHERE b.id = o.id
                        """, dono, codigos)
                # ── A CONTAGEM É GATE, não enfeite ──────────────────────────
                # O `ON CONFLICT DO NOTHING` engole linha em silêncio, e a
                # contagem TOTAL do dono não denuncia isso — ela cresce de
                # qualquer jeito. Confira a FAIXA contra o que foi mandado.
                #
                # Isto não é hipótese: numa medição posterior à primeira
                # gravação faltavam 6 desta faixa (190 de 196) com o total
                # parecendo certo, e quem acusou foi o script de atribuição de
                # autor, que confere código a código. A causa não ficou provada;
                # o gate fica de qualquer forma, porque o modo de falha (linha
                # que some sem erro) é o que importa.
                gravadas = await conn.fetchval(
                    'SELECT COUNT(*) FROM bilhetes WHERE dono=$1 AND codigo_bilhete = ANY($2::text[])',
                    dono, codigos)
                if gravadas != len(registros):
                    faltam = await conn.fetch(
                        'SELECT c FROM unnest($2::text[]) AS c WHERE NOT EXISTS ('
                        '  SELECT 1 FROM bilhetes b WHERE b.dono=$1 AND b.codigo_bilhete=c)',
                        dono, codigos)
                    raise SystemExit(
                        f'✋ ABORTADO — mandei {len(registros)} linhas e o banco ficou com '
                        f'{gravadas}. Faltando: {[r["c"] for r in faltam][:10]}'
                    )
                n = await conn.fetchval('SELECT COUNT(*) FROM bilhetes WHERE dono=$1', dono)
                ab = await conn.fetchval(
                    "SELECT COUNT(*) FROM bilhetes WHERE dono=$1 AND extraction_state='aberta'", dono)
                print(f'\nOK — base de {dono}: {n} bilhetes ({ab} em aberto)')
                print(f'\n⚠ ÚLTIMO CÓDIGO: {rows[-1]["codigo"]}. Suba o contador do bot '
                      f'(/contador N no apoio) para além dele ANTES da 1ª aposta pelo bot.')
                return
            finally:
                await conn.close()
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'falhou após 3 tentativas: {last_err}')


def relatorio(rows: list[dict], dono: str):
    print(f'DONO={dono!r} | tipster={TIPSTER!r} | linhas: {len(rows)} | '
          f'mensagens: {len({r["msg"] for r in rows})}')
    print(f'período (evento): {min(r["_dt"] for r in rows):%d/%m/%Y} → '
          f'{max(r["_dt"] for r in rows):%d/%m/%Y} | '
          f'códigos {rows[0]["codigo"]} … {rows[-1]["codigo"]}')

    print('\ncasa:', dict(Counter(r['casa'] for r in rows).most_common()))
    print('esporte:', dict(Counter(r['esporte'] for r in rows).most_common()))
    print('aposta:', dict(Counter(categoria(r) for r in rows).most_common()))
    print('resultado:', dict(Counter(resultado(r) or '(aberta)' for r in rows).most_common()))
    print('extraction_state:', dict(Counter(
        estado_extracao(resultado(r), fmt_odd(r['odd'])) for r in rows)))
    print('por dia:', dict(sorted(Counter(r['data'] for r in rows).items())))

    sem_odd = [r for r in rows if not fmt_odd(r['odd'])]
    print(f'\nlinhas sem odd: {len(sem_odd)}')
    ruim = [r for r in rows if (_f(r['odd']) or 0) < 1.01]
    if ruim:
        print(f'⚠ {len(ruim)} linha(s) com odd < 1,01:')
        for r in ruim:
            print(f'    {r["codigo"]} | {descricao(r)[:60]} | @{r["odd"]}')

    cods = [r['codigo'] for r in rows]
    sigs = [assinatura(r) for r in rows]
    print(f'códigos: {len(set(cods))} únicos de {len(cods)}')
    print(f'assinaturas: {len(set(sigs))} únicas de {len(sigs)}')
    dup = [d for d, n in Counter(descricao(r) for r in rows).items() if n > 1]
    if dup:
        print(f'\n⚠ {len(dup)} descrição(ões) repetida(s) — conferir se são apostas '
              f'distintas (o código as separa, mas a leitura humana não):')
        for d in dup[:10]:
            print(f'    {d[:75]}')

    # ── GATE: a leitura dos prints contra a contagem CEGA dos emojis ─────────
    # `EMOJI_NO_EXPORT` foi contado por regex sobre as 79 mensagens do export,
    # sem olhar print nenhum. Se a minha leitura tivesse perdido ou inventado
    # uma marca, os números não fechariam. É a conferência mais barata que esta
    # fonte oferece, e a única que não depende de mim ter lido certo.
    #
    # PROVADO POR MUTAÇÃO (4 de 5 aplicadas e pegas): trocar um `W` por `L`,
    # trocar um `L` por aberta, remover uma linha e duplicar uma linha — o gate
    # quebra nas quatro.
    #
    # ⚠️ O QUE ELE **NÃO** COBRE: **valor**. Trocar a stake de uma linha
    # (`1.75` → `1.00`) passa reto — a mutação foi aplicada e escapou. O gate
    # conta MARCAS e LINHAS, não confere número. A conferência da stake é a que
    # foi feita a olho na leitura (a caixa de valor do print traz o R$ igual ao
    # `%` da legenda) e não é automatizável sem reler as 79 imagens. Odd e
    # confronto estão no mesmo caso.
    obs = Counter(resultado(r) or 'A' for r in rows)
    esp = {'L': EMOJI_NO_EXPORT['❌'], 'W': EMOJI_NO_EXPORT['✔️'],
           'A': EMOJI_NO_EXPORT['⌛'] + EMOJI_NO_EXPORT['sem marca']}
    print('\n— gate: marcas lidas × emojis contados no export —')
    for k, rot in (('L', '❌'), ('W', '✔️/✅'), ('A', '⌛ + sem marca')):
        ok = 'OK' if obs[k] == esp[k] else '✋ DIVERGE'
        print(f'  {rot:<16} export={esp[k]:>3} | lido={obs[k]:>3}   {ok}')
    if any(obs[k] != esp[k] for k in esp):
        raise SystemExit(
            '✋ ABORTADO — a leitura dos prints não bate com as marcas do export. '
            'Alguma linha foi perdida, duplicada ou lida com a marca errada.')

    liq = [r for r in rows if resultado(r)]
    ab = [r for r in rows if not resultado(r)]
    tur = sum(_f(r['stake']) or 0 for r in rows)
    tur_liq = sum(_f(r['stake']) or 0 for r in liq)
    p = sum(v for r in liq if (v := pl(r)) is not None)
    print(f'\nlinhas liquidadas: {len(liq)} | em aberto: {len(ab)}')
    print(f'turnover total (u):        {tur:>9,.2f}')
    print(f'turnover liquidado (u):    {tur_liq:>9,.2f}')
    print(f'P/L do que liquidou (u):   {p:>+9,.2f}')
    print(f'ROI do que liquidou:       {100 * p / tur_liq if tur_liq else 0:>+8.2f}%')
    print('  (o P/L do que está em aberto é indefinido de propósito — '
        'ele completa o resultado à mão)')

    print('\n— amostra (12 primeiras) —')
    for r in rows[:12]:
        print(f'  {r["codigo"]:<14} {r["data"]} | {r["esporte"]:<10} | '
              f'{categoria(r):<14} | {r["casa"]:<8} | {descricao(r)[:58]:<58} | '
              f'u={fmt_stake(r["stake"]):<5} @{fmt_odd(r["odd"]):<7} '
              f'{resultado(r) or "-"}')
    print('\n— amostra (6 últimas) —')
    for r in rows[-6:]:
        print(f'  {r["codigo"]:<14} {r["data"]} | {r["esporte"]:<10} | '
              f'{categoria(r):<14} | {r["casa"]:<8} | {descricao(r)[:58]:<58} | '
              f'u={fmt_stake(r["stake"]):<5} @{fmt_odd(r["odd"]):<7} '
              f'{resultado(r) or "-"}')


def main():
    ap = argparse.ArgumentParser(
        description='Planilha o atraso do canal Grego Tips - VIP (msg 969 → 1110).')
    ap.add_argument('--dono', required=True, help='USERNAME do cadastro')
    ap.add_argument('--go', action='store_true', help='escreve no banco (sem isto é DRY RUN)')
    a = ap.parse_args()

    rows = numerar(carregar())
    print(f'{"=" * 78}\n{"GRAVAÇÃO" if a.go else "DRY RUN"} — atraso do canal '
          f'Grego Tips - VIP\n{"=" * 78}')
    relatorio(rows, a.dono)
    if not a.go:
        print('\nDRY RUN — nada foi escrito. Repita com --go para gravar.')
        return
    carregar_env()
    if not os.environ.get('DATABASE_URL'):
        raise SystemExit('DATABASE_URL ausente (.env).')
    print()
    asyncio.run(gravar(rows, a.dono))


if __name__ == '__main__':
    main()

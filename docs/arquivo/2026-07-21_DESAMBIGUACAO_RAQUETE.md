# Desambiguação — Badminton × Tênis × Dardos (rosters Tier 1/2)

> **Status:** RELATÓRIO / BLOCOS PRONTOS PRA COLAR (não aplicado). Nada foi escrito nos MASTERs.
> Companheiro de [`PESQUISA_BADMINTON_2026.md`](PESQUISA_BADMINTON_2026.md).
> Rosters verificados por 3 agentes nos rankings **oficiais** (BWF jun/2026, PDC Order of Merit jul/2026).
> Objetivo: dar ao extrator listas de nomes + regras estruturais para separar os **3 esportes de alta colisão** (todos usam ML/H2H/Handicap/Over-Under entre dois indivíduos).

---

## 0. Por que este documento existe

Hoje já há confusão **Tênis ↔ Dardos** (o `MASTER_ESPORTES §7` já corrige vários casos inline com `(não confundir com dardista)`). Adicionar **Badminton** — terceiro esporte de raquete, que também fala "set" — sobe o risco de 2 para 3 vias. A base já tem o padrão de defesa (listas de "Referências auxiliares" + "Contextos auxiliares" + "Regra Crítica"). Este doc entrega esse trio para o Badminton **e** um mapa de colisão dos 3.

**Princípio herdado (não quebrar):** o desempate de raquete **nunca** cria um novo "ralo padrão". Quando não há sinal positivo, o padrão continua sendo **Tênis** (o circuito ITF tem ordens de magnitude mais atletas obscuros que BWF ou PDC). Badminton e Dardos só vencem o desempate **com sinal positivo** (liga, torneio, vocabulário ou nome na lista).

---

## 1. Âncora de decisão (ordem de prioridade — vale pra qualquer print de raquete/dardos)

1. **Liga/torneio** — o sinal mais barato e inequívoco:
   - **Badminton:** BWF, World Tour, Super 1000/750/500/300/100, All England, China/Malaysia/Indonesia/Japan/Denmark/India Open, Thomas/Uber/Sudirman Cup, World Championships (badminton).
   - **Tênis:** ATP, WTA, ITF, Challenger, Grand Slam, Wimbledon, Roland Garros, US/Australian Open.
   - **Dardos:** PDC, WDF, BDO, MODUS, Premier League Darts, World Matchplay, World Grand Prix, UK Open, Grand Slam of Darts.
2. **Vocabulário de placar:**
   - **Badminton:** pontos até **21** (teto 30) ou **15** (teto 21, a partir de 2027), `21-18`, `rally`, melhor de 3 **games**.
   - **Tênis:** `games`, `ace`, `break`, `tie-break`, `deuce`, `6-4 7-6`.
   - **Dardos:** `legs`, `checkout`, `180`, `oche`, `average`, `501`, `nine-darter`.
3. **Nome do jogador** (as listas do §2/§3) — apenas **reforço terciário**, nunca decisor único quando houver colisão (ver §4).

> ⚠️ **`set` sozinho não desambigua nada** — aparece nos 3 (dardos: sets de legs; tênis: sets de games; badminton: "game" chamado de "set" por algumas casas). Só vale combinado com um sinal acima.

---

## 2. ⏹ PRONTO PRA COLAR — `### Referências auxiliares — Badminton`

> Vai em `global/MASTER_ESPORTES_2026.md §7`, logo após a entrada `## Badminton` (ver bloco no §9.1 do PESQUISA_BADMINTON_2026). Mesmo formato das de Tênis/Dardos.
> **Regra de grafia (vale para TODA a lista):** casas escrevem nomes asiáticos de formas variadas — **sobrenome primeiro**, às vezes em **CAIXA ALTA**, com ou sem hífen (`An Se-young` = `An Seyoung` = `AN Se Young`). Indexar por qualquer token distintivo.

```markdown
### Referências auxiliares — Badminton

Utilizar os nomes abaixo como apoio de desambiguação em mercados ML/H2H. A lista não é exaustiva — **quando o atleta não estiver listado, usar conhecimento próprio do modelo para identificar o esporte** (ver §5 item 4). Complementar com sinais contextuais (BWF, Super 1000/750/500/300, All England, Thomas/Uber Cup, pontos até 21). Nomes asiáticos podem vir com sobrenome primeiro, em CAIXA ALTA e com hífen variável.

**Simples Masculino (MS) — BWF:**
- Shi Yuqi
- Kunlavut Vitidsarn
- Anders Antonsen
- Jonatan Christie
- Christo Popov
- Chou Tien-chen
- Alex Lanier
- Li Shifeng
- Victor Lai
- Lin Chun-yi
- Lakshya Sen
- Kodai Naraoka
- Alwi Farhan
- Loh Kean Yew
- Weng Hongyang
- Toma Junior Popov
- Koki Watanabe
- Panitchaphon Teeraratsakul
- Chi Yu-jen
- Kenta Nishimoto
- Ayush Shetty
- Yushi Tanaka
- Nhat Nguyen
- Rasmus Gemke
- Leong Jun Hao
- Lu Guangzu
- Jason Teh Jia Heng
- Brian Yang
- Yudai Okimoto
- Arnaud Merkle
- H. S. Prannoy
- Lee Chia-hao
- Moh. Zaki Ubaidillah
- Kidambi Srikanth
- Wang Tzu-wei
- Wang Zhengxing
- Jeon Hyeok-jin
- Magnus Johannesen
- Prahdiska Bagas Shujiwo
- Wang Po-wei
- Anthony Sinisuka Ginting
- Tharun Mannepalli
- Su Li-yang
- Justin Hoh
- Julien Carraggi
- Minoru Koga
- Kiran George

**Simples Feminino (WS) — BWF:**
- An Se-young
- Wang Zhiyi
- Akane Yamaguchi
- Chen Yufei
- Han Yue
- Putri Kusuma Wardani
- Ratchanok Intanon
- Pornpawee Chochuwong
- Tomoka Miyazaki
- P. V. Sindhu
- Chiu Pin-chien
- Nozomi Okuhara
- Michelle Li
- Mia Blichfeldt
- Sim Yu-jin
- Lin Hsiang-ti
- Line Christophersen
- Kim Ga-eun
- Riko Gunji
- Busanan Ongbamrungphan
- Line Højmark Kjærsfeldt
- Hina Akechi
- Pitchamon Opatniput
- Unnati Hooda
- Supanida Katethong
- Letshanaa Karupathevan
- Natsuki Nidaira
- Huang Yu-hsun
- Kirsty Gilmour
- Devika Sihag
- Wong Ling Ching
- Han Qianxi
- Tanvi Sharma
- Amalie Schulz
- Sung Shuo-yun
- Isharani Baruah
- Yeo Jia Min
- Polina Buhrova
- Manami Suizu
- Kaloyana Nalbantova
- Tung Ciou-tong
- Yvonne Li
- Hsu Wen-chi
- Wendy Zhang
- Shriyanshi Valishetty
- Julie Dawall Jakobsen

**Duplas (MD/WD/XD) — nomes individuais, BWF:**
- Aaron Chia
- Soh Wooi Yik
- Kim Won Ho
- Seo Seung Jae
- Fajar Alfian
- Muhammad Shohibul Fikri
- Satwiksairaj Rankireddy
- Chirag Shetty
- Liang Weikeng
- Wang Chang
- Goh Sze Fei
- Nur Izzuddin
- Man Wei Chong
- Tee Kai Wun
- Takuro Hoki
- Yugo Kobayashi
- Kim Astrup
- Anders Skaarup Rasmussen
- Ben Lane
- Sean Vendy
- Wang Chi-lin
- Toma Junior Popov
- Liu Shengshu
- Tan Ning
- Baek Ha Na
- Lee So Hee
- Yuki Fukushima
- Mayu Matsumoto
- Pearly Tan
- Thinaah Muralitharan
- Jia Yifan
- Zhang Shuxian
- Kim Hye Jeong
- Kong Hee Yong
- Chiharu Shida
- Arisa Higashino
- Gabriela Stoeva
- Stefani Stoeva
- Feng Yanzhe
- Huang Dongping
- Jiang Zhenbang
- Wei Yaxin
- Mathias Christiansen
- Alexandra Bøje
- Chen Tang Jie
- Toh Ee Wei
- Dechapol Puavaranukroh
- Supissara Paewsampran
- Thom Gicquel
- Delphine Delrue
- Sapsiree Taerattanachai
- Jesper Toft
- Amalie Magelund
- Tanisha Crasto
- Dhruv Kapila
- Yuta Watanabe
```

> **Nota de escopo:** a lista de duplas acima é o núcleo (top ~15 pares por disciplina, achatado). O roster completo top-30 de MD/WD/XD (~150 nomes) está no §3 deste doc — cole mais nomes se quiser cobertura maior; o núcleo já pega quem tem liquidez em Super 300+.

---

## 3. Roster completo top-30 de duplas (banco de nomes — cole conforme precisar)

*(Fonte: BWF via badminton-navi, jun/2026, top-10 cruzado com Wikipedia 21/07/2026. Postos MD#25, XD#8, XD#20 não vieram na fonte pública — omitidos, não inventados.)*

**Duplas Masculinas (MD):** Kim Won Ho/Seo Seung Jae (KOR) · Fajar Alfian/Shohibul Fikri (INA) · Aaron Chia/Soh Wooi Yik (MAS) · Satwiksairaj Rankireddy/Chirag Shetty (IND) · Liang Weikeng/Wang Chang (CHN) · Goh Sze Fei/Nur Izzuddin (MAS) · Sabar Karyaman Gutama/Moh Reza Pahlevi Isfahani (INA) · Man Wei Chong/Tee Kai Wun (MAS) · Takuro Hoki/Yugo Kobayashi (JPN) · Raymond Indra/Nikolaus Joaquin (INA) · Chen Boyang/Liu Yi (CHN) · Ben Lane/Sean Vendy (ENG) · Chiu Hsiang Chieh/Wang Chi-lin (TPE) · Kim Astrup/Anders Skaarup Rasmussen (DEN) · Daniel Lundgaard/Mads Vestergaard (DEN) · Lee Jhe-Huei/Yang Po-Hsuan (TPE) · Kang Min Hyuk/Ki Dong Ju (KOR) · Wan Arif Shaharuddin/Yap Roy King (MAS) · Lee Fang-Chih/Lee Fang-Jen (TPE) · Christo Popov/Toma Junior Popov (FRA) · Leo Rolly Carnando/Bagas Maulana (INA) · Kang Khai Xing/Aaron Tai (MAS) · Kakeru Kumagai/Hiroki Nishi (JPN) · Nur Azriyn Ayub/Tan Wee Kiong (MAS) · Liu Kuang Heng/Yang Po Han (TPE) · Hariharan Amsakarunan/Arjun M.R. (IND) · Hiroki Midorikawa/Kyohei Yamashita (JPN) · Rian Ardianto/Rahmat Hidayat (INA) · Hu Ke Yuan/Lin Xiang Yi (CHN)

**Duplas Femininas (WD):** Liu Shengshu/Tan Ning (CHN) · Baek Ha Na/Lee So Hee (KOR) · Yuki Fukushima/Mayu Matsumoto (JPN) · Pearly Tan/Thinaah Muralitharan (MAS) · Jia Yifan/Zhang Shuxian (CHN) · Kim Hye Jeong/Kong Hee Yong (KOR) · Rin Iwanaga/Kie Nakanishi (JPN) · Hsieh Pei Shan/Hung En-Tzu (TPE) · Li Yi Jing/Luo Xumin (CHN) · Gabriela Stoeva/Stefani Stoeva (BUL) · Rachel Allessya Rose/Febi Setianingrum (INA) · Rui Hirokami/Sayaka Hobara (JPN) · Hsu Yin-Hui/Lin Jhih Yun (TPE) · Arisa Higashino/Chiharu Shida (JPN) · Febriana Kusuma/Meilysa Trias Puspitasari (INA) · Hsu Ya Ching/Sung Yu-Hsuan (TPE) · Kaho Osawa/Mai Tanabe (JPN) · Jeong Na Eun/Lee Eun Ji (KOR) · Chang Ching Hui/Yang Ching Tun (TPE) · Amalia Cahaya Pratiwi/Siti Fadia Silva Ramadhanti (INA) · Ririna Hiramoto/Kokona Ishikawa (JPN) · Ong Xin Yee/Carmen Ting (MAS) · Margot Lambert/Camille Pognante (FRA) · Hinata Suzuki/Nao Yamakita (JPN) · Hu Ling Fang/Jheng Yu Chieh (TPE) · Polina Buhrova/Yevheniia Kantemyr (UKR) · Isyana Meida/Rinjani Nastine (INA) · Luo Yi/Wang Ting Ge (CHN) · Lin Xiao Min/Wang Yu Qiao (TPE) · Hathaithip Mijad/Napapakorn Tungkasatan (THA)

**Duplas Mistas (XD):** Feng Yanzhe/Huang Dongping (CHN) · Jiang Zhenbang/Wei Yaxin (CHN) · Mathias Christiansen/Alexandra Bøje (DEN) · Chen Tang Jie/Toh Ee Wei (MAS) · Dechapol Puavaranukroh/Supissara Paewsampran (THA) · Thom Gicquel/Delphine Delrue (FRA) · Guo Xinwa/Chen Fanghui (CHN) · Jafar Hidayatullah/Felisha Pasaribu (INA) · Cheng Xing/Zhang Chi (CHN) · Ye Hong Wei/Nicole Gonzales Chan (TPE) · Goh Soon Huat/Shevon Jemie Lai (MAS) · Ruttanapak Oupthong/Kwanchanok Sudjaipraparat (THA) · Pakkapon Teeraratsakul/Sapsiree Taerattanachai (THA) · Hiroki Midorikawa/Natsu Saito (JPN) · Yuichi Shimogami/Sayaka Hobara (JPN) · Amri Syahnawi/Nita Violina Marwah (INA) · Jesper Toft/Amalie Magelund (DEN) · Yang Po-Hsuan/Hu Ling Fang (TPE) · Dhruv Kapila/Tanisha Crasto (IND) · Adnan Maulana/Indah Cahya Sari Jamil (INA) · Mads Vestergaard/Christine Busch (DEN) · Marwan Faza/Aisyah Salsabila Pranata (INA) · Pang Ron Hoo/Cheng Su Yin (MAS) · Chen Cheng Kuan/Hsu Yin-Hui (TPE) · Marvin Seidel/Thuc Phuong Nguyen (GER) · Jimmy Wong/Lai Pei Jing (MAS) · Rasmus Espersen/Amalie Kudsk (DEN) · Yuta Watanabe/Maya Taguchi (JPN)

---

## 4. Mapa de colisão — os únicos nomes que precisam de regra dura

A boa notícia: **Badminton quase não colide** com Tênis nem Dardos por nome inteiro. Os riscos são de **sobrenome isolado**.

### 4a. Badminton ↔ Tênis (risco real: sobrenomes chineses/coreanos)
Quando o print mostra **só o sobrenome**, estes colidem com tenistas chineses de elite (WTA/ATP). O **nome completo + liga BWF** desempata; sobrenome sozinho **nunca** decide:

| Sobrenome | Badminton | Tênis (colisão) |
|---|---|---|
| **Wang** | Wang Zhiyi, Wang Tzu-wei, Wang Chang | Wang Xinyu, Wang Yafan (WTA) |
| **Zhang** | Zhang Shuxian, Wendy Zhang | Zhang Zhizhen (ATP) |
| **Chen** | Chen Yufei, Chen Tang Jie | (chineses ITF) |
| **Li** | Michelle Li, Yvonne Li, Li Shifeng | Li Zhe / chineses ITF |
| **Lin / Liu / Han / Huang** | vários | chineses ITF |
| **Lee / Kim / Seo** | duplas coreanas | coreanos ITF |
| **Popov** | Christo Popov, Toma Junior Popov (FRA) | *(sem tenista de elite atual; risco baixo — mas note Dmitry Popko, grafia próxima)* |
| **Nguyen** | Nhat Nguyen (IRL) | Nguyens do circuito ITF |

**Regra:** nomes chineses/coreanos/taiwaneses **surname-first em CAIXA ALTA** (`SHI Yuqi`, `WANG Zhiyi`, `AN Se Young`) são típicos de badminton **quando há contexto BWF**; sem contexto, exigir o nome completo antes de decidir raquete.

### 4b. Badminton ↔ Dardos
**Colisão desprezível.** Topo do badminton é asiático/nórdico/francês/indiano; topo dos dardos é britânico/holandês/alemão. Não há choque forte de sobrenome. Um `180`/`checkout`/`leg`/`PDC` no print resolve na hora.

### 4c. Tênis ↔ Dardos (JÁ existe na base — reforço)
Continua sendo a colisão mais perigosa. Os **5 sobrenomes** que exigem sinal de liga/vocabulário antes de decidir (nunca pelo nome só):

| Sobrenome | Dardos (PDC) | Tênis |
|---|---|---|
| **Anderson** | Gary Anderson | Kevin Anderson |
| **Evans** | Ricky Evans | Dan Evans |
| **Williams** | Scott Williams | Serena/Venus Williams |
| **Wade** | James Wade | Virginia Wade |
| **Smith** | Michael/Ross Smith | (genérico, alta frequência) |

*(O `MASTER_ESPORTES §7` já anota vários tenistas ITF com `(não confundir com dardista)`. Recomendo estender essa nota aos 5 acima se ainda não estiverem cobertos.)*

---

## 5. ⏹ PRONTO PRA COLAR — `### Contextos auxiliares — Badminton`

```markdown
### Contextos auxiliares — Badminton

Os seguintes termos fortalecem identificação como Badminton:

**Termos de mercado / placar:**
- rally
- game (parcial; algumas casas chamam de "set" ou "jogo")
- melhor de 3 games
- pontos até 21 (teto 30) — ou até 15 (teto 21) a partir de 2027
- 21-18 / 21-15 / 24-22 (placar de game)

**Ligas e torneios:**
- BWF
- BWF World Tour
- Super 1000 / 750 / 500 / 300 / 100
- All England Open
- China Open / Malaysia Open / Indonesia Open / Japan Open / Denmark Open / India Open
- Thomas Cup / Uber Cup / Sudirman Cup
- World Championships (Badminton)

**Disciplinas (notação):**
- MS (simples masc.) / WS (simples fem.) / MD (duplas masc.) / WD (duplas fem.) / XD (duplas mistas)
```

---

## 6. ⏹ PRONTO PRA COLAR — `### Regra Crítica — Badminton vs Tênis vs Dardos`

```markdown
### Regra Crítica — Badminton vs Tênis vs Dardos

Os três são esportes de confronto individual (ou duplas) com alta colisão em ML/H2H/Handicap/Over-Under. Desambiguar SEMPRE por sinal positivo — nunca só pelo nome.

Regras obrigatórias (em ordem de prioridade):

1. `legs` / `checkout` / `180` / `oche` / `average` / `PDC` / `WDF` / `MODUS` → **Dardos** (prioridade máxima)
2. `games` / `ace` / `break` / `tie-break` / `deuce` / `ATP` / `WTA` / `ITF` / Grand Slam → **Tênis** (prioridade máxima)
3. `BWF` / `Super 1000/750/500/300` / `All England` / `China Open` / `Thomas Cup` / `Uber Cup` / `rally` / pontos até 21 (teto 30) → **Badminton** (prioridade máxima)
4. Participante na lista auxiliar de Dardos → Dardos · de Badminton → Badminton · de Tênis → Tênis
5. `set` SOZINHO NÃO desambigua (aparece nos três) — só vale combinado com um sinal acima.

**Regra de desempate — atleta não identificado:**
Quando o confronto for entre dois individuais/duplas em ML/H2H, nenhum identificável, e NÃO houver sinal positivo de Dardos nem de Badminton, o esporte padrão é **Tênis** (o circuito ITF tem ordens de magnitude mais atletas de nicho que BWF ou PDC). **Nunca** usar Badminton nem Dardos como padrão de desempate — ambos exigem sinal positivo.

**Notação de duplas `X/Y v W/Z`:** por padrão é **Tênis (duplas)** (ver Regra Crítica — Tênis vs Padel); só vira **Badminton (duplas)** com sinal positivo de badminton (BWF, torneio, dupla na lista) e só vira **Dardos** com sinal de dardos.

Conflito genuinamente insolúvel:

```text
Outro
```
```

---

## 7. Confiança e lacunas

- **Rankings:** BWF **jun/2026** (badminton-navi, espelha o oficial), #1 confirmado em 21/07/2026 (Shi Yuqi / An Se-young); PDC Order of Merit **jul/2026** (dartrankings + Wikipedia). Confiança alta.
- **Cobertura simples:** 47/50 em MS e WS (a fonte pública pula 3 postos em cada — **não inventamos** os faltantes: MS #23/#28/#41, WS #25/#27/#30).
- **Doubles:** top-30 por disciplina; postos MD#25, XD#8, XD#20 omitidos (não vieram na fonte).
- **Fontes bloqueadas (403):** site oficial BWF, Flashscore, AiScore, Livesport — não deu pra usar como 3ª fonte; cruzamos badminton-navi × Wikipedia × Olympics.com.
- **Manutenção:** ranking de badminton gira devagar no topo (pool estável), mas convém **revisitar a cada ~6 meses**; duplas mudam mais que simples. O sistema já cai no "conhecimento do modelo" (§5 item 4) para quem não está na lista — a lista é atalho, não a única defesa.

---

*Rosters gerados por pesquisa automatizada nos rankings oficiais. Nenhuma edição aplicada aos MASTERs — aguardando revisão do Feca.*

# Recon de casa nova — o roteiro para quem TEM a conta

> **Para que serve:** ligar uma casa ao SharpenUp **sem que a gente tenha conta nela**.
> Quem tem a conta gasta 5 minutos e manda um arquivo. Não empresta login, não empresta
> senha, não instala nada.
>
> **Para quem lê do lado de cá:** o roteiro técnico é [`GUIA_CASA_SHARPENUP.md`](GUIA_CASA_SHARPENUP.md)
> (Fase 0). Este documento é o **texto para repassar ao tester** — está em linguagem de
> quem nunca abriu o F12 de propósito. A ferramenta é [`../tools/recon_casa.js`](../tools/recon_casa.js).

---

## Antes de pedir: o que o tester precisa saber

Peça **autorização explícita**, com estas três frases na mesa. Elas são verdade e ele
tem direito de saber antes, não depois:

1. **O arquivo contém o histórico de apostas dele.** É esse o dado que a gente precisa
   ler para ensinar o robô. Não dá para tirar — é o conteúdo.
2. **Não contém senha nem token.** O coletor apaga o valor de todo cabeçalho de
   credencial antes de salvar (guarda só o nome), e apaga campos de identidade que
   reconhece pelo nome — e-mail, CPF, telefone, nome. Essa limpeza é **por nome de
   campo** e não é infalível: se a casa chamar o CPF de outra coisa, passa.
3. **O arquivo vai para o repositório da Sharpen** (vira a "fixture" que trava a
   regressão da casa para sempre). Conferimos e anonimizamos à mão antes disso, mas o
   destino é esse.

Se ele topar, mande **duas coisas**: o arquivo `tools/recon_casa.js` (abre no Bloco de
Notas, é só texto) e o roteiro abaixo.

---

## Roteiro para o tester (pode copiar e colar como está)

> Preciso de uns 5 minutos seus no computador — **não no celular**, precisa ser no
> Chrome do PC. Você não vai instalar nada e não vai me mandar senha nenhuma.
>
> **1.** Entre na sua conta da casa e abra a página **"Minhas apostas"** (o histórico de
> bilhetes, onde aparecem as apostas ganhas e perdidas).
>
> **2.** Aperte **F12**. Abre um painel do lado ou embaixo. Clique na aba **Console**.
>
> **3.** Abra o arquivo que te mandei no Bloco de Notas, **selecione tudo** (Ctrl+A),
> **copie** (Ctrl+C) e **cole** dentro do Console (Ctrl+V). Aperte Enter.
>
> - Se o Chrome disser algo como *"Allow pasting"* / *"Warning: Don't paste code…"*,
>   digite `allow pasting` e dê Enter. Aí cole de novo.
>
> Ele responde **"coletor ligado"** em verde. Deu certo.
>
> **4.** Agora **use o site normalmente por uns 30 segundos**, sem fechar o F12. Faça
> estas quatro coisas:
>
> - clique na aba das apostas **resolvidas** (ganhas/perdidas);
> - clique na aba das apostas **em aberto**;
> - **role a lista até o fim**, ou clique em "carregar mais" / "mostrar mais"
>   **pelo menos duas vezes** — isso é o mais importante de todos;
> - abra o **detalhe de um bilhete** qualquer, se a casa deixar clicar.
>
> **5.** Volte no Console, digite `SharpenUpRecon.resumo()` e dê Enter. Aparece uma
> tabelinha. As linhas marcadas com **◆** são as que eu procuro.
>
> **6.** Digite `SharpenUpRecon.salvar()` e dê Enter. Vai baixar um arquivo
> `recon-<casa>-<data>.json`. **Me manda esse arquivo.**
>
> Pode fechar tudo depois. Se quiser desligar antes de fechar, digite
> `SharpenUpRecon.parar()`.

---

## O que precisa aparecer na amostra

O valor do arquivo está na **variedade**, não na quantidade. O ideal cobre:

| | Por quê |
|---|---|
| 1 aposta **ganha** | é onde a odd tem de bater com `retorno ÷ stake` |
| 1 aposta **perdida** | várias casas zeram a odd ou o stake justo na perdida (KTO, Jonbet, Stake) |
| 1 aposta **em aberto** | o retorno dela é *potencial* — quem lê errado marca vitória fantasma |
| 1 **múltipla** ou bet builder | é o que separa perna de bilhete |
| 1 com **boost**, se houver | muda a regra da odd |
| 1 **anulada / cashout**, se houver | o dinheiro sozinho não distingue V de W |

Se faltar alguma, o arquivo continua servindo — só deixa aquela armadilha sem trava no
harness. **Vale mais mandar o que tem do que esperar a amostra perfeita.**

---

## Quando der errado

| Sintoma | O que é |
|---|---|
| "Uncaught SyntaxError" ao colar | veio pedaço do arquivo. Copiar tudo de novo (Ctrl+A no Bloco de Notas) |
| Chrome não deixa colar | digitar `allow pasting` no Console, dar Enter, e colar de novo |
| `resumo()` volta vazio | a página foi **recarregada** depois de colar — o coletor morre no reload. Colar de novo e usar o site sem dar F5 |
| Nenhuma linha com **◆** | pode ser casa que usa nome esquisito de endereço. **Manda assim mesmo** — a marcação é palpite, o arquivo inteiro é que vale |
| O download não acontece | rodar `SharpenUpRecon.salvar()` de novo; se o Chrome bloquear, liberar o download no ícone da barra de endereços |
| Arquivo gigante (> 25 MB) | o coletor já corta sozinho. Se incomodar, `SharpenUpRecon.remover(<número da linha>)` tira uma captura do pacote |

---

## Do lado de cá, depois que o arquivo chegar

1. **Ler antes de qualquer coisa.** Conferir que não passou credencial nem identidade
   que a varredura por nome não pegou.
2. Extrair a resposta da lista de bilhetes para
   `extensor/harness/fixtures/<casa>.<endpoint>.json` — **só o payload**, não o pacote
   inteiro de recon.
3. Seguir a Fase 1 em diante do [`GUIA_CASA_SHARPENUP.md`](GUIA_CASA_SHARPENUP.md).
   Da Fase 0 à 6 **não é preciso sessão nenhuma**: o harness roda sem navegador e sem rede.
4. **A Fase 7 volta a precisar do tester** — e só dela: instalar o SharpenUp, conectar e
   clicar "Copiar bilhetes" uma vez. Enquanto isso não rodar na casa, não rodou.

> ⚠️ **O `params` e os NOMES dos headers são load-bearing; os valores não.** O inject
> aprende url + headers de uma requisição real dentro do navegador do dono, em tempo de
> execução (`nv_inject.js::capturarReq`). Saber que a casa exige `x-gw-application-name`
> é metade do recon; saber o valor do token dela não serve para nada aqui.

---

VERSÃO: 2026
ATUALIZADO: 2026-08-26 (sessão 298 — nasce com o `tools/recon_casa.js`)

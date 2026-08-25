#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Publica um aviso no grupo `Sharpen - Testers` E grava a MESMA nota no changelog da home.

POR QUE ESTE SCRIPT EXISTE
--------------------------
Avisar o grupo e atualizar a home eram dois atos separados, feitos à mão em momentos
diferentes. O primeiro nunca era esquecido (o Feca vê), o segundo sim — e a caixa
"SharpenUp — versão a versão" ficou 8 versões atrás duas vezes (s254 e s292). Aqui os
dois viram UMA operação: a mensagem publicada é, literalmente, o item que a home mostra.

USO
---
  # sempre comece pelo ensaio (padrão): mostra a mensagem e o item, não envia nada
  python scripts/avisar_testers.py --versao 0.6.53 --texto "Nova casa: **Betsson**." \
      --item "Capture com **Minhas Apostas** aberta."

  # com o "pode mandar" do Feca:
  python scripts/avisar_testers.py --versao 0.6.53 --texto "..." --enviar

  # novidade do painel (não é versão da extensão):
  python scripts/avisar_testers.py --novidade --titulo "Relatórios por tipster" \
      --texto "..." --enviar

  # o Feca decidiu NÃO avisar, mas a nota deve constar na home:
  python scripts/avisar_testers.py --versao 0.6.53 --texto "..." --so-changelog

REGRAS QUE ESTE SCRIPT OBEDECE (CLAUDE.md)
------------------------------------------
* Nunca envia sem `--enviar`. O padrão é ensaio — grupo real não tem desfazer.
* Confere o destino por `getChat` (id E título) antes de enviar, e aborta se divergir.
* Nunca chama `getUpdates` (brigaria com o polling do bot em produção).
* Falhou o envio: imprime o `description` da resposta e PARA. Não reenvia, não
  "testa de novo" — a segunda chamada publicaria o teste no grupo.
* Só grava no changelog depois do `ok=true` (ou com `--so-changelog`, que não envia).

DEPOIS DE RODAR: `git add app/changelog.json && git commit && git push`.
A home lê o arquivo do deploy; sem push, o grupo sabe e a home não.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# O console do Windows abre em cp1252 e a PRÉVIA da mensagem tem acento: sem isto o
# script morre justamente no passo em que o humano lê o que vai publicar.
for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
CHANGELOG = RAIZ / "app" / "changelog.json"
MANIFEST = RAIZ / "extensor" / "manifest.json"

# Grupo `Sharpen - Testers`. É grupo COMUM: se algum dia virar supergrupo o id passa a
# -100…, e o getChat abaixo acusa antes de qualquer envio.
CHAT_ID = "-5172183099"
CHAT_TITULO = "Sharpen - Testers"
ENV_BOT = Path.home() / "Downloads" / "BOTS" / "sharpen-bot" / ".env"

API = "https://api.telegram.org/bot{token}/{metodo}"


# ── Telegram ─────────────────────────────────────────────────────────────────
def ler_token() -> str:
    """BOT_TOKEN do .env do sharpen-bot. Fora do git, sempre — nunca hardcode."""
    if not ENV_BOT.is_file():
        sair(f"Não achei o .env do bot em {ENV_BOT}. Passe --token ou ajuste o caminho.")
    for linha in ENV_BOT.read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("BOT_TOKEN"):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sair(f"{ENV_BOT} não tem BOT_TOKEN.")


def chamar(token: str, metodo: str, payload: dict) -> dict:
    """POST em JSON — UTF-8 de ponta a ponta, sem shell no meio (a lição da s282: o
    curl do Windows mutilava o texto e o teste de diagnóstico foi parar no grupo)."""
    req = urllib.request.Request(
        API.format(token=token, metodo=metodo),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:            # 4xx traz o `description`, que é o diagnóstico
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": f"HTTP {e.code} sem corpo legível"}
    except Exception as e:                          # rede: não sabemos se publicou — não reenviar
        return {"ok": False, "description": f"falha de transporte: {e}"}


def conferir_destino(token: str) -> None:
    r = chamar(token, "getChat", {"chat_id": CHAT_ID})
    if not r.get("ok"):
        sair(f"getChat falhou: {r.get('description')}")
    chat = r.get("result") or {}
    if str(chat.get("id")) != CHAT_ID or (chat.get("title") or "") != CHAT_TITULO:
        sair(f"DESTINO DIVERGE — id={chat.get('id')} título={chat.get('title')!r}. Abortado.")
    print(f"destino conferido: {chat.get('title')} · id {chat.get('id')} · type {chat.get('type')}")


# ── Texto ────────────────────────────────────────────────────────────────────
def esc_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para_telegram(s: str) -> str:
    """`**x**` → <b>x</b>, com o resto escapado. Mesmo negrito que a home renderiza."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc_html(s))


def montar_mensagem(entrada: dict, versao: str | None) -> str:
    linhas: list[str] = []
    if versao:
        linhas.append(f"<b>SharpenUp {versao}</b>")
        linhas.append("")
    elif entrada.get("titulo"):
        linhas.append(f"<b>{esc_html(entrada['titulo'])}</b>")
        linhas.append("")
    if entrada.get("texto"):
        linhas.append(para_telegram(entrada["texto"]))
    for item in entrada.get("itens") or []:
        linhas.append("• " + para_telegram(item))
    if entrada.get("fecho"):
        linhas.append("")
        linhas.append(para_telegram(entrada["fecho"]))
    linhas.append("")
    linhas.append(
        "Atualize em sharpen.bet/extensao" if versao
        else "Já está no ar — é só recarregar a página."
    )
    return "\n".join(linhas)


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:48]


# ── Changelog ────────────────────────────────────────────────────────────────
def gravar(entrada: dict, versao: str | None) -> None:
    dados = json.loads(CHANGELOG.read_text(encoding="utf-8"))
    chave = "sharpenup" if versao else "novidades"
    lista = dados.setdefault(chave, [])
    # Republicar a mesma nota SUBSTITUI em vez de duplicar: o id é a identidade, e
    # duas linhas da mesma versão na home é pior que uma nota corrigida.
    lista[:] = [x for x in lista if x.get("id") != entrada["id"]]
    lista.insert(0, entrada)
    CHANGELOG.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"changelog: {chave} ← {entrada['id']} (agora com {len(lista)} itens)")


def sair(msg: str) -> "None":
    print(f"ABORTADO: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Avisa o grupo de testers e grava a nota na home.")
    ap.add_argument("--versao", help="versão do SharpenUp (ex.: 0.6.53). Sem ela, é novidade do painel.")
    ap.add_argument("--novidade", action="store_true", help="entrada da caixa Novidades (painel/site).")
    ap.add_argument("--titulo", help="título da novidade (só para --novidade).")
    ap.add_argument("--texto", default="", help="a linha principal. Aceita **negrito**.")
    ap.add_argument("--item", action="append", default=[], help="item de lista (repetível).")
    ap.add_argument("--fecho", help="parágrafo de fechamento (só novidade).")
    ap.add_argument("--data", help="AAAA-MM-DD (padrão: hoje).")
    ap.add_argument("--id", help="id da entrada (padrão: derivado da versão/título).")
    ap.add_argument("--enviar", action="store_true", help="publica de verdade. Sem isto, é ensaio.")
    ap.add_argument("--so-changelog", action="store_true", help="grava a nota SEM avisar o grupo.")
    ap.add_argument("--token", help="BOT_TOKEN (padrão: .env do sharpen-bot).")
    a = ap.parse_args()

    if not a.versao and not a.novidade:
        sair("diga --versao 0.6.53 (extensão) ou --novidade --titulo '…' (painel).")
    if a.versao and a.novidade:
        sair("--versao e --novidade são excludentes: a nota é de uma caixa só.")
    if a.novidade and not a.titulo:
        sair("--novidade exige --titulo.")
    if not a.texto and not a.item:
        sair("nota vazia: use --texto e/ou --item.")
    if a.enviar and a.so_changelog:
        sair("--enviar e --so-changelog são excludentes.")

    data = a.data or datetime.now().strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        sair(f"--data {data!r} não é AAAA-MM-DD.")

    if a.versao:
        v = a.versao.lstrip("v")
        if not re.fullmatch(r"\d+\.\d+\.\d+", v):
            sair(f"--versao {a.versao!r} não é X.Y.Z.")
        manifesto = json.loads(MANIFEST.read_text(encoding="utf-8")).get("version", "")
        if manifesto != v:
            # Nota de uma versão que não é a publicada quase sempre é bump esquecido —
            # ou nota escrita antes do bump. Nos dois casos o tester baixaria outra coisa.
            sair(f"o manifest.json está em {manifesto} e a nota é da {v}. Bumpe primeiro.")
        entrada = {"id": a.id or f"su-{v.replace('.', '')[-4:]}", "v": f"v{v}", "data": data}
    else:
        entrada = {"id": a.id or f"sharpen-{slug(a.titulo)}", "data": data,
                   "tag": "Sharpen", "titulo": a.titulo}
    if a.texto:
        entrada["texto"] = a.texto
    if a.item:
        entrada["itens"] = a.item
    if a.fecho:
        entrada["fecho"] = a.fecho

    msg = montar_mensagem(entrada, a.versao)
    print("\n─── mensagem ao grupo ───")
    print(msg)
    print("--- item da home ---")
    print(json.dumps(entrada, ensure_ascii=False, indent=2))
    print()

    if a.so_changelog:
        gravar(entrada, a.versao)
        print("nada foi enviado ao grupo (--so-changelog).")
    elif not a.enviar:
        print("ENSAIO — nada foi enviado e nada foi gravado. Repita com --enviar.")
        return
    else:
        token = a.token or ler_token()
        conferir_destino(token)
        r = chamar(token, "sendMessage",
                   {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                    "disable_web_page_preview": True})
        if not r.get("ok"):
            # NÃO reenviar e NÃO "testar" de novo: o description já diz a causa.
            sair(f"sendMessage falhou: {r.get('description')} — nada foi gravado no changelog.")
        print(f"publicado · message_id {r.get('result', {}).get('message_id')}")
        gravar(entrada, a.versao)

    print("\nAgora: git add app/changelog.json && git commit -m '...' && git push")
    print("(sem push, o grupo sabe da novidade e a home não.)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Monitor de cupons — checa a cada minuto se os cupons divulgados continuam ativos.
Se um cupom cair, publica o aviso de "CUPOM ENCERRADO" respondendo ao post original
no Telegram e avisa você no chat de administração.

Uso:
  pip install requests
  export TELEGRAM_BOT_TOKEN="..."        # token do @BotFather
  export TELEGRAM_CHANNEL_ID="@seucanal" # canal onde os posts foram enviados
  export TELEGRAM_ADMIN_CHAT_ID="..."    # seu chat pessoal com o bot (alertas)
  python monitor_cupons.py               # roda em loop, a cada 60s
  python monitor_cupons.py --uma-vez     # roda só uma checagem
  python monitor_cupons.py --simular     # não envia nada, só mostra no terminal
"""
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ARQ_CUPONS = Path("cupons.json")
ARQ_HISTORICO = Path("historico_cupons.csv")
INTERVALO_SEG = 60
FALHAS_PARA_CANCELAR = 3  # nº de checagens seguidas sem encontrar o cupom
JANELA_TEXTO = 300        # caracteres ao redor do código analisados
MARCAS_EXPIRADO = re.compile(
    r"expirad|esgotad|encerrad|vencid|indispon|n[aã]o (est[aá]|funciona)|outofstock",
    re.IGNORECASE,
)
HEADERS = {"User-Agent": "Mozilla/5.0 (monitor-cupons; uso pessoal)"}

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CANAL = os.getenv("TELEGRAM_CHANNEL_ID", "")
ADMIN = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
SIMULAR = "--simular" in sys.argv


def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def carregar():
    return json.loads(ARQ_CUPONS.read_text(encoding="utf-8"))


def salvar(dados):
    ARQ_CUPONS.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def registrar(post, status, motivo):
    novo = not ARQ_HISTORICO.exists()
    with ARQ_HISTORICO.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["data_hora", "post", "titulo", "codigo", "loja", "status", "motivo"])
        w.writerow([agora(), post["post_id"], post["titulo"], post["codigo"],
                    post["loja"], status, motivo])


def telegram(chat_id, texto, responder_a=None):
    if SIMULAR or not TOKEN or not chat_id:
        print(f"[SIMULAÇÃO → {chat_id or 'sem chat'}]\n{texto}\n")
        return
    dados = {"chat_id": chat_id, "text": texto}
    if responder_a:
        dados["reply_parameters"] = json.dumps(
            {"message_id": responder_a, "allow_sending_without_reply": True})
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data=dados, timeout=15).raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao enviar no Telegram: {e}")


def baixar_fontes(cupons):
    """Baixa cada página de fonte uma única vez por ciclo."""
    urls = {u for c in cupons if c["status"] != "cancelado" for u in c.get("fontes", [])}
    paginas = {}
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            paginas[url] = r.text if r.ok else None
        except requests.RequestException:
            paginas[url] = None
    return paginas


def avaliar(cupom, paginas):
    """Retorna (status, motivo): ativo | suspeito | cancelado."""
    validade = cupom.get("valido_ate")
    if validade and datetime.now() > datetime.fromisoformat(validade):
        return "cancelado", f"validade encerrada em {validade}"

    codigo = cupom["codigo"].upper()
    encontrado, expirado, lidas = False, False, 0
    for url in cupom.get("fontes", []):
        html = paginas.get(url)
        if html is None:
            continue
        lidas += 1
        texto = re.sub(r"<[^>]+>", " ", html)
        for m in re.finditer(re.escape(codigo), texto.upper()):
            encontrado = True
            trecho = texto[max(0, m.start() - JANELA_TEXTO): m.end() + JANELA_TEXTO]
            if MARCAS_EXPIRADO.search(trecho):
                expirado = True
    if lidas == 0:
        return "sem_dados", "nenhuma fonte respondeu (falha de rede, não conta como queda)"
    if expirado and not encontrado_sem_marca(codigo, cupom, paginas):
        return "cancelado", "fonte marca o cupom como expirado/esgotado"
    if not encontrado:
        return "suspeito", "cupom sumiu das fontes"
    return "ativo", "listado nas fontes"


def encontrado_sem_marca(codigo, cupom, paginas):
    """True se alguma fonte lista o código sem marca de expirado."""
    for url in cupom.get("fontes", []):
        html = paginas.get(url)
        if not html:
            continue
        texto = re.sub(r"<[^>]+>", " ", html)
        for m in re.finditer(re.escape(codigo), texto.upper()):
            trecho = texto[max(0, m.start() - JANELA_TEXTO): m.end() + JANELA_TEXTO]
            if not MARCAS_EXPIRADO.search(trecho):
                return True
    return False


def aviso_cancelamento(c):
    alt = c.get("alternativa") or "fique de olho no próximo post aqui no canal"
    return (
        "⛔ CUPOM ENCERRADO\n\n"
        f"Referente ao post: \"{c['titulo']}\" ({c['post_id']}) — enviado em {c['enviado_em']}\n"
        f"🎟️ Cupom {c['codigo']} não está mais ativo.\n\n"
        f"✅ Alternativa: {alt}\n\n"
        "Desculpe o transtorno! 🙏"
    )


def ciclo():
    dados = carregar()
    cupons = dados["cupons"]
    paginas = baixar_fontes(cupons)

    for c in cupons:
        if c["status"] == "cancelado" and c.get("aviso_enviado"):
            continue
        status, motivo = avaliar(c, paginas)

        if status == "sem_dados":  # sem internet/fonte fora do ar: mantém o status
            print(f"  {c['post_id']} {c['codigo']}: {motivo}")
            continue

        if status == "suspeito":
            c["falhas"] = c.get("falhas", 0) + 1
            if c["falhas"] >= FALHAS_PARA_CANCELAR:
                status, motivo = "cancelado", f"ausente em {c['falhas']} checagens seguidas"
        elif status == "ativo":
            c["falhas"] = 0

        if status != c["status"]:
            registrar(c, status, motivo)
            telegram(ADMIN, f"🔔 {c['post_id']} | {c['codigo']} ({c['loja']}): "
                            f"{c['status']} → {status}\nMotivo: {motivo}")
            c["status"] = status

        if status == "cancelado" and not c.get("aviso_enviado"):
            telegram(CANAL, aviso_cancelamento(c), responder_a=c.get("telegram_message_id"))
            c["aviso_enviado"] = agora()

        c["ultima_checagem"] = agora()

    salvar(dados)
    ativos = sum(c["status"] == "ativo" for c in cupons)
    print(f"[{agora()}] {ativos}/{len(cupons)} cupons ativos")


if __name__ == "__main__":
    if "--uma-vez" in sys.argv:
        ciclo()
    else:
        while True:
            try:
                ciclo()
            except Exception as e:  # mantém o monitor vivo
                print(f"[{agora()}] erro no ciclo: {e}")
            time.sleep(INTERVALO_SEG)

#!/usr/bin/env python3
"""
Buscador de preços — compara o mesmo produto em Mercado Livre, Shopee e
Google Shopping, guarda o histórico e marca se o desconto é real.

Exemplos:
  python buscar.py "garrafa térmica"                 # busca uma vez
  python buscar.py "garrafa térmica" --demo          # testa com dados fictícios
  python buscar.py --lista produtos.txt              # busca todos da lista
  python buscar.py --lista produtos.txt --a-cada 60  # repete a cada 60 min
  python buscar.py "air fryer" --alvo 299.90         # avisa se ficar abaixo de R$ 299,90
"""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

import historico
import relatorio
from fontes import TODAS, Demo

RAIZ = Path(__file__).parent


def carregar_env():
    """Lê o arquivo .env (CHAVE=valor) sem precisar de biblioteca extra."""
    arq = RAIZ / ".env"
    if not arq.exists():
        return
    for linha in arq.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def avisar_telegram(texto):
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    if not (token and chat):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": texto}, timeout=15)
    except requests.RequestException:
        pass


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_termo(termo, fontes, limite, alvo=None):
    ofertas, erros = [], []
    for f in fontes:
        try:
            ofertas += f.buscar(termo, limite)
        except Exception as e:
            erros.append(f"{f.nome}: {e}")
    ofertas = [o for o in ofertas if o.preco > 0]

    # analisa contra o histórico ANTES de gravar a busca atual
    linhas = []
    for o in ofertas:
        selo, mediana, menor = historico.analisar(o)
        d = o.to_dict()
        d.update(selo=selo, mediana_30d=mediana, menor_30d=menor)
        linhas.append(d)
    historico.registrar(termo, ofertas)
    linhas.sort(key=lambda d: d["preco"])

    print(f"\n🔎 {termo} — {len(linhas)} ofertas ({datetime.now():%d/%m %H:%M})")
    for e in erros:
        print(f"   ⚠️  {e}")
    resumo = RAIZ / "saida" / "ultima_execucao.txt"
    resumo.parent.mkdir(exist_ok=True)
    with resumo.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%d/%m %H:%M} | {termo} | {len(linhas)} ofertas"
                + "".join(f"\n    erro: {e}" for e in erros) + "\n")
    for d in linhas[:10]:
        desc = f" (-{d['desconto_anunciado']}%)" if d["desconto_anunciado"] else ""
        print(f"   {brl(d['preco']):>12}{desc:<9} {d['fonte']:<16} {d['selo']:<26} {d['titulo'][:55]}")

    if linhas:
        csv_arq = relatorio.salvar_csv(termo, linhas)
        html_arq = relatorio.salvar_html(termo, linhas)
        print(f"   📄 {csv_arq.name}  |  🌐 {html_arq.name}")
        melhor = linhas[0]
        if alvo and melhor["preco"] <= alvo:
            msg = (f"🎯 {termo} abaixo do alvo!\n{brl(melhor['preco'])} em {melhor['fonte']}\n"
                   f"{melhor['titulo']}\n{melhor['link']}")
            print("   " + msg.replace("\n", " | "))
            avisar_telegram(msg)
    return linhas


def main():
    p = argparse.ArgumentParser(description="Buscador de preços")
    p.add_argument("termo", nargs="?", help="produto a buscar")
    p.add_argument("--lista", help="arquivo com um produto por linha (opcional: ';preço-alvo')")
    p.add_argument("--limite", type=int, default=10, help="ofertas por fonte")
    p.add_argument("--alvo", type=float, help="preço-alvo para alerta")
    p.add_argument("--a-cada", type=int, metavar="MIN", help="repete a busca a cada N minutos")
    p.add_argument("--demo", action="store_true", help="usa dados fictícios (sem chaves)")
    a = p.parse_args()

    carregar_env()
    if a.demo:
        fontes = [Demo()]
    else:
        fontes = [F() for F in TODAS]
        ativas = [f for f in fontes if f.configurada()]
        desligadas = [f.nome for f in fontes if not f.configurada()]
        if desligadas:
            print("Fontes sem credenciais (desligadas):", ", ".join(desligadas))
        fontes = ativas

    itens = []
    if a.lista:
        for linha in Path(a.lista).read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            termo, _, alvo = linha.partition(";")
            itens.append((termo.strip(), float(alvo.replace(",", ".")) if alvo.strip() else None))
    elif a.termo:
        itens.append((a.termo, a.alvo))
    else:
        p.print_help()
        sys.exit(1)

    while True:
        (RAIZ / "saida" / "ultima_execucao.txt").unlink(missing_ok=True)
        for termo, alvo in itens:
            buscar_termo(termo, fontes, a.limite, alvo)
        if not a.a_cada:
            break
        print(f"\n⏳ próxima rodada em {a.a_cada} min (Ctrl+C para parar)")
        time.sleep(a.a_cada * 60)


if __name__ == "__main__":
    main()

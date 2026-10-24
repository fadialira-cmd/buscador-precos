"""Gera CSV e página HTML com o comparativo de preços."""
import csv
import html
import os
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).parent / "saida"


def _nome(termo):
    base = "".join(ch if ch.isalnum() else "-" for ch in termo.lower()).strip("-")
    if os.getenv("RELATORIO_FIXO"):  # na nuvem: sobrescreve, guardando só o último
        return f"ultimo_{base}"
    return f"{datetime.now():%Y%m%d-%H%M}_{base}"


def salvar_csv(termo, linhas):
    PASTA.mkdir(exist_ok=True)
    arq = PASTA / f"{_nome(termo)}.csv"
    campos = ["fonte", "loja", "titulo", "preco", "preco_original", "desconto_anunciado",
              "selo", "mediana_30d", "menor_30d", "frete_gratis", "comissao",
              "avaliacao", "link"]
    with arq.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig abre certo no Excel
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore", delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    return arq


def _brl(v):
    if v is None:
        return ""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def salvar_html(termo, linhas):
    PASTA.mkdir(exist_ok=True)
    arq = PASTA / f"{_nome(termo)}.html"
    cards = []
    for i, l in enumerate(linhas):
        de = f'<s>{_brl(l["preco_original"])}</s> ' if l.get("preco_original") else ""
        desc = f' <span class="tag">-{l["desconto_anunciado"]}%</span>' if l.get("desconto_anunciado") else ""
        extras = " · ".join(x for x in [
            "frete grátis" if l.get("frete_gratis") else "",
            f'comissão {l["comissao"]}%' if l.get("comissao") else "",
            f'★ {l["avaliacao"]}' if l.get("avaliacao") else "",
            f'mediana 30d {_brl(l["mediana_30d"])}' if l.get("mediana_30d") else "",
        ] if x)
        cards.append(f"""
        <a class="card{' melhor' if i == 0 else ''}" href="{html.escape(l['link'])}" target="_blank" rel="noopener">
          <div class="topo"><span class="fonte">{html.escape(l['fonte'])}</span>
            <span class="selo">{html.escape(l['selo'])}</span></div>
          <div class="titulo">{html.escape(l['titulo'])}</div>
          <div class="preco">{de}<b>{_brl(l['preco'])}</b>{desc}</div>
          <div class="extras">{html.escape(extras)}</div>
        </a>""")
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Preços: {html.escape(termo)}</title>
<style>
:root{{--bg:#f6f5f2;--card:#fff;--txt:#1d1d1f;--sub:#6b6b70;--ok:#0a7d45;--borda:#e4e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141416;--card:#1f1f22;--txt:#f2f2f2;--sub:#a0a0a6;--ok:#4cd38a;--borda:#2e2e33}}}}
body{{margin:0;background:var(--bg);color:var(--txt);font:15px/1.45 system-ui,sans-serif;padding:24px 16px}}
h1{{font-size:22px;margin:0 0 4px}} p.sub{{color:var(--sub);margin:0 0 20px}}
.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));max-width:1100px}}
.card{{display:block;background:var(--card);border:1px solid var(--borda);border-radius:12px;padding:14px;color:inherit;text-decoration:none}}
.card.melhor{{border:2px solid var(--ok)}}
.topo{{display:flex;justify-content:space-between;font-size:12px;color:var(--sub)}}
.titulo{{margin:8px 0;font-weight:500}} .preco b{{font-size:20px;color:var(--ok)}}
s{{color:var(--sub)}} .tag{{background:var(--ok);color:#fff;border-radius:6px;padding:1px 6px;font-size:12px}}
.extras{{font-size:12px;color:var(--sub);margin-top:6px}}
</style></head><body>
<h1>Comparativo: {html.escape(termo)}</h1>
<p class="sub">{len(linhas)} ofertas · ordenadas do menor preço · gerado em {datetime.now():%d/%m/%Y %H:%M}</p>
<div class="grid">{''.join(cards)}</div></body></html>"""
    arq.write_text(pagina, encoding="utf-8")
    return arq

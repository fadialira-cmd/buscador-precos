"""Histórico de preços em SQLite — é o que separa promoção real de desconto inflado."""
import re
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path

ARQ = Path(__file__).parent / "dados" / "historico.db"


def _conn():
    ARQ.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(ARQ)
    c.execute("""CREATE TABLE IF NOT EXISTS precos (
        chave TEXT, termo TEXT, fonte TEXT, titulo TEXT,
        preco REAL, preco_original REAL, link TEXT, data TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chave ON precos(chave, data)")
    return c


def chave(oferta):
    """Identifica o mesmo produto entre buscas (id da loja ou título normalizado)."""
    ident = oferta.extra.get("id") if oferta.extra else None
    if ident:
        return f"{oferta.fonte}:{ident}"
    titulo = re.sub(r"[^a-z0-9]+", " ", oferta.titulo.lower()).strip()
    return f"{oferta.fonte}:{titulo[:80]}"


def registrar(termo, ofertas):
    agora = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        c.executemany("INSERT INTO precos VALUES (?,?,?,?,?,?,?,?)", [
            (chave(o), termo, o.fonte, o.titulo, o.preco, o.preco_original, o.link, agora)
            for o in ofertas])


def analisar(oferta, dias=30):
    """Compara o preço atual com a mediana dos últimos `dias`.
    Retorna (selo, mediana, menor_preco_historico)."""
    desde = (datetime.now() - timedelta(days=dias)).isoformat()
    with _conn() as c:
        precos = [p for (p,) in c.execute(
            "SELECT preco FROM precos WHERE chave=? AND data>=?", (chave(oferta), desde))]
    if len(precos) < 3:
        return "sem histórico", None, None
    mediana = statistics.median(precos)
    menor = min(precos)
    if oferta.preco <= menor and oferta.preco < mediana:
        return "🔥 menor preço do período", mediana, menor
    if oferta.preco <= mediana * 0.90:
        return "✅ promoção real", mediana, menor
    if (oferta.desconto_anunciado or 0) >= 20 and oferta.preco >= mediana * 0.97:
        return "⚠️ desconto inflado", mediana, menor
    return "preço normal", mediana, menor

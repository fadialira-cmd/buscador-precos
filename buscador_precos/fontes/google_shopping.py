"""Google Shopping via SerpApi (serpapi.com) — compara preços de várias lojas.

Precisa de SERPAPI_KEY no .env (há plano gratuito com cota mensal).
Os links não são de afiliado; servem para comparar e achar o menor preço.
"""
import os
import requests
from .base import Fonte, Oferta

URL = "https://serpapi.com/search.json"


class GoogleShopping(Fonte):
    nome = "Google Shopping"

    def __init__(self):
        self.key = os.getenv("SERPAPI_KEY", "")

    def configurada(self):
        return bool(self.key)

    def buscar(self, termo, limite=10):
        r = requests.get(URL, params={
            "engine": "google_shopping", "q": termo, "gl": "br", "hl": "pt-br",
            "location": "Brazil", "api_key": self.key}, timeout=30)
        r.raise_for_status()
        ofertas = []
        for it in r.json().get("shopping_results", [])[:limite]:
            preco = it.get("extracted_price")
            if preco is None:
                continue
            ofertas.append(Oferta(
                fonte=self.nome,
                titulo=it.get("title", ""),
                preco=float(preco),
                preco_original=it.get("extracted_old_price"),
                link=it.get("product_link") or it.get("link", ""),
                loja=it.get("source", ""),
                imagem=it.get("thumbnail", ""),
                avaliacao=it.get("rating"),
            ))
        return ofertas
